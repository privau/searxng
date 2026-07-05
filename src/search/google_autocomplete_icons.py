# SPDX-License-Identifier: AGPL-3.0-or-later
"""Runtime patch Google autocomplete icons for the autocompleter responses."""

import base64
import html
import json
import re
import typing as t
from urllib.parse import urlencode, urlparse

import lxml.html

Result = dict[str, t.Any]
Suggestion = t.Union[str, Result]


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


def _is_trending_meta(meta: dict[str, t.Any]) -> bool:
    zp = meta.get('zp')
    return isinstance(zp, dict) and zp.get('gs_ss') == '1'


def _fields_from_google_meta(meta: dict[str, t.Any]) -> dict[str, t.Any]:
    fields: dict[str, t.Any] = {}
    if isinstance(meta.get('zs'), str) and (icon := _normalize_icon_url(meta['zs'])):
        fields['icon'] = icon
    if isinstance(meta.get('zi'), str) and meta['zi']:
        fields['description'] = html.unescape(meta['zi'])
    if _is_trending_meta(meta):
        fields['trending'] = True
    return fields


def _google_complete_with_icons(query: str, sxng_locale: str) -> list[Suggestion]:
    from searx.autocomplete import get
    from searx.data import ENGINE_TRAITS
    from searx.enginelib.traits import EngineTraits
    from searx.engines import engines, google

    traits = engines['google'].traits if 'google' in engines else EngineTraits(**ENGINE_TRAITS['google'])
    google_info = google.get_google_info({'searxng_locale': sxng_locale}, traits)
    args = urlencode({'q': query, 'client': 'gws-wiz', 'hl': google_info['params']['hl']})
    url = f'https://{google_info["subdomain"]}/complete/search?{args}'

    results: list[Suggestion] = []
    resp = get(url, timeout=2.0)
    if not resp or not resp.ok:
        return results

    for item in json.loads(_slice_google_json(resp.text))[0]:
        text = lxml.html.fromstring(item[0]).text_content()
        meta = item[3] if len(item) > 3 and isinstance(item[3], dict) else {}
        entry: Result = {'text': text, **_fields_from_google_meta(meta)}
        results.append(_compact_suggestion(entry))
    return results


def _compact_suggestion(entry: Result) -> Suggestion:
    return entry if len(entry) > 1 else entry['text']


def _normalize_icon_url(url: str) -> str | None:
    url = url.strip()
    if not url:
        return None
    if url.startswith('data:'):
        return url
    if url.startswith('//'):
        url = f'https:{url}'
    if url.startswith(('http://', 'https://')):
        return _sharpen_google_thumb(url)
    return None


def _sharpen_google_thumb(url: str) -> str:
    if 'encrypted-tbn0.gstatic.com' in url and '&s=' in url:
        return re.sub(r'&s=\d+', '&s=64', url)
    return url


def _is_usable_icon(icon: t.Any) -> bool:
    return isinstance(icon, str) and (
        icon.startswith('data:') or icon.startswith(('http://', 'https://'))
    )


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
    if url.startswith('data:'):
        return url
    url = _sharpen_google_thumb(url)
    h = webapp_module.new_hmac(webapp_module.settings['server']['secret_key'], url.encode())
    path = f'{webapp_module.url_for("image_proxy")}?{urlencode({"url": url.encode(), "h": h})}'
    return f'{_external_root(webapp_module)}{path}' if absolute else path


def _as_result(result: Suggestion) -> Result:
    if isinstance(result, str):
        return {'text': result}
    return {
        'text': result.get('text', ''),
        **{
            key: value
            for key in ('icon', 'description', 'trending')
            if (value := result.get(key)) not in (None, '', False)
        },
    }


def _rich_result(webapp_module: t.Any, result: Suggestion) -> Suggestion:
    item = _as_result(result)
    icon = item.get('icon')
    if _is_usable_icon(icon) and not str(icon).startswith('data:'):
        item['icon'] = _proxy_icon(webapp_module, str(icon))
    elif icon and not _is_usable_icon(icon):
        item.pop('icon', None)
    return _compact_suggestion(item)


