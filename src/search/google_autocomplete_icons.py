# SPDX-License-Identifier: AGPL-3.0-or-later
"""Runtime patch rich autocomplete icons for the autocompleter responses."""

import base64
import html
import json
import re
import typing as t
from urllib.parse import urlencode, urlparse

import lxml.html

Result = dict[str, t.Any]
Suggestion = t.Union[str, Result]


def _first_json_array(text: str) -> t.Any:
    start = text.find('[')
    if start < 0:
        return []
    depth = 0
    for index, char in enumerate(text[start:], start):
        depth += (char == '[') - (char == ']')
        if depth == 0:
            return json.loads(text[start : index + 1])
    return []


def _hl(locale: str) -> str:
    lang = (locale or 'en').replace('_', '-')
    if lang.lower() in ('', 'all', 'auto'):
        return 'en'
    primary, _, region = lang.partition('-')
    if primary.lower() == 'zh':
        return f'zh-{region.upper()}' if region else 'zh-CN'
    return primary.lower()


def _normalize_icon_url(url: str) -> str | None:
    url = url.strip()
    if url.startswith('data:'):
        return url
    if url.startswith('//'):
        url = f'https:{url}'
    if not url.startswith(('http://', 'https://')):
        return None
    if 'encrypted-tbn0.gstatic.com' in url and '&s=' in url:
        return re.sub(r'&s=\d+', '&s=64', url)
    return url


def _rich_fields(*, icon: t.Any = None, description: t.Any = None, trending: bool = False) -> dict[str, t.Any]:
    fields: dict[str, t.Any] = {}
    if isinstance(icon, str) and (url := _normalize_icon_url(icon)):
        fields['icon'] = url
    if isinstance(description, str) and description:
        fields['description'] = html.unescape(description)
    if trending:
        fields['trending'] = True
    return fields


def _compact(entry: Result) -> Suggestion:
    return entry if len(entry) > 1 else entry['text']


def _as_result(result: Suggestion) -> Result:
    if isinstance(result, str):
        return {'text': result}
    item: Result = {'text': result.get('text', '')}
    for key in ('icon', 'description', 'trending'):
        if value := result.get(key):
            item[key] = value
    return item


def _google_complete_with_icons(query: str, sxng_locale: str) -> list[Suggestion]:
    from searx.autocomplete import get

    args = urlencode({'q': query, 'client': 'gws-wiz', 'hl': _hl(sxng_locale)})
    resp = get(f'https://www.google.com/complete/search?{args}')
    if not resp.ok:
        return []

    payload = _first_json_array(resp.text)
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        return []

    results: list[Suggestion] = []
    for item in payload[0]:
        if not isinstance(item, list) or not item or not isinstance(item[0], str):
            continue
        try:
            text = lxml.html.fromstring(item[0]).text_content()
        except Exception:
            text = item[0]
        if not text:
            continue
        meta = item[3] if len(item) > 3 and isinstance(item[3], dict) else {}
        zp = meta.get('zp')
        results.append(
            _compact(
                {
                    'text': text,
                    **_rich_fields(
                        icon=meta.get('zs'),
                        description=meta.get('zi'),
                        trending=isinstance(zp, dict) and zp.get('gs_ss') == '1',
                    ),
                }
            )
        )
    return results


def _suggestions_from_kagi(resp) -> list[Suggestion]:
    if not resp or not resp.ok:
        return []
    try:
        data = resp.json()
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list) or not data:
        return []
    if isinstance(data[0], dict):
        results: list[Suggestion] = []
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get('t'), str) or not item['t']:
                continue
            results.append(
                _compact({'text': item['t'], **_rich_fields(icon=item.get('img'), description=item.get('txt'))})
            )
        return results
    if len(data) > 1 and isinstance(data[1], list):
        return [text for text in data[1] if isinstance(text, str) and text]
    return []


def _kagi_complete_with_icons(query: str, _sxng_locale: str) -> list[Suggestion]:
    from searx.autocomplete import get

    args = urlencode({'q': query})
    headers = {'Accept': '*/*', 'Referer': 'https://kagi.com/'}
    for url in (
        f'https://kagi.com/autosuggest?{args}',
        f'https://kagisuggest.com/api/autosuggest?{args}',
    ):
        try:
            results = _suggestions_from_kagi(get(url, headers=headers))
        except Exception:
            results = []
        if results:
            return results
    return []


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
    h = webapp_module.new_hmac(webapp_module.settings['server']['secret_key'], url.encode())
    path = f'{webapp_module.url_for("image_proxy")}?{urlencode({"url": url.encode(), "h": h})}'
    return f'{_external_root(webapp_module)}{path}' if absolute else path


def _rich_result(webapp_module: t.Any, result: Suggestion) -> Suggestion:
    item = _as_result(result)
    icon = item.get('icon')
    if isinstance(icon, str) and icon.startswith(('http://', 'https://')):
        item['icon'] = _proxy_icon(webapp_module, icon)
    elif icon and not (isinstance(icon, str) and icon.startswith('data:')):
        item.pop('icon', None)
    return _compact(item)


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


