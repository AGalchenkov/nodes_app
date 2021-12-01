import os

def ping(host):
    resp = os.system(f'ping -c 1 -w 1 -n {host} > /dev/null')
    return False if resp else True
