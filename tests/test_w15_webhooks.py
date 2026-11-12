"""Suite de pruebas W15 — Webhook de Stripe y descuento de stock."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from ventas.models        import Pedido


def _crear_evento(tipo: str, pedido_id: int) -> dict:
    return {
        'type': tipo,
        'data': {
            'object': {
                'id':       f'pi_test_{pedido_id}',
                'status':   'succeeded' if 'succeeded' in tipo else 'failed',
                'metadata': {'pedido_id': str(pedido_id)},
            }
        }
    }


def _crear_pedido(cliente, producto, cantidad=2) -> Pedido:
    return Pedido.objects.create(
        numero_pedido  = 'PED-2025-TEST',
        cliente        = cliente,
        estado         = 'pendiente',
        total_pagado   = Decimal('1000.00'),
        items_snapshot = [
            {
                'producto_id': producto.pk,
                'nombre':      producto.nombre,
                'cantidad':    cantidad,
                'precio':      str(producto.precio),
            }
        ]
    )


class WebhookSeguridadTest(TestCase):

    def test_get_rechazado_con_405(self):
        r = self.client.get(reverse('catalogo:webhook'))
        self.assertEqual(r.status_code, 405)

    @patch('catalogo.webhook_views.stripe.Webhook.construct_event')
    def test_firma_invalida_devuelve_400(self, mock_construct):
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError('Error', 'sig')
        r = self.client.post(
            reverse('catalogo:webhook'),
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid'
        )
        self.assertEqual(r.status_code, 400)


class WebhookPagoExitosoTest(TestCase):

    def setUp(self):
        ConfiguracionERP.get_instance()
        cat         = Categoria.objects.create(nombre='Cat')
        self.prod   = Producto.objects.create(nombre='P', precio=Decimal('500.00'), stock=10, categoria=cat)
        self.cli    = Cliente.objects.create(nombre='C', correo='c@t.com')
        self.pedido = _crear_pedido(self.cli, self.prod, cantidad=2)

    @patch('catalogo.webhook_views.stripe.Webhook.construct_event')
    def test_payment_succeeded_actualiza_estado(self, mock_construct):
        mock_construct.return_value = _crear_evento('payment_intent.succeeded', self.pedido.pk)
        r = self.client.post(reverse('catalogo:webhook'), data=b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='ok')
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')

    @patch('catalogo.webhook_views.stripe.Webhook.construct_event')
    def test_payment_succeeded_descuenta_stock(self, mock_construct):
        mock_construct.return_value = _crear_evento('payment_intent.succeeded', self.pedido.pk)
        self.client.post(reverse('catalogo:webhook'), data=b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='ok')
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 8)  # 10 - 2 = 8

    @patch('catalogo.webhook_views.stripe.Webhook.construct_event')
    def test_payment_succeeded_idempotente(self, mock_construct):
        self.pedido.estado = 'pagado'
        self.pedido.save()
        mock_construct.return_value = _crear_evento('payment_intent.succeeded', self.pedido.pk)
        self.client.post(reverse('catalogo:webhook'), data=b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='ok')
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 10)


class WebhookPagoFallidoTest(TestCase):

    def setUp(self):
        cat         = Categoria.objects.create(nombre='Cat')
        prod        = Producto.objects.create(nombre='P', precio=Decimal('100.00'), stock=5, categoria=cat)
        cli         = Cliente.objects.create(nombre='C', correo='c2@t.com')
        self.pedido = _crear_pedido(cli, prod)

    @patch('catalogo.webhook_views.stripe.Webhook.construct_event')
    def test_payment_failed_cancela_pedido(self, mock_construct):
        mock_construct.return_value = _crear_evento('payment_intent.payment_failed', self.pedido.pk)
        r = self.client.post(reverse('catalogo:webhook'), data=b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='ok')
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'cancelado')