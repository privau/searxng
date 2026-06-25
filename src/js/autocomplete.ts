// SPDX-License-Identifier: AGPL-3.0-or-later

import { listen, settings } from "../toolkit.ts";

let suppressAutocomplete = false;

type RichSuggestion = {
  text?: string;
  icon?: string;
  description?: string;
  trending?: boolean;
};

type SuggestionItem = string | RichSuggestion;

const autocomplete = document.querySelector<HTMLElement>(".autocomplete");
const autocompleteList = document.querySelector<HTMLUListElement>(".autocomplete ul");
const searchIconTemplate = document.querySelector<SVGElement>("#send_search svg");

const asRich = (item: SuggestionItem): RichSuggestion | null =>
  typeof item === "string" ? null : item;

const suggestionText = (item: SuggestionItem): string =>
  typeof item === "string" ? item : (item.text ?? "");

const suggestionDescription = (item: SuggestionItem): string | null => {
  const description = asRich(item)?.description;
  return description ? description : null;
};

const suggestionIcon = (item: SuggestionItem): string | null => {
  if (settings.autocomplete !== "google") return null;
  const icon = asRich(item)?.icon;
  return icon ? icon.replace(/&amp;/g, "&") : null;
};

const isTrending = (item: SuggestionItem): boolean => asRich(item)?.trending === true;

const shouldFetch = (query: string): boolean => {
  const minLength = settings.autocomplete_min ?? 2;
  return query.length === 0 || query.length >= minLength;
};

const fillSuggestion = (el: HTMLElement, suggestion: string, query: string): void => {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) {
    el.textContent = suggestion;
    return;
  }

  const typed = words[words.length - 1];
  const complete = new Set(words.slice(0, -1));
  const bold = (text: string): void => {
    if (!text) return;
    const node = document.createElement("b");
    node.textContent = text;
    el.append(node);
  };

  for (const token of suggestion.split(/(\s+)/)) {
    const lower = token.toLowerCase();
    if (token === "" || /\s/.test(token) || complete.has(lower)) {
      el.append(token);
    } else if (lower.startsWith(typed)) {
      el.append(token.slice(0, typed.length));
      bold(token.slice(typed.length));
    } else {
      bold(token);
    }
  }
};

const createTrendingIcon = (): HTMLSpanElement => {
  const icon = document.createElement("span");
  icon.className = "autocomplete-icon-trending";
  icon.ariaHidden = "true";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z");
  svg.append(path);
  icon.append(svg);
  return icon;
};

const createFallbackIcon = (): HTMLSpanElement => {
  const icon = document.createElement("span");
  icon.className = "autocomplete-icon-fallback";
  icon.ariaHidden = "true";
  if (searchIconTemplate) {
    icon.append(searchIconTemplate.cloneNode(true));
  }
  return icon;
};

const createIconSlot = (iconUrl: string | null, hasDescription: boolean, trending: boolean): HTMLSpanElement => {
  const slot = document.createElement("span");
  slot.className = "autocomplete-icon-slot";
  if (hasDescription) slot.classList.add("is-entity");
  if (trending) slot.classList.add("is-trending");

  if (!iconUrl) {
    slot.append(trending ? createTrendingIcon() : createFallbackIcon());
    return slot;
  }

  const img = document.createElement("img");
  img.className = "autocomplete-icon-image";
  img.src = iconUrl;
  img.alt = "";
  img.decoding = "async";
  slot.append(img);
  return slot;
};

const hideAutocomplete = (): void => {
  suppressAutocomplete = true;
  autocomplete?.classList.remove("open");
};

const closeAutocomplete = (): void => {
  hideAutocomplete();
  autocompleteList?.replaceChildren();
};

