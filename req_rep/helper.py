import socket
from pprint import pprint
import os
import re
import psutil
from requests import get


# WORKS ONLY ON UNIX
def get_ip_data(ether_adapter):
    ip_data = os.popen(f'ifconfig {ether_adapter}')
    for line in ip_data:
        match2 = re.search(r'inet +(\d+.\d+.\d+.\d+)', line)
        if match2:
            ip = match2.group(0)
            return ip

# LOCAL IP'S 
def get_ip(family):
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == family:
                yield (interface, snic.address)

# PUBLIC IP'S
def get_public_ip():
    return get('https://api.ipify.org').text

def fill_network_enum():
    pass


ips = list(get_ip(socket.AF_INET))
pprint(ips)

print(f"My public IP is: {get_public_ip()}")