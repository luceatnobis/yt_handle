#!/usr/bin/env python3

from __future__ import print_function

import os
import sys
import shutil
import httplib2

import oauth2client
try:
    import apiclient as googleapiclient
except ImportError:
    import googleapiclient

from oauth2client.file import Storage, Credentials
from oauth2client.client import flow_from_clientsecrets


CS = "client_secrets.json"
CREDS = "credentials.json"
YOUTUBE_DATA_ROOT = '~/.youtube'
YOUTUBE_READ_WRITE_SSL_SCOPE = (
    "https://www.googleapis.com/auth/youtube.force-ssl")


def return_handle(id_name):
    identity_root = os.path.expanduser(YOUTUBE_DATA_ROOT)
    identity_folder = os.path.join(identity_root, id_name)

    if not os.path.exists(identity_folder):
        n = input("Identity %s is not known; create it? [Y|n] " % id_name)
        if not n or n.lower().startswith('y'):
            create_identity(id_name)
        else:
            sys.exit()
    identity = _retrieve_files(identity_folder)
    c = Credentials().new_from_json(identity['credentials'])
    handle = c.authorize(http=httplib2.Http())

    return googleapiclient.discovery.build(
        "youtube", "v3", http=handle)


def create_identity(id_name, cs_location=None):
    if cs_location is None:
        n = input("Please specify the location of the client_secrets file: ")
        cs_location = os.path.abspath(os.path.expanduser(n))

    if os.path.isdir(cs_location):
        cs_location = os.path.join(cs_location, CS)

    identity_root = os.path.expanduser(YOUTUBE_DATA_ROOT)
    identity_folder = os.path.join(identity_root, id_name)

    if os.path.exists(identity_folder):
        return

    id_cs_location = os.path.join(identity_root, id_name, CS)
    id_cred_location = os.path.join(identity_root, id_name, CREDS)

    storage = Storage(id_cred_location)
    credentials = storage.get()

    if credentials and not credentials.invalid:
        return credentials  # credentials exist

    flow = flow_from_clientsecrets(
        cs_location, scope=YOUTUBE_READ_WRITE_SSL_SCOPE)

    flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
    authorize_url = flow.step1_get_authorize_url()
    code = _console_auth(authorize_url)

    if code:
        credential = flow.step2_exchange(code, http=None)
        os.makedirs(identity_folder)
        storage.put(credential)
        credential.set_store(storage)
        shutil.copyfile(cs_location, id_cs_location)
        return credential
    else:
        print("Invalid input, exiting", file=sys.stderr)
        sys.exit()


def _console_auth(authorize_url):
    """Show authorization URL and return the code the user wrote."""
    message = "Check this link in your browser: {0}".format(authorize_url)
    sys.stderr.write(message + "\n")
    try:
        input = raw_input  # For Python2 compatability
    except NameError:
        # For Python3 on Windows compatability
        try:
            from builtins import input as input
        except ImportError:
            pass
    return input("Enter verification code: ")


def _retrieve_files(folder):
    cs_f = os.path.join(folder, CS)
    creds_f = os.path.join(folder, CREDS)

    with open(cs_f) as sec, open(creds_f) as cred:
        secrets = sec.read()
        credentials = cred.read()

    return dict(secrets=secrets, credentials=credentials)
