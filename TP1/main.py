from clases import Cotizacion, Producto, Presupuesto

print("--- INICIANDO SIMULACIÓN DE STOCKPAR ---\n")

# creo cotizacion inicial
cotiz = Cotizacion(id_cotizacion=1, valor_dolar=1200.0, origen="Oficial")

# creo productos en el catalogo
prod1 = Producto("FIL-01", "Filtro de Aceite Honda", precio_usd=10.0, porcentaje_margen=30.0, stock=15)
prod2 = Producto("PAST-02", "Pastillas de Freno Bosch", precio_usd=25.0, porcentaje_margen=25.0, stock=5)

# emito un presupuesto
presup1 = Presupuesto(id_presupuesto=101, nombre_cliente="Taller Mecánico Pérez", cotizacion_aplicada=cotiz)
presup1.agregar_item(prod1, cantidad=2)
presup1.agregar_item(prod2, cantidad=1)

presup1.mostrar_presupuesto()

# pruebo actualizacion del dolar
cotiz.actualizar_valor(nuevo_valor=1250.0, usuario="admin")

# nuevo presupuesto con dolar actualizado
presup2 = Presupuesto(id_presupuesto=102, nombre_cliente="Repuestos Juan", cotizacion_aplicada=cotiz)
presup2.agregar_item(prod1, cantidad=1)
presup2.mostrar_presupuesto()