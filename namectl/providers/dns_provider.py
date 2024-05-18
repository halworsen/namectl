from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from namectl.config import DNSRecord

class DNSProvider(ABC):
    name: str = ''
    '''
    Name of this DNS provider.
    This is used by account config to select the correct provider class.
    '''

    account_name: str = ''
    '''
    Name of the account which this specific `DNSProvider` instance represents.
    This is used to select the account that should be used to reconcile a set of records.
    '''

    def __init__(self, account_name: str) -> None:
        self.account_name = account_name

    @abstractmethod
    def authenticate(self, credentials: dict) -> None:
        '''
        Authenticate against the registrar using the given credentials.
        The credentials are read from the `auth` key of each account.
        '''
        raise NotImplementedError(f'DNS provider "{self.name}" must implement method authenticate')

    @abstractmethod
    def list(self, domain: str) -> list['DNSRecord']:
        '''List all records for a given domain'''
        raise NotImplementedError(f'DNS provider "{self.name}" must implement method list')

    @abstractmethod
    def create(self, domain: str, record: 'DNSRecord') -> None:
        '''Create a record on a domain'''
        raise NotImplementedError(f'DNS provider "{self.name}" must implement method create')

    @abstractmethod
    def update(self, domain: str, record: 'DNSRecord', new_record: 'DNSRecord') -> None:
        '''Update a given record on a domain'''
        raise NotImplementedError(f'DNS provider "{self.name}" must implement method update')

    @abstractmethod
    def delete(self, domain: str, record: 'DNSRecord') -> None:
        '''Delete a record on a domain'''
        raise NotImplementedError(f'DNS provider "{self.name}" must implement method delete')
