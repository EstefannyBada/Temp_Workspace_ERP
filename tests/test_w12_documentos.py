"""Suite de pruebas W12 — Documentos y Reportes (Compatible con y sin Docker)."""
from decimal import Decimal
import unittest

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import DetalleVenta, Venta

# Detectar si WeasyPrint y sus librerías nativas (cairo, pango) están disponibles
HAY_WEASYPRINT = False
try:
    import weasyprint
    # Prueba mínima para comprobar enlace con libcairo
    weasyprint.HTML(string="<p></p>")
    HAY_WEASYPRINT = True
except (ImportError, OSError):
    HAY_WEASYPRINT = False


class VentaDocumentosTest(TestCase):
    """Tests de exportación y generación de documentos en Ventas."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        self.user = User.objects.create_user('docuser', password='pass123')
        cat = Categoria.objects.create(nombre='Cat Documentos')
        prod = Producto.objects.create(
            nombre='Producto Test',
            precio=Decimal('500.00'),
            stock=10,
            categoria=cat
        )
        cli = Cliente.objects.create(
            nombre='Cliente Test',
            correo='cliente_doc@test.com'
        )
        self.venta = Venta.objects.create(cliente=cli)
        DetalleVenta.objects.create(
            venta=self.venta,
            producto=prod,
            cantidad=2,
            precio_unitario=Decimal('500.00')
        )

    # ── PRUEBAS BÁSICAS Y SEGURIDAD (Corren sin Docker) ───────────

    def test_pdf_sin_auth_redirige_a_login(self):
        """GET /ventas/<id>/pdf/ sin login debe redirigir a /accounts/login/."""
        r = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_pdf_venta_inexistente_devuelve_404(self):
        """GET /ventas/9999/pdf/ con ID inexistente debe devolver HTTP 404."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('ventas:pdf', args=[9999]))
        self.assertEqual(r.status_code, 404)

    def test_exportacion_excel_funciona(self):
        """La exportación a Excel (openpyxl) debe responder HTTP 200 y archivo .xlsx."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('productos:exportar_excel'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r.get('Content-Type', ''))

    # ── PRUEBAS DE RENDERIZADO WEASYPRINT (Requieren Docker/Linux) ─

    @unittest.skipIf(not HAY_WEASYPRINT, "WeasyPrint requiere librerías nativas C (Docker/Linux)")
    def test_pdf_con_auth_devuelve_200(self):
        """GET /ventas/<id>/pdf/ con login genera PDF y responde HTTP 200."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertEqual(r.status_code, 200)

    @unittest.skipIf(not HAY_WEASYPRINT, "WeasyPrint requiere librerías nativas C (Docker/Linux)")
    def test_pdf_content_type_application_pdf(self):
        """La respuesta debe tener Content-Type application/pdf."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertIn('application/pdf', r.get('Content-Type', ''))

    @unittest.skipIf(not HAY_WEASYPRINT, "WeasyPrint requiere librerías nativas C (Docker/Linux)")
    def test_pdf_empieza_con_header_pdf(self):
        """El binario del PDF debe comenzar con '%PDF'."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertTrue(r.content[:4] == b'%PDF')

    @unittest.skipIf(not HAY_WEASYPRINT, "WeasyPrint requiere librerías nativas C (Docker/Linux)")
    def test_pdf_content_disposition_attachment(self):
        """La cabecera Content-Disposition debe indicar descarga como adjunto."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        disposition = r.get('Content-Disposition', '')
        self.assertIn('attachment', disposition)
        self.assertIn('.pdf', disposition)

    @unittest.skipIf(not HAY_WEASYPRINT, "WeasyPrint requiere librerías nativas C (Docker/Linux)")
    def test_pdf_tamano_mayor_a_1kb(self):
        """El PDF generado debe tener al menos 1 KB."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertGreater(len(r.content), 1024)