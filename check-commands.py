#!/usr/bin/env python3

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import os, sys, json, time, argparse


def get_token():
    client_id = os.environ['API42_ID']
    client_secret = os.environ['API42_SECRET']

    client = BackendApplicationClient(client_id=client_id)
    api = OAuth2Session(client=client)
    api.fetch_token(token_url='https://api.intra.42.fr/oauth/token', client_id=client_id, client_secret=client_secret)
    return api


def check_login(api, login):
    time.sleep(1)
    response = api.get(f"https://api.intra.42.fr/v2/users/{login}").json()
    if response:
        response = api.get(f"https://api.intra.42.fr/v2/campus/1/products/15/commands?filter[owner_id]={response['id']}").json()

        if response:
            if args.verbose:
                print(f"{login}: OK")
            return True
        else:
            if args.verbose:
                print(f"{login}: KO! User did not purchase Hall Voice Change on intra shop")
            return False
    else:
        if args.verbose:
            print(f"{login}: User does not exist")
        return False


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose mode')
        parser.add_argument('logins', nargs='*', default=[], help='Logins to check')
        args = parser.parse_args()

        if not args.logins:
            sys.exit()

        if args.verbose:
            print('Logins:', args.logins, '\n')

        token = get_token()
        checks = [check_login(token, login) for login in args.logins]
        if False in checks:
            sys.exit(1)
    except KeyboardInterrupt:
        sys.exit()
