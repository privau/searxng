#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the Authorized API."""

import base64
from os import environ
from flask import abort

def valid_api_key(request):
    api_key = environ.get('AUTHORIZED_API')
    
    if not api_key:
        return False
        
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Basic '):
        return False
        
    try:
        encoded_credentials = auth_header[6:]  # remove 'Basic ' prefix
        decoded = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded.split(':', 1)
        return password == api_key
    except Exception:
        return False