def _omnibox_detail(webapp_module: t.Any, item: Result, *, firefox: bool) -> dict[str, str]:
    icon = item.get('icon')
    if not isinstance(icon, str) or not icon.startswith(('http://', 'https://', 'data:')):
        return {}
    proxied = _proxy_icon(webapp_module, icon, absolute=True)
    if firefox:
        detail = {'i': proxied}
        if description := item.get('description'):
            detail['a'] = str(description)
        return detail
    return {
        'google:suggesttemplate': _suggest_template_b64(
            image_url=proxied,
            description=str(item.get('description', '')),
        )
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
    firefox = 'Firefox' in user_agent

    if firefox:
        details = [_omnibox_detail(webapp_module, item, firefox=True) for item in items]
        descriptions = [str(item.get('description', '')) for item in items]
    else:
        extras['google:verbatimrelevance'] = 1300
        extras['google:suggesttype'] = ['QUERY'] * len(texts)
        details = []
        if not _is_ungoogled_chromium(webapp_module.sxng_request.headers):
            extras['google:clientdata'] = {'bpc': False, 'tlw': False}
            details = [_omnibox_detail(webapp_module, item, firefox=False) for item in items]
        descriptions = [''] * len(texts)

    if any(details):
        extras['google:suggestdetail'] = details
    return json.dumps([omnibox_prefix, texts, descriptions, [], extras])


RICH_BACKENDS: dict[str, t.Callable[[str, str], list[Suggestion]]] = {
    'google': _google_complete_with_icons,
    'kagi': _kagi_complete_with_icons,
}


def _search_autocomplete(backend_name: str, query: str, sxng_locale: str) -> list[Suggestion]:
    from searx.autocomplete import backends

    fn = RICH_BACKENDS.get(backend_name) or backends.get(backend_name)
    if fn is None:
        return []
    try:
        return fn(query, sxng_locale)
    except Exception:
        return []


def _autocompleter_with_icons(webapp_module):
    req = webapp_module.sxng_request
    raw_text_query = webapp_module.RawTextQuery(req.form.get('q', ''), req.preferences.engines.get_disabled())
    sug_prefix = raw_text_query.getQuery()
    results: list[Suggestion] = []

    for obj in webapp_module.searx.answerers.STORAGE.ask(sug_prefix):
        if isinstance(obj, webapp_module.Answer):
            results.append(obj.answer)

    if not raw_text_query.autocomplete_list:
        for result in _search_autocomplete(
            req.preferences.get_value('autocomplete'),
            sug_prefix,
            req.preferences.get_value('language'),
        ):
            item = _as_result(result)
            if not item['text']:
                continue
            item['text'] = raw_text_query.changeQuery(item['text']).getFullQuery()
            results.append(_compact(item))

    results.extend(raw_text_query.get_autocomplete_full_query(text) for text in raw_text_query.autocomplete_list)

    if req.headers.get('Accept', '').startswith('application/json'):
        response = webapp_module.Response(
            json.dumps([sug_prefix, [_rich_result(webapp_module, result) for result in results]]),
            mimetype='application/json',
        )
        response.headers['Cache-Control'] = 'no-store'
        return response

    return webapp_module.Response(
        _omnibox_suggestions_json(
            webapp_module,
            req.form.get('q', ''),
            results,
            user_agent=req.headers.get('User-Agent', ''),
        ),
        mimetype='application/x-suggestions+json',
    )


def apply_google_autocomplete_icons(app) -> None:
    from flask import request
    from searx import autocomplete as sx_autocomplete
    from searx import webapp as sx_webapp

    sx_autocomplete.backends.update(RICH_BACKENDS)
    sx_autocomplete.search_autocomplete = _search_autocomplete
    if hasattr(sx_autocomplete, 'google_complete'):
        sx_autocomplete.google_complete = _google_complete_with_icons
    sx_webapp.search_autocomplete = _search_autocomplete

    @app.after_request
    def add_image_proxy_cache_headers(response):
        if request.path == '/autocompleter' and request.method == 'GET' and 200 <= response.status_code < 300:
            json_ui = request.headers.get('Accept', '').startswith('application/json')
            response.headers['Cache-Control'] = (
                'no-store' if json_ui else 'private, max-age=3600, stale-while-revalidate=300'
            )
            response.headers['Vary'] = 'Cookie, User-Agent, Accept'
        elif request.path == '/image_proxy':
            if 200 <= response.status_code < 300:
                response.headers['Cache-Control'] = 'public, max-age=86400'
            elif response.status_code in (404, 410):
                response.headers['Cache-Control'] = 'public, max-age=300'
        return response

    def patched_autocompleter():
        return _autocompleter_with_icons(sx_webapp)

    sx_webapp.autocompleter = patched_autocompleter
    app.view_functions['autocompleter'] = patched_autocompleter
