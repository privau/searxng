# SPDX-License-Identifier: AGPL-3.0-or-later
"""WSGI entrypoint that applies PrivAU patches before loading the app."""

from searx.search.supplemental_timeout import apply_supplemental_timeout
from searx.search.google_autocomplete_icons import apply_google_autocomplete_icons

apply_supplemental_timeout()

from searx.webapp import app  # noqa: F401

apply_google_autocomplete_icons(app)
