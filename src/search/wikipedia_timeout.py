# SPDX-License-Identifier: AGPL-3.0-or-later
"""Early timeout for the Wikipedia engine so it does not block other results."""

import threading
from timeit import default_timer
from uuid import uuid4

from flask import copy_current_request_context

from searx.search.processors import PROCESSORS
from searx.search.processors.abstract import RequestParams

WIKIPEDIA_REFERENCE_ENGINE = "google"
WIKIPEDIA_SUPPLEMENTAL_ENGINE = "wikipedia"
WIKIPEDIA_MIN_TIMEOUT = 0.5
WIKIPEDIA_SKIPPED_ERROR = "skipped"


def search_multiple_requests(
    search,
    requests: list[tuple[str, str, RequestParams]],
) -> None:
    # pylint: disable=protected-access
    search_id = str(uuid4())
    threads: list[threading.Thread] = []

    for engine_name, query, request_params in requests:
        _search = copy_current_request_context(PROCESSORS[engine_name].search)
        th = threading.Thread(  # pylint: disable=invalid-name
            target=_search,
            args=(query, request_params, search.result_container, search.start_time, search.actual_timeout),
            name=search_id,
        )
        th._timeout = False
        th._engine_name = engine_name
        th.start()
        threads.append(th)

    def elapsed() -> float:
        return default_timer() - search.start_time

    def join_thread(
        th: threading.Thread,
        remaining_time: float | None = None,
        error_type: str = "timeout",
    ) -> None:
        if remaining_time is None:
            remaining_time = max(0.0, search.actual_timeout - elapsed())
        th.join(remaining_time)
        if th.is_alive():
            th._timeout = True
            search.result_container.add_unresponsive_engine(th._engine_name, error_type)
            PROCESSORS[th._engine_name].logger.error("engine %s", error_type)

    engine_names = {th._engine_name for th in threads}

    if engine_names == {WIKIPEDIA_SUPPLEMENTAL_ENGINE}:
        for th in threads:
            join_thread(th)
        return

    reference_thread = None
    wikipedia_threads: list[threading.Thread] = []
    other_threads: list[threading.Thread] = []

    for th in threads:
        if th._engine_name == WIKIPEDIA_REFERENCE_ENGINE:
            reference_thread = th
        elif th._engine_name == WIKIPEDIA_SUPPLEMENTAL_ENGINE:
            wikipedia_threads.append(th)
        else:
            other_threads.append(th)

    if reference_thread:
        join_thread(reference_thread)
        reference_elapsed = max(WIKIPEDIA_MIN_TIMEOUT, elapsed())
    else:
        reference_elapsed = WIKIPEDIA_MIN_TIMEOUT

    for th in other_threads:
        join_thread(th)

    for th in wikipedia_threads:
        remaining = max(0.0, reference_elapsed - elapsed())
        join_thread(th, remaining, error_type=WIKIPEDIA_SKIPPED_ERROR)


def apply_wikipedia_timeout() -> None:
    from flask_babel import gettext

    from searx import webutils
    from searx.search import Search

    webutils.exception_classname_to_text[WIKIPEDIA_SKIPPED_ERROR] = gettext("skipped")
    Search.search_multiple_requests = search_multiple_requests  # type: ignore[method-assign]
