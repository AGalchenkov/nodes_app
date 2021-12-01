from nodes.models import *
import os

u = Units.objects.filter(mng_ip__isnull=False)
for item in u:
    resp = os.system(f'ping -c 1 -w 1 {item.mng_ip}')
    if not resp:
        item.is_avaliable = True
        item.save()
    else:
        item.is_avaliable = False
        item.save()
