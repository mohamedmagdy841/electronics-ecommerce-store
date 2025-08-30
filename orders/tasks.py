from celery import shared_task
from .utils import send_email

@shared_task
def send_order_email_async(mail_subject, mail_template, context):
    send_email(mail_subject, mail_template, context)
