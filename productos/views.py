# productos/views.py
"""Vistas de la app productos — CRUD Web y exportación Excel (W12)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .forms import ProductoForm
from .models import Producto


class ProductoListView(ListView):
    """Lista paginada de productos activos."""

    model = Producto
    template_name = 'productos/lista.html'
    context_object_name = 'productos'
    paginate_by = 20

    def get_queryset(self):
        return (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )


class ProductoDetailView(DetailView):
    """Detalle de un producto individual por ID."""

    model = Producto
    template_name = 'productos/detalle.html'
    context_object_name = 'producto'
    pk_url_kwarg = 'producto_id'

    def get_queryset(self):
        return Producto.objects.select_related('categoria', 'proveedor')


class ProductoCreateView(LoginRequiredMixin, CreateView):
    """Formulario para dar de alta un nuevo producto."""

    model = Producto
    form_class = ProductoForm
    template_name = 'productos/crear.html'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" creado exitosamente.'
        )
        return response


class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    """Formulario para editar un producto existente."""

    model = Producto
    form_class = ProductoForm
    template_name = 'productos/editar.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" actualizado.'
        )
        return response


class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Confirmación y borrado de un producto."""

    model = Producto
    template_name = 'productos/eliminar.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('productos:lista')
    permission_required = 'productos.delete_producto'
    raise_exception = True

    def form_valid(self, form):
        nombre = self.object.nombre
        response = super().form_valid(form)
        messages.success(self.request, f'Producto "{nombre}" eliminado.')
        return response


@login_required
def exportar_excel(request):
    """Genera y descarga el catálogo completo de productos en Excel (.xlsx)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catálogo de Productos"

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0A2342", end_color="0A2342", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    headers = [
        "ID", "Nombre", "Categoría", "Proveedor",
        "Precio", "Stock", "Activo", "Fecha Registro"
    ]
    ws.append(headers)

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    productos = Producto.objects.select_related('categoria', 'proveedor').all().order_by('nombre')
    for p in productos:
        ws.append([
            p.pk,
            p.nombre,
            p.categoria.nombre if p.categoria else "Sin categoría",
            p.proveedor.nombre if p.proveedor else "Sin asignar",
            float(p.precio),
            p.stock,
            "Sí" if p.activo else "No",
            p.creado.strftime("%d/%m/%Y %H:%M") if p.creado else "—"
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col.column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="catalogo_productos.xlsx"'
    wb.save(response)
    return response