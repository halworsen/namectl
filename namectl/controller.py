import os
import time
import logging
import yaml
from namectl.config import Account, DomainConfig, DNSRecord
from namectl.providers import ALL_PROVIDERS
from namectl.ping import ping4, ping6

LOG = logging.getLogger('namectl')

def read_dns_config(config_path: str, machine_ipv4: str, machine_ipv6: str) -> list[DomainConfig]:
    '''
    Reads the DNS configuration file used for the desired state and marshals it into a list of
    DomainConfigs
    '''
    if not os.path.exists(config_path):
        LOG.warning(f'The configuration file {config_path} does not exist!')
        return []

    LOG.info(f'Reading DNS configuration from {config_path}')
    with open(config_path, 'r') as cfg_file:
        config = yaml.load(cfg_file, yaml.Loader)

    if 'accounts' not in config:
        LOG.warning('The DNS config file is missing account configuration!')
        return []

    # Deal with reading account config and setting those up first
    all_accounts = {}
    for account in config['accounts']:
        # Check for account misconfiguration
        if 'name' not in account:
            LOG.warning(f'Misconfigured account detected. '
                        'An account is missing a name and will not be created!')
            continue
        name = account['name']

        if 'provider' not in account:
            LOG.warning(f'Misconfigured account detected. '
                        f'The account {name} has not set the provider and will not be created!')
            continue

        # Setup the account provider
        account_provider = ALL_PROVIDERS[account['provider']](name)
        try:
            account_provider.authenticate(account.get('credentials', {}))
        except Exception as E:
            LOG.warning(f'Failed to configure credentials for account {name}. '
                        f'This account will not be created!\n{E}')
            continue

        all_accounts[name] = Account(name=name, provider=account_provider)
        LOG.info(f'Registered account {name} with provider {account["provider"]}')

    if 'domains' not in config:
        LOG.warning('The DNS config file is missing domain configuration!')
        return []

    domain_configs = []
    for domain in config['domains']:
        # Check for misconfiguration of the domain
        if 'name' not in domain:
            LOG.warning(f'Misconfigured domain detected. '
                        'A domain is missing a name and will not be reconciled!')
            continue
        name = domain['name']

        if 'account' not in domain:
            LOG.warning(f'Misconfigured domain detected. '
                        f'The domain {name} has not set the account and will not be reconciled!')
            continue
        if domain['account'] not in all_accounts:
            LOG.warning(f'Misconfigured domain detected. '
                        f'The domain {name} is using the non-existent account {domain["account"]} '
                        'and will not be reconciled!')
            continue

        if 'records' not in domain:
            LOG.warning(f'Misconfigured domain detected. '
                        f'The domain {name} has no records and will not be reconciled!')
            continue

        # Now read the desired records for this domain
        records = []
        for record in domain['records']:
            # Check for misconfiguration of the record
            if 'type' not in record:
                LOG.warning(f'Misconfigured record detected. '
                            f'A record for {name} has not set type and will not be reconciled!')
                continue

            # If this is a dynamic record, use the machine's detected IP
            dynamic_record = record.get('dynamic', False)
            dynamic_answer = machine_ipv6 if record['type'] == 'AAAA' else machine_ipv4
            if dynamic_record and dynamic_answer == '':
                LOG.warning('Could not find machine IP for dynamic record. '
                            f'{record.get("type")} {record.get("hostname", "")}.{name} will not be reconciled!')
                continue

            if not dynamic_record and 'answer' not in record:
                LOG.warning(f'Misconfigured record detected. '
                            f'A record for {name} has not set answer and will not be reconciled!')
                continue

            # Marshal the record configuration
            records.append(DNSRecord(
                hostname=record.get('hostname', ''),
                type=record['type'],
                answer=(dynamic_answer if dynamic_record else record.get('answer', '')),
                ttl=record.get('ttl', 600),
                priority=record.get('priority'),
                dynamic=dynamic_record,
            ))
        
        # Then get the list of *ignored* records
        ignored_records = []
        for record in domain.get('ignored_records', []):
            if 'hostname' not in record:
                LOG.warning(f'Misconfigured ignore record detected. '
                            f'An ignore record for {name} has not set hostname and will not be ignored!')
                continue

            ignored_records.append(DNSRecord(
                hostname=record['hostname'],
                type=record.get('type', ''),
                answer='',
            ))

        domain_configs.append(DomainConfig(
            name=name,
            records=records,
            ignored_records=ignored_records,
            account=all_accounts[domain['account']],
        ))
        ignore_info = f' and {len(ignored_records)} ignored record(s)' if len(ignored_records) else ''
        LOG.info(f'Registered domain {name} with {len(records)} record(s){ignore_info} using account {domain["account"]}')

    return domain_configs

