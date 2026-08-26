#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Authorised API"""

import base64
from os import environ


def _keys():
    keys = {}
    for item in environ.get('AUTHORISED_API', '').replace('\n', ',').split(','):
        item = item.strip()
        if not item:
            continue
        name, sep, limit = item.rpartition(':')
        if sep and name and limit.isdigit():
            keys[name] = int(limit)
        else:
            keys[item] = 0
    return keys


def _offered(request):
    offered = []
    scheme, _, rest = request.headers.get('Authorization', '').partition(' ')
    rest, kind = rest.strip(), scheme.lower()
    if kind == 'bearer' and rest:
        offered.append(rest)
    elif kind == 'basic' and rest:
        try:
            user, _, password = base64.b64decode(rest).decode().partition(':')
            offered.extend(part for part in (password, user) if part)
        except (ValueError, UnicodeDecodeError):
            pass
    if header := request.headers.get('X-API-Key', '').strip():
        offered.append(header)
    return offered


def _match(request, keys):
    offered = _offered(request)
    return next((key for key in keys if key in offered), None)


class _Formats(list):
    def __init__(self, formats, keys):
        super().__init__(formats)
        self._keys = keys

    def __contains__(self, item):
        if list.__contains__(self, item):
            return True
        from flask import has_request_context
        from searx.extended_types import sxng_request

        return has_request_context() and _match(sxng_request, self._keys)


def apply_authorised_api(app):
    keys = _keys()
    if not keys:
        return

    from flask import Response, abort
    from searx import limiter, settings, valkeydb, valkeylib, webapp as sx_webapp
    from searx.extended_types import sxng_request

    if not isinstance(settings['search']['formats'], _Formats):
        settings['search']['formats'] = _Formats(settings['search']['formats'], keys)

    original = app.view_functions['search']

    def _ratelimit(resp, limit, remaining, retry=None):
        body = resp[0] if isinstance(resp, tuple) else resp
        body.headers['X-RateLimit-Limit'] = str(limit)
        body.headers['X-RateLimit-Remaining'] = str(max(0, remaining))
        if retry is not None:
            body.headers['Retry-After'] = str(retry)
        return resp

    def search(*args, **kwargs):
        key = _match(sxng_request, keys) if sxng_request.form.get('format', 'html') != 'html' else None
        if key and (limit := keys[key]):
            client = valkeydb.client()
            if client is None:
                abort(503)
            name = f'authorised_api:{key}'
            count = valkeylib.incr_counter(client, name, expire=86400)
            remaining = limit - count
            if count > limit:
                ttl = client.ttl('SearXNG_counter_' + valkeylib.secret_hash(name))
                response = Response('{"error": "Too Many Requests"}', 429, mimetype='application/json')
                abort(_ratelimit(response, limit, 0, ttl if ttl and ttl > 0 else 86400))
            return _ratelimit(original(*args, **kwargs), limit, remaining)
        return original(*args, **kwargs)

    app.view_functions['search'] = sx_webapp.search = search
    check = limiter.filter_request
    limiter.filter_request = lambda request: None if _match(request, keys) else check(request)
