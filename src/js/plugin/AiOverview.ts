// SPDX-License-Identifier: AGPL-3.0-or-later

import { Plugin } from "../Plugin.ts";
import { settings } from "../toolkit.ts";

const MAX_SOURCES = 24;
const API_URL =
  document.querySelector<HTMLMetaElement>('meta[name="ai-overview"]')?.content?.trim() ?? "";

function queryFromPage(): string {
  return new URLSearchParams(window.location.search).get("q")?.trim() ?? "";
}

function isFirstResultsPage(): boolean {
  const page = new URLSearchParams(window.location.search).get("pageno");
  return !page || page === "1";
}

function isPluginEnabled(): boolean {
  return settings.plugins?.includes("aiOverview") ?? false;
}

/** True when search engines rendered a knowledge infobox (Wikipedia, etc.). */
function hasEngineInfobox(): boolean {
  return (
    document.querySelector("#infoboxes details") !== null ||
    document.querySelector("#infoboxes aside.infobox:not(#ai-overview-slot)") !== null
  );
}

function scrapeResults(): Array<{ title: string; content: string; url: string }> {
  return [...document.querySelectorAll<HTMLElement>("#urls article.result")]
    .slice(0, MAX_SOURCES)
    .map((article) => {
      const title = article.querySelector("h3")?.textContent?.trim() ?? "";
      const content = article.querySelector(".content")?.textContent?.trim() ?? "";
      return {
        title,
        content: content || title,
        url: article.querySelector<HTMLAnchorElement>("h3 a")?.href ?? ""
      };
    })
    .filter((item) => item.title || item.content);
}

function loadingMarkup(): string {
  return (
    '<div class="ai-overview ai-overview--loading">' +
    '<div class="ai-overview-skeleton" aria-hidden="true">' +
    "<span></span><span></span><span></span>" +
    "</div></div>"
  );
}

function showLoading(slot: HTMLElement): void {
  slot.className = "ai-overview-pending";
  slot.setAttribute("role", "complementary");
  slot.setAttribute("aria-busy", "true");
  slot.innerHTML = loadingMarkup();
}

function removeSlot(slot: HTMLElement): void {
  slot.remove();
}

function ensureSlot(): HTMLElement | null {
  if (hasEngineInfobox()) return null;

  const enginesMsg = document.getElementById("engines_msg");
  if (!enginesMsg) return null;

  let slot = document.getElementById("ai-overview-slot");
  if (!slot) {
    slot = document.createElement("aside");
    slot.id = "ai-overview-slot";
    enginesMsg.insertAdjacentElement("afterend", slot);
  }

  if (!slot.querySelector(".ai-overview")) {
    showLoading(slot);
  }

  return slot;
}

export default class AiOverview extends Plugin {
  public constructor() {
    super("aiOverview");
  }

  protected async run(): Promise<null> {
    if (!isPluginEnabled() || !API_URL) {
      document.getElementById("ai-overview-slot")?.remove();
      return null;
    }

    if (hasEngineInfobox()) {
      document.getElementById("ai-overview-slot")?.remove();
      return null;
    }

    if (!isFirstResultsPage() || !queryFromPage()) {
      document.getElementById("ai-overview-slot")?.remove();
      return null;
    }

    const slot = ensureSlot();
    if (!slot || slot.dataset.loaded === "1") return null;

    const query = queryFromPage();
    const results = scrapeResults();
    if (results.length === 0) {
      removeSlot(slot);
      return null;
    }

    slot.dataset.loaded = "1";

    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, results }),
      signal: AbortSignal.timeout(35_000)
    });

    if (!response.ok) {
      removeSlot(slot);
      return null;
    }

    const data = (await response.json()) as { html?: string | null };
    if (!data.html) {
      removeSlot(slot);
      return null;
    }

    slot.innerHTML = data.html;
    slot.classList.remove("ai-overview-pending");
    slot.removeAttribute("aria-busy");

    return null;
  }
}
