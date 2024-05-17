import requests

def ping4() -> str:
    '''Get the IPv4 of the machine performing this ping'''
    resp = requests.get('https://api.ipify.org?format=json')
    if resp.status_code != 200:
        raise RuntimeError('Failed to ping against ipify.org')
    return resp.json()['ip']

def ping6() -> str:
    '''Get the IPv6 of the machine performing this ping'''
    resp = requests.get('https://api6.ipify.org?format=json')
    if resp.status_code != 200:
        raise RuntimeError('Failed to ping against ipify.org')
    return resp.json()['ip']
