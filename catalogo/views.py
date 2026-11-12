
"""Vistas del módulo de catálogo y carrito — W13/W14.

Módulo público (no requiere autenticación para lectura).
El carrito se almacena en la sesión Django.
"""

import logging
from decimal import Decimal

import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from productos.models import Producto
from ventas.models import Pedido

from .filters import ProductoFilter
from .checkout_utils import (
    calcular_totales,
    generar_numero_pedido,
    obtener_o_crear_cliente,
)


# ── REGISTRO DE ERRORES ────────────────────────────────────────────────────

logger = logging.getLogger(__name__)


# ── CONFIGURACIÓN DE STRIPE ────────────────────────────────────────────────

stripe.api_key = settings.STRIPE_SECRET_KEY


# ── CATÁLOGO ────────────────────────────────────────────────────────────────

class CatalogoView(ListView):
    """Catálogo público de productos con filtros."""

    model = Producto
    template_name = 'catalogo/catalogo.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )

        self.filtro = ProductoFilter(
            self.request.GET,
            queryset=qs
        )

        return self.filtro.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtro'] = self.filtro
        ctx['categorias'] = (
            self.filtro.form.fields['categoria'].queryset
        )
        return ctx


# ── CARRITO ─────────────────────────────────────────────────────────────────

def _obtener_carrito(request):
    """Obtiene el carrito de la sesión o crea uno vacío."""

    return request.session.get('carrito', {})


def _guardar_carrito(request, carrito):
    """Guarda el carrito de la sesión."""

    request.session['carrito'] = carrito
    request.session.modified = True


def ver_carrito(request):
    """Muestra los productos y el total del carrito."""

    carrito = _obtener_carrito(request)

    items = []
    total = Decimal('0.00')

    for prod_id, datos in carrito.items():
        precio = Decimal(str(datos['precio']))
        cantidad = int(datos['cantidad'])
        subtotal = precio * cantidad

        total += subtotal

        items.append({
            'prod_id': prod_id,
            'nombre': datos['nombre'],
            'precio': precio,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'imagen': datos.get('imagen'),
        })

    return render(
        request,
        'catalogo/carrito.html',
        {
            'items': items,
            'total': total,
        }
    )


def agregar_al_carrito(request, producto_id: int):
    """Agrega un producto al carrito o incrementa su cantidad."""

    if request.method != 'POST':
        return redirect('catalogo:catalogo')

    producto = get_object_or_404(
        Producto,
        pk=producto_id,
        activo=True
    )

    carrito = _obtener_carrito(request)

    clave = str(producto_id)

    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        messages.error(request, 'Cantidad inválida.')
        return redirect('catalogo:catalogo')

    if cantidad <= 0:
        messages.warning(
            request,
            'La cantidad debe ser mayor que cero.'
        )
        return redirect('catalogo:catalogo')

    if clave in carrito:
        carrito[clave]['cantidad'] += cantidad
    else:
        carrito[clave] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': cantidad,
            'imagen': (
                producto.imagen.name
                if producto.imagen else None
            ),
        }

    _guardar_carrito(request, carrito)

    messages.success(
        request,
        f'"{producto.nombre}" agregado al carrito.'
    )

    next_url = (
        request.POST.get('next')
        or request.META.get('HTTP_REFERER')
    )

    return redirect(next_url or 'catalogo:catalogo')


def remover_del_carrito(request, producto_id: int):
    """Elimina un producto del carrito."""

    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    nombre = carrito.get(clave, {}).get(
        'nombre',
        'Producto'
    )

    carrito.pop(clave, None)

    _guardar_carrito(request, carrito)

    messages.warning(
        request,
        f'"{nombre}" eliminado del carrito.'
    )

    return redirect('catalogo:carrito')


def actualizar_cantidad(request, producto_id: int):
    """Actualiza la cantidad de un producto."""

    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        messages.error(request, 'Cantidad inválida.')
        return redirect('catalogo:carrito')

    if clave in carrito:
        if cantidad > 0:
            carrito[clave]['cantidad'] = cantidad
        else:
            carrito.pop(clave)

    _guardar_carrito(request, carrito)

    return redirect('catalogo:carrito')


