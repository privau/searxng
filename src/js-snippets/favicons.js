// SPDX-License-Identifier: AGPL-3.0-or-later

/* global searxng */

searxng.ready(function () {
  'use strict';

  if (searxng.endpoint !== 'results') {
    return;
  }

  const defaultFavicon = 'data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="fill: rgb(64, 73, 81);"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>';
  // const currentDomain = window.location.host;
  const currentDomain = 'priv.au';

  function createFaviconElement (host) {
    const faviconDiv = document.createElement('div');
    faviconDiv.className = 'favicon';

    const icon = document.createElement('img');
    icon.alt = host;
    icon.src = `https://${currentDomain}/favicon/${host}`;
    icon.onerror = () => {
      icon.src = defaultFavicon;
    };

    faviconDiv.appendChild(icon);
    return faviconDiv;
  }

  function addFavicons () {
    document.querySelectorAll('.result > .url_wrapper, .result > .result_header').forEach(el => {
      if (!el.querySelector('.favicon')) {
        const link = el.href || el.querySelector('a').href;
        const host = new URL(link).host;
        const faviconElement = createFaviconElement(host);
        el.prepend(faviconElement);
      }
    });
  }

  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === 1) { // Check if node is an element
            if (node.matches('.result > .url_wrapper, .result > .result_header') || node.querySelector('.result > .url_wrapper, .result > .result_header')) {
              addFavicons();
            }
          }
        });
      }
    });
  });

  const resultsContainer = document.querySelector('#results');
  if (resultsContainer) {
    observer.observe(resultsContainer, { childList: true, subtree: true });
  }

  addFavicons();
});