const requestAutocomplete = (query: string): Promise<Response> => {
  const headers = { Accept: "application/json" };
  const cache: RequestCache = "no-store";
  if (settings.method === "GET") {
    return fetch(`./autocompleter?q=${encodeURIComponent(query)}`, { method: "GET", headers, cache });
  }
  return fetch("./autocompleter", {
    method: "POST",
    headers: { ...headers, "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ q: query }),
    cache,
  });
};

const renderSuggestion = (
  item: SuggestionItem,
  query: string,
  qInput: HTMLInputElement,
): HTMLLIElement => {
  const text = suggestionText(item);
  const description = suggestionDescription(item);

  const li = document.createElement("li");
  const content = document.createElement("div");
  content.className = "autocomplete-content";

  const title = document.createElement("span");
  title.className = "autocomplete-text";
  fillSuggestion(title, text, query);
  content.append(title);

  if (description) {
    const subtitle = document.createElement("span");
    subtitle.className = "autocomplete-description";
    subtitle.textContent = description;
    content.append(subtitle);
  }

  li.append(createIconSlot(suggestionIcon(item), description !== null, isTrending(item)));
  li.append(content);

  listen("mousedown", li, () => {
    qInput.value = text;
    document.querySelector<HTMLFormElement>("#search")?.submit();
  });

  return li;
};

let requestCounter = 0;
let displayedRequestId = 0;
let cachedTrendingResults: SuggestionItem[] | null = null;

const displayResults = (
  qInput: HTMLInputElement,
  items: SuggestionItem[],
  requestId: number,
): void => {
  if (!autocomplete || !autocompleteList) return;
  if (suppressAutocomplete) return;
  if (requestId <= displayedRequestId) return;
  if (items.length === 0) return;

  displayedRequestId = requestId;
  autocomplete.classList.add("open");
  autocompleteList.replaceChildren();

  const highlightQuery = qInput.value;
  const fragment = new DocumentFragment();
  for (const item of items) {
    if (!suggestionText(item)) continue;
    fragment.append(renderSuggestion(item, highlightQuery, qInput));
  }
  autocompleteList.append(fragment);
};

const fetchResults = (qInput: HTMLInputElement, query: string, requestId: number): void => {
  if (query.length === 0 && cachedTrendingResults !== null) {
    displayResults(qInput, cachedTrendingResults, requestId);
    return;
  }

  requestAutocomplete(query)
    .then((res) => {
      if (!res.ok) throw new Error(res.statusText);
      return res.json();
    })
    .then((results) => {
      const items = (results?.[1] ?? []) as SuggestionItem[];
      if (query.length === 0 && items.length > 0) {
        cachedTrendingResults = items;
      }
      displayResults(qInput, items, requestId);
    })
    .catch((error) => {
      if (requestId > displayedRequestId && !suppressAutocomplete) {
        console.error("Error fetching autocomplete results:", error);
      }
    });
};

const qInput = document.getElementById("q");
if (!(qInput instanceof HTMLInputElement)) {
  throw new Error("Search input #q not found");
}

const clearSearchButton = document.getElementById("clear_search");

const scheduleAutocomplete = (query: string): void => {
  if (!shouldFetch(query)) {
    closeAutocomplete();
    return;
  }
  suppressAutocomplete = false;
  requestCounter += 1;
  autocomplete?.classList.add("open");
  void fetchResults(qInput, query, requestCounter);
};

listen("input", qInput, () => scheduleAutocomplete(qInput.value));

if (autocompleteList) {
  if (clearSearchButton) {
    listen("click", clearSearchButton, () => closeAutocomplete());
  }

  listen("keydown", qInput, (event: KeyboardEvent) => {
    if (event.key === "Escape") closeAutocomplete();
  });

  listen("keyup", qInput, (event: KeyboardEvent) => {
    const items = [...autocompleteList.children] as HTMLElement[];
    if (items.length === 0) {
      if (event.key === "Enter") closeAutocomplete();
      return;
    }

    const currentIndex = items.findIndex((item) => item.classList.contains("active"));
    if (currentIndex >= 0) items[currentIndex]?.classList.remove("active");

    let nextIndex = -1;
    if (event.key === "ArrowUp") {
      nextIndex = (currentIndex - 1 + items.length) % items.length;
    } else if (event.key === "ArrowDown") {
      nextIndex = (currentIndex + 1) % items.length;
    } else if (event.key === "Enter") {
      closeAutocomplete();
      return;
    }

    if (nextIndex === -1) return;

    const selected = items[nextIndex];
    selected?.classList.add("active");
    qInput.value = selected?.querySelector<HTMLElement>(".autocomplete-text")?.textContent ?? "";
  });

  listen("blur", qInput, () => hideAutocomplete());

  listen("focus", qInput, () => {
    suppressAutocomplete = false;
    if ((autocompleteList.children.length ?? 0) > 0) {
      autocomplete?.classList.add("open");
      return;
    }
    if (shouldFetch(qInput.value)) scheduleAutocomplete(qInput.value);
  });
}
