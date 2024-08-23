from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY") 
# "namespace" refers to a container or scope that holds a set of identifiers (such as variables, functions, classes, or objects)

app.autodiscover_tasks()

print("adding periodic tasks")
app.conf.beat_schedule = {
    # Executes every Monday morning at 7:30 a.m.
    'add-every-monday-morning': {
        'task': 'tasks.add',
        'schedule': crontab(minute="*/1"),
        'args': (16, 16),
    },
}
print("added periodic tasks")