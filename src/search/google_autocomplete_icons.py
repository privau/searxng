# SPDX-License-Identifier: AGPL-3.0-or-later
"""Runtime patch Google autocomplete icons for the autocompleter responses."""

import json
import typing as t
from urllib.parse import urlencode

import lxml.html


def _google_complete_with_icons(query: str, sxng_locale: str) -> list[t.Union[str, dict[str, str]]]:
    from searx.autocomplete import get
    from searx.engines import engines, google

    google_info: dict[str, t.Any] = google.get_google_info({'searxng_locale': sxng_locale}, engines['google'].traits)
    url = 'https://{subdomain}/complete/search?{args}'
    args = urlencode(
        {
            'q': query,
            'client': 'gws-wiz',
            'hl': google_info['params']['hl'],
        }
    )

    results: list[t.Union[str, dict[str, str]]] = []

    resp = get(url.format(subdomain=google_info['subdomain'], args=args))
    if resp and resp.ok:
        json_txt = resp.text[resp.text.find('[') : resp.text.find(']', -3) + 1]
        data = json.loads(json_txt)

        for item in data[0]:
            suggestion_text = lxml.html.fromstring(item[0]).text_content()
            icon_url = None
            if len(item) > 3 and isinstance(item[3], dict):
                icon_url = item[3].get('zs')

            if isinstance(icon_url, str) and icon_url:
                results.append({'text': suggestion_text, 'icon': icon_url})
            else:
                results.append(suggestion_text)

    return results


def _autocompleter_with_icons(webapp_module):
    results = []

    disabled_engines = webapp_module.sxng_request.preferences.engines.get_disabled()
    raw_text_query = webapp_module.RawTextQuery(webapp_module.sxng_request.form.get('q', ''), disabled_engines)
    sug_prefix = raw_text_query.getQuery()

    for obj in webapp_module.searx.answerers.STORAGE.ask(sug_prefix):
        if isinstance(obj, webapp_module.Answer):
            results.append(obj.answer)

    if len(raw_text_query.autocomplete_list) == 0 and len(sug_prefix) > 0:
        sxng_locale = webapp_module.sxng_request.preferences.get_value('language')
        backend_name = webapp_module.sxng_request.preferences.get_value('autocomplete')

        for result in webapp_module.search_autocomplete(backend_name, sug_prefix, sxng_locale):
            result_text = result if isinstance(result, str) else result.get('text', '')
            icon_url = None if isinstance(result, str) else result.get('icon')

            if result_text != sug_prefix:
                suggestion_text = raw_text_query.changeQuery(result_text).getFullQuery()
                if isinstance(icon_url, str) and icon_url:
                    results.append({'text': suggestion_text, 'icon': webapp_module.image_proxify(icon_url)})
                else:
                    results.append(suggestion_text)

    if len(raw_text_query.autocomplete_list) > 0:
        for autocomplete_text in raw_text_query.autocomplete_list:
            results.append(raw_text_query.get_autocomplete_full_query(autocomplete_text))

    if webapp_module.sxng_request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return webapp_module.Response(json.dumps(results), mimetype='application/json')
    else:
        # chromium only shows 3 suggestions unless we attach relevances
        relevances = {'google:suggestrelevance': [600 - i for i in range(len(results))]}
        suggestions = json.dumps([sug_prefix, results, [], [], relevances])
        mimetype = 'application/x-suggestions+json'

    suggestions = webapp_module.escape(suggestions, False)
    return webapp_module.Response(suggestions, mimetype=mimetype)


def apply_google_autocomplete_icons(app) -> None:
    from flask import request
    from searx import autocomplete as sx_autocomplete
    from searx import webapp as sx_webapp

    sx_autocomplete.google_complete = _google_complete_with_icons
    sx_autocomplete.backends['google'] = _google_complete_with_icons

    def patched_autocompleter():
        return _autocompleter_with_icons(sx_webapp)

    @app.after_request
    def add_image_proxy_cache_headers(response):
        if request.path == '/autocompleter' and request.method == 'GET':
            if 200 <= response.status_code < 300:
                response.headers['Cache-Control'] = 'private, max-age=3600, stale-while-revalidate=300'
                response.headers['Vary'] = 'Cookie'
            return response

        if request.path != '/image_proxy':
            return response

        # Cache successful proxied images for one day.
        if 200 <= response.status_code < 300:
            response.headers['Cache-Control'] = 'public, max-age=86400'
            return response

        # Cache misses briefly to avoid immediate repeated 404 fetches.
        if response.status_code in (404, 410):
            response.headers['Cache-Control'] = 'public, max-age=300'

        return response

    sx_webapp.autocompleter = patched_autocompleter
    app.view_functions['autocompleter'] = patched_autocompleter
