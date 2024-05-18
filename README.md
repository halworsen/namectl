# namectl

Simple controller that reads a DNS configuration for your domains and uses it to reconcile with the
domain registrar to keep your actual records up to date with the local config. Supports multiple
accounts within and across multiple registrars at once.

Dynamic DNS for both IPv4 and IPv6 are supported through using the [ipify](https://www.ipify.org/)
API to fetch the machine's IP.

## Installation & use

```shell
# From this folder
pip install -e .

# Run namectl using the config at "path/to/config.yaml", reconcile every 5 minutes 
python -m namectl -c path/to/config.yaml -p 300
```

The DNS config is re-read on every reconciliation attempt. You can change/fix the config and the
changes will be used for the next reconciliation.

## Configuration

namectl configuration files specify a list of `accounts` which can be used to reconcile the
desired `records` specified for each of the `domains`.

### Configuration reference

| Field | Type | Description |
|-------|------|-------------|
| `accounts` | list | Top level key for account configuration |
| `accounts[].name` | string | Name of the account |
| `accounts[].provider` | string | Name of the [DNS provider](#providers) to use for this account |
| `accounts[].credentials` | dict | Credential config for this account. Check the [provider](#providers) for information on what's required |
| `domains` | list | Top level key for domain configuration |
| `domains[].name` | string | The name of the domain |
| `domains[].account` | string | The name of the account to use when reconciling records for this domain |
| `domains[].records` | list | List of desired DNS records for this domain |
| `domains[].records[].name` | string | Subdomain/hostname of the record |
| `domains[].records[].type` | string | DNS record type |
| `domains[].records[].content` | string | The desired content of the DNS record |
| `domains[].records[].ttl` | int | The desired TTL of the DNS record |
| `domains[].records[].priority` | int | For types that support it, the desired priority of the DNS record |
| `domains[].records[].dynamic` | bool | If `true`, the DNS record content will dynamically be set to the machine's IPv4 if the record type is A, or the IPv6 if the record type is AAAA |

### Example configuration

```yaml
# List of all accounts
accounts:
- name: my-pb-acct
  provider: porkbun
  credentials:
    key:
      value: "pk1_xxxxxxxxx" # specify the API key directly
    secret:
      fromEnv: "PORKBUN_APISECRET" # read the API secret from the env variable PORKBUN_APISECRET

# List of domains to manage records for
domains:
- name: domain.com
  account: my-pb-acct # domain.com should be updated with the my-pb-acct account
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

This provider will not reconcile NS records on the bare domain, this is because Porkbun seems to
treat NS records on your domains as inherently different to any other records for some reason.
It just doesn't work with how namectl is designed. You'll have to specify the authoritative name
servers through the web UI (sorry!)

#### Credentials configuration reference

| Field | Type | Description |
|-------|------|-------------|
| `key` | dict | Top level key for configuring the API key |
| `key.fromEnv` | string | Name of the environment variable to read the API key from. This takes precedence over `key.value` |
| `key.value` | string | The API key to use |
| `secret` | dict | Top level secret for configuring the API secret |
| `secret.fromEnv` | string | Name of the environment variable to read the API secret from. This takes precedence over `secret.value` |
| `secret.value` | string | The API secret to use |
