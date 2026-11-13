from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
from .models import Producto, Cotizacion, Presupuesto, DetallePresupuesto

def index(request):
    cotizacion = Cotizacion.objects.order_by('-fecha_hora').first()
    busqueda = request.GET.get('q', '').strip()

    productos = Producto.objects.all().order_by('codigo')
    if busqueda:
        productos = productos.filter(
            Q(codigo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    productos_con_precio = []
    for producto in productos:
        precio_ars = None
        if cotizacion:
            precio_ars = round(
                producto.precio_usd * (1 + producto.porcentaje_margen / Decimal('100')) * cotizacion.valor_dolar,
                2
            )
        productos_con_precio.append({
            'producto': producto,
            'precio_ars': precio_ars
        })

    return render(request, 'stockpar_app/index.html', {
        'cotizacion': cotizacion,
        'productos_con_precio': productos_con_precio,
        'busqueda': busqueda,
    })

def actualizar_cotizacion(request):
    if request.method == 'POST':
        valor = Decimal(request.POST.get('valor_dolar', '0'))
        origen = request.POST.get('origen', 'Oficial')
        usuario_actual = request.user if request.user.is_authenticated else None

        if valor > 0:
            Cotizacion.objects.create(
                valor_dolar=valor,
                origen=origen,
                usuario=usuario_actual
            )
            messages.success(request, f"Cotización actualizada a ${valor} ARS.")
        else:
            messages.error(request, "La cotización debe ser mayor a cero.")
    return redirect('index')

def crear_producto(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        descripcion = request.POST.get('descripcion', '').strip()
        precio_usd = Decimal(request.POST.get('precio_usd', '0'))
        porcentaje_margen = Decimal(request.POST.get('porcentaje_margen', '0'))
        stock = int(request.POST.get('stock', '0'))

        if precio_usd <= 0:
            messages.error(request, "El precio base en USD debe ser mayor a cero.")
        elif Producto.objects.filter(codigo=codigo).exists():
            messages.error(request, f"Ya existe un repuesto con el código {codigo}.")
        else:
            Producto.objects.create(
                codigo=codigo,
                descripcion=descripcion,
                precio_usd=precio_usd,
                porcentaje_margen=porcentaje_margen,
                stock=stock
            )
            messages.success(request, f"Repuesto [{codigo}] agregado correctamente.")
    return redirect('index')

def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        precio_usd = Decimal(request.POST.get('precio_usd', '0'))
        porcentaje_margen = Decimal(request.POST.get('porcentaje_margen', '0'))
        stock = int(request.POST.get('stock', '0'))
        descripcion = request.POST.get('descripcion', '').strip()

        if precio_usd <= 0:
            messages.error(request, "El precio base en USD debe ser mayor a cero.")
        else:
            producto.descripcion = descripcion
            producto.precio_usd = precio_usd
            producto.porcentaje_margen = porcentaje_margen
            producto.stock = stock
            producto.save()
            messages.success(request, f"Repuesto [{producto.codigo}] actualizado.")
    return redirect('index')

def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        codigo = producto.codigo
        producto.delete()
        messages.warning(request, f"Repuesto [{codigo}] eliminado del catálogo.")
    return redirect('index')

def crear_presupuesto(request):
    cotizacion = Cotizacion.objects.order_by('-fecha_hora').first()
    if not cotizacion:
        messages.warning(request, "Primero debés cargar una cotización del dólar.")
        return redirect('index')

    productos = Producto.objects.filter(stock__gt=0).order_by('descripcion')

    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre_cliente', '').strip()
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        try:
            with transaction.atomic():
                presupuesto = Presupuesto.objects.create(
                    nombre_cliente=nombre_cliente,
                    cotizacion_aplicada=cotizacion,
                    total_ars=Decimal('0.00')
                )
                total_general = Decimal('0.00')

                for prod_id, cant_str in zip(productos_ids, cantidades):
                    if not prod_id:
                        continue
                    cantidad = int(cant_str)
                    producto = Producto.objects.select_for_update().get(id=prod_id)

                    if cantidad > producto.stock:
                        raise ValueError(f"Stock insuficiente para {producto.descripcion}.")

                    precio_unitario = round(
                        producto.precio_usd * (1 + producto.porcentaje_margen / Decimal('100')) * cotizacion.valor_dolar,
                        2
                    )
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