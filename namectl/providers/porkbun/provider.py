import requests
import os
from namectl.config import DNSRecord
from namectl.providers import DNSProvider

class PorkbunProvider(DNSProvider):
    '''
    DNS provider for Porkbun.

    Credentials format:
    ```yaml
    credentials:
      key:
        fromEnv: PORKBUN_APIKEY        # if set, read the API key from this environment variable
        value: "pk1_xxxxxxxxxxxxxxxxx" # fromEnv takes precedence over this
      secret:
        fromEnv: PORKBUN_SECRETAPIKEY  # if set, read the API secret from this environment variable
        value: "sk1_xxxxxxxxxxxxxxxxx" # fromEnv takes precedence over this
    ```
    '''
    name = 'porkbun'

    api_url = 'https://api.porkbun.com/api/json/v3/dns'

    def authenticate(self, credentials: dict) -> None:
        if 'key' not in credentials:
            raise ValueError(f'Account {self.account_name} has not set key in credential config')
        if 'secret' not in credentials:
            raise ValueError(f'Account {self.account_name} has not set secret in credential config')

        # Read API key
        key_cfg = credentials['key']
        if ('fromEnv' not in key_cfg) and ('value' not in key_cfg):
            raise ValueError(f'Invalid key config for account {self.account_name}. '
                             'You must specify the API key through either fromEnv or value.')

        if 'fromEnv' in key_cfg:
            env_var = key_cfg['fromEnv']
            if env_var not in os.environ:
                raise ValueError(f'key.fromEnv = "{env_var}" for account {self.account_name} but '
                                 f'"{env_var}" is not set in the environment!')
            self.key = os.environ[env_var]
        else:
            self.key = key_cfg['value']

        # Read API secret
        secret_cfg = credentials['secret']
        if ('fromEnv' not in secret_cfg) and ('value' not in secret_cfg):
            raise ValueError(f'Invalid secret config for account {self.account_name}. '
                             'You must specify the API secret through either fromEnv or value.')

        if 'fromEnv' in secret_cfg:
            env_var = secret_cfg['fromEnv']
            if env_var not in os.environ:
                raise ValueError(f'secret.fromEnv = "{env_var}" for account {self.account_name} but '
                                 f'"{env_var}" is not set in the environment!')
            self.secret = os.environ[env_var]
        else:
            self.secret = secret_cfg['value']

    def list(self, domain: str) -> list:
        read_all_uri = f'{self.api_url}/retrieve/{domain}'
        data = {
            'apikey': self.key,
            'secretapikey': self.secret,
            'start': '1',
            'includeLabels': 'yes',
        }
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

            priority = None
            if 'prio' in record and record['prio'] is not None:
                priority = int(record.get('prio'))
            all_records.append(DNSRecord(
                hostname=hostname,
                type=record.get('type'),
                answer=record.get('content'),
                ttl=int(record.get('ttl')),
                priority=priority,
                data={'id': record['id']},
            ))

        return all_records

    def create(self, domain: str, record: DNSRecord) -> str:
        '''Returns the ID of the created record'''
        create_uri = f'{self.api_url}/create/{domain}'
        data = {
            'apikey': self.key,
            'secretapikey': self.secret,
            'type': record.type,
            'content': record.answer,
            'ttl': str(record.ttl),
        }
        if record.hostname != '':
            data['name'] = record.hostname
        if record.priority != '':
            data['prio'] = str(record.priority)

        resp = requests.post(create_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])

        return resp['id']

    def update(self, domain: str, record: DNSRecord, new_record: DNSRecord) -> None:
        record_id = record.data['id']
        edit_uri = f'{self.api_url}/edit/{domain}/{record_id}'
        data = {
            'apikey': self.key,
            'secretapikey': self.secret,
            'name': new_record.hostname,
            'type': record.type,
            'content': new_record.answer,
            'ttl': str(new_record.ttl),
        }
        if record.priority != '':
            data['prio'] = str(record.priority)

        resp = requests.post(edit_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])

    def delete(self, domain: str, record: DNSRecord) -> None:
        record_id = record.data['id']
        delete_uri = f'{self.api_url}/delete/{domain}/{record_id}'
        data = {
            'apikey': self.key,
            'secretapikey': self.secret,
            'start': '1',
            'includeLabels': 'yes',
        }
        resp = requests.post(delete_uri, json=data).json()
        if resp['status'] != 'SUCCESS':
            raise RuntimeError(resp['message'])
