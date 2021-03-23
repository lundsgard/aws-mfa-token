from helpers import iam_login_default
import click


@click.command()
@click.option('--role-name', '-r', required='true', type=click.STRING, help='Name of the role that will be assumed')
@click.option('--long-term-cred-profile', '-l', required='true', type=click.STRING, help='The name of the AWS profile in ~/.aws/credentials where long term credentials are')
@click.option('--account-id', '-i', type=click.STRING, help='Bypass the Organization accounts check with providing the account id directly')
@click.option('--profile-to-configure', '-p', default='default', type=click.STRING, help='The profile to be configured. Default is \'default\' profile')
@click.option('--configure', '-c', is_flag='true', help='Initiate a configuration of an aws-mfa-token profile')
def main(**kwargs):
    configure = kwargs['configure']
    if configure:
        print('Ready to configure!!')
        long_term_cred_profile = input('./aws/config profile with long term access keys: ')
        account_id = input('AWS Account ID: ')

        return

    role_name = kwargs['role_name']
    long_term_cred_profile = kwargs['long_term_cred_profile']
    account_id = kwargs['account_id']
    profile_to_configure = kwargs['profile_to_configure']
    iam_login_default(long_term_cred_profile, role_name, account_id, profile_to_configure)


if __name__ == '__main__':
    main()
    