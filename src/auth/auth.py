#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the Authorized API."""

import flask

from flask import current_app, abort
from os import environ

valid_tokens_set = None

def get_tokens():
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

    if auth is None:
        auth = request.path.split('/')[0]

    return auth in get_tokens()

def auth_search_key(request, key):
    if not environ.get('AUTHORIZED_API'):
        return flask.abort(403)
    
    with current_app.test_client() as client:
        headers = {'Authorization': f'Bearer {key}','User-Agent': 'AuthorizedAPI'}
        if request.method == 'GET':
            response = client.get('/search', query_string=request.args, headers=headers)
        elif request.method == 'POST':
            response = client.post('/search', data=request.form, headers=headers)
    
    return response
