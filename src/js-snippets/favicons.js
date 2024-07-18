// SPDX-License-Identifier: AGPL-3.0-or-later

/* global searxng */

searxng.ready(function () {
  'use strict';

  if (searxng.endpoint !== 'results') {
    return;
  }

  const defaultFavicon = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAACiElEQVQ4EaVTzU8TURCf2tJuS7tQtlRb6UKBIkQwkRRSEzkQgyEc6lkOKgcOph78Y+CgjXjDs2i44FXY9AMTlQRUELZapVlouy3d7kKtb0Zr0MSLTvL2zb75eL838xtTvV6H/xELBptMJojeXLCXyobnyog4YhzXYvmCFi6qVSfaeRdXdrfaU1areV5KykmX06rcvzumjY/1ggkR3Jh+bNf1mr8v1D5bLuvR3qDgFbvbBJYIrE1mCIoCrKxsHuzK+Rzvsi29+6DEbTZz9unijEYI8ObBgXOzlcrx9OAlXyDYKUCzwwrDQx1wVDGg089Dt+gR3mxmhcUnaWeoxwMbm/vzDFzmDEKMMNhquRqduT1KwXiGt0vre6iSeAUHNDE0d26NBtAXY9BACQyjFusKuL2Ry+IPb/Y9ZglwuVscdHaknUChqLF/O4jn3V5dP4mhgRJgwSYm+gV0Oi3XrvYB30yvhGa7BS70eGFHPoTJyQHhMK+F0ZesRVVznvXw5Ixv7/C10moEo6OZXbWvlFAF9FVZDOqEABUMRIkMd8GnLwVWg9/RkJF9sA4oDfYQAuzzjqzwvnaRUFxn/X2ZlmGLXAE7AL52B4xHgqAUqrC1nSNuoJkQtLkdqReszz/9aRvq90NOKdOS1nch8TpL555WDp49f3uAMXhACRjD5j4ykuCtf5PP7Fm1b0DIsl/VHGezzP1KwOiZQobFF9YyjSRYQETRENSlVzI8iK9mWlzckpSSCQHVALmN9Az1euDho9Xo8vKGd2rqooA8yBcrwHgCqYR0kMkWci08t/R+W4ljDCanWTg9TJGwGNaNk3vYZ7VUdeKsYJGFNkfSzjXNrSX20s4/h6kB81/271ghG17l+rPTAAAAAElFTkSuQmCC'

  function addFavicons () {
    document.querySelectorAll('.result > .url_wrapper, .result > .result_header').forEach(el => {
      if (el.querySelector('.favicon')) {
        return;
      }

      const link = el.href || el.querySelector('a').href;
      const host = new URL(link).host;
      const icon = document.createElement('img');
      const currentDomain = window.location.hostname;

      icon.className = 'favicon';
      icon.alt = host;
      icon.src = `https://${currentDomain}/favicon/${host}`;
      icon.onerror = () => {
        icon.src = defaultFavicon;
      };

      el.prepend(icon);
    });
  }

  // Initial call to add favicons to existing elements
  addFavicons();

  // Set up a MutationObserver to watch for new elements
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === 1) { // Check if node is an element
            if (node.matches('.result > .url_wrapper, .result > .result_header')) {
              addFavicons();
            } else if (node.querySelector('.result > .url_wrapper, .result > .result_header')) {
              addFavicons();
            }
          }
        });
      }
    });
  });

  // Start observing the results container for changes
  const resultsContainer = document.querySelector('#results');
  if (resultsContainer) {
    observer.observe(resultsContainer, { childList: true, subtree: true });
  }
});
