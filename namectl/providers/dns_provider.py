from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from namectl.dns import DNSRecord

class DNSProvider(ABC):
    name: str = ''

    @staticmethod
    @abstractmethod
    def list(domain: str) -> list['DNSRecord']:
        '''List all records for a given domain'''
        raise NotImplementedError(f'DNS provider must implement method list')

    @staticmethod
    @abstractmethod
    def create(domain: str, record: 'DNSRecord') -> None:
        '''Create a record on a domain'''
        raise NotImplementedError(f'DNS provider must implement method create')

    @staticmethod
    @abstractmethod
    def update(domain: str, record: 'DNSRecord', new_record: 'DNSRecord') -> None:
        '''Update a given record on a domain'''
        raise NotImplementedError(f'DNS provider must implement method update')

    @staticmethod
    @abstractmethod
    def delete(domain: str, record: 'DNSRecord') -> None:
        '''Delete a record on a domain'''
        raise NotImplementedError(f'DNS provider must implement method delete')
