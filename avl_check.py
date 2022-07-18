from nodes.models import *
import os

def main():
    u = Units.objects.filter(mng_ip__isnull=False)
    for item in u:
        resp = os.system(f'ping -c 1 -w 1 {item.mng_ip}')
        if not resp:
            item.is_avaliable = True
            item.save()
        else:
            item.is_avaliable = False
            item.save()
    u = Units.objects.filter(ipmi_bmc__isnull=False)
    for item in u:
        resp = os.system(f'ping -c 1 -w 1 {item.ipmi_bmc}')
        if not resp:
            item.ipmi_is_avaliable = True
            item.save()
        else:
            item.ipmi_is_avaliable = False
            item.save()

if args:
    if args[0] == 'loop':
        while True:
            main()
            sleep(300)
    else:
        print("Error: unknown parameters")
else:
    main()