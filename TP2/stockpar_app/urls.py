from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cotizacion/nueva/', views.actualizar_cotizacion, name='actualizar_cotizacion'),
    path('presupuestos/', views.lista_presupuestos, name='lista_presupuestos'),
    path('presupuestos/nuevo/', views.crear_presupuesto, name='crear_presupuesto'),
    path('presupuestos/<int:presupuesto_id>/', views.detalle_presupuesto, name='detalle_presupuesto'),
]