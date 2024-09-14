#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the Authorized API."""

from os import environ

valid_tokens_set = None

def load_tokens():
    global valid_tokens_set
    if valid_tokens_set is None:
        try:
            with open("/auth_tokens.txt") as file:
                valid_tokens_set = {line.strip() for line in file}
        except Exception:
            valid_tokens_set = set()
    return valid_tokens_set

def valid_api_key(request):
    if not environ.get('AUTHORIZED_API'):
        return False
    auth = request.headers.get('Authorization', '')[7:]
    return auth and auth in load_tokens()
