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