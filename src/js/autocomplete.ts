// SPDX-License-Identifier: AGPL-3.0-or-later

import { listen, settings } from "../toolkit.ts";

let suppressAutocomplete = false;

type SuggestionItem = string | { text?: string; icon?: string; description?: string };

const getSuggestionText = (item: SuggestionItem): string =>
  typeof item === "string" ? item : (item.text ?? "");

const getSuggestionDescription = (item: SuggestionItem): string | null => {
  if (typeof item === "string") {
    return null;
  }

  return typeof item.description === "string" && item.description.length > 0 ? item.description : null;
};

const fillSuggestion = (el: HTMLElement, suggestion: string, query: string): void => {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) {
    el.textContent = suggestion;
    return;
  }
  const typed = words[words.length - 1];
  const complete = new Set(words.slice(0, -1));

  const appendBold = (s: string): void => {
    if (!s) return;
    const b = document.createElement("b");
    b.textContent = s;
    el.append(b);
  };

  for (const token of suggestion.split(/(\s+)/)) {
    const lc = token.toLowerCase();
    if (token === "" || /\s/.test(token) || complete.has(lc)) {
      el.append(token);
    } else if (lc.startsWith(typed)) {
      el.append(token.slice(0, typed.length));
      appendBold(token.slice(typed.length));
    } else {
      appendBold(token);
    }
  }
};

const getSuggestionIcon = (item: SuggestionItem): string | null => {
  if (typeof item === "string" || settings.autocomplete !== "google") {
    return null;
  }

  if (typeof item.icon === "string" && item.icon.length > 0) {
    return item.icon.replace(/&amp;/g, "&");
  }

  return null;
};

const autocomplete: HTMLElement | null = document.querySelector<HTMLElement>(".autocomplete");
const autocompleteList: HTMLUListElement | null = document.querySelector<HTMLUListElement>(".autocomplete ul");
const searchIconTemplate = document.querySelector<SVGElement>("#send_search svg");

const createFallbackAutocompleteIcon = (): HTMLSpanElement => {
  const fallback = document.createElement("span");
  fallback.className = "autocomplete-icon autocomplete-icon-fallback";
  fallback.ariaHidden = "true";

  if (searchIconTemplate) {
    fallback.append(searchIconTemplate.cloneNode(true));
  }

  return fallback;
};

const createAutocompleteIcon = (iconUrl: string | null): HTMLElement => {
  const fallback = createFallbackAutocompleteIcon();
  if (!iconUrl) {
    return fallback;
  }

  const img = document.createElement("img");
  img.className = "autocomplete-icon autocomplete-icon-image";
  img.src = iconUrl;
  img.alt = "";

  listen("load", img, () => {
    if (fallback.isConnected) {
      fallback.replaceWith(img);
    }
  });

  return fallback;
};

const hideAutocomplete = (): void => {
  suppressAutocomplete = true;
  autocomplete?.classList.remove("open");
};

const closeAutocomplete = (): void => {
  hideAutocomplete();
  autocompleteList?.replaceChildren();
};

const fetchResults = async (qInput: HTMLInputElement, query: string): Promise<void> => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 30_000);

  try {
    const headers = { Accept: "application/json" };
    const res =
      settings.method === "GET"
        ? await fetch(`./autocompleter?q=${encodeURIComponent(query)}`, {
            method: "GET",
            headers,
            signal: controller.signal,
          })
        : await fetch("./autocompleter", {
            method: "POST",
            headers: {
              ...headers,
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({ q: query }),
            signal: controller.signal,
          });

    if (!res.ok) {
      throw new Error(res.statusText);
    }

    const results = await res.json();

    if (!autocomplete || !autocompleteList) return;

    if (suppressAutocomplete || query !== qInput.value) return;
    autocomplete.classList.add("open");
    autocompleteList.replaceChildren();

    if (results?.[1]?.length === 0) {
      return;
    }

    const fragment = new DocumentFragment();

    for (const result of results[1] as SuggestionItem[]) {
      const suggestionText = getSuggestionText(result);
      if (suggestionText.length === 0) continue;

      const li = document.createElement("li");
      const iconUrl = getSuggestionIcon(result);
      const content = document.createElement("div");
      content.className = "autocomplete-content";

      const text = document.createElement("span");
      text.className = "autocomplete-text";
      fillSuggestion(text, suggestionText, query);
      content.append(text);

      const description = getSuggestionDescription(result);
      if (description) {
        const desc = document.createElement("span");
        desc.className = "autocomplete-description";
        desc.textContent = description;
        content.append(desc);
      }

      li.append(createAutocompleteIcon(iconUrl));
      li.append(content);

      listen("mousedown", li, () => {
        qInput.value = suggestionText;

        const form = document.querySelector<HTMLFormElement>("#search");
        form?.submit();
      });

      fragment.append(li);
    }

    autocompleteList.append(fragment);
  } catch (error) {
    console.error("Error fetching autocomplete results:", error);
  } finally {
    clearTimeout(timeoutId);
  }
};

const qInput = document.getElementById("q") as HTMLInputElement | null;
if (!(qInput instanceof HTMLInputElement)) {
  throw new Error("Search input #q not found");
}

const clearSearchButton = document.getElementById("clear_search") as HTMLButtonElement | null;

let timeoutId: number;

listen("input", qInput, () => {
  clearTimeout(timeoutId);

  const query = qInput.value;
  const minLength = settings.autocomplete_min ?? 2;

  if (query.length < minLength) {
    closeAutocomplete();
    return;
  }

  suppressAutocomplete = false;

  timeoutId = window.setTimeout(async () => {
    if (query === qInput.value) {
      await fetchResults(qInput, query);
    }
  }, 0);
});
if (autocompleteList) {
  if (clearSearchButton) {
    listen("click", clearSearchButton, () => {
      closeAutocomplete();
    });
  }

  listen("keydown", qInput, (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      closeAutocomplete();
    }
  });
  listen("keyup", qInput, (event: KeyboardEvent) => {
    const listItems = [...autocompleteList.children] as HTMLElement[];
    if (listItems.length === 0) {
      if (event.key === "Enter") {
        closeAutocomplete();
      }
      return;
    }

    const currentIndex = listItems.findIndex((item) => item.classList.contains("active"));
    const currentItem = listItems[currentIndex];
    if (currentItem && currentIndex >= 0) {
      currentItem.classList.remove("active");
    }

    let newCurrentIndex = -1;

    switch (event.key) {
      case "ArrowUp": {
        // we need to add listItems.length to the index calculation here because the JavaScript modulos
        // operator doesn't work with negative numbers
        newCurrentIndex = (currentIndex - 1 + listItems.length) % listItems.length;
        break;
      }
      case "ArrowDown": {
        newCurrentIndex = (currentIndex + 1) % listItems.length;
        break;
      }
      case "Enter":
        closeAutocomplete();
        break;
      default:
        break;
    }

    if (newCurrentIndex !== -1) {
      const selectedItem = listItems[newCurrentIndex];
      if (selectedItem) {
        selectedItem.classList.add("active");

        const suggestionTextElement = selectedItem.querySelector<HTMLElement>(".autocomplete-text");
        qInput.value = suggestionTextElement?.textContent ?? "";
      }
    }
  });

  listen("blur", qInput, () => {
    hideAutocomplete();
  });

  listen("focus", qInput, () => {
    suppressAutocomplete = false;
    if ((autocompleteList?.children.length ?? 0) > 0) {
      autocomplete?.classList.add("open");
    }
  });
}
