# catalogo/filters.py
"""Filtros para el catálogo público de productos — W13 / W15."""
import django_filters

from productos.models import Categoria, Producto


class ProductoFilter(django_filters.FilterSet):
    """Filtro de productos para el catálogo público."""

    nombre = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains',
        label='Buscar por nombre',
    )
    categoria = django_filters.ModelChoiceFilter(
        queryset=Categoria.objects.all(),
        label='Categoría',
        empty_label='Todas las categorías',
    )
    precio_min = django_filters.NumberFilter(
        field_name='precio',
        lookup_expr='gte',
        label='Precio mínimo ($)',
    )
    precio_max = django_filters.NumberFilter(
        field_name='precio',
        lookup_expr='lte',
        label='Precio máximo ($)',
    )

    class Meta:
        model  = Producto
        fields = ['nombre', 'categoria', 'precio_min', 'precio_max']