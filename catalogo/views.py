# catalogo/views.py
"""Vistas para el catálogo, carrito en sesión, checkout Stripe y webhooks — W15 Completo."""
from decimal import Decimal
import logging
from typing import Any

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from productos.models import Producto
from ventas.models import Pedido

from .checkout_utils import (
    calcular_totales,
    generar_numero_pedido,
    obtener_o_crear_cliente,
)
from .filters import ProductoFilter

# Configurar API Key de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


# ── CATÁLOGO PÚBLICO ────────────────────────────────────────────────────────

class CatalogoView(ListView):
    """Catálogo público de productos activos con filtros."""

    model               = Producto
    template_name       = 'catalogo/catalogo.html'
    context_object_name = 'productos'
    paginate_by         = 12

    def get_queryset(self):
        """Filtra productos activos aplicando el filtro del request."""
        qs = (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )
        self.filtro = ProductoFilter(self.request.GET, queryset=qs)
        return self.filtro.qs

    def get_context_data(self, **kwargs):
        """Pasa el formulario de filtro al contexto."""
        ctx = super().get_context_data(**kwargs)
        ctx['filtro']     = self.filtro
        ctx['categorias'] = self.filtro.form.fields['categoria'].queryset
        return ctx


# ── CARRITO EN SESIÓN ──────────────────────────────────────────────────────

def _obtener_carrito(request: object) -> dict:
    """Obtiene el carrito de la sesión o crea uno vacío."""
    return request.session.get('carrito', {})


def _guardar_carrito(request: object, carrito: dict) -> None:
    """Guarda el carrito en la sesión y marca la sesión como modificada."""
    request.session['carrito'] = carrito
    request.session.modified   = True


def ver_carrito(request):
    """Muestra el contenido del carrito con subtotales calculados."""
    carrito = _obtener_carrito(request)

    items = []
    total = Decimal('0.00')

    for prod_id, datos in carrito.items():
        precio    = Decimal(str(datos['precio']))
        cantidad  = int(datos['cantidad'])
        subtotal  = precio * cantidad
        total    += subtotal
        items.append({
            'prod_id':  prod_id,
            'nombre':   datos['nombre'],
            'precio':   precio,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'imagen':   datos.get('imagen'),
        })

    return render(request, 'catalogo/carrito.html', {
        'items': items,
        'total': total,
    })


