(function () {
  const SIMPLE_ICONS = {
    telegram: ["telegram", "229ED9"],
    bitcoin: ["bitcoin", "F7931A"],
    ethereum: ["ethereum", "627EEA"],
    monero: ["monero", "FF6600"],
    tron: ["tron", "EF0027"],
    etherscan: ["etherscan", "21325B"],
    google: ["google", "4285F4"],
    github: ["github", "181717"],
    shodan: ["shodan", "111111"],
    virustotal: ["virustotal", "394EFF"],
    haveibeenpwned: ["haveibeenpwned", "2A2A2A"],
    tor: ["torproject", "7D4698"],
  };

  const CATEGORY_VISUALS = {
    crypto: { key: "bitcoin", text: "₿", label: "Blockchain", theme: "crypto" },
    telegram: { key: "telegram", text: "TG", label: "Telegram", theme: "telegram" },
    username: { iconify: "user-search", text: "@", label: "Username", theme: "username" },
    search: { iconify: "search", text: "Q", label: "Google · Yandex · Bing · 2GIS", theme: "network" },
    network: { iconify: "network", text: "IP", label: "IP · DNS", theme: "network" },
    "mobile-threats": { iconify: "shield-alert", text: "APK", label: "APK · PHISHING", theme: "media" },
    media: { iconify: "file-search-2", text: "EXIF", label: "Rasm · fayl", theme: "media" },
  };

  const CATEGORY_FALLBACK_ICONS = {
    crypto: "blocks",
    telegram: "telegram",
    username: "userSearch",
    search: "search",
    network: "network",
    "mobile-threats": "shield",
    media: "fileSearch",
  };

  function fallbackIconFor(item, kind) {
    const categorySlug = kind === "category" ? item?.slug : item?.category_slug;
    if (brandKey(item) === "telegram") return "telegram";
    return CATEGORY_FALLBACK_ICONS[categorySlug] || "globe";
  }

  function simpleIcon(key) {
    const entry = SIMPLE_ICONS[key];
    return entry ? `https://cdn.simpleicons.org/${entry[0]}/${entry[1]}` : "";
  }

  function iconifyIcon(name) {
    return `https://api.iconify.design/lucide/${name}.svg?color=%23465fff`;
  }

  function favicon(url) {
    try {
      const parsed = new URL(url);
      if (!/^https?:$/.test(parsed.protocol)) return "";
      return `https://www.google.com/s2/favicons?domain_url=${encodeURIComponent(parsed.origin)}&sz=128`;
    } catch {
      return "";
    }
  }

  function brandKey(item) {
    const source = `${item?.name || ""} ${item?.slug || ""} ${item?.url || ""}`.toLocaleLowerCase("en");
    if (/telegram|t\.me/.test(source) && !/tgstat|telemetr|telemetrio|lyzem/.test(source)) return "telegram";
    if (/etherscan/.test(source)) return "etherscan";
    if (/ethereum/.test(source)) return "ethereum";
    if (/tronscan|\btron\b/.test(source)) return "tron";
    if (/xmr|monero/.test(source)) return "monero";
    if (/bitcoin/.test(source)) return "bitcoin";
    if (/virustotal/.test(source)) return "virustotal";
    if (/shodan/.test(source)) return "shodan";
    if (/have i been pwned|haveibeenpwned/.test(source)) return "haveibeenpwned";
    if (/google/.test(source)) return "google";
    return "";
  }

  function themeFor(item, kind) {
    const slug = kind === "category" ? item?.slug : item?.category_slug;
    return CATEGORY_VISUALS[slug]?.theme || "username";
  }

  function resolve(item, kind) {
    const raw = String(item?.icon || "").trim();
    const normalized = raw.toLocaleLowerCase("en");
    const legacyText = raw && !["auto", "◈"].includes(normalized) ? raw : "OS";
    const sources = [];
    let text = legacyText;

    if (normalized.startsWith("text:")) {
      return { sources, text: raw.slice(5).trim().slice(0, 8) || "OS", theme: themeFor(item, kind), fallbackIcon: fallbackIconFor(item, kind) };
    }
    if (/^https?:\/\//i.test(raw)) sources.push(raw);
    else if (SIMPLE_ICONS[normalized]) sources.push(simpleIcon(normalized));

    if (kind === "category") {
      const visual = CATEGORY_VISUALS[item?.slug] || {};
      if (!sources.length && visual.key) sources.push(simpleIcon(visual.key));
      if (!sources.length && visual.iconify) sources.push(iconifyIcon(visual.iconify));
      text = visual.text || text;
      return { sources, text, theme: visual.theme || "username", label: visual.label || "OSINT", fallbackIcon: fallbackIconFor(item, kind) };
    }

    const detectedBrand = brandKey(item);
    if (!sources.length && detectedBrand) sources.push(simpleIcon(detectedBrand));
    const siteIcon = favicon(item?.url);
    if (siteIcon && !sources.includes(siteIcon)) sources.push(siteIcon);
    text = raw && !["auto", "◈"].includes(normalized) ? raw.slice(0, 8) : String(item?.name || "OS").slice(0, 2).toUpperCase();
    return { sources, text, theme: themeFor(item, kind), fallbackIcon: fallbackIconFor(item, kind) };
  }

  function mount(container, image, text, visual) {
    const sources = [...new Set((visual.sources || []).filter(Boolean))];
    let sourceIndex = 0;
    container.classList.remove("has-image");
    container.classList.remove("telegram-icon");
    const uiIcons = window.OSINT_UI_ICONS;
    text.textContent = "";
    text.innerHTML = uiIcons ? uiIcons.svg(visual.fallbackIcon || "globe", "", 26) : "&#9670;";
    if (!image || !sources.length) return;
    image.loading = "lazy";
    image.decoding = "async";

    const loadNext = () => {
      if (sourceIndex >= sources.length) {
        image.removeAttribute("src");
        container.classList.remove("has-image");
        return;
      }
      image.src = sources[sourceIndex++];
    };
    image.onload = () => container.classList.add("has-image");
    image.onerror = loadNext;
    image.referrerPolicy = "no-referrer";
    loadNext();
  }

  window.OSINT_ICONS = { resolve, mount, categoryVisuals: CATEGORY_VISUALS };
})();
