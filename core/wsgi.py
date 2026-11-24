# core/wsgi.py
"""WSGI config del ERP Django.

Además de exponer la aplicación WSGI, arranca Celery worker y/o Beat dentro
del mismo servicio web cuando CELERY_EMBEDDED_WORKER / CELERY_EMBEDDED_BEAT
están activadas (pensado para Render con un solo servicio).

Requisito: gunicorn con UN solo worker (--workers 1); si no, se lanzarían
varios Celery/Beat y las tareas se duplicarían.
"""
import logging
import os
import subprocess
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

logger = logging.getLogger(__name__)


def _arrancar_celery_embebido():
    from django.conf import settings

    worker = getattr(settings, 'CELERY_EMBEDDED_WORKER', False)
    beat = getattr(settings, 'CELERY_EMBEDDED_BEAT', False)

    if not (worker or beat):
        return

    base = [sys.executable, '-m', 'celery', '-A', 'core']

    if worker:
        # Worker que consume la cola del ERP; con -B lleva el Beat integrado.
        cmd = base + ['worker', '-l', 'info', '--concurrency=1', '-Q', 'erp_django']
        if beat:
            cmd += ['-B', '-s', '/tmp/celerybeat-schedule']
    else:
        # Solo Beat (sin worker).
        cmd = base + ['beat', '-l', 'info', '-s', '/tmp/celerybeat-schedule']

    try:
        subprocess.Popen(cmd, cwd=str(settings.BASE_DIR))
        print(f'[celery-embebido] arrancado: {" ".join(cmd)}', flush=True)
    except Exception:
        logger.exception('No se pudo arrancar Celery embebido')


_arrancar_celery_embebido()