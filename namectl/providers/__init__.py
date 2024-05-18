from namectl.providers.dns_provider import DNSProvider
from namectl.providers.porkbun import PorkbunProvider

ALL_PROVIDERS: dict[str, DNSProvider.__class__] = {
    PorkbunProvider.name: PorkbunProvider,
}

__all__ = [
    'DNSProvider',
    'ALL_PROVIDERS',
]