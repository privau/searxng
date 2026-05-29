# SPDX-License-Identifier: AGPL-3.0-or-later
"""Early timeout for supplemental engines so they do not block other results."""

import threading
from timeit import default_timer
from uuid import uuid4

from flask import copy_current_request_context

from searx.search.processors import PROCESSORS
from searx.search.processors.abstract import RequestParams

REFERENCE_ENGINE = "google"
SUPPLEMENTAL_ENGINES = frozenset({"wikipedia", "wikidata", "ddg definitions"})
MIN_SUPPLEMENTAL_TIMEOUT = 0.5
SKIPPED_ERROR = "skipped"


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

    if len(engine_names) == 1 and engine_names <= SUPPLEMENTAL_ENGINES:
        for th in threads:
            join_thread(th)
        return

    reference_thread = None
    supplemental_threads: list[threading.Thread] = []
    other_threads: list[threading.Thread] = []

    for th in threads:
        if th._engine_name == REFERENCE_ENGINE:
            reference_thread = th
        elif th._engine_name in SUPPLEMENTAL_ENGINES:
            supplemental_threads.append(th)
        else:
            other_threads.append(th)

    if reference_thread:
        join_thread(reference_thread)
        supplemental_deadline = max(MIN_SUPPLEMENTAL_TIMEOUT, elapsed())
    else:
        supplemental_deadline = MIN_SUPPLEMENTAL_TIMEOUT

    for th in other_threads:
        join_thread(th)

    for th in supplemental_threads:
        remaining = max(0.0, supplemental_deadline - elapsed())
        join_thread(th, remaining, error_type=SKIPPED_ERROR)


def apply_supplemental_timeout() -> None:
    from flask_babel import gettext

    from searx import webutils
    from searx.search import Search

    webutils.exception_classname_to_text[SKIPPED_ERROR] = gettext("skipped")
    Search.search_multiple_requests = search_multiple_requests  # type: ignore[method-assign]
