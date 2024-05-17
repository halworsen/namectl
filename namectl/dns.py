from typing import Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from namectl.providers import DNSProvider

@dataclass
class DNSRecord:
    hostname: str
    '''Host name/subdomain for this record'''

    type: str
    '''The type of record'''

    answer: Optional[str]
    '''
    The answer/content of the DNS record.
    Can be `None` until populated if this is a desired record with `dynamic = True`.
    '''

    ttl: int = 600
    '''TTL of the DNS record'''

    priority: Optional[int] = None
    '''Priority of the DNS record, for records that support it'''

    dynamic: bool = False
    '''
    Only set for desired state records.
    If true, this record will be dynamically updated with the host machine's IP address
    '''

    reconciled: bool = False
    '''Whether or not this record has been reconciled with desired state'''

    data: Any = None
    '''Arbitrary additional data related to the record, as set by the DNS provider'''


@dataclass
class DomainConfig:
    name: str
    '''The name of the domain this config is for'''

    records: list[DNSRecord]
    '''A list of desired records for this domain'''

    provider: 'DNSProvider' = None
    '''The DNS registrar provider to use when reconciling records for this domain'''
