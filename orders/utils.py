from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_email(mail_subject, mail_template, context):
    message = render_to_string(mail_template, context)
    mail = EmailMessage(
        mail_subject,
        message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[context["customer_email"]]
    )
    mail.content_subtype = 'html'
    mail.send()
