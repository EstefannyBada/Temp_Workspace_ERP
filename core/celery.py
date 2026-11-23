# core/celery.py
"""Configuración de Celery para el proyecto ERP Django — W16."""
import os
from celery import Celery

# Establecer settings de Django antes de inicializar Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Cargar configuración desde settings.py usando el prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubrir automáticamente tareas en los archivos tasks.py de cada app
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de diagnóstico para verificar que Celery está activo."""
    print(f'Request: {self.request!r}')