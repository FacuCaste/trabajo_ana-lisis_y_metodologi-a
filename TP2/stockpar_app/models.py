from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200)
    precio_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    porcentaje_margen = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"[{self.codigo}] {self.descripcion}"

    def calcular_precio_ars(self, cotizacion):
        """Precio de venta en ARS: precio base en USD + margen, convertido con la cotización dada."""
        return round(
            self.precio_usd * (1 + self.porcentaje_margen / Decimal('100')) * cotizacion.valor_dolar,
            2
        )

class Cotizacion(models.Model):
    valor_dolar = models.DecimalField(max_digits=10, decimal_places=2)
    origen = models.CharField(max_length=50, default="Oficial")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"${self.valor_dolar} ({self.origen})"

class Presupuesto(models.Model):
    nombre_cliente = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)
    cotizacion_aplicada = models.ForeignKey(Cotizacion, on_delete=models.PROTECT)
    total_ars = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Presupuesto #{self.id} - {self.nombre_cliente}"

class DetallePresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario_ars = models.DecimalField(max_digits=12, decimal_places=2)

    def get_subtotal_ars(self):
        return round(self.cantidad * self.precio_unitario_ars, 2)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.descripcion}"