def _encode_varint(value: int) -> bytes:
    parts: list[int] = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts)


def _encode_proto_string(field_number: int, value: str) -> bytes:
    encoded = value.encode('utf-8')
    return _encode_varint((field_number << 3) | 2) + _encode_varint(len(encoded)) + encoded


def _encode_proto_varint_field(field_number: int, value: int) -> bytes:
    return _encode_varint((field_number << 3) | 0) + _encode_varint(value)


def _encode_proto_message(field_number: int, payload: bytes) -> bytes:
    return _encode_varint((field_number << 3) | 2) + _encode_varint(len(payload)) + payload


def _suggest_template_b64(*, image_url: str = '', description: str = '') -> str:
    parts: list[bytes] = [_encode_proto_varint_field(1, 2)]
    if description:
        parts.append(_encode_proto_message(4, _encode_proto_string(1, description)))
    if image_url:
        image = _encode_proto_string(1, image_url) + _encode_proto_varint_field(3, 2)
        parts.append(_encode_proto_message(5, image))
    return base64.b64encode(b''.join(parts)).decode('ascii')


def _is_ungoogled_chromium(headers: t.Mapping[str, str]) -> bool:
    sec_ch_ua = headers.get('Sec-CH-UA', '')
    if not sec_ch_ua or 'Google Chrome' in sec_ch_ua or 'Microsoft Edge' in sec_ch_ua:
        return False
    return 'Chromium' in sec_ch_ua


def _firefox_suggest_detail(webapp_module: t.Any, item: Result) -> dict[str, str]:
    icon = item.get('icon')
    if not _is_usable_icon(icon):
        return {}
    detail: dict[str, str] = {'i': _proxy_icon(webapp_module, str(icon), absolute=True)}
    if description := item.get('description'):
        detail['a'] = str(description)
    return detail


def _chromium_suggest_detail(webapp_module: t.Any, item: Result) -> dict[str, str]:
    icon = item.get('icon')
    if not _is_usable_icon(icon):
        return {}
    return {
        'google:suggesttemplate': _suggest_template_b64(
            image_url=_proxy_icon(webapp_module, str(icon), absolute=True),
            description=str(item.get('description', '')),
        ),
    }


def _omnibox_suggestions_json(
    webapp_module: t.Any,
    omnibox_prefix: str,
    results: list[Suggestion],
    *,
    user_agent: str = '',
) -> str:
    items = [_as_result(result) for result in results]
    texts = [item['text'] for item in items]
    extras: dict[str, t.Any] = {'google:suggestrelevance': [600 - i for i in range(len(texts))]}

    if 'Firefox' in user_agent:
        details = [_firefox_suggest_detail(webapp_module, item) for item in items]
        if any(details):
            extras['google:suggestdetail'] = details
        descriptions = [str(item.get('description', '')) for item in items]
    else:
        extras['google:verbatimrelevance'] = 1300
        extras['google:suggesttype'] = ['QUERY'] * len(texts)
        if not _is_ungoogled_chromium(webapp_module.sxng_request.headers):
            extras['google:clientdata'] = {'bpc': False, 'tlw': False}
            details = [_chromium_suggest_detail(webapp_module, item) for item in items]
            if any(details):
                extras['google:suggestdetail'] = details
        descriptions = [''] * len(texts)

    return json.dumps([omnibox_prefix, texts, descriptions, [], extras])


def _call_autocomplete_backend(backend: str, query: str, locale: str) -> list[Suggestion]:
    from httpx import HTTPError

    from searx.autocomplete import backends
    from searx.exceptions import SearxEngineResponseException

    fn = _google_complete_with_icons if backend == 'google' else backends.get(backend)
    if fn is None:
        return []
    try:
        return fn(query, locale)
    except (HTTPError, SearxEngineResponseException):
        return []


