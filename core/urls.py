# core/urls.py
"""Enrutador principal del ERP Django."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

# Importar y combinar todas las rutas de la API REST
from clientes.api_urls import urlpatterns as clientes_api
from productos.api_urls import urlpatterns as productos_api
from proveedores.api_urls import urlpatterns as proveedores_api
from ventas.api_urls import urlpatterns as ventas_api


api_urlpatterns = (
    productos_api +
    clientes_api +
    proveedores_api +
    ventas_api
)

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # Vista principal / Inicio
    path('', views.bienvenida, name='inicio'),
    
    # Autenticación (django-allauth)
    path('accounts/', include('allauth.urls')),
    
    # API REST (W10)
    path('api/', include((api_urlpatterns, 'api'))),
    path('api/auth/token/', obtain_auth_token, name='api_token'),
    
    # E-commerce público (W13 y W14)
    path('catalogo/', include(('catalogo.urls', 'catalogo'), namespace='catalogo')),
    
    # Apps del ERP (MVT interno)
    path('clientes/', include(('clientes.urls', 'clientes'), namespace='clientes')),
    path('proveedores/', include(('proveedores.urls', 'proveedores'), namespace='proveedores')),
    path('productos/', include(('productos.urls', 'productos'), namespace='productos')),
    path('ventas/', include(('ventas.urls', 'ventas'), namespace='ventas')),
    path('reportes/', include(('reportes.urls', 'reportes'), namespace='reportes')),
]

# Servir archivos estáticos y subidos por usuarios (Media) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)