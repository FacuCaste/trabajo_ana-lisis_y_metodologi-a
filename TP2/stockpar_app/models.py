from django.db import models

class Cotizacion(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    valor_dolar = models.DecimalField(max_digits=10, decimal_places=2)
    origen = models.CharField(max_length=50, default="Oficial")

    def __str__(self):
        return f"USD 1 = ${self.valor_dolar} ARS ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"


class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=100)
    precio_usd = models.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_margen = models.DecimalField(max_digits=5, decimal_places=2, default=30.0)
    stock = models.IntegerField(default=0)

    def calcular_precio_ars(self, cotizacion_valor):
        precio_con_margen = float(self.precio_usd) * (1 + (float(self.porcentaje_margen) / 100))
        precio_final_ars = precio_con_margen * float(cotizacion_valor)
        return round(precio_final_ars, 2)

    def descontar_stock(self, cantidad):
        if cantidad > self.stock:
            return False
        self.stock -= cantidad
        self.save()
        return True

    def __str__(self):
        return f"[{self.codigo}] {self.descripcion}"


class Presupuesto(models.Model):
    nombre_cliente = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    cotizacion_aplicada = models.ForeignKey(Cotizacion, on_delete=models.PROTECT)
    total_ars = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Presupuesto #{self.id} - {self.nombre_cliente}"


class DetallePresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario_usd = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario_ars = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal_ars(self):
        return round(float(self.precio_unitario_ars) * self.cantidad, 2)