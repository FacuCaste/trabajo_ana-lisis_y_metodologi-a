from django.contrib import admin
from .models import Cotizacion, Producto, Presupuesto, DetallePresupuesto

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'valor_dolar', 'origen', 'fecha_hora')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'precio_usd', 'porcentaje_margen', 'stock')
    search_fields = ('codigo', 'descripcion')

class DetallePresupuestoInline(admin.TabularInline):
    model = DetallePresupuesto
    extra = 1

@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_cliente', 'fecha', 'total_ars')
    inlines = [DetallePresupuestoInline]
