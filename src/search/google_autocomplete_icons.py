# SPDX-License-Identifier: AGPL-3.0-or-later
"""Runtime patch Google autocomplete icons for the autocompleter responses."""

import base64
import html
import json
import typing as t
from urllib.parse import urlencode, urlparse

import lxml.html

Result = dict[str, str]


def _slice_google_json(text: str) -> str:
    start = text.find('[')
    if start < 0:
        return '[]'
    blob = text[start:]
    depth = 0
    for index, char in enumerate(blob):
        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                return blob[: index + 1]
    return blob


def _google_complete_with_icons(query: str, sxng_locale: str) -> list[t.Union[str, Result]]:
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

    results: list[t.Union[str, Result]] = []

    resp = get(url.format(subdomain=google_info['subdomain'], args=args))
    if resp and resp.ok:
        for item in json.loads(_slice_google_json(resp.text))[0]:
            suggestion_text = lxml.html.fromstring(item[0]).text_content()
            meta = item[3] if len(item) > 3 and isinstance(item[3], dict) else {}

            entry: Result = {'text': suggestion_text}
            if isinstance(meta.get('zs'), str) and meta['zs']:
                entry['icon'] = meta['zs']
            if isinstance(meta.get('zi'), str) and meta['zi']:
                entry['description'] = html.unescape(meta['zi'])
            results.append(entry if len(entry) > 1 else suggestion_text)

    return results


def _encode_varint(value: int) -> bytes:
    parts: list[int] = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts)


def _encode_proto_string(field_number: int, value: str) -> bytes:
    encoded = value.encode('utf-8')
    tag = (field_number << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(encoded)) + encoded


def _encode_proto_varint_field(field_number: int, value: int) -> bytes:
    tag = (field_number << 3) | 0
    return _encode_varint(tag) + _encode_varint(value)


def _encode_proto_message(field_number: int, payload: bytes) -> bytes:
    tag = (field_number << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(payload)) + payload


def _suggest_template_b64(*, image_url: str = '', description: str = '') -> str:
    parts: list[bytes] = [_encode_proto_varint_field(1, 2)]
    if description:
        parts.append(_encode_proto_message(4, _encode_proto_string(1, description)))
    if image_url:
        image = _encode_proto_string(1, image_url) + _encode_proto_varint_field(3, 2)
        parts.append(_encode_proto_message(5, image))
    return base64.b64encode(b''.join(parts)).decode('ascii')


def _external_root(webapp_module: t.Any) -> str:
    base_url = webapp_module.settings.get('server', {}).get('base_url')
    if base_url:
        parsed = urlparse(base_url)
        return f'{parsed.scheme}://{parsed.netloc}'
    req = webapp_module.sxng_request
    scheme = req.headers.get('X-Forwarded-Proto', req.scheme)
    host = (req.headers.get('X-Forwarded-Host') or req.headers.get('Host') or req.host).split(',')[0].strip()
    return f'{scheme}://{host}'


def _proxy_icon(webapp_module: t.Any, url: str, *, absolute: bool = False) -> str:
    h = webapp_module.new_hmac(webapp_module.settings['server']['secret_key'], url.encode())
    path = '{0}?{1}'.format(webapp_module.url_for('image_proxy'), urlencode(dict(url=url.encode(), h=h)))
    if not absolute:
        return path
    return _external_root(webapp_module) + path


def _as_result(result: t.Union[str, Result]) -> Result:
    if isinstance(result, str):
        return {'text': result}
    return {
        'text': result.get('text', ''),
        **({key: value for key in ('icon', 'description') if (value := result.get(key))}),
    }


def _rich_result(webapp_module: t.Any, result: t.Union[str, Result]) -> t.Union[str, Result]:
    item = dict(_as_result(result))
    if icon := item.get('icon'):
        item['icon'] = _proxy_icon(webapp_module, icon)
    return item if len(item) > 1 else item['text']


