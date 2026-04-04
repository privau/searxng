#!/usr/bin/env python

import base64
import json
import time
from ipaddress import ip_address
from os import environ
from urllib.parse import urlencode

from flask import redirect, make_response, url_for
from searx import limiter
from searx.auth import valid_api_key
from searx.botdetection import ip_lists
from searx.webutils import new_hmac, is_hmac_of


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


def _params(request):
    out = []
    for k, vals in request.args.lists():
        if k.startswith("captcha_"):
            continue
        for v in vals:
            out.append((k, v))
    return out


def _fix_params(x):
    out = []
    for i in x or []:
        if isinstance(i, (list, tuple)) and len(i) == 2:
            out.append((i[0], i[1]))
    return out


def _url(params):
    p = _fix_params(params)
    u = url_for("search")
    if not p:
        return u
    return u + "?" + urlencode(p, doseq=True)


def _pass(secret):
    a, b = _pack(secret, {"exp": int(time.time()) + 43200})
    return a + "." + b


def _pass_ok(secret, token):
    if not token or "." not in token:
        return False
    a, b = token.split(".", 1)
    x = _unpack(secret, a, b)
    return bool(x and x.get("exp", 0) >= int(time.time()))


def _challenge(secret, params):
    now = int(time.time() * 1000)
    return _pack(
        secret,
        {
            "iat_ms": now,
            "exp_ms": now + 300000,
            "params": _fix_params(params),
        },
    )


def _go_search(params, token):
    r = redirect(_url(params), code=302)
    r.set_cookie(
        "captcha_token",
        token,
        max_age=43200,
        httponly=True,
        secure=True,
        samesite="Strict",
    )
    return r


def _wait_page(request, secret):
    p = _params(request)
    a, b = _challenge(secret, p)
    p.append(("captcha_challenge", a))
    p.append(("captcha_signature", b))

    html = (
        "<!doctype html>"
        "<html>"
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark">'
        '<meta http-equiv="refresh" content="1;url=' + _url(p) + '">'
        "<style>"
        ":root{color-scheme:light dark;}"
        "html,body{margin:0;padding:0;width:100%;height:100%;background:#ffffff;}"
        "@media (prefers-color-scheme: dark){html,body{background:#0f1115;}}"
        "</style>"
        "</head>"
        "<body></body>"
        "</html>"
    )

    r = make_response(html, 200)
    r.headers["Content-Type"] = "text/html; charset=utf-8"
    r.headers["Cache-Control"] = "no-store"
    return r


def handle_captcha(request, secret, *_):
    if not environ.get("CAPTCHA"):
        return None

    if valid_api_key(request):
        return None

    ip = ip_address(request.remote_addr)
    ok, _ = ip_lists.pass_ip(ip, limiter.get_cfg())

    if ok:
        return None

    token = request.cookies.get("captcha_token")
    if _pass_ok(secret, token):
        if request.args.get("captcha_challenge") or request.args.get("captcha_signature"):
            return redirect(_url(_params(request)), code=302)
        return None

    a = request.args.get("captcha_challenge", "")
    b = request.args.get("captcha_signature", "")

    if a and b:
        x = _unpack(secret, a, b)
        now = int(time.time() * 1000)

        if x and x.get("iat_ms", 0) <= now <= x.get("exp_ms", 0):
            if now - x.get("iat_ms", 0) < 800:
                return "Too fast", 403
            return _go_search(x.get("params", []), _pass(secret))

    return _wait_page(request, secret)