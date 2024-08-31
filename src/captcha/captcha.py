#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the CAPTCHA."""

import hashlib
from ipaddress import ip_address

from flask import redirect, url_for
from searx import limiter
from searx.botdetection import ip_lists, get_real_ip
from searx.webutils import new_hmac, is_hmac_of


def redirect_to_search(token, request):
    form_data = {k: v for k, v in request.form.items() if k != 'captcha_answer'}
    response = redirect(url_for('search', **form_data))
    response.set_cookie('captcha_token', token, max_age=60 * 60 * 24 * 365 * 5)  # 5 years
    return response


def render_captcha(raw_text_query, search_query, selected_locale, render, captcha_answer):
    # Render CAPTCHA question
    return render(
        'captcha.html',
        title="Click to Continue",
        line1="priv.au is under heavy attack.",
        line2="This safeguard will be removed once the attack subsides.",
        button="Continue",
        captcha_answer=captcha_answer,
        query=raw_text_query.getQuery(),
        time_range=search_query.time_range or '',
        current_language=selected_locale,
    )


def handle_captcha(request, secret_key, raw_text_query, search_query, selected_locale, render):
    # convert IP into bytes
    ip = ip_address(get_real_ip(request))
    match, _ = ip_lists.pass_ip(ip, limiter.get_cfg())

    # Check if the IP is in the whitelist
    if not match:
        # make sure captcha_token is a valid HMAC
        captcha_token = request.cookies.get('captcha_token')
        ip_hash = hashlib.sha256(ip.packed).digest()
        ip_hash_plus_salt = hashlib.sha256(ip_hash + "blahblahblah".encode()).digest()

        # Check if the CAPTCHA token is valid
        if not captcha_token or not is_hmac_of(secret_key, ip_hash, captcha_token):

            # Check if the CAPTCHA was answered correctly
            captcha_answer = request.form.get('captcha_answer')

            if (
                captcha_answer
                and request.method == 'POST'
                and is_hmac_of(secret_key, ip_hash_plus_salt, captcha_answer)
            ):
                # Redirect to search page with the new token
                token = new_hmac(secret_key, ip_hash)
                return redirect_to_search(token, request)

            return render_captcha(
                raw_text_query, search_query, selected_locale, render, new_hmac(secret_key, ip_hash_plus_salt)
            )

    return None
