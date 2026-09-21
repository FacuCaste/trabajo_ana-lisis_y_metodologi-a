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
        if cantidad < self._stock:
            print(f"Error. Stock insuficiente para {self._descripcion}. Disponible: {self._stock}")
        
        self._stock -= cantidad
        return True