#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the Authorized API."""

from flask import current_app, abort
from os import environ

def valid_api_key(request):
    return environ.get('AUTHORIZED_API') and request.headers.get('Authorization', '')[7:] == environ.get('AUTHORIZED_API')
