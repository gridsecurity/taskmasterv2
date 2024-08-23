from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.decorators import periodic_task
from celery.schedules import crontab
from core.celery import app 
import time
from datetime import datetime

@periodic_task(run_every=(crontab(minute="*/1")),)
def my_task():
    print("listing time {}".format(datetime.today()))

@app.task
def fibonacci(n):
    if n <= 0:
        return "Invalid input"
    elif n == 1:
        return "0"
    elif n == 2:
        return "0, 1"
    else:
        fib_sequence = [0, 1]
        while len(fib_sequence) < n:
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        return ', '.join(map(str, fib_sequence))

@shared_task
def list_time():
    print(datetime.today())

@shared_task
def task_with_delay():
    time.sleep(10)
    return "Task with a runit 10-second delay completed"+str(time.time())


@shared_task
def get_name_rr():
    time.sleep(10)
    return "Task with get_name_rr comp."



@shared_task
def add(x, y):
    return x + y



