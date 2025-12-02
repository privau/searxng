// SPDX-License-Identifier: AGPL-3.0-or-later

import { http, listen, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";

let latestRequestSeq = 0;
let lastRenderedSeq = 0;

const fetchResults = async (qInput: HTMLInputElement, query: string, requestSeq: number): Promise<void> => {
  try {
    let res: Response;

    if (settings.method === "GET") {
      res = await http("GET", `./autocompleter?q=${encodeURIComponent(query)}`);
    } else {
      res = await http("POST", "./autocompleter", { body: new URLSearchParams({ q: query }) });
    }

    const results = await res.json();

    // Render only if this response is newer than what is currently rendered
    if (requestSeq <= lastRenderedSeq) {
      return;
    }

    const autocomplete = document.querySelector<HTMLElement>(".autocomplete");
    if (!autocomplete) {
      return;
    }

    const autocompleteList = document.querySelector<HTMLUListElement>(".autocomplete ul");
    if (!autocompleteList) {
      return;
    }

    autocomplete.classList.add("open");
    autocompleteList.replaceChildren();

    // show an error message that no result was found
    if (results?.[1]?.length === 0) {
      const noItemFoundMessage = Object.assign(document.createElement("li"), {
        className: "no-item-found",
        textContent: settings.translations?.no_item_found ?? "No results found"
      });
      autocompleteList.append(noItemFoundMessage);
      lastRenderedSeq = requestSeq;
      return;
    }

    const fragment = new DocumentFragment();

    for (const result of results[1] ?? []) {
      const li = Object.assign(document.createElement("li"), { textContent: result });

      listen("mousedown", li, () => {
        qInput.value = result;

        const form = document.querySelector<HTMLFormElement>("#search");
        form?.submit();

        autocomplete.classList.remove("open");
      });

      fragment.append(li);
    }

    autocompleteList.append(fragment);
    lastRenderedSeq = requestSeq;
  } catch (error) {
    console.error("Error fetching autocomplete results:", error);
  }
};

const qInputEl = document.getElementById("q") as HTMLInputElement | null;

let timeoutId: number;

if (qInputEl) {
  listen("input", qInputEl, () => {
    clearTimeout(timeoutId);

    const query = qInputEl.value;
    const minLength = settings.autocomplete_min ?? 2;

    if (query.length < minLength) return;

    timeoutId = window.setTimeout(async () => {
      if (query === qInputEl.value) {
        const seq = ++latestRequestSeq;
        await fetchResults(qInputEl, query, seq);
      }
    }, 0);
  });
}

const autocomplete: HTMLElement | null = document.querySelector<HTMLElement>(".autocomplete");
const autocompleteList: HTMLUListElement | null = document.querySelector<HTMLUListElement>(".autocomplete ul");
if (autocompleteList && qInputEl) {
  listen("keyup", qInputEl, (event: KeyboardEvent) => {
    const listItems = [...autocompleteList.children] as HTMLElement[];

    const currentIndex = listItems.findIndex((item) => item.classList.contains("active"));
    let newCurrentIndex = -1;

    switch (event.key) {
      case "ArrowUp": {
        const currentItem = listItems[currentIndex];
        if (currentItem && currentIndex >= 0) {
          currentItem.classList.remove("active");
        }
        // we need to add listItems.length to the index calculation here because the JavaScript modulos
        // operator doesn't work with negative numbers
        newCurrentIndex = (currentIndex - 1 + listItems.length) % listItems.length;
        break;
      }
      case "ArrowDown": {
        const currentItem = listItems[currentIndex];
        if (currentItem && currentIndex >= 0) {
          currentItem.classList.remove("active");
        }
        newCurrentIndex = (currentIndex + 1) % listItems.length;
        break;
      }
      case "Tab":
      case "Enter":
        if (autocomplete) {
          autocomplete.classList.remove("open");
        }
        break;
      default:
        break;
    }

    if (newCurrentIndex !== -1) {
      const selectedItem = listItems[newCurrentIndex];
      if (selectedItem) {
        selectedItem.classList.add("active");

        if (!selectedItem.classList.contains("no-item-found")) {
          const qInput = document.getElementById("q") as HTMLInputElement | null;
          if (qInput) {
            qInput.value = selectedItem.textContent ?? "";
          }
        }
      }
    }
  });
}