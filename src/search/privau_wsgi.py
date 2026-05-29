# SPDX-License-Identifier: AGPL-3.0-or-later
"""WSGI entrypoint that applies PrivAU patches before loading the app."""

from searx.search.supplemental_timeout import apply_supplemental_timeout

apply_supplemental_timeout()

from searx.webapp import app  # noqa: F401