def reconcile_domain_records(domain: 'DomainConfig') -> None:
    LOG.info(f'Reconciling DNS records for domain: {domain.name}')

    existing_records = domain.account.provider.list(domain.name)

    # Filter out any ignored records
    for ignore_record in domain.ignored_records:
        records_to_check = filter(
            lambda r: (not r.reconciled) and \
                      (r.hostname == ignore_record.hostname),
            existing_records
        )
        for record in records_to_check:
            should_ignore = True
            # If type is set, check type as well
            if ignore_record.type != '' and ignore_record.type != record.type:
                should_ignore = False

            # Mark as reconciled early to ignore
            if should_ignore:
                LOG.info(f'Found record {record.type} {record.hostname}.{domain.name} that will be ignored')
                record.reconciled = True

    # For each desired record, check if we can correct an existing record to match it if there is
    # a mismatch. Otherwise, if we find a match, there's nothing to reconcile.
    for desired_record in domain.records:
        # We only consider records for edit if they fulfill all these criteria:
        # * The record hasn't already been reconciled with another desired record
        # * The record type matches the desired record type
        # * The record hostname matches the desired hostname
        records_to_check = filter(
            lambda r: (not r.reconciled) and \
                      (r.type == desired_record.type) and \
                      (r.hostname == desired_record.hostname),
            existing_records
        )

        mismatching_record = None
        for record in records_to_check:
            # Check if there is a mismatch in the record content, TTL or priority (if set)
            mismatch = False
            if record.answer != desired_record.answer:
                mismatch = True
            if record.ttl != desired_record.ttl:
                mismatch = True
            if desired_record.priority is not None and record.priority != desired_record.priority:
                mismatch = True

            # Found a match, no need to update any records
            if not mismatch:
                mismatching_record = None
                record.reconciled = True
                desired_record.reconciled = True
                break
            else:
                mismatching_record = record

        # Of the records that matched the desired type and hostname,
        # we couldn't find one with the correct config. Correct one of them.
        if mismatching_record:
            assert(mismatching_record is not None)
            LOG.info(f'Mismatch detected: updating record - '
                     f'{desired_record.type} {desired_record.hostname}.{domain.name} -> {desired_record.answer} (TTL={desired_record.ttl})')
            domain.account.provider.update(domain.name, mismatching_record, desired_record)
            mismatching_record.reconciled = True
            desired_record.reconciled = True

    # Find out which records are not being used anymore (orphaned) and delete them
    orphaned_records = list(filter(
        lambda r: not r.reconciled,
        existing_records
    ))
    for record in orphaned_records:
        LOG.info(f'Deleting orphaned record - {record.type} {record.hostname}.{domain.name} -> {record.answer}')
        domain.account.provider.delete(domain.name, record)
        record.reconciled = True

    # Then create records for any desired records that haven't been reconciled yet
    records_to_create = list(filter(
        lambda r: not r.reconciled,
        domain.records
    ))
    for desired_record in records_to_create:
        LOG.info(f'Creating DNS record: {desired_record.type} {desired_record.hostname}.{domain.name} -> {desired_record.answer} (TTL={desired_record.ttl})')
        domain.account.provider.create(domain.name, desired_record)
        desired_record.reconciled = True

def controller_loop(args):
    LOG.info('Entering namectl controller loop')
    while True:
        try:
            current_ipv4 = ping4()
            LOG.info(f'Current IPv4 is: {current_ipv4}')
        except:
            LOG.warning('Failed to get IPv4, dynamic A records will not be reconciled')
            current_ipv4 = ''

        try:
            current_ipv6 = ping6()
            LOG.info(f'Current IPv6 is: {current_ipv6}')
        except:
            LOG.warning('Failed to get IPv6, dynamic AAAA records will not be reconciled')
            current_ipv6 = ''

        try:
            domains = read_dns_config(args.config, current_ipv4, current_ipv6)
        except Exception as E:
            LOG.warning('An error occured while reading the DNS configuration. '
                        f'Reconciliation will resume when the configuration file is valid.\n{E}')
            time.sleep(args.loop_period)
            continue

        if not len(domains):
            LOG.warning('No domain configuration detected!')
            continue

        for domain in domains:
            try:
                reconcile_domain_records(domain)
            except Exception as E:
                LOG.warning(f'An error occured while reconciling records for {domain.name}\n{E}')
        
        time.sleep(args.loop_period)
