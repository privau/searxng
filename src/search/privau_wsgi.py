# SPDX-License-Identifier: AGPL-3.0-or-later
"""WSGI entrypoint that applies PrivAU patches before loading the app."""

from searx.search.wikipedia_timeout import apply_wikipedia_timeout

apply_wikipedia_timeout()

from searx.webapp import app  # noqa: F401  # loads engines via init()

from searx.search.google_patch import apply_google_patch

apply_google_patch()
