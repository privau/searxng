#!/usr/bin/env python

# Stub file

def handle_captcha(request, secret, *_):
    return None

def captcha(request, secret):
    from searx.webapp import render

    return render("captcha.html")
