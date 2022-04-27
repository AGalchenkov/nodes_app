import os, pexpect

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from nodes.models import Units

platform = {
    'EcoNat': 'ecw',
}

units = Units.objects.filter(model__is_rdp=True)
for u in units:
    if u.mng_ip and u.is_avaliable:
        try:
            with pexpect.spawn(f"ssh -i /home/gal/.ssh/dev root@{u.mng_ip} interactive", timeout=2, encoding="utf-8") as ssh:
                #ssh.expect("Password:")
                #ssh.sendline("econat")
                ssh.expect("#")
                print(platform[u.rdp_name])
                ssh.sendline(f"{platform[u.rdp_name]}")
                ssh.expect(":>")
                ssh.sendline("show version")
                ssh.expect(":>")
                #print(ssh.before)
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


