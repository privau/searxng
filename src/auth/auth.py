#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Authorised API"""

import base64
from os import environ
from threading import Lock
from time import monotonic


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
    from searx import limiter, settings, webapp as sx_webapp
    from searx.extended_types import sxng_request

    if not isinstance(settings['search']['formats'], _Formats):
        settings['search']['formats'] = _Formats(settings['search']['formats'], keys)

    hits, lock = {}, Lock()
    original = app.view_functions['search']

    def search(*args, **kwargs):
        key = _match(sxng_request, keys) if sxng_request.form.get('format', 'html') != 'html' else None
        if key and (limit := keys[key]):
            now = monotonic()
            with lock:
                start, count = hits.get(key, (now, 0))
                if now - start >= 86400:
                    start, count = now, 0
                if count >= limit:
                    retry = max(1, int(start + 86400 - now) + 1)
                    response = Response('{"error": "Too Many Requests"}', 429, mimetype='application/json')
                    response.headers['Retry-After'] = str(retry)
                    abort(response)
                hits[key] = (start, count + 1)
        return original(*args, **kwargs)

    app.view_functions['search'] = sx_webapp.search = search
    check = limiter.filter_request
    limiter.filter_request = lambda request: None if _match(request, keys) else check(request)
