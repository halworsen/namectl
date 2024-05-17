# namectl

Simple controller that reads a DNS configuration for your domains and uses it to reconcile with the
domain registrar to keep your actual records up to date with the local config.

Supports dynamic DNS records for both IPv4 and IPv6 by using the [ipify](https://www.ipify.org/) API
to fetch the machine's IP.

## Installation & use

```shell
# From this folder
pip install -e .

# Run namectl using the config at "path/to/config.yaml", reconcile every 5 minutes 
python -m namectl -c path/to/config.yaml -p 300
```

## Example config

```yaml
domains:
- name: domain.com
  # domain.com should be updated through porkbun
  provider: porkbun
  # DNS records for domain.com
  records:
  # A domain.com -> 1.2.3.4
  # TTL defaults to 600
  - hostname: ""
    type: A
    answer: "1.2.3.4"
  # A domain.com -> dynamically updated IP of machine
  - hostname: ""
    type: A
    dynamic: true
  # ALIAS alias.domain.com -> domain.com
  - hostname: "alias"
    type: ALIAS
    answer: "domain.com"
    ttl: 1200
  # NS sub.domain.com -> ns.someother.io
  - hostname: "sub"
    type: NS
    answer: "ns.someother.io"
    ttl: 86400
  # TXT _note.domain.com -> "hi there"
  - hostname: "_note"
    type: TXT
    answer: "hi there"
```

## Providers

Only `porkbun` is supported as a provider. This is because it's the only registrar I have domains
with as of making this tool. namectl providers are pluggable, however, so you could make a provider
if you wanted to. See [dns_provider.py](./namectl/providers/dns_provider.py) for information on
what's required of a provider.

### porkbun

To use the `porkbun` provider, you must set `PORKBUN_APIKEY` and `PORKBUN_SECRETAPIKEY` in your
environment.

This provider will not reconcile NS records on the bare domain, this is because Porkbun will
automatically set them on your domains.