def vaciar_carrito(request):
    """Elimina todos los productos del carrito."""

    if request.method == 'POST':
        _guardar_carrito(request, {})

        messages.info(
            request,
            'Carrito vaciado.'
        )

    return redirect('catalogo:carrito')


# ── CHECKOUT ────────────────────────────────────────────────────────────────

@login_required
def checkout(request):
    """Proceso de pago mediante Stripe.

    GET: Muestra el resumen del carrito.

    POST: Crea el pedido y genera el PaymentIntent.
    """

    carrito = _obtener_carrito(request)

    if not carrito:
        messages.warning(
            request,
            'Tu carrito está vacío.'
        )
        return redirect('catalogo:catalogo')

    # Comprobar configuración de Stripe.
    publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    secret_key = settings.STRIPE_SECRET_KEY

    if not secret_key or not publishable_key:
        logger.error(
            'Stripe no está configurado: faltan las claves '
            'STRIPE_SECRET_KEY o STRIPE_PUBLISHABLE_KEY.'
        )

        messages.error(
            request,
            'El servicio de pago no está disponible temporalmente.'
        )

        return redirect('catalogo:pago_error')

    # Calcular totales.
    try:
        totales = calcular_totales(carrito)

        if totales['total'] <= 0:
            messages.error(
                request,
                'El total del carrito no es válido.'
            )
            return redirect('catalogo:carrito')

    except Exception:
        logger.exception(
            'Error al calcular los totales del checkout.'
        )

        messages.error(
            request,
            'No fue posible calcular el total del carrito.'
        )

        return redirect('catalogo:pago_error')

    # Preparar productos para el resumen.
    items_checkout = []

    try:
        for prod_id, datos in carrito.items():
            precio = Decimal(str(datos['precio']))
            cantidad = int(datos['cantidad'])

            if precio < 0 or cantidad <= 0:
                raise ValueError('Precio o cantidad inválidos.')

            subtotal = precio * cantidad

            items_checkout.append({
                'prod_id': prod_id,
                'nombre': datos['nombre'],
                'precio': precio,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'imagen': datos.get('imagen'),
            })

    except (KeyError, TypeError, ValueError):
        logger.exception(
            'El carrito contiene información inválida.'
        )

        messages.error(
            request,
            'Hay información inválida en tu carrito.'
        )

        return redirect('catalogo:carrito')

    # ── POST: Procesar pago ─────────────────────────────────────────────

    if request.method == 'POST':

        pedido = None

        try:
            # Configurar la clave para esta solicitud.
            stripe.api_key = secret_key

            # 1. Obtener o crear cliente ERP.
            cliente = obtener_o_crear_cliente(request.user)

            # ── 2. Crear el Pedido con snapshot del carrito ────────────
            numero = generar_numero_pedido()

            # Construir el snapshot: lista de dicts serializables.
            snapshot = [
                {
                    'producto_id': int(prod_id),
                    'nombre': datos['nombre'],
                    'cantidad': int(datos['cantidad']),
                    'precio': datos['precio'],
                }
                for prod_id, datos in carrito.items()
            ]

            pedido = Pedido.objects.create(
                numero_pedido=numero,
                cliente=cliente,
                estado='pendiente',
                total_pagado=totales['total'],
                items_snapshot=snapshot,
            )

            # 4. Convertir el total a centavos.
            monto_centavos = int(
                (totales['total'] * 100).quantize(
                    Decimal('1')
                )
            )

            # 5. Crear PaymentIntent.
            intent = stripe.PaymentIntent.create(
                amount=monto_centavos,
                currency='mxn',
                metadata={
                    'pedido_id': str(pedido.pk),
                    'pedido_num': pedido.numero_pedido,
                    'cliente': cliente.nombre,
                },
                idempotency_key=f'pedido-{pedido.pk}',
            )

            # 6. Guardar la referencia del pago en la sesión.
            pagos = request.session.get(
                'stripe_payment_intents',
                {}
            )

            pagos[str(pedido.pk)] = str(intent.id)

            request.session['stripe_payment_intents'] = pagos
            request.session.modified = True

            logger.info(
                'PaymentIntent creado correctamente para '
                'el pedido %s.',
                pedido.numero_pedido
            )

            # 7. Mostrar formulario de pago.
            return render(
                request,
                'catalogo/checkout.html',
                {
                    'carrito': carrito,
                    'items': items_checkout,
                    'totales': totales,
                    'pedido': pedido,
                    'client_secret': intent.client_secret,
                    'publishable_key': publishable_key,
                }
            )

        except stripe.error.StripeError as exc:

            logger.exception(
                'Error de Stripe durante el checkout.'
            )

            # Eliminar pedido pendiente si Stripe no pudo iniciar
            # el proceso de pago.
            if pedido is not None:
                pedido.delete()

            mensaje = (
                getattr(exc, 'user_message', None)
                or 'No fue posible conectar con el servicio de pago.'
            )

            messages.error(
                request,
                mensaje
            )

            return redirect('catalogo:pago_error')

        except Exception:

            # Registrar el traceback completo en Render.
            logger.exception(
                'ERROR COMPLETO DURANTE EL CHECKOUT'
            )

            if pedido is not None:
                pedido.delete()

            messages.error(
                request,
                'No se pudo iniciar el pago. '
                'Inténtalo nuevamente.'
            )

            return redirect('catalogo:pago_error')

    # ── GET: Mostrar resumen sin crear PaymentIntent ────────────────────

    return render(
        request,
        'catalogo/checkout.html',
        {
            'carrito': carrito,
            'items': items_checkout,
            'totales': totales,
            'pedido': None,
            'client_secret': None,
            'publishable_key': publishable_key,
        }
    )


