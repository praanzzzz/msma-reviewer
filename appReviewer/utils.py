from django.core.signing import Signer
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

signer = Signer()


def generate_verification_token(user):
    return signer.sign(user.pk)


def send_verification_email(user):
    token = generate_verification_token(user)
    verification_url = f"http://127.0.0.1:8000{reverse('verify_email', args=[token])}"
    subject = "Verify Your Email"
    message = f"Click the link to verify your email: {verification_url}"
    sender_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, sender_email, [user.email])