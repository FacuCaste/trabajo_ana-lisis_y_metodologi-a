from datetime import datetime

class Cotizacion:
    def __init__(self, id_cotizacion, valor_dolar, origen):        
        self._id_cotizacion = id_cotizacion
        self._fecha_hora = datetime.now()
        self._valor_dolar = valor_dolar
        self._origen = origen
    
    def get_valor_dolar(self):
        return self._valor_dolar
    
    def actualizar_valor(self, nuevo_valor, usuario):
        if nuevo_valor <= 0:
            print("Error: EL nuevo valor del dolar debe ser mayor a cero")
            return
        
        self._valor_dolar = nuevo_valor
        self._fecha_hora = datetime.now()
        print(f"Cotizacion actualizada a ${nuevo_valor} ARS por {usuario}")
        
class Producto:
    def __init__(self, codigo, descripcion, precio_usd, porcentaje_margen, stock):
        if precio_usd <= 0:
            print("Error: El precio en USD debe ser mayor a cero.")
            self._precio_usd = 1.0
        else:
            self._precio_usd = precio_usd
        
        self._codigo= codigo
        self._descripcion = descripcion
        self._porcentaje_margen = porcentaje_margen
        self._stock = stock
    
    def get_codigo(self):
        return self._codigo

    def get_descripcion(self):
        return self._descripcion

    def get_precio_usd(self):
        return self._precio_usd

    def get_stock(self):
        return self._stock
    
    def calcular_precio_ars(self, cotizacion_actual):
        precio_con_margen = self._precio_usd * (1 + (self._porcentaje_margen/100))
        precio_final_ars = precio_con_margen * cotizacion_actual.get_valor_dolar()
        return round(precio_final_ars,2)
        
    def descontar_stock(self, cantidad):
        if cantidad > self._stock:
            print(f"Error. Stock insuficiente para {self._descripcion}. Disponible: {self._stock}")
            return False
        
        self._stock -= cantidad
        return True
    
class DetallePresupuesto:
    def __init__(self, producto, cantidad, cotizacion):
        self._producto = producto
        self._cantidad = cantidad
        self._precio_unitario_usd = producto.get_precio_usd()
        self._precio_unitario_ars = producto.calcular_precio_ars(cotizacion)
        
        self._producto.descontar_stock(cantidad)

    def get_subtotal_ars(self):
        return round(self._precio_unitario_ars * self._cantidad, 2)

    def get_producto(self):
        return self._producto

    def get_cantidad(self):
        return self._cantidad

    def get_precio_unitario_ars(self):
        return self._precio_unitario_ars
    

class Presupuesto:
    def __init__(self, id_presupuesto, nombre_cliente, cotizacion_aplicada):
        self._id_presupuesto = id_presupuesto
        self._nombre_cliente = nombre_cliente
        self._fecha = datetime.now()
        self._cotizacion_aplicada = cotizacion_aplicada
        self._items = []
        self._total_ars = 0.0
        
    def agregar_item(self,producto, cantidad):
        detalle = DetallePresupuesto(producto, cantidad, self._cotizacion_aplicada)
        self._items.append(detalle)
        self._total_ars += detalle.get_subtotal_ars()
    
    def mostrar_presupuesto(self):
        print("\n==========================================")
        print(f" PRESUPUESTO N° {self._id_presupuesto}")
        print(f" Fecha: {self._fecha.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f" Cliente: {self._nombre_cliente}")
        print(f" Dólar aplicado: ${self._cotizacion_aplicada.get_valor_dolar()} ARS")
        print("------------------------------------------")
        print(" ÍTEMS:")
        for item in self._items:
            p = item.get_producto()
            print(f"  - [{p.get_codigo()}] {p.get_descripcion()}")
            print(f"    Cant: {item.get_cantidad()} x ${item.get_precio_unitario_ars()} ARS = ${item.get_subtotal_ars()} ARS")
        print("------------------------------------------")
        print(f" TOTAL GENERAL: ${round(self._total_ars, 2)} ARS")
        print("==========================================\n")
        