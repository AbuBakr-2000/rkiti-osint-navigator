(() => {
  const paths = {
    search: '<circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path>',
    x: '<path d="M18 6 6 18M6 6l12 12"></path>',
    sun: '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"></path>',
    moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"></path>',
    external: '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>',
    arrowRight: '<path d="M5 12h14M13 6l6 6-6 6"></path>',
    arrowLeft: '<path d="m19 12H5m6 6-6-6 6-6"></path>',
    plus: '<path d="M12 5v14M5 12h14"></path>',
    phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.12.9.33 1.78.62 2.63a2 2 0 0 1-.45 2.11L8 9.73a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.85.29 1.73.5 2.63.62A2 2 0 0 1 22 16.92Z"></path>',
    message: '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z"></path>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"></path>',
    pencil: '<path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z"></path>',
    trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v6M14 11v6"></path>',
    upload: '<path d="M12 16V3m0 0-5 5m5-5 5 5M4 14v6h16v-6"></path>',
    download: '<path d="M12 3v13m0 0 5-5m-5 5-5-5M4 20h16"></path>',
    logout: '<path d="M10 17l5-5-5-5M15 12H3M21 19V5a2 2 0 0 0-2-2h-6"></path>',
    layers: '<path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5"></path>',
    wrench: '<path d="M14.7 6.3a4 4 0 0 0-5-5L12 3.6 8.6 7 6.3 4.7a4 4 0 0 0 5 5L4 17a2.1 2.1 0 1 0 3 3l7.7-7.7a4 4 0 0 0 5-5L17.4 9.6 14 6.2l.7.1Z"></path>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>',
    inbox: '<path d="M4 4h16l2 10v6H2v-6L4 4Zm-2 10h5l2 3h6l2-3h5"></path>',
    eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"></path><circle cx="12" cy="12" r="3"></circle>',
    check: '<path d="m20 6-11 11-5-5"></path>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"></path>',
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"></ellipse><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"></path>',
    telegram: '<path d="m22 2-7 20-4.2-8.8L2 9.4 22 2Z"></path><path d="m22 2-11.2 11.2"></path>',
    network: '<rect x="8" y="2" width="8" height="5" rx="1"></rect><rect x="2" y="17" width="8" height="5" rx="1"></rect><rect x="14" y="17" width="8" height="5" rx="1"></rect><path d="M12 7v5M6 17v-5h12v5"></path>',
    userSearch: '<circle cx="10" cy="8" r="4"></circle><path d="M3 21a7 7 0 0 1 11.3-5.5"></path><circle cx="18" cy="18" r="3"></circle><path d="m20.2 20.2 1.8 1.8"></path>',
    fileSearch: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h7"></path><path d="M14 2v6h6M16 13a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"></path><path d="m19 20 2 2"></path>',
    blocks: '<rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="8.5" y="14" width="7" height="7" rx="1"></rect><path d="M10 6.5h4M7 10v2l3 3M17 10v2l-3 3"></path>',
    globe: '<circle cx="12" cy="12" r="9"></circle><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"></path>'
  };

  function svg(name, className = "", size = 18) {
    const body = paths[name] || paths.external;
    return `<svg class="ui-icon ${className}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
  }

  function mountAll(root = document) {
    root.querySelectorAll("[data-ui-icon]").forEach((node) => {
      node.innerHTML = svg(node.dataset.uiIcon, node.dataset.iconClass || "", Number(node.dataset.iconSize || 18));
    });
  }

  window.OSINT_UI_ICONS = { svg, mountAll };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => mountAll());
  else mountAll();
})();