# ── CONFIRMACIÓN DE PAGO ────────────────────────────────────────────────────

@login_required
def pago_exitoso(request, pedido_id: int):
    """Verifica el PaymentIntent antes de confirmar el pedido."""

    pedido = get_object_or_404(
        Pedido,
        pk=pedido_id
    )

    pagos = request.session.get(
        'stripe_payment_intents',
        {}
    )

    intent_id = pagos.get(str(pedido.pk))

    if not intent_id:
        logger.warning(
            'Intento de confirmar el pedido %s sin PaymentIntent '
            'registrado en la sesión.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'No se pudo verificar el pago de este pedido.'
        )

        return redirect('catalogo:pago_error')

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY

        intent = stripe.PaymentIntent.retrieve(intent_id)

        if (
            intent.status != 'succeeded'
            or str(intent.metadata.get('pedido_id')) != str(pedido.pk)
        ):
            logger.warning(
                'Pago no confirmado para el pedido %s. Estado: %s',
                pedido.numero_pedido,
                intent.status
            )

            messages.error(
                request,
                'El pago todavía no ha sido confirmado.'
            )

            return redirect('catalogo:pago_error')

    except stripe.error.StripeError:
        logger.exception(
            'No se pudo verificar el PaymentIntent del pedido %s.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'No fue posible verificar el pago.'
        )

        return redirect('catalogo:pago_error')

    except Exception:
        logger.exception(
            'Error inesperado al verificar el pago del pedido %s.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'Ocurrió un error al verificar el pago.'
        )

        return redirect('catalogo:pago_error')

    # El pago sí fue confirmado por Stripe.
    _guardar_carrito(request, {})

    pagos.pop(str(pedido.pk), None)
    request.session['stripe_payment_intents'] = pagos
    request.session.modified = True

    messages.success(
        request,
        f'¡Pago exitoso! Tu pedido {pedido.numero_pedido} '
        f'está confirmado. Total: ${pedido.total_pagado}'
    )

    return render(
        request,
        'catalogo/pago_exitoso.html',
        {
            'pedido': pedido,
        }
    )


def pago_error(request):
    """Muestra la página de error de pago."""

    return render(
        request,
        'catalogo/pago_error.html'
    )