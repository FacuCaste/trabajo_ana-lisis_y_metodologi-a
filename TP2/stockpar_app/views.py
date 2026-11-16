from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cotizacion, DetallePresupuesto, Presupuesto, Producto


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _texto_errores(error):
    """Convierte un ValidationError de Django en un texto para mostrar al usuario."""
    return " ".join(error.messages)


def _validar_producto(producto):
    """Aplica las reglas del modelo (full_clean) y que el margen no sea negativo.

    Lanza ValidationError si algo está mal. Si todo está bien, los campos del
    producto quedan convertidos a sus tipos correctos (Decimal, int).
    """
    producto.full_clean()
    if producto.porcentaje_margen < 0:
        raise ValidationError("El margen no puede ser negativo.")


def _leer_items(post):
    """Lee los ítems del formulario de presupuesto: devuelve [(producto_id, cantidad)].

    Lanza ValueError con un mensaje legible si hay algún dato inválido.
    """
    items = []
    for prod_id, cant_str in zip(post.getlist('producto_id[]'), post.getlist('cantidad[]')):
        if not prod_id:
            continue
        try:
            prod_id = int(prod_id)
        except ValueError:
            raise ValueError("Producto inválido.") from None
        try:
            cantidad = int(cant_str)
        except ValueError:
            raise ValueError("La cantidad debe ser un número entero.") from None
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        items.append((prod_id, cantidad))

    if not items:
        raise ValueError("Agregá al menos un producto al presupuesto.")
    return items


# ---------------------------------------------------------------------------
# Catálogo y cotización
# ---------------------------------------------------------------------------

def index(request):
    cotizacion = Cotizacion.objects.order_by('-fecha_hora').first()
    busqueda = request.GET.get('q', '').strip()

    productos = Producto.objects.all().order_by('codigo')
    if busqueda:
        productos = productos.filter(
            Q(codigo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    productos_con_precio = [
        {
            'producto': producto,
            'precio_ars': producto.calcular_precio_ars(cotizacion) if cotizacion else None,
        }
        for producto in productos
    ]

    return render(request, 'stockpar_app/index.html', {
        'cotizacion': cotizacion,
        'productos_con_precio': productos_con_precio,
        'busqueda': busqueda,
    })


def actualizar_cotizacion(request):
    if request.method == 'POST':
        nueva = Cotizacion(
            valor_dolar=request.POST.get('valor_dolar', ''),
            origen=request.POST.get('origen', 'Oficial'),
            usuario=request.user if request.user.is_authenticated else None,
        )
        try:
            nueva.full_clean()
            if nueva.valor_dolar <= 0:
                raise ValidationError("La cotización debe ser mayor a cero.")
        except ValidationError as error:
            messages.error(request, _texto_errores(error))
        else:
            nueva.save()
            messages.success(request, f"Cotización actualizada a ${nueva.valor_dolar} ARS.")
    return redirect('index')


def crear_producto(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        producto = Producto(
            codigo=codigo,
            descripcion=request.POST.get('descripcion', '').strip(),
            precio_usd=request.POST.get('precio_usd', ''),
            porcentaje_margen=request.POST.get('porcentaje_margen', '0'),
            stock=request.POST.get('stock', '0'),
        )

        if Producto.objects.filter(codigo=codigo).exists():
            messages.error(request, f"Ya existe un repuesto con el código {codigo}.")
        else:
            try:
                _validar_producto(producto)
            except ValidationError as error:
                messages.error(request, _texto_errores(error))
            else:
                producto.save()
                messages.success(request, f"Repuesto [{codigo}] agregado correctamente.")
    return redirect('index')


def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.descripcion = request.POST.get('descripcion', '').strip()
        producto.precio_usd = request.POST.get('precio_usd', '')
        producto.porcentaje_margen = request.POST.get('porcentaje_margen', '0')
        producto.stock = request.POST.get('stock', '0')

        try:
            _validar_producto(producto)
        except ValidationError as error:
            messages.error(request, _texto_errores(error))
        else:
            producto.save()
            messages.success(request, f"Repuesto [{producto.codigo}] actualizado.")
    return redirect('index')


def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        codigo = producto.codigo
        try:
            producto.delete()
        except ProtectedError:
            # DetallePresupuesto.producto usa on_delete=PROTECT: un repuesto que
            # ya figura en algún presupuesto no se puede borrar.
            messages.error(
                request,
                f"No se puede eliminar [{codigo}] porque figura en presupuestos existentes."
            )
        else:
            messages.warning(request, f"Repuesto [{codigo}] eliminado del catálogo.")
    return redirect('index')


# ---------------------------------------------------------------------------
# Presupuestos
# ---------------------------------------------------------------------------

def crear_presupuesto(request):
    cotizacion = Cotizacion.objects.order_by('-fecha_hora').first()
    if not cotizacion:
        messages.warning(request, "Primero debés cargar una cotización del dólar.")
        return redirect('index')

    productos = Producto.objects.filter(stock__gt=0).order_by('descripcion')

    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre_cliente', '').strip()

        try:
            if not nombre_cliente:
                raise ValueError("Ingresá el nombre del cliente.")
            if len(nombre_cliente) > 150:
                raise ValueError("El nombre del cliente no puede superar los 150 caracteres.")
            items = _leer_items(request.POST)

            # Todo o nada: si algo falla, no se guarda el presupuesto ni se toca el stock.
            with transaction.atomic():
                presupuesto = Presupuesto.objects.create(
                    nombre_cliente=nombre_cliente,
                    cotizacion_aplicada=cotizacion,
                    total_ars=Decimal('0.00')
                )
                total_general = Decimal('0.00')

                for producto_id, cantidad in items:
                    producto = Producto.objects.select_for_update().filter(id=producto_id).first()
                    if producto is None:
                        raise ValueError("Uno de los productos seleccionados ya no existe.")
                    if cantidad > producto.stock:
                        raise ValueError(
                            f"Stock insuficiente para {producto.descripcion} "
                            f"(disponible: {producto.stock})."
                        )

                    precio_unitario = producto.calcular_precio_ars(cotizacion)
                    DetallePresupuesto.objects.create(
                        presupuesto=presupuesto,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario_ars=precio_unitario
                    )
                    producto.stock -= cantidad
                    producto.save()
                    total_general += precio_unitario * cantidad

                presupuesto.total_ars = round(total_general, 2)
                presupuesto.save()
                messages.success(request, f"Presupuesto #{presupuesto.id} guardado y stock descontado.")
                return redirect('detalle_presupuesto', presupuesto_id=presupuesto.id)

        except ValueError as error:
            messages.error(request, str(error))

    return render(request, 'stockpar_app/crear_presupuesto.html', {
        'cotizacion': cotizacion,
        'productos': productos
    })


def lista_presupuestos(request):
    presupuestos = Presupuesto.objects.all().order_by('-fecha')
    return render(request, 'stockpar_app/lista_presupuestos.html', {
        'presupuestos': presupuestos
    })


def detalle_presupuesto(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)
    return render(request, 'stockpar_app/detalle_presupuesto.html', {
        'presupuesto': presupuesto
    })