def _fields_from_backend_result(result: Suggestion) -> dict[str, t.Any]:
    if isinstance(result, str):
        return {}
    fields: dict[str, t.Any] = {}
    if isinstance(result.get('icon'), str) and (icon := _normalize_icon_url(result['icon'])):
        fields['icon'] = icon
    if isinstance(result.get('description'), str) and result['description']:
        fields['description'] = result['description']
    if result.get('trending'):
        fields['trending'] = True
    return fields


def _autocompleter_with_icons(webapp_module):
    req = webapp_module.sxng_request
    disabled_engines = req.preferences.engines.get_disabled()
    raw_text_query = webapp_module.RawTextQuery(req.form.get('q', ''), disabled_engines)
    sug_prefix = raw_text_query.getQuery()
    results: list[Suggestion] = []

    for obj in webapp_module.searx.answerers.STORAGE.ask(sug_prefix):
        if isinstance(obj, webapp_module.Answer):
            results.append(obj.answer)

    if not raw_text_query.autocomplete_list:
        backend = req.preferences.get_value('autocomplete')
        locale = req.preferences.get_value('language')
        for result in _call_autocomplete_backend(backend, sug_prefix, locale):
            text = result if isinstance(result, str) else result.get('text', '')
            entry: Result = {
                'text': raw_text_query.changeQuery(text).getFullQuery(),
                **_fields_from_backend_result(result),
            }
            results.append(_compact_suggestion(entry))

    for autocomplete_text in raw_text_query.autocomplete_list:
        results.append(raw_text_query.get_autocomplete_full_query(autocomplete_text))

    if req.headers.get('Accept', '').startswith('application/json'):
        payload = [sug_prefix, [_rich_result(webapp_module, result) for result in results]]
        response = webapp_module.Response(json.dumps(payload), mimetype='application/json')
        response.headers['Cache-Control'] = 'no-store'
        return response

    body = _omnibox_suggestions_json(
        webapp_module,
        req.form.get('q', ''),
        results,
        user_agent=req.headers.get('User-Agent', ''),
    )
    return webapp_module.Response(body, mimetype='application/x-suggestions+json')


def apply_google_autocomplete_icons(app) -> None:
    from flask import request
    from searx import autocomplete as sx_autocomplete
    from searx import webapp as sx_webapp

    upstream_search_autocomplete = sx_autocomplete.search_autocomplete

    def search_autocomplete(backend_name: str, query: str, sxng_locale: str) -> list:
        if backend_name == 'google':
            return _google_complete_with_icons(query, sxng_locale)
        return upstream_search_autocomplete(backend_name, query, sxng_locale)

    sx_autocomplete.backends['google'] = _google_complete_with_icons
    sx_autocomplete.search_autocomplete = search_autocomplete
    if hasattr(sx_autocomplete, 'google_complete'):
        sx_autocomplete.google_complete = _google_complete_with_icons
    sx_webapp.search_autocomplete = search_autocomplete

    @app.after_request
    def add_image_proxy_cache_headers(response):
        if request.path == '/autocompleter' and request.method == 'GET' and 200 <= response.status_code < 300:
            if request.headers.get('Accept', '').startswith('application/json'):
                response.headers['Cache-Control'] = 'no-store'
            else:
                response.headers['Cache-Control'] = 'private, max-age=3600, stale-while-revalidate=300'
            response.headers['Vary'] = 'Cookie, User-Agent, Accept'
            return response
        if request.path != '/image_proxy':
            return response
        if 200 <= response.status_code < 300:
            response.headers['Cache-Control'] = 'public, max-age=86400'
        elif response.status_code in (404, 410):
            response.headers['Cache-Control'] = 'public, max-age=300'
        return response

    def patched_autocompleter():
        return _autocompleter_with_icons(sx_webapp)

    sx_webapp.autocompleter = patched_autocompleter
    app.view_functions['autocompleter'] = patched_autocompleter
