import socket
import os
import re
# import psutil
from requests import get
# try:
#     import ifcfg
# except ImportError:
#     print("SOMETHING GOES WRONG")
#     def fill_network_enum():
#         networks = []
#         private_ip = get_private_ip()
#         networks.append((private_ip, f"Private: {private_ip}", ""))

#         public_ip = get_public_ip()
#         networks.append((public_ip, f"Public: {public_ip}", ""))


#         return networks

# # WORKS ONLY ON UNIX
# def get_ip_data(ether_adapter):
#     ip_data = os.popen(f'ifconfig {ether_adapter}')
#     for line in ip_data:
#         match2 = re.search(r'inet +(\d+.\d+.\d+.\d+)', line)
#         if match2:
#             ip = match2.group(0)
#             return ip

# # LOCAL IP'S 
# def get_ip(family):
#     for interface, snics in psutil.net_if_addrs().items():
#         for snic in snics:
#             if snic.family == family:
#                 yield (interface, snic.address)

# PUBLIC IP'S
def get_ips_ifcfg():
    return [(interface['inet4'][0], f"{name[:6]}:{interface['inet4'][0]}", "") 
            for name, interface in ifcfg.interfaces().items() if interface['inet4'] and name.startswith(('lo', 'eth', 'wlp'))]

def get_public_ip():
    return get('https://api.ipify.org').text

def get_private_ip():
    ''' Requires intenet connection '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
    

def fill_network_enum():
    networks = []
    # ipv4_networks = get_ip(socket.AF_INET) # returns generator
    private_ip = get_private_ip()
    networks.append((private_ip, f"Private: {private_ip}", ""))

    public_ip = get_public_ip()
    networks.append((public_ip, f"Public: {public_ip}", ""))
    # networks.append(get_ips_ifcfg())

    # for network, address in ipv4_networks:
        # networks.append((address, f"{network[:6]}:{address}", ""))

    return networks



