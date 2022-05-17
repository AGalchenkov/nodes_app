import os, pexpect
from time import sleep

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from nodes.models import Units

platform = {
    'EcoNat': 'ecw',
}

while True:
    units = Units.objects.filter(model__is_rdp=True)
    for u in units:
        if u.mng_ip and u.is_avaliable:
            try:
                with pexpect.spawn(f"ssh -i /home/gal/.ssh/dev -oStrictHostKeyChecking=no root@{u.mng_ip}", timeout=5, encoding="utf-8") as ssh:
                    ssh.expect("#")
                    ssh.sendline('ecw -c "sh version"')
                    ssh.expect("#")
                    version_raw = ssh.before.split('\r\n')
                    try:
                        version = next(ver for ver in version_raw if ver.find('version:') > 0).split(':')[1].strip()
                        if version:
                            print(f'{u.mng_ip} -> version : {version}')
                            u.rdp_firmware = version
                            u.save()
                    except StopIteration:
                        continue
            except Exception as e:
                print(f'FAIL: {u.mng_ip} BECAUSE: {e.value[:17]}')
                #pass
    sleep(120)

