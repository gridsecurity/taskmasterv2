from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY") 
# "namespace" refers to a container or scope that holds a set of identifiers (such as variables, functions, classes, or objects)

app.autodiscover_tasks()

@app.on_after_configure.connect
def set_up_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(1, test.s('hello'), name='add every 10')

@app.task
def test(arg):
    print(arg)
