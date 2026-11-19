# catalogo/urls.py — agregar la URL del webhook:
from django.urls import path

from . import views
from .webhook_views import stripe_webhook

app_name = 'catalogo'

urlpatterns = [
    # Catálogo público
    path('', views.CatalogoView.as_view(), name='catalogo'),

    # Carrito (W13)
    path('carrito/',                              views.ver_carrito,        name='carrito'),
    path('carrito/agregar/<int:producto_id>/',    views.agregar_al_carrito, name='agregar'),
    path('carrito/remover/<int:producto_id>/',    views.remover_del_carrito,name='remover'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_cantidad, name='actualizar'),
    path('carrito/vaciar/',                       views.vaciar_carrito,     name='vaciar'),

    # Checkout con Stripe (W14)
    path("crear-payment-intent/", views.checkout, name="crear_payment_intent"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
    path("pago-exitoso/", views.pago_exitoso, name="pago_exitoso"),

    # Webhook de Stripe (W15)
    path('webhook/', stripe_webhook, name='webhook'),
]