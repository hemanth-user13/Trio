from celery import shared_task



@shared_task
def add_number(a,b):
    return a+b