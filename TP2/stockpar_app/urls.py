from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('actualizar-cotizacion/', views.actualizar_cotizacion, name='actualizar_cotizacion'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('presupuestos/nuevo/', views.crear_presupuesto, name='crear_presupuesto'),
    path('presupuestos/', views.lista_presupuestos, name='lista_presupuestos'),
    path('presupuestos/<int:presupuesto_id>/', views.detalle_presupuesto, name='detalle_presupuesto'),
]