from django.test import TestCase
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Cotizacion, DetallePresupuesto, Presupuesto, Producto


class BaseTestCase(TestCase):
    """Deja cargada una cotización de $1000 y un repuesto de USD 10 con 20% de margen."""

    def setUp(self):
        self.cotizacion = Cotizacion.objects.create(valor_dolar=Decimal('1000.00'))
        self.producto = Producto.objects.create(
            codigo='FIL-001',
            descripcion='Filtro de aceite',
            precio_usd=Decimal('10.00'),
            porcentaje_margen=Decimal('20.00'),
            stock=5,
        )

    def post_presupuesto(self, cliente='Ana', productos=None, cantidades=None):
        productos = [self.producto.id] if productos is None else productos
        cantidades = ['2'] if cantidades is None else cantidades
        return self.client.post(reverse('crear_presupuesto'), {
            'nombre_cliente': cliente,
            'producto_id[]': productos,
            'cantidad[]': cantidades,
        })


class ProductoModelTests(BaseTestCase):
    def test_precio_ars_aplica_margen_y_cotizacion(self):
        # 10 USD + 20% = 12 USD  ->  12 * 1000 = 12000 ARS
        self.assertEqual(self.producto.calcular_precio_ars(self.cotizacion), Decimal('12000.00'))

    def test_subtotal_del_detalle(self):
        presupuesto = Presupuesto.objects.create(
            nombre_cliente='Ana', cotizacion_aplicada=self.cotizacion
        )
        detalle = DetallePresupuesto.objects.create(
            presupuesto=presupuesto, producto=self.producto,
            cantidad=3, precio_unitario_ars=Decimal('12000.00'),
        )
        self.assertEqual(detalle.get_subtotal_ars(), Decimal('36000.00'))


class PaginasTests(BaseTestCase):
    def test_index_lista_productos_con_precio_ars(self):
        respuesta = self.client.get(reverse('index'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'FIL-001')

    def test_busqueda_filtra_por_codigo_o_descripcion(self):
        Producto.objects.create(
            codigo='BUJ-002', descripcion='Bujía', precio_usd=Decimal('5.00'), stock=1
        )
        respuesta = self.client.get(reverse('index'), {'q': 'buj'})
        self.assertContains(respuesta, 'BUJ-002')
        self.assertNotContains(respuesta, 'FIL-001')

    def test_lista_presupuestos_carga(self):
        self.assertEqual(self.client.get(reverse('lista_presupuestos')).status_code, 200)

    def test_detalle_inexistente_da_404(self):
        self.assertEqual(
            self.client.get(reverse('detalle_presupuesto', args=[999])).status_code, 404
        )


class CotizacionTests(BaseTestCase):
    def test_actualizar_cotizacion_crea_registro_nuevo(self):
        self.client.post(reverse('actualizar_cotizacion'),
                         {'valor_dolar': '1200.50', 'origen': 'Blue'})
        ultima = Cotizacion.objects.order_by('-fecha_hora', '-id').first()
        self.assertEqual(ultima.valor_dolar, Decimal('1200.50'))
        self.assertEqual(ultima.origen, 'Blue')
        self.assertEqual(Cotizacion.objects.count(), 2)  # se conserva el historial

    def test_cotizacion_cero_o_negativa_se_rechaza(self):
        for valor in ('0', '-5'):
            self.client.post(reverse('actualizar_cotizacion'), {'valor_dolar': valor})
        self.assertEqual(Cotizacion.objects.count(), 1)

    def test_cotizacion_con_texto_no_rompe(self):
        respuesta = self.client.post(reverse('actualizar_cotizacion'), {'valor_dolar': 'abc'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Cotizacion.objects.count(), 1)


class ProductoViewsTests(BaseTestCase):
    def datos(self, **cambios):
        datos = {'codigo': 'bat-003', 'descripcion': 'Batería', 'precio_usd': '80.00',
                 'porcentaje_margen': '30', 'stock': '4'}
        datos.update(cambios)
        return datos

    def test_crear_producto_guarda_codigo_en_mayusculas(self):
        self.client.post(reverse('crear_producto'), self.datos())
        self.assertTrue(Producto.objects.filter(codigo='BAT-003').exists())

    def test_codigo_duplicado_se_rechaza(self):
        self.client.post(reverse('crear_producto'), self.datos(codigo='fil-001'))
        self.assertEqual(Producto.objects.filter(codigo='FIL-001').count(), 1)

    def test_datos_invalidos_no_rompen_ni_guardan(self):
        invalidos = [
            {'precio_usd': 'abc'},
            {'precio_usd': '0'},
            {'precio_usd': '-3'},
            {'porcentaje_margen': '-10'},
            {'stock': '-1'},
            {'stock': 'x'},
            {'descripcion': ''},
        ]
        for cambio in invalidos:
            with self.subTest(cambio=cambio):
                respuesta = self.client.post(reverse('crear_producto'), self.datos(**cambio))
                self.assertEqual(respuesta.status_code, 302)
                self.assertFalse(Producto.objects.filter(codigo='BAT-003').exists())

    def test_editar_producto(self):
        self.client.post(reverse('editar_producto', args=[self.producto.id]), {
            'descripcion': 'Filtro nuevo', 'precio_usd': '12.00',
            'porcentaje_margen': '10', 'stock': '9',
        })
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.descripcion, 'Filtro nuevo')
        self.assertEqual(self.producto.precio_usd, Decimal('12.00'))
        self.assertEqual(self.producto.stock, 9)

    def test_editar_con_datos_invalidos_no_modifica(self):
        self.client.post(reverse('editar_producto', args=[self.producto.id]), {
            'descripcion': 'X', 'precio_usd': 'abc', 'porcentaje_margen': '10', 'stock': '9',
        })
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.descripcion, 'Filtro de aceite')

    def test_eliminar_producto_sin_presupuestos(self):
        self.client.post(reverse('eliminar_producto', args=[self.producto.id]))
        self.assertFalse(Producto.objects.filter(id=self.producto.id).exists())

    def test_no_se_puede_eliminar_producto_usado_en_presupuesto(self):
        self.post_presupuesto()
        respuesta = self.client.post(reverse('eliminar_producto', args=[self.producto.id]))
        self.assertEqual(respuesta.status_code, 302)  # antes: error 500
        self.assertTrue(Producto.objects.filter(id=self.producto.id).exists())


