from namectl.providers.dns_provider import DNSProvider
from namectl.providers.porkbun import PorkbunProvider

ALL_PROVIDERS = {
    PorkbunProvider.name: PorkbunProvider,
}