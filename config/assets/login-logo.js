(() => {
  const defaultLogo = '/assets/logo.svg';
  const loginLogo = '/assets/logo-login.svg';

  const isLoginRoute = () => window.location.pathname.replace(/\/+$/, '') === '/login';

  const parseColor = (color) => {
    const match = color.match(/rgba?\(([^)]+)\)/);
    if (!match) {
      return null;
    }

    const [r, g, b, a = '1'] = match[1].split(',').map((part) => part.trim());
    return {
      r: Number.parseFloat(r),
      g: Number.parseFloat(g),
      b: Number.parseFloat(b),
      a: Number.parseFloat(a),
    };
  };

  const blend = (foreground, background) => {
    const alpha = foreground.a;
    return {
      r: foreground.r * alpha + background.r * (1 - alpha),
      g: foreground.g * alpha + background.g * (1 - alpha),
      b: foreground.b * alpha + background.b * (1 - alpha),
      a: 1,
    };
  };

  const luminance = ({ r, g, b }) => {
    const channel = (value) => {
      const normalized = value / 255;
      return normalized <= 0.03928
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    };

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  };

  const effectiveBackground = (element) => {
    let background = { r: 255, g: 255, b: 255, a: 1 };
    const layers = [];

    for (let current = element; current; current = current.parentElement) {
      const color = parseColor(window.getComputedStyle(current).backgroundColor);
      if (color && color.a > 0) {
        layers.push(color);
      }
    }

    const htmlColor = parseColor(window.getComputedStyle(document.documentElement).backgroundColor);
    if (htmlColor && htmlColor.a > 0) {
      layers.push(htmlColor);
    }

    const bodyColor = parseColor(window.getComputedStyle(document.body).backgroundColor);
    if (bodyColor && bodyColor.a > 0) {
      layers.push(bodyColor);
    }

    for (const layer of layers.reverse()) {
      background = blend(layer, background);
    }

    return background;
  };

  const logoForBackground = (img) =>
    luminance(effectiveBackground(img)) < 0.45 ? loginLogo : defaultLogo;

  const logoImages = () =>
    Array.from(document.querySelectorAll('img')).filter((img) => {
      const src = img.getAttribute('src') || '';
      return src.includes('/assets/logo.svg') || src.includes('/assets/logo-login.svg');
    });

  const applyLoginLogo = () => {
    for (const img of logoImages()) {
      const nextSrc = isLoginRoute() ? logoForBackground(img) : defaultLogo;

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
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyLoginLogo);

  const observer = new MutationObserver(applyLoginLogo);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyLoginLogo);
  } else {
    applyLoginLogo();
  }
})();
