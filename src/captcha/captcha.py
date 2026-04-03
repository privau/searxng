#!/usr/bin/env python

import base64 as _0
import hashlib as _1
import json as _2
import time as _3
from ipaddress import ip_address as _4
from os import environ

from flask import redirect as _5, url_for as _6
from searx import limiter as _7
from searx.botdetection import ip_lists as _8
from searx.webutils import new_hmac as _9, is_hmac_of as _A


MIN_WAIT_SECONDS = int(environ.get("CAPTCHA_MIN_WAIT", "1"))


def _B(x):
    return _0.urlsafe_b64encode(x).rstrip(b"=").decode()


def _C(x):
    return _0.urlsafe_b64decode(x + "=" * (-len(x) % 4))


def _D(r):
    return _1.sha256(_4(r.remote_addr).packed).hexdigest()


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
            "ip": _D(request),
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
        and z.get("ip") == _D(request)
    )


def make_challenge(secret, request):
    t = int(_3.time())
    return _E(
        secret,
        {
            "iat": t,
            "exp": t + 300,
            "ip": _D(request),
        },
    )


def redirect_to_search(token, request):
    q = {
        k: v
        for k, v in request.values.items()
        if not (k[:8] == "captcha_" or k == "company")
    }
    r = _5(_6("search", **q))
    r.set_cookie(
        "captcha_token",
        token,
        max_age=(60 * 60 * 12),
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return r


def render_captcha(raw_text_query, search_query, selected_locale, render, request, secret):
    a, b = make_challenge(secret, request)
    return render(
        "captcha.html",
        title="Checking your browser",
        captcha_wait=MIN_WAIT_SECONDS,
        captcha_url=_6(
            "search",
            captcha_verify="1",
            captcha_challenge=a,
            captcha_signature=b,
            q=raw_text_query.getQuery(),
            time_range=search_query.time_range or "",
            language=selected_locale,
            safesearch=request.values.get("safesearch", ""),
            theme=request.values.get("theme", ""),
        ),
    )


def handle_captcha(request, secret, raw_text_query, search_query, selected_locale, render):
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
        n = _3.time()

        if c and (
            c.get("exp", 0) >= int(n)
            and c.get("ip") == _D(request)
            and n >= c.get("iat", 0) + MIN_WAIT_SECONDS
        ):
            return redirect_to_search(make_pass_token(secret, request), request)

    return render_captcha(
        raw_text_query,
        search_query,
        selected_locale,
        render,
        request,
        secret,
    )