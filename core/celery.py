from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY") 
# "namespace" refers to a container or scope that holds a set of identifiers (such as variables, functions, classes, or objects)

app.autodiscover_tasks()



app.conf.beat_schedule = {
    'print-message-every-hour': {
        'task': 'list_time',
        'schedule': crontab(minute="*/1"),  # Every minute
    },
}