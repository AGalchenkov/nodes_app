import os
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from nodes.models import Units
from django.contrib.auth.models import User
from django.core.mail import send_mail
from urllib import request

while True:
    units = Units.objects.exclude(expired_date__isnull=True)
    for u in units:
        if u.expired_date and u.owner:
            d = u.expired_date - datetime.now()
            if d.total_seconds() < 3600 and not u.is_notifi_send:
                try:
                    send_mail(
                                    f'[NodesApp] Бронь истекает для {u} ',
                                    '',
                                    #f'<a src="http://127.0.0.1:8080/nodes/rack/{u.rack_id}/unit_detail/{u.unit_num}">мой юнит</a>\r\n\r\nДата истечения: {u.expired_date.strftime("%d/%m/%Y %H:%M")}',
                                    '',
                                    [f'{u.owner.email}'],
                                    auth_user='a.galchenkov@rdp.ru',
                                    fail_silently=False,
                                    html_message=f'<a href="http://127.0.0.1:8080/nodes/rack/{u.rack_id}/unit_detail/{u.unit_num}">{u}</a><br><br>Дата истечения: {u.expired_date.strftime("%d/%m/%Y %H:%M")}'
                            )
                    u.is_notifi_send = True
                    u.save()
                    with open('sendmail.log', 'a+') as f:
                        f.write(f'{datetime.now()} SEND MAIL TO {u.owner.email} ABOUT EXPIRED {u}\r\n')
                except Exception as e:
                    with open('sendmail_error.log', 'a+') as f:
                        f.write(f'{datetime.now()} {e}\r\n')
sleep(60)
