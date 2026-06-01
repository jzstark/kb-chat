(() => {
  const defaultLogo = '/assets/logo.svg';
  const loginLogo = '/assets/logo-login.svg';

  const isLoginRoute = () => window.location.pathname.replace(/\/+$/, '') === '/login';

  const logoImages = () =>
    Array.from(document.querySelectorAll('img')).filter((img) => {
      const src = img.getAttribute('src') || '';
      return src.includes('/assets/logo.svg') || src.includes('/assets/logo-login.svg');
    });

  const applyLoginLogo = () => {
    const nextSrc = isLoginRoute() ? loginLogo : defaultLogo;

    for (const img of logoImages()) {
      if (img.getAttribute('src') !== nextSrc) {
        img.removeAttribute('srcset');
        img.setAttribute('src', nextSrc);
      }
    }
  };

  const patchHistory = (method) => {
    const original = window.history[method];
    window.history[method] = function patchedHistoryMethod(...args) {
      const result = original.apply(this, args);
      window.dispatchEvent(new Event('locationchange'));
      return result;
    };
  };

  patchHistory('pushState');
  patchHistory('replaceState');
  window.addEventListener('popstate', () => window.dispatchEvent(new Event('locationchange')));
  window.addEventListener('locationchange', () => window.requestAnimationFrame(applyLoginLogo));

  const observer = new MutationObserver(applyLoginLogo);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyLoginLogo);
  } else {
    applyLoginLogo();
  }
})();
