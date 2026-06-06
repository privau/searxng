// SPDX-License-Identifier: AGPL-3.0-or-later

import { http, listen, settings } from "../toolkit.ts";

let suppressAutocomplete = false;

type SuggestionItem = string | { text?: string; icon?: string };

const getSuggestionText = (item: SuggestionItem): string =>
  typeof item === "string" ? item : (item.text ?? "");

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
  try {
    let res: Response;

    if (settings.method === "GET") {
      res = await http("GET", `./autocompleter?q=${query}`);
    } else {
      res = await http("POST", "./autocompleter", { body: new URLSearchParams({ q: query }) });
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
      const text = document.createElement("span");
      text.className = "autocomplete-text";
      text.textContent = suggestionText;

      li.append(createAutocompleteIcon(iconUrl));
      li.append(text);

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