def agregar_al_carrito(request, producto_id: int):
    """Agrega un producto al carrito (manejo defensivo de imagen)."""
    if request.method != 'POST':
        return redirect('catalogo:catalogo')

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito  = _obtener_carrito(request)

    clave    = str(producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    # Lectura defensiva por si el modelo no tiene la propiedad 'imagen'
    imagen_obj = getattr(producto, 'imagen', None)
    imagen_url = imagen_obj.name if (imagen_obj and hasattr(imagen_obj, 'name')) else None

    if clave in carrito:
        carrito[clave]['cantidad'] += cantidad
    else:
        carrito[clave] = {
            'nombre':   producto.nombre,
            'precio':   str(producto.precio),
            'cantidad': cantidad,
            'imagen':   imagen_url,
        }

    _guardar_carrito(request, carrito)
    messages.success(request, f'"{producto.nombre}" agregado al carrito.')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    return redirect(next_url or 'catalogo:catalogo')


def remover_del_carrito(request, producto_id: int):
    """Elimina un producto del carrito."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave   = str(producto_id)

    nombre = carrito.get(clave, {}).get('nombre', 'Producto')
    carrito.pop(clave, None)
    _guardar_carrito(request, carrito)

    messages.warning(request, f'"{nombre}" eliminado del carrito.')
    return redirect('catalogo:carrito')


def actualizar_cantidad(request, producto_id: int):
    """Actualiza la cantidad de un item en el carrito."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito  = _obtener_carrito(request)
    clave    = str(producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    if clave in carrito:
        if cantidad > 0:
            carrito[clave]['cantidad'] = cantidad
        else:
            carrito.pop(clave)

    _guardar_carrito(request, carrito)
    return redirect('catalogo:carrito')


def vaciar_carrito(request):
    """Limpia la sesión del carrito."""
    if request.method == 'POST':
        _guardar_carrito(request, {})
        messages.info(request, 'Carrito vaciado.')
    return redirect('catalogo:carrito')


# ── CHECKOUT Y STRIPE (W14 / W15) ──────────────────────────────────────────

@login_required
def checkout(request):
    """Proceso de pago: crea Pedido con items_snapshot y PaymentIntent de Stripe."""
    carrito = _obtener_carrito(request)
    if not carrito:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('catalogo:catalogo')

    totales         = calcular_totales(carrito)
    publishable_key = settings.STRIPE_PUBLISHABLE_KEY

    # Prepara la lista de items para la plantilla
    items = []
    for prod_id, datos in carrito.items():
        precio   = Decimal(str(datos['precio']))
        cantidad = int(datos['cantidad'])
        items.append({
            'prod_id':  prod_id,
            'nombre':   datos['nombre'],
            'cantidad': cantidad,
            'precio':   precio,
            'subtotal': precio * cantidad,
        })

    if request.method == 'POST':
        try:
            # 1. Vincular usuario con Cliente ERP
            cliente = obtener_o_crear_cliente(request.user)

            # 2. Construir snapshot del carrito (W15)
            snapshot = [
                {
                    'producto_id': int(prod_id),
                    'nombre':      datos['nombre'],
                    'cantidad':    int(datos['cantidad']),
                    'precio':      str(datos['precio']),
                }
                for prod_id, datos in carrito.items()
            ]

            # 3. Crear el Pedido en BD
            numero = generar_numero_pedido()
            pedido = Pedido.objects.create(
                numero_pedido  = numero,
                cliente        = cliente,
                estado         = 'pendiente',
                total_pagado   = totales['total'],
                items_snapshot = snapshot,
            )

            # 4. Crear PaymentIntent en Stripe
            monto_centavos = int(totales['total'] * 100)
            intent = stripe.PaymentIntent.create(
                amount          = monto_centavos,
                currency        = 'mxn',
                metadata        = {
                    'pedido_id':  pedido.pk,
                    'pedido_num': pedido.numero_pedido,
                    'cliente':    cliente.nombre,
                },
                idempotency_key = f'pedido-{pedido.pk}',
            )

            # 5. Renderizar checkout con client_secret
            return render(request, 'catalogo/checkout.html', {
                'items':           items,
                'carrito':         carrito,
                'totales':         totales,
                'pedido':          pedido,
                'client_secret':   intent.client_secret,
                'publishable_key': publishable_key,
            })

        except stripe.error.StripeError as exc:
            logger.error(f'Error de Stripe durante el checkout: {exc}')
            messages.error(request, f'Error al conectar con Stripe: {exc.user_message or str(exc)}')
            return redirect('catalogo:pago_error')

        except Exception as exc:
            logger.error(f'Error inesperado en checkout: {exc}')
            messages.error(request, f'Error inesperado en el proceso de pago: {exc}')
            return redirect('catalogo:pago_error')

    # GET — Resumen inicial
    return render(request, 'catalogo/checkout.html', {
        'items':           items,
        'carrito':         carrito,
        'totales':         totales,
        'client_secret':   None,
        'publishable_key': publishable_key,
    })


def pago_exitoso(request, pedido_id: int):
    """Confirmación post-pago exitoso y vaciado de carrito."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    # Vaciar el carrito de la sesión
    _guardar_carrito(request, {})
    messages.success(
        request,
        f'¡Pago exitoso! Tu pedido {pedido.numero_pedido} está confirmado. Total: ${pedido.total_pagado}'
    )

    return render(request, 'catalogo/pago_exitoso.html', {
        'pedido': pedido,
    })


def pago_error(request):
    """Vista de error de pago."""
    return render(request, 'catalogo/pago_error.html')


# ── STRIPE WEBHOOKS CON ATOMIC STOCK DECREMENT (W15) ───────────────────────

@csrf_exempt
@require_POST
def stripe_webhook(request) -> HttpResponse:
    """Recibe y procesa los eventos asíncronos de Stripe."""
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload    = payload,
            sig_header = sig_header,
            secret     = settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        logger.warning('Webhook: payload inválido recibido.')
        return HttpResponse('Payload inválido.', status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning('Webhook: firma inválida — posible ataque.')
        return HttpResponse('Firma inválida.', status=400)

    tipo = event['type']
    logger.info(f'Webhook recibido: {tipo}')

    if tipo == 'payment_intent.succeeded':
        _manejar_pago_exitoso(event['data']['object'])
    elif tipo == 'payment_intent.payment_failed':
        _manejar_pago_fallido(event['data']['object'])
    else:
        logger.debug(f'Evento ignorado: {tipo}')

    return HttpResponse(status=200)


def _manejar_pago_exitoso(payment_intent: dict) -> None:
    """Actualiza Pedido a 'pagado' y descuenta stock vía items_snapshot."""
    pedido_id = _extraer_pedido_id(payment_intent)
    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(f'Webhook: Pedido {pedido_id} no encontrado en BD.')
        return

    if pedido.estado != 'pagado':
        pedido.estado = 'pagado'
        pedido.save(update_fields=['estado'])
        logger.info(f'Pedido {pedido.numero_pedido} actualizado a "pagado".')
        _descontar_stock(pedido)
    else:
        logger.info(f'Pedido {pedido.numero_pedido} ya estaba pagado — operación idempotente.')


def _manejar_pago_fallido(payment_intent: dict) -> None:
    """Cancela un pedido cuando el cobro falla."""
    pedido_id = _extraer_pedido_id(payment_intent)
    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(f'Webhook: Pedido {pedido_id} no encontrado.')
        return

    if pedido.estado == 'pendiente':
        pedido.estado = 'cancelado'
        pedido.save(update_fields=['estado'])
        logger.info(f'Pedido {pedido.numero_pedido} cancelado por pago fallido.')


def _extraer_pedido_id(payment_intent: dict) -> int | None:
    """Extrae el pedido_id del metadata del PaymentIntent."""
    metadata  = payment_intent.get('metadata', {})
    pedido_id = metadata.get('pedido_id')

    if not pedido_id:
        logger.warning('Webhook: PaymentIntent sin pedido_id en metadata.')
        return None

    try:
        return int(pedido_id)
    except (ValueError, TypeError):
        logger.error(f'Webhook: pedido_id inválido: {pedido_id!r}')
        return None


def _descontar_stock(pedido: Pedido) -> None:
    """Descuenta el stock usando expresiones F() atómicas en SQL."""
    items = getattr(pedido, 'items_snapshot', []) or []

    for item in items:
        producto_id = item.get('producto_id')
        cantidad    = int(item.get('cantidad', 0))

        if not producto_id or cantidad <= 0:
            continue

        filas_actualizadas = Producto.objects.filter(
            pk=producto_id,
            stock__gte=cantidad
        ).update(
            stock=F('stock') - cantidad
        )

        if filas_actualizadas:
            logger.info(f'Stock decrementado: Producto {producto_id} - {cantidad} unidades.')
        else:
            logger.warning(f'Producto {producto_id}: stock insuficiente para decrementar {cantidad} unidades.')