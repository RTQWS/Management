from django.core.mail import send_mail

def send(user_email):
    send_mail(
            'sds',
            'dasd',
            'artemkoshlyakov11@mail.ru',
            [user_email],
            fail_silently=False
            )