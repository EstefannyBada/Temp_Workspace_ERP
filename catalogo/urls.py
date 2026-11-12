# catalogo/urls.py
"""URLs del módulo catálogo — W13 / W14 / W15."""
from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    # Catálogo público y Carrito
    path('', views.CatalogoView.as_view(), name='catalogo'),
    path('carrito/', views.ver_carrito, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar'),
    path('carrito/remover/<int:producto_id>/', views.remover_del_carrito, name='remover'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_cantidad, name='actualizar'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar'),

    # Proceso de pago y Stripe (W14 / W15)
    path('checkout/', views.checkout, name='checkout'),
    path('pago-exitoso/<int:pedido_id>/', views.pago_exitoso, name='pago_exitoso'),
    path('pago-error/', views.pago_error, name='pago_error'),
    path('webhook/', views.stripe_webhook, name='webhook'),
]