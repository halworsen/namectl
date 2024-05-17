import requests
import os
from namectl.dns import DNSRecord
from namectl.providers import DNSProvider

class PorkbunProvider(DNSProvider):
    '''
    This provider requires the following environment variables to be set:
    - PORKBUN_APIKEY
    - PORKBUN_SECRETAPIKEY
    '''
    name = 'porkbun'

    def get_keys() -> tuple[str, str]:
        if 'PORKBUN_APIKEY' not in os.environ:
            raise EnvironmentError('PORKBUN_APIKEY is not set!')
        if 'PORKBUN_SECRETAPIKEY' not in os.environ:
            raise EnvironmentError('PORKBUN_SECRETAPIKEY is not set!')
        return (os.environ['PORKBUN_APIKEY'], os.environ['PORKBUN_SECRETAPIKEY'])

    @staticmethod
    def list(domain: str) -> list:
        read_all_uri = f'https://porkbun.com/api/json/v3/dns/retrieve/{domain}'
        key, secret = PorkbunProvider.get_keys()
        data = {'apikey': key, 'secretapikey': secret, 'start': '1', 'includeLabels': 'yes'}
        resp = requests.post(read_all_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])

        all_records = []
        for record in resp['records']:
            hostname = ''
            if record['name'] != domain:
                hostname = record['name'].split(domain)[0][:-1]

            # Don't include the NS records for the bare domain
            if record['name'] == domain and record['type'] == 'NS' and 'porkbun' in record['content']:
                continue

            all_records.append(DNSRecord(
                hostname=hostname,
                type=record.get('type'),
                answer=record.get('content'),
                ttl=int(record.get('ttl')),
                priority=int(record.get('prio', '0')) if 'prio' in record else None,
                data={'id': record['id']},
            ))

        return all_records

    @staticmethod
    def create(domain: str, record: DNSRecord) -> str:
        '''Returns the ID of the created record'''
        create_uri = f'https://porkbun.com/api/json/v3/dns/create/{domain}'
        key, secret = PorkbunProvider.get_keys()
        data = {
            'apikey': key,
            'secretapikey': secret,
            'type': record.type,
            'content': record.answer,
            'ttl': str(record.ttl),
        }
        if record.hostname != '':
            data['name'] = record.hostname
        if record.priority != '':
            data['prio'] = record.priority

        resp = requests.post(create_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])

        return resp['id']

    @staticmethod
    def update(domain: str, record: DNSRecord, new_record: DNSRecord) -> None:
        record_id = record.data['id']
        edit_uri = f'https://porkbun.com/api/json/v3/dns/edit/{domain}/{record_id}'
        key, secret = PorkbunProvider.get_keys()
        data = {
            'apikey': key,
            'secretapikey': secret,
            'name': new_record.hostname,
            'type': record.type,
            'content': new_record.answer,
            'ttl': str(new_record.ttl),
        }
        if record.priority != '':
            data['prio'] = record.priority

        resp = requests.post(edit_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])

    @staticmethod
    def delete(domain: str, record: DNSRecord) -> None:
        record_id = record.data['id']
        delete_uri = f'https://porkbun.com/api/json/v3/dns/delete/{domain}/{record_id}'
        key, secret = PorkbunProvider.get_keys()
        data = {'apikey': key, 'secretapikey': secret, 'start': '1', 'includeLabels': 'yes'}
        resp = requests.post(delete_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])
