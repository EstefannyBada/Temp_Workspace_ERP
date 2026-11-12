# catalogo/context_processors.py
"""Context processors de la app catalogo — W13."""
from typing import Any


def carrito_info(request) -> dict[str, Any]:
    """Calcula el total de items en el carrito y lo inyecta globalmente."""
    carrito = request.session.get('carrito', {})

    total_items     = sum(
        int(item.get('cantidad', 0)) for item in carrito.values()
    )
    total_productos = len(carrito)

    return {
        'carrito_total_items':     total_items,
        'carrito_total_productos': total_productos,
    }