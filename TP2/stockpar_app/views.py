from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Cotizacion, Producto, Presupuesto, DetallePresupuesto

def index(request):
    cotizacion_actual = Cotizacion.objects.order_by('-fecha_hora').first()
    productos = Producto.objects.all().order_by('descripcion')
    
    # Calculamos el precio en ARS para cada producto si existe una cotización
    productos_con_precio = []
    for p in productos:
        precio_ars = p.calcular_precio_ars(cotizacion_actual.valor_dolar) if cotizacion_actual else 0
        productos_con_precio.append({
            'producto': p,
            'precio_ars': precio_ars
        })

    context = {
        'cotizacion': cotizacion_actual,
        'productos_con_precio': productos_con_precio,
    }
    return render(request, 'stockpar_app/index.html', context)

def actualizar_cotizacion(request):
    if request.method == 'POST':
        valor = request.POST.get('valor_dolar')
        origen = request.POST.get('origen', 'Oficial')
        if valor:
            Cotizacion.objects.create(valor_dolar=Decimal(valor), origen=origen)
            messages.success(request, f'Cotización actualizada a ${valor} ARS ({origen}).')
    return redirect('index')

def lista_presupuestos(request):
    presupuestos = Presupuesto.objects.all().order_by('-fecha')
    return render(request, 'stockpar_app/lista_presupuestos.html', {'presupuestos': presupuestos})

def crear_presupuesto(request):
    cotizacion_actual = Cotizacion.objects.order_by('-fecha_hora').first()
    if not cotizacion_actual:
        messages.error(request, 'Primero debés cargar una cotización del dólar antes de crear presupuestos.')
        return redirect('index')

    productos = Producto.objects.filter(stock__gt=0).order_by('descripcion')

    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre_cliente')
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        if not nombre_cliente or not productos_ids:
            messages.error(request, 'Completá el nombre del cliente y agregá al menos un producto.')
            return redirect('crear_presupuesto')

        try:
            with transaction.atomic():
                presupuesto = Presupuesto.objects.create(
                    nombre_cliente=nombre_cliente,
                    cotizacion_aplicada=cotizacion_actual,
                    total_ars=0
                )
                total_general_ars = Decimal('0.00')

                for prod_id, cant_str in zip(productos_ids, cantidades):
                    if not prod_id or not cant_str:
                        continue
                    cantidad = int(cant_str)
                    if cantidad <= 0:
                        continue

                    producto = Producto.objects.select_for_update().get(id=prod_id)
                    
                    # Validamos y descontamos stock usando tu método del modelo
                    if not producto.descontar_stock(cantidad):
                        raise ValueError(f'Stock insuficiente para {producto.descripcion} (Disponible: {producto.stock}).')

                    precio_unit_ars = Decimal(str(producto.calcular_precio_ars(cotizacion_actual.valor_dolar)))
                    
                    detalle = DetallePresupuesto.objects.create(
                        presupuesto=presupuesto,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario_usd=producto.precio_usd,
                        precio_unitario_ars=precio_unit_ars
                    )
                    total_general_ars += Decimal(str(detalle.get_subtotal_ars()))

                if total_general_ars == 0:
                    raise ValueError('No se agregaron ítems válidos al presupuesto.')

                presupuesto.total_ars = total_general_ars
                presupuesto.save()
                messages.success(request, f'Presupuesto #{presupuesto.id} generado correctamente.')
                return redirect('detalle_presupuesto', presupuesto_id=presupuesto.id)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('crear_presupuesto')

    return render(request, 'stockpar_app/crear_presupuesto.html', {
        'cotizacion': cotizacion_actual,
        'productos': productos
    })

def detalle_presupuesto(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)
    return render(request, 'stockpar_app/detalle_presupuesto.html', {'presupuesto': presupuesto})