# SPDX-License-Identifier: AGPL-3.0-or-later
"""WSGI entrypoint that applies PrivAU patches before loading the app."""

import os

from searx.search.supplemental_timeout import apply_supplemental_timeout
from searx.search.google_autocomplete_icons import apply_google_autocomplete_icons

apply_supplemental_timeout()

from searx.webapp import app, render  # noqa: F401

if os.environ.get('PRIVACYPOLICY') == '/privacy':
    @app.route('/privacy', methods=['GET'])
    def privau_privacy_policy():
        return render('privacy-policy.html')

if os.environ.get('DONATE') == '/donate':
    @app.route('/donate', methods=['GET'])
    def privau_donate():
        return render('donation.html')

apply_google_autocomplete_icons(app)
