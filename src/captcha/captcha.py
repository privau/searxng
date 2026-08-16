#!/usr/bin/env python

# Stub file

def handle_captcha(request, secret, *_):
    return False

def captcha(request, secret):
    from flask import Response

    return Response('', status=404)
