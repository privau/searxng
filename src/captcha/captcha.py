#!/usr/bin/env python

import base64
import json
import time
from ipaddress import ip_address
from os import environ
from urllib.parse import urlencode

from flask import make_response, redirect, url_for
from searx import limiter
from searx.auth import valid_api_key
from searx.botdetection import ip_lists
from searx.extended_types import sxng_request
from searx.webadapter import get_selected_categories
from searx.webapp import render
from searx.webutils import is_hmac_of, new_hmac


def _b64e(x):
    return base64.urlsafe_b64encode(x).rstrip(b"=").decode()


def _b64d(x):
    return base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))


def _pack(secret, obj):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return _b64e(raw), new_hmac(secret, raw)


def _unpack(secret, payload, sig):
    try:
        raw = _b64d(payload)
        if not is_hmac_of(secret, raw, sig):
            return None
        return json.loads(raw)
    except Exception:
        return None


def _original_params(request):
    src = request.form if request.method == "POST" and request.form else request.args
    if hasattr(src, "lists"):
        return [(k, v) for k, vals in src.lists() for v in vals if not k.startswith("captcha_")]
    return [(k, v) for k, v in src.items() if not k.startswith("captcha_")]


def _q_from_params(params):
    q = ""
    for k, v in params:
        if k == "q":
            q = v
    return q


def _search_url(params):
    url = url_for("search")
    return url + "?" + urlencode(params) if params else url


def _captcha_url(params):
    url = url_for("captcha")
    return url + "?" + urlencode(params) if params else url


def _pass(secret):
    now = int(time.time())
    # users put into groups / decrease uniqueness of the token
    exp = round((now + 50000) / 10000) * 10000
    a, b = _pack(secret, {"exp": exp})
    return a + "." + b, exp - now


def _pass_ok(secret, token):
    if not token or "." not in token:
        return False
    a, b = token.split(".", 1)
    x = _unpack(secret, a, b)
    return bool(x and x.get("exp", 0) >= int(time.time()))


def _challenge(secret):
    now = int(time.time() * 1000)
    return _pack(secret, {"iat_ms": now, "exp_ms": now + 300000})


def _grant(secret):
    a, b = _pack(secret, {"exp_ms": int(time.time() * 1000) + 5000})
    return a + "." + b


def _grant_ok(secret, request):
    token = request.args.get("captcha_pass") or request.form.get("captcha_pass", "")
    if not token or "." not in token:
        return False
    a, b = token.split(".", 1)
    x = _unpack(secret, a, b)
    return bool(x and x.get("exp_ms", 0) >= int(time.time() * 1000))


def _should_skip(request):
    if not environ.get("CAPTCHA"):
        return True
    if valid_api_key(request):
        return True
    ip = ip_address(request.remote_addr)
    ok, _ = ip_lists.pass_ip(ip, limiter.get_cfg())
    return ok


def _wait_page(secret, params):
    a, b = _challenge(secret)
    url = _captcha_url(params + [("captcha_challenge", a), ("captcha_signature", b)])
    html = render(
        "captcha.html",
        refresh_url=url,
        q=_q_from_params(params),
        selected_categories=get_selected_categories(sxng_request.preferences, sxng_request.form),
    )
    r = make_response(html, 200)
    r.headers["Content-Type"] = "text/html; charset=utf-8"
    r.headers["Cache-Control"] = "no-store"
    r.headers["X-Robots-Tag"] = "noindex, nofollow"
    return r


def _complete(params, secret):
    grant = _grant(secret)
    token, max_age = _pass(secret)

    r = redirect(_search_url(params + [("captcha_pass", grant)]), code=302)
    r.set_cookie(
        "captcha_token",
        token,
        max_age=max_age,
    )
    return r


def handle_captcha(request, secret, *_):
    if _should_skip(request):
        return None
    if _pass_ok(secret, request.cookies.get("captcha_token")):
        return None
    if _grant_ok(secret, request): # for people without cookies
        return None
    return redirect(_captcha_url(_original_params(request)), code=302)


def captcha(request, secret):
    params = _original_params(request)

    if _should_skip(request):
        return _complete(params, secret)
    if _pass_ok(secret, request.cookies.get("captcha_token")):
        return _complete(params, secret)

    a = request.args.get("captcha_challenge", "")
    b = request.args.get("captcha_signature", "")

    if a and b:
        x = _unpack(secret, a, b)
        now = int(time.time() * 1000)
        if x and x.get("iat_ms", 0) <= now <= x.get("exp_ms", 0):
            if now - x["iat_ms"] < 800:
                return "Too fast", 403
            return _complete(params, secret)

    return _wait_page(secret, params)