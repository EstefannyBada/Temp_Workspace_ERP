
"""Vistas de la aplicación clientes — W07 y W08."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ClienteForm
from .models import Cliente


def inicio(request):
    """Vista de inicio compatible con las pruebas de W02."""
    return render(request, 'clientes/index.html')


class ClienteListView(ListView):
    """Lista paginada de clientes activos."""

    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 20

    def get_queryset(self):
        return Cliente.objects.filter(activo=True).order_by('nombre')


class ClienteDetailView(DetailView):
    """Muestra los detalles de un cliente y sus últimas ventas."""

    model = Cliente
    template_name = 'clientes/detalle.html'
    context_object_name = 'cliente'
    pk_url_kwarg = 'cliente_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ventas'] = self.object.ventas.order_by('-fecha')[:10]
        return context


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """Crea un cliente nuevo."""

    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/crear.html'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Cliente "{self.object.nombre}" creado exitosamente.'
        )
        return response


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """Actualiza los datos de un cliente."""

    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/editar.html'
    pk_url_kwarg = 'cliente_id'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Cliente "{self.object.nombre}" actualizado.'
        )
        return response


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """Elimina un cliente."""

    model = Cliente
    template_name = 'clientes/eliminar.html'
    pk_url_kwarg = 'cliente_id'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        nombre = self.object.nombre
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Cliente "{nombre}" eliminado.'
        )
        return response
