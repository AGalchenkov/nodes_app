from nodes.models import *
from ping3 import ping, verbose_ping

u = Units.objects.filter(mng_ip__isnull=False)
for item in u:
    if ping(item.mng_ip, timeout=0.5):
        item.is_avaliable = True
        item.save()
    else:
        item.is_avaliable = False
        item.save()
