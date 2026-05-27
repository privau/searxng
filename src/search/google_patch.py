# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retry and fallback parsing for the Google's stub HTML responses."""

import typing as t
from urllib.parse import unquote

from lxml import html

from searx.network import Request, multi_requests
from searx.result_types import EngineResults
from searx.utils import eval_xpath_getindex, eval_xpath_list, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

_response = None
_request = None

# Google sometimes returns a small HTML shell without organic result links.  Parallel
# refetches with a fresh GSA user agent (from :py:obj:`google.request`) often get
# the full SERP.
STUB_PARALLEL_RETRIES = 3
STUB_MAX_BYTES = 60_000

# specific xpath variables
# ------------------------

stub_result_xpath = '//a[@data-ved and not(@class)]'
fallback_result_xpath = '//div[contains(@class, "MjjYud")]'
fallback_title_xpath = './/h3[contains(@class, "LC20lb")] | .//div[@role="heading"]'
fallback_url_xpath = './/a[@href][contains(@href,"/url?q=")]/@href'
fallback_content_xpath = './/div[contains(@class, "VwiC3b")] | .//div[contains(@class, "ilUpNd")]'


def _has_url_results(results: EngineResults) -> bool:
    for item in results:
        if isinstance(item, dict) and item.get("url"):
            return True
        if getattr(item, "url", None):
            return True
    return False


def is_stub_response(resp_text: str) -> bool:
    """Return True if *resp_text* looks like Google's empty SERP shell."""
    if len(resp_text) >= STUB_MAX_BYTES:
        return False
    dom = html.fromstring(resp_text)
    return not eval_xpath_list(dom, stub_result_xpath)


def _parse_fallback_results(resp_text: str) -> EngineResults:
    results = EngineResults()
    dom = html.fromstring(resp_text)

    for result in eval_xpath_list(dom, fallback_result_xpath):
        title = extract_text(
            eval_xpath_getindex(result, fallback_title_xpath, 0, default=None),
            allow_none=True,
        )
        raw_url = eval_xpath_getindex(result, fallback_url_xpath, 0, default=None)
        if not title or not raw_url:
            continue

        if raw_url.startswith("/url?q="):
            url = unquote(raw_url[7:].split("&sa=U")[0])  # remove the google redirector
        else:
            url = raw_url

        content_nodes = eval_xpath_list(result, fallback_content_xpath)
        content = extract_text(content_nodes[0]) if content_nodes else ""

        results.append({"url": url, "title": title, "content": content or ""})

    return results


def _parse_results(resp: "SXNG_Response") -> EngineResults:
    results = _response(resp)
    if _has_url_results(results):
        return results

    fallback_results = _parse_fallback_results(resp.text)
    if not _has_url_results(fallback_results):
        return results

    for item in fallback_results:
        results.append(item)
    return results


def _request_http_args(params: "OnlineParams") -> dict[str, t.Any]:
    request_args: dict[str, t.Any] = {
        "headers": params.get("headers") or {},
        "cookies": params.get("cookies") or {},
        "auth": params.get("auth"),
        "raise_for_httperror": params.get("raise_for_httperror", True),
    }

    verify = params.get("verify")
    if verify is not None:
        request_args["verify"] = verify

    max_redirects = params.get("max_redirects")
    if max_redirects:
        request_args["max_redirects"] = max_redirects

    if "allow_redirects" in params:
        request_args["allow_redirects"] = params["allow_redirects"]

    return request_args


def _build_retry_request(resp: "SXNG_Response") -> tuple["OnlineParams", Request] | None:
    params: "OnlineParams | None" = getattr(resp, "search_params", None)
    if not params or not params.get("query"):
        return None

    retry_params: "OnlineParams" = {
        **params,
        "headers": dict(params.get("headers") or {}),
        "cookies": dict(params.get("cookies") or {}),
    }
    _request(params["query"], retry_params)

    if not retry_params.get("url"):
        return None

    return retry_params, Request.get(retry_params["url"], **_request_http_args(retry_params))


def _retry_stub_parallel(resp: "SXNG_Response") -> EngineResults | None:
    pending: list[tuple["OnlineParams", Request]] = []
    for _ in range(STUB_PARALLEL_RETRIES):
        retry = _build_retry_request(resp)
        if retry is not None:
            pending.append(retry)

    if not pending:
        return None

    for (retry_params, _), retry_resp in zip(pending, multi_requests([req for _, req in pending])):
        if isinstance(retry_resp, Exception):
            continue

        retry_resp.search_params = retry_params
        retry_results = _parse_results(retry_resp)
        if _has_url_results(retry_results):
            return retry_results

    return None


def response(resp: "SXNG_Response") -> EngineResults:
    """Get response from google's search request."""
    results = _parse_results(resp)
    if _has_url_results(results):
        return results

    params: "OnlineParams" = getattr(resp, "search_params", None) or {}
    if params.get("pageno", 1) != 1:
        return results

    if not is_stub_response(resp.text):
        return results

    retry_results = _retry_stub_parallel(resp)
    if retry_results is not None:
        return retry_results

    return results


def apply_google_patch() -> None:
    # pylint: disable=import-outside-toplevel
    from searx import engines

    google_engine = engines.engines.get("google")
    if google_engine is None or getattr(google_engine, "response", None) is response:
        return

    global _response, _request  # pylint: disable=global-statement
    _response = google_engine.response
    _request = google_engine.request
    google_engine.response = response  # type: ignore[method-assign]