def _omnibox_suggestions_json(
    webapp_module: t.Any,
    omnibox_prefix: str,
    results: list[t.Union[str, Result]],
    *,
    user_agent: str = '',
) -> str:
    items = [_as_result(result) for result in results]
    texts = [item['text'] for item in items]
    extras: dict[str, t.Any] = {
        'google:suggestrelevance': [600 - index for index in range(len(texts))],
    }

    if 'Firefox' in user_agent:
        details = []
        for item in items:
            if not (icon := item.get('icon')):
                details.append({})
                continue
            detail: dict[str, str] = {'i': _proxy_icon(webapp_module, icon, absolute=True)}
            if description := item.get('description'):
                detail['a'] = description
            details.append(detail)
        if any(details):
            extras['google:suggestdetail'] = details
        descriptions = [item.get('description', '') for item in items]
    else:
        extras['google:verbatimrelevance'] = 1300
        extras['google:suggesttype'] = ['QUERY'] * len(texts)
        extras['google:clientdata'] = {'bpc': False, 'tlw': False}
        details = []
        for item in items:
            if not (icon := item.get('icon')):
                details.append({})
                continue
            details.append(
                {
                    'google:suggesttemplate': _suggest_template_b64(
                        image_url=_proxy_icon(webapp_module, icon, absolute=True),
                        description=item.get('description', ''),
                    ),
                }
            )
        if any(details):
            extras['google:suggestdetail'] = details
        descriptions = [''] * len(texts)

    return json.dumps([omnibox_prefix, texts, descriptions, [], extras])


def _autocompleter_with_icons(webapp_module):
    results: list[t.Union[str, Result]] = []
    req = webapp_module.sxng_request

    disabled_engines = req.preferences.engines.get_disabled()
    raw_text_query = webapp_module.RawTextQuery(req.form.get('q', ''), disabled_engines)
    sug_prefix = raw_text_query.getQuery()
    omnibox_prefix = req.form.get('q', '')

    for obj in webapp_module.searx.answerers.STORAGE.ask(sug_prefix):
        if isinstance(obj, webapp_module.Answer):
            results.append(obj.answer)

    if len(raw_text_query.autocomplete_list) == 0 and len(sug_prefix) > 0:
        sxng_locale = req.preferences.get_value('language')
        backend_name = req.preferences.get_value('autocomplete')

        for result in webapp_module.search_autocomplete(backend_name, sug_prefix, sxng_locale):
            result_text = result if isinstance(result, str) else result.get('text', '')
            icon_url = None if isinstance(result, str) else result.get('icon')
            description = None if isinstance(result, str) else result.get('description')

            if result_text != sug_prefix:
                suggestion_text = raw_text_query.changeQuery(result_text).getFullQuery()
                entry: Result = {'text': suggestion_text}
                if isinstance(icon_url, str) and icon_url:
                    entry['icon'] = icon_url
                if isinstance(description, str) and description:
                    entry['description'] = description
                results.append(entry if len(entry) > 1 else suggestion_text)

    if len(raw_text_query.autocomplete_list) > 0:
        for autocomplete_text in raw_text_query.autocomplete_list:
            results.append(raw_text_query.get_autocomplete_full_query(autocomplete_text))

    if req.headers.get('Accept', '').startswith('application/json'):
        return webapp_module.Response(
            json.dumps([sug_prefix, [_rich_result(webapp_module, result) for result in results]]),
            mimetype='application/json',
        )

    suggestions = _omnibox_suggestions_json(
        webapp_module,
        omnibox_prefix,
        results,
        user_agent=req.headers.get('User-Agent', ''),
    )
    return webapp_module.Response(suggestions, mimetype='application/x-suggestions+json')


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
        if request.path == '/autocompleter' and request.method == 'GET' and 200 <= response.status_code < 300:
            response.headers['Cache-Control'] = 'private, max-age=3600, stale-while-revalidate=300'
            response.headers['Vary'] = 'Cookie, User-Agent, Accept'
            return response

        if request.path != '/image_proxy':
            return response

        if 200 <= response.status_code < 300:
            response.headers['Cache-Control'] = 'public, max-age=86400'
            return response

        if response.status_code in (404, 410):
            response.headers['Cache-Control'] = 'public, max-age=300'

        return response

    sx_webapp.autocompleter = patched_autocompleter
    app.view_functions['autocompleter'] = patched_autocompleter
