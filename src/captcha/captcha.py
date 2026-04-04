#!/usr/bin/env python

import base64 as _0
import json as _2
import time as _3
from ipaddress import ip_address as _4
from os import environ

from flask import redirect as _5, url_for as _6
from searx import limiter as _7
from searx.botdetection import ip_lists as _8
from searx.webutils import new_hmac as _9, is_hmac_of as _A


def _B(x):
    return _0.urlsafe_b64encode(x).rstrip(b"=").decode()


def _C(x):
    return _0.urlsafe_b64decode(x + "=" * (-len(x) % 4))


def _E(s, o):
    z = _2.dumps(o, separators=(",", ":"), sort_keys=True).encode()
    return _B(z), _9(s, z)


def _F(s, p, g):
    try:
        z = _C(p)
        return _2.loads(z) if _A(s, z, g) else None
    except Exception:
        return None


def make_pass_token(secret, request):
    x, y = _E(
        secret,
        {
            "exp": int(_3.time()) + (60 * 60 * 12),
        },
    )
    return f"{x}.{y}"


def valid_pass_token(secret, request, token):
    if not token or "." not in token:
        return False
    x, y = token.split(".", 1)
    z = _F(secret, x, y)
    return bool(
        z
        and z.get("exp", 0) >= int(_3.time())
    )


def make_challenge(secret, request):
    t = int(_3.time() * 1000)
    return _E(
        secret,
        {
            "iat_ms": t,
            "exp_ms": t + (300 * 1000),
        },
    )


def redirect_to_search(token, request):
    q = {
        k: v
        for k, v in request.values.items()
        if not (k[:8] == "captcha_" or k == "company")
        and v != ""
    }
    r = _5(_6("search", **q))
    r.set_cookie(
        "captcha_token",
        token,
        max_age=(60 * 60 * 12),
        httponly=True,
        secure=True,
        samesite="Strict",
    )
    return r


def redirect_to_challenge(raw_text_query, search_query, selected_locale, request, secret):
    a, b = make_challenge(secret, request)
    u = request.values.get("theme") or ""
    z = {
        "captcha_verify": "1",
        "captcha_challenge": a,
        "captcha_signature": b,
        "q": raw_text_query.getQuery(),
        "time_range": search_query.time_range or "",
        "language": selected_locale,
        # Must be "0".."2": empty safesearch in the URL makes parse_safesearch() raise.
        "safesearch": str(search_query.safesearch),
    }
    if u:
        z["theme"] = u
    return _5(_6("search", **z), code=302)


def handle_captcha(request, secret, raw_text_query, search_query, selected_locale):
    u = _4(request.remote_addr)
    v, _ = _8.pass_ip(u, _7.get_cfg())

    if v or not environ.get("CAPTCHA"):
        return None

    w = request.cookies.get("captcha_token")
    if valid_pass_token(secret, request, w):
        return None

    if request.values.get("captcha_verify"):
        a = request.values.get("captcha_challenge", "")
        b = request.values.get("captcha_signature", "")
        c = _F(secret, a, b)
        n = int(_3.time() * 1000)

        if c and c.get("exp_ms", 0) >= n >= c.get("iat_ms", 0):
            return redirect_to_search(make_pass_token(secret, request), request)

    return redirect_to_challenge(
        raw_text_query,
        search_query,
        selected_locale,
        request,
        secret,
    )
