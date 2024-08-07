// SPDX-License-Identifier: AGPL-3.0-or-later

/* global searxng */

searxng.ready(function () {
  'use strict';

  if (searxng.endpoint !== 'results') {
    return;
  }

  const defaultFavicon = 'data:image/svg+xml;utf8,<svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"><path d="M187.772,42.94336a8.06306,8.06306,0,0,0-1.13965-.79053A103.94567,103.94567,0,0,0,42.61768,187.31152c.04.07129.07324.145.11572.21582a7.9667,7.9667,0,0,0,.80664,1.08985A103.847,103.847,0,0,0,191.2627,210.48242a7.98,7.98,0,0,0,1.40283-1.0957,104.572,104.572,0,0,0,30.82177-40.20606,7.96262,7.96262,0,0,0,.49805-1.166A103.91753,103.91753,0,0,0,187.772,42.94336Zm25.06446,108.44141-15.93116-14.57032a16.05451,16.05451,0,0,0-16.939-2.96777l-30.45166,12.65723a15.99816,15.99816,0,0,0-9.6875,12.44238l-2.38477,16.19629a15.98468,15.98468,0,0,0,11.76807,17.80762l21.4585,5.63085,3.98828,3.9961A87.85932,87.85932,0,0,1,61.48,185.55664l3.91357-2.3623A16.00017,16.00017,0,0,0,73.126,169.585l.18945-33.81836a8.00588,8.00588,0,0,1,1.25586-4.2583L88.606,109.5127a7.99981,7.99981,0,0,1,11.4375-2.17481l12.78369,9.26172a15.95634,15.95634,0,0,0,11.53418,2.89844l31.48144-4.26367a15.99269,15.99269,0,0,0,9.94971-5.38477L187.94873,84.25A15.92874,15.92874,0,0,0,191.833,73.01074l-.2793-5.813a87.914,87.914,0,0,1,21.28272,84.187Z"/></svg>';

  const currentDomain = window.location.host;

  // const currentDomain = 'priv.au'

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
