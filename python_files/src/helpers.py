import configparser
import getpass
import sys
import os

import boto3
import requests
from bs4 import BeautifulSoup
from os.path import expanduser
import pytz
from tzlocal import get_localzone
from urllib.parse import urlparse
import base64
import subprocess
from subprocess import Popen, PIPE
import json


awsconfigdirectory = '.aws'
awsconfigfile = os.path.join(awsconfigdirectory, 'credentials')
region = 'eu-west-1'
outputformat = 'json'


def iam_login_default(long_term_cred_profile, role_name, account_id, profile_to_configure):
    print(f'Long term profile: {long_term_cred_profile}')
    print(f'Role: {role_name}')

    profile_name = long_term_cred_profile 

    credentialsFile = readCredentialsFile()
    verifyCredentialsFile(credentialsFile, profile_name)

    profile_name_mfa = profile_to_configure  # 'default'

    aws_accesskey_id = credentialsFile.get(profile_name, "aws_access_key_id")
    aws_secret_accesskey = credentialsFile.get(profile_name, "aws_secret_access_key")
    iamClient = boto3.client('iam', aws_access_key_id=aws_accesskey_id, aws_secret_access_key=aws_secret_accesskey)
    client_sts = boto3.client('sts', aws_access_key_id=aws_accesskey_id, aws_secret_access_key=aws_secret_accesskey)
    
    response = client_sts.get_caller_identity()
    arn = response['Arn']
    print(f'Arn: {arn}')

    if credentialsFile.has_option(profile_name, "username"):
        username = credentialsFile.get(profile_name, "username")
    else:
        username = input("Username: ")

    mfaDevices = iamClient.list_mfa_devices(UserName=username)
    mfa_device = mfaDevices['MFADevices'][0]['SerialNumber']
    print((f'Using MFADevice: {mfa_device}'))

    mfa_code = input("Enter the MFA code: ")

    session_token = client_sts.get_session_token(DurationSeconds=43200, SerialNumber=mfa_device, TokenCode=mfa_code)
    aws_accesskey_id_mfa = session_token['Credentials']['AccessKeyId']
    aws_secret_access_key_mfa = session_token['Credentials']['SecretAccessKey']
    aws_session_token_mfa = session_token['Credentials']['SessionToken']
    
    role = ''

    if not account_id:
        client_organizations_mfa = boto3.client('organizations', aws_access_key_id=aws_accesskey_id_mfa, aws_secret_access_key=aws_secret_access_key_mfa, aws_session_token=aws_session_token_mfa)
        response = client_organizations_mfa.list_accounts()
        accounts = []
        print('***** Accounts *****')
        count = 0
        for account in response['Accounts']:
            account_name = account['Name']
            account_id = account['Id']
            accounts.append(account_id)
            print(f'{count}: {account_name} ({account_id})')
            count += 1

        account_index = int(input("Choose account: "))
        account_id = accounts[account_index]
        role = f'arn:aws:iam::{account_id}:role/{role_name}'
    else:
        role = f'arn:aws:iam::{account_id}:role/{role_name}'

    writeTokenToCredentialsFile(credentialsFile, profile_name_mfa, session_token, role, username)

    session = boto3.session.Session(profile_name=profile_name_mfa)
    client = session.client('sts')
    response = client.get_caller_identity()
    assumed_arn = response['Arn']

    local_tz = get_localzone()
    expiration = session_token['Credentials']['Expiration'].replace(tzinfo=pytz.utc).astimezone(local_tz)
    print('-------------------------------------------------------------------')
    print(f'Assumed Arn: {assumed_arn}')
    print(f'Profile:     {profile_name_mfa}')
    print(f'Expire:      {expiration}')
    print('-------------------------------------------------------------------')
    

def readCredentialsFile():
    home = expanduser("~")
    filename = os.path.join(home, awsconfigfile)
    print(f'path: {filename}')
    credentialsFile = configparser.RawConfigParser()
    credentialsFile.read(filename)
    return credentialsFile


def verifyCredentialsFile(credentialsFile, profileName):
    if not credentialsFile.has_section(profileName):
        print(("Profile '{0}' doesn't exist. Use create instead.".format(profileName)))
        sys.exit(0)


def writeTokenToCredentialsFile(credentialsFile, profileName, token, role, username):
    if not credentialsFile.has_section(profileName):
        credentialsFile.add_section(profileName)

    credentialsFile.set(profileName, 'output', outputformat)
    credentialsFile.set(profileName, 'region', region)
    credentialsFile.set(profileName, 'aws_access_key_id', token['Credentials']['AccessKeyId'])
    credentialsFile.set(profileName, 'aws_secret_access_key', token['Credentials']['SecretAccessKey'])
    credentialsFile.set(profileName, 'aws_session_token', token['Credentials']['SessionToken'])
    credentialsFile.set(profileName, 'source_profile', 'default')
    if role:
        credentialsFile.set(profileName, 'role_arn', role)
    if username:
        credentialsFile.set(profileName, 'username', username)
    credentialsFile.remove_option(profileName, 'role')

    writeCredentialsFile(credentialsFile)


def writeCredentialsFile(credentialsFile):
    home = expanduser("~")
    filename = os.path.join(home, awsconfigfile)
    # Write the updated config file
    with open(filename, 'w+') as configfile:
        credentialsFile.write(configfile)