class PresupuestoTests(BaseTestCase):
    def test_sin_cotizacion_redirige_al_index(self):
        Cotizacion.objects.all().delete()
        respuesta = self.client.get(reverse('crear_presupuesto'))
        self.assertRedirects(respuesta, reverse('index'))

    def test_presupuesto_valido_calcula_total_y_descuenta_stock(self):
        respuesta = self.post_presupuesto(cantidades=['2'])
        presupuesto = Presupuesto.objects.get()
        self.assertRedirects(respuesta, reverse('detalle_presupuesto', args=[presupuesto.id]))
        self.assertEqual(presupuesto.total_ars, Decimal('24000.00'))
        self.assertEqual(presupuesto.items.count(), 1)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    def test_presupuesto_con_varios_items(self):
        otro = Producto.objects.create(
            codigo='BUJ-002', descripcion='Bujía', precio_usd=Decimal('5.00'),
            porcentaje_margen=Decimal('0'), stock=10,
        )
        self.post_presupuesto(productos=[self.producto.id, otro.id], cantidades=['1', '4'])
        # 12000*1 + 5000*4 = 32000
        self.assertEqual(Presupuesto.objects.get().total_ars, Decimal('32000.00'))

    def test_el_precio_queda_congelado_aunque_cambie_la_cotizacion(self):
        self.post_presupuesto(cantidades=['1'])
        Cotizacion.objects.create(valor_dolar=Decimal('2000.00'))
        detalle = DetallePresupuesto.objects.get()
        self.assertEqual(detalle.precio_unitario_ars, Decimal('12000.00'))
        self.assertEqual(Presupuesto.objects.get().total_ars, Decimal('12000.00'))

    def test_stock_insuficiente_no_guarda_nada(self):
        self.post_presupuesto(cantidades=['99'])
        self.assertEqual(Presupuesto.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_si_falla_un_item_se_revierte_todo(self):
        otro = Producto.objects.create(
            codigo='BUJ-002', descripcion='Bujía', precio_usd=Decimal('5.00'), stock=1,
        )
        self.post_presupuesto(productos=[self.producto.id, otro.id], cantidades=['2', '50'])
        self.assertEqual(Presupuesto.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)  # el primer ítem tampoco descontó

    def test_presupuesto_vacio_se_rechaza(self):
        self.post_presupuesto(productos=[''], cantidades=[''])
        self.assertEqual(Presupuesto.objects.count(), 0)

    def test_cliente_vacio_se_rechaza(self):
        self.post_presupuesto(cliente='   ')
        self.assertEqual(Presupuesto.objects.count(), 0)

    def test_cantidades_invalidas_no_rompen(self):
        for cantidad in ('0', '-3', 'abc', '1.5'):
            with self.subTest(cantidad=cantidad):
                respuesta = self.post_presupuesto(cantidades=[cantidad])
                self.assertEqual(respuesta.status_code, 200)  # vuelve al formulario con error
                self.assertEqual(Presupuesto.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_producto_inexistente_no_rompe(self):
        respuesta = self.post_presupuesto(productos=[9999])
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Presupuesto.objects.count(), 0)

    def test_detalle_muestra_el_presupuesto(self):
        self.post_presupuesto()
        presupuesto = Presupuesto.objects.get()
        respuesta = self.client.get(reverse('detalle_presupuesto', args=[presupuesto.id]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ana')
