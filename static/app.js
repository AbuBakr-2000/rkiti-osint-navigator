const state = {
  categories: [],
  tools: [],
  query: "",
  activeFilter: "all",
  category: null,
  selectedFile: null,
  selectedFileHash: "",
  selectedFileHashStatus: "idle",
  selectedFilePreviewUrl: "",
  botConfig: { enabled: false, url: "" },
};

const elements = {
  heroSection: document.querySelector(".hero-section"),
  grid: document.querySelector("#card-grid"),
  search: document.querySelector("#global-search"),
  searchDropZone: document.querySelector("#search-drop-zone"),
  fileInput: document.querySelector("#file-search-input"),
  fileButton: document.querySelector("#file-search-button"),
  fileFeedback: document.querySelector("#file-feedback"),
  selectedFile: document.querySelector("#selected-file"),
  selectedFilePreview: document.querySelector("#selected-file-preview"),
  selectedFileName: document.querySelector("#selected-file-name"),
  selectedFileMeta: document.querySelector("#selected-file-meta"),
  selectedFileHash: document.querySelector("#selected-file-hash"),
  removeSelectedFile: document.querySelector("#remove-selected-file"),
  clear: document.querySelector("#clear-search"),
  filters: document.querySelector("#filter-bar"),
  detected: document.querySelector("#detected-type"),
  recommendations: document.querySelector("#tool-recommendations"),
  recommendationList: document.querySelector("#recommendation-list"),
  recommendationContext: document.querySelector("#recommendations-context"),
  title: document.querySelector("#page-title"),
  subtitle: document.querySelector("#page-subtitle"),
  back: document.querySelector("#back-link"),
  sectionTitle: document.querySelector("#section-title"),
  sectionEyebrow: document.querySelector("#section-eyebrow"),
  heroKicker: document.querySelector(".hero-kicker"),
  count: document.querySelector("#result-count"),
  empty: document.querySelector("#empty-state"),
  emptyTitle: document.querySelector("#empty-title"),
  emptyCopy: document.querySelector("#empty-copy"),
  reset: document.querySelector("#reset-empty"),
  themeToggle: document.querySelector("#theme-toggle"),
  mobileMenuToggle: document.querySelector("#mobile-menu-toggle"),
  primaryNav: document.querySelector("#primary-nav"),
  contactButton: document.querySelector("#contact-button"),
  contactMenu: document.querySelector("#contact-menu"),
  contactTelegram: document.querySelector("#contact-telegram"),
  contactTelegramMeta: document.querySelector("#contact-telegram-meta"),
  assistantLink: document.querySelector("#assistant-link"),
  marqueeRows: document.querySelector("#marquee-rows"),
  storyList: document.querySelector("#story-list"),
  categoryIntro: document.querySelector("#category-intro"),
  categoryTemplate: document.querySelector("#category-card-template"),
  toolTemplate: document.querySelector("#tool-card-template"),
  detailsModal: document.querySelector("#details-modal"),
  detailsDialog: document.querySelector(".details-dialog"),
  detailsKind: document.querySelector("#details-kind"),
  detailsTitle: document.querySelector("#details-title"),
  detailsSummary: document.querySelector("#details-summary"),
  detailsContent: document.querySelector("#details-content"),
  detailsMeta: document.querySelector("#details-meta"),
  detailsAction: document.querySelector("#details-action"),
  guidePage: document.querySelector("#guide-page"),
  guideEyebrow: document.querySelector("#guide-eyebrow"),
  guideTitle: document.querySelector("#guide-title"),
  guideDescription: document.querySelector("#guide-description"),
  guideTabs: document.querySelector("#guide-tabs"),
  guidePanel: document.querySelector("#guide-panel"),
  guideDetailIndex: document.querySelector("#guide-detail-index"),
  guideDetailTitle: document.querySelector("#guide-detail-title"),
  guideDetailDescription: document.querySelector("#guide-detail-description"),
  guideTip: document.querySelector("#guide-tip"),
  guideDemo: document.querySelector("#guide-demo"),
  guidePrevious: document.querySelector("#guide-prev"),
  guideNext: document.querySelector("#guide-next"),
  guideStatus: document.querySelector("#guide-status"),
};

const accessLabels = {
  free: "Bepul foydalanish",
  "free-tier": "Cheklangan bepul tarif",
  paid: "Pullik foydalanish",
};

const i18n = window.OSINT_I18N;
const display = (value) => i18n.display(value);
const iconSystem = window.OSINT_ICONS;
const uiIcons = window.OSINT_UI_ICONS;
let detailsReturnFocus = null;
let guideStepIndex = 0;
let smoothScrollController = null;
let toolCarouselObserver = null;
let toolCarouselTimers = [];
let fileHashRequestId = 0;

const MAX_BROWSER_HASH_BYTES = 256 * 1024 * 1024;

function normalize(value) {
  return i18n.toLatin(String(value || "")).toLocaleLowerCase("uz").trim();
}

function compactTelegramQuery(value) {
  return value.trim().replace(/^https?:\/\/(?:www\.)?t\.me\//i, "").replace(/^@/, "").split(/[/?#]/)[0];
}

function detectIndicator(raw) {
  const value = i18n.toLatin(raw).trim();
  if (!value) return null;
  if (/^0x[a-fA-F0-9]{64}$/.test(value)) return { type: "tx-hash", label: "EVM tranzaksiya hashi", categories: ["crypto", "search"] };
  if (/^0x[a-fA-F0-9]{40}$/.test(value)) return { type: "wallet", label: "Ethereum/EVM manzili", categories: ["crypto", "search"] };
  if (/^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$/.test(value)) return { type: "wallet", label: "Bitcoin manzili", categories: ["crypto", "search"] };
  if (/^T[a-zA-Z0-9]{33}$/.test(value)) return { type: "wallet", label: "TRON manzili", categories: ["crypto", "search"] };
  if (/^[a-fA-F0-9]{64}$/.test(value)) return { type: "file-hash", types: ["tx-hash", "file-hash"], label: "64 belgili tranzaksiya yoki fayl hashi", categories: ["crypto", "mobile-threats", "media", "search"] };
  if (/^(?:https?:\/\/)?(?:www\.)?t\.me\/[a-zA-Z0-9_]+/i.test(value) || /^@[a-zA-Z][a-zA-Z0-9_]{3,}$/.test(value)) return { type: "telegram-username", types: ["telegram-username", "username"], label: "Telegram username/havola", categories: ["telegram", "username", "search"] };
  if (/^(?:\d{1,3}\.){3}\d{1,3}$/.test(value) || /^[a-fA-F0-9:]{4,}$/.test(value) && value.includes(":")) return { type: "ip", label: "IP manzil", categories: ["network", "search"] };
  if (/^AS\s*\d+$/i.test(value)) return { type: "asn", label: "ASN raqami", categories: ["network", "search"] };
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return { type: "email", label: "Email manzil", categories: ["username", "search"] };
  if (/^-?\d{5,15}$/.test(value)) return { type: "telegram-id", types: ["telegram-id", "phone"], label: "Raqamli ID yoki telefon raqami", categories: ["telegram", "username", "search"] };
  if (/^\+?[\d\s().-]{8,}$/.test(value)) return { type: "phone", label: "Telefon raqami", categories: ["search", "username"] };
  if (/^https?:\/\//i.test(value)) return { type: "url", label: "URL manzil", categories: ["mobile-threats", "network", "search"] };
  if (/^[^\s]+\.(?:apk|aab)$/i.test(value)) return { type: "apk", types: ["apk", "file"], label: "Android ilova paketi", categories: ["mobile-threats", "media"] };
  if (/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i.test(value)) return { type: "domain", label: "Domen nomi", categories: ["network", "mobile-threats", "search"] };
  if (/^[a-fA-F0-9]{32}$|^[a-fA-F0-9]{40}$/.test(value)) return { type: "file-hash", label: "Fayl hashi", categories: ["mobile-threats", "media", "search"] };
  if (/^[a-zA-Z][a-zA-Z0-9_.-]{2,31}$/.test(value)) return { type: "username", label: "Username yoki kalit so'z", categories: ["username", "telegram", "search"] };
  if (/^[\p{L}][\p{L}\s.'’ʻʼ-]{2,99}$/u.test(value) && /\s/.test(value)) return { type: "name", label: "Shaxs nomi yoki qidiruv iborasi", categories: ["username", "search"] };
  if (value.length >= 2) return { type: "keyword", label: "Qidiruv iborasi", categories: ["search", "username", "network"] };
  return null;
}

function selectedFileKind(file = state.selectedFile) {
  if (!file) return null;
  if ((file.type || "").startsWith("image/")) return "image";
  if ((file.type || "").startsWith("video/")) return "video";
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (["jpg", "jpeg", "png", "gif", "webp", "bmp", "tif", "tiff", "heic", "avif"].includes(extension)) return "image";
  if (["mp4", "mov", "avi", "mkv", "webm", "m4v", "mpeg", "mpg", "3gp"].includes(extension)) return "video";
  return null;
}

function detectSelectedFile() {
  const kind = selectedFileKind();
  if (!kind) return null;
  return {
    type: kind,
    types: [kind, "file-hash"],
    label: kind === "image" ? "Rasm fayli" : "Video fayli",
    categories: kind === "image" ? ["media", "mobile-threats", "search"] : ["media", "mobile-threats", "search"],
    file: state.selectedFile,
  };
}

function currentDetection() {
  return detectSelectedFile() || detectIndicator(state.query);
}

function acceptedIndicatorTypes(detection = currentDetection()) {
  return detection?.types || (detection ? [detection.type] : []);
}

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / (1024 ** unitIndex);
  return `${value >= 10 || unitIndex === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[unitIndex]}`;
}

function hideFileFeedback() {
  elements.fileFeedback.classList.add("hidden");
  elements.fileFeedback.textContent = "";
}

function showFileFeedback(message) {
  elements.fileFeedback.textContent = display(message);
  elements.fileFeedback.classList.remove("hidden");
}

function releaseSelectedFilePreview() {
  if (!state.selectedFilePreviewUrl) return;
  URL.revokeObjectURL(state.selectedFilePreviewUrl);
  state.selectedFilePreviewUrl = "";
}

function clearSelectedFile({ renderView = false } = {}) {
  fileHashRequestId += 1;
  releaseSelectedFilePreview();
  state.selectedFile = null;
  state.selectedFileHash = "";
  state.selectedFileHashStatus = "idle";
  elements.fileInput.value = "";
  elements.fileButton.setAttribute("aria-pressed", "false");
  elements.selectedFile.classList.add("hidden");
  elements.selectedFilePreview.replaceChildren();
  if (renderView) render();
}

function renderSelectedFile() {
  const file = state.selectedFile;
  elements.selectedFile.classList.toggle("hidden", !file);
  elements.fileButton.setAttribute("aria-pressed", String(Boolean(file)));
  if (!file) return;

  const kind = selectedFileKind(file);
  elements.selectedFileName.textContent = file.name;
  elements.selectedFileMeta.textContent = `${kind === "image" ? display("Rasm") : display("Video")} · ${formatFileSize(file.size)}`;
  elements.selectedFileHash.removeAttribute("title");
  if (state.selectedFileHashStatus === "hashing") elements.selectedFileHash.textContent = display("SHA-256 hisoblanmoqda…");
  else if (state.selectedFileHashStatus === "ready") {
    elements.selectedFileHash.textContent = `SHA-256 · ${state.selectedFileHash.slice(0, 20)}…`;
    elements.selectedFileHash.title = state.selectedFileHash;
  } else if (state.selectedFileHashStatus === "skipped") elements.selectedFileHash.textContent = display("Katta fayl: hash hisoblanmadi, vositaga qo'lda yuklanadi");
  else if (state.selectedFileHashStatus === "error") elements.selectedFileHash.textContent = display("Hash hisoblanmadi, vositaga qo'lda yuklanadi");
  else elements.selectedFileHash.textContent = "";

  elements.selectedFilePreview.replaceChildren();
  if (kind === "image") {
    const image = document.createElement("img");
    image.src = state.selectedFilePreviewUrl;
    image.alt = "";
    elements.selectedFilePreview.append(image);
  } else {
    const video = document.createElement("video");
    video.src = state.selectedFilePreviewUrl;
    video.muted = true;
    video.preload = "metadata";
    video.tabIndex = -1;
    elements.selectedFilePreview.append(video);
    const badge = document.createElement("span");
    badge.innerHTML = uiIcons.svg("fileSearch", "", 20);
    elements.selectedFilePreview.append(badge);
  }
}

async function calculateSelectedFileHash(file, requestId) {
  if (!window.crypto?.subtle || file.size > MAX_BROWSER_HASH_BYTES) {
    if (requestId !== fileHashRequestId) return;
    state.selectedFileHashStatus = file.size > MAX_BROWSER_HASH_BYTES ? "skipped" : "error";
    render();
    return;
  }
  try {
    const digest = await window.crypto.subtle.digest("SHA-256", await file.arrayBuffer());
    if (requestId !== fileHashRequestId) return;
    state.selectedFileHash = [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    state.selectedFileHashStatus = "ready";
  } catch (_error) {
    if (requestId !== fileHashRequestId) return;
    state.selectedFileHashStatus = "error";
  }
  render();
}

function selectEvidenceFile(file) {
  if (!file) return;
  if (!selectedFileKind(file)) {
    showFileFeedback("Faqat rasm yoki video faylini tanlang.");
    return;
  }
  clearSelectedFile();
  state.query = "";
  state.activeFilter = "all";
  elements.search.value = "";
  state.selectedFile = file;
  state.selectedFileHashStatus = "hashing";
  state.selectedFilePreviewUrl = URL.createObjectURL(file);
  showFileFeedback("Fayl qurilmangizda tahlil qilinadi. Hash-qidiruv bevosita ochiladi; boshqa vositalarda faylni ochilgan sahifada tasdiqlab yuklaysiz.");
  const url = new URL(window.location.href);
  url.searchParams.delete("q");
  history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  const requestId = ++fileHashRequestId;
  render();
  calculateSelectedFileHash(file, requestId);
}

function allSearchText(item) {
  return normalize([
    item.name,
    item.description,
    item.details,
    item.category_name,
    ...(item.tags || []),
    ...(item.networks || []),
    ...(item.input_types || []),
  ].join(" "));
}

function createTag(label) {
  const span = document.createElement("span");
  span.className = "mini-tag";
  span.textContent = label;
  span.dataset.noTransliterate = "true";
  return span;
}

function toolVisualLabel(tool) {
  const types = tool.input_types || [];
  if (types.includes("telegram-id")) return "Telegram ID";
  if (types.some((type) => ["telegram-username", "username-telegram"].includes(type))) return "@username";
  if (types.includes("telegram-channel")) return "Telegram kanal";
  if (types.includes("wallet")) return "Wallet";
  if (types.includes("tx-hash")) return "TX hash";
  if (types.includes("ip")) return "IP manzil";
  if (types.includes("asn")) return "ASN";
  if (types.includes("domain")) return "Domen";
  if (types.includes("url")) return "URL";
  if (types.includes("email")) return "Email";
  if (types.includes("phone")) return "Telefon";
  if (types.includes("name")) return "Shaxs nomi";
  if (types.includes("address")) return "Manzil";
  if (types.includes("image")) return "Rasm";
  if (types.includes("apk")) return "APK · AAB";
  if (types.includes("package")) return "Paket nomi";
  if (types.includes("file-hash")) return "File hash";
  if (types.includes("file")) return "Fayl";
  return "OSINT vositasi";
}

function applyCardVisual(card, item, kind) {
  const visual = iconSystem.resolve(item, kind);
  const icon = card.querySelector(".card-icon");
  const image = card.querySelector(".card-icon-image");
  const text = card.querySelector(".card-icon-text");
  const label = card.querySelector(".card-icon-label");
  card.dataset.iconTheme = visual.theme;
  label.textContent = display(kind === "category" ? visual.label : toolVisualLabel(item));
  iconSystem.mount(icon, image, text, visual);
}

function renderCategoryCard(category, index) {
  const card = elements.categoryTemplate.content.firstElementChild.cloneNode(true);
  const link = card.querySelector(".card-main-link");
  link.href = `/category/${category.slug}`;
  link.setAttribute("aria-label", display(`${category.name} tekshiruv yo'nalishini ochish`));
  card.querySelector(".card-index").textContent = String(index + 1).padStart(2, "0");
  card.querySelector(".tool-count").textContent = display(`${category.tool_count} ta vosita`);
  card.querySelector(".details-button b").textContent = display("Batafsil");
  card.querySelector("h3").textContent = display(category.name);
  card.querySelector(".card-description").textContent = display(category.description);
  applyCardVisual(card, category, "category");
  card.querySelector(".details-button").addEventListener("click", (event) => openDetails(category, "category", event.currentTarget));
  category.tags.slice(0, 4).forEach((tag) => card.querySelector(".card-tags").append(createTag(tag)));
  return card;
}

const storyTags = {
  telegram: ["Public ID", "Ochiq kanallar", "Kontent va faollik"],
  search: ["Google", "Yandex", "Bing", "2GIS"],
  network: ["Domen", "IP", "URL", "DNS"],
  crypto: ["Hamyon", "Tranzaksiya hashi", "Blockchain"],
  username: ["Username", "Email", "Telefon"],
  "mobile-threats": ["APK", "Hash", "Phishing URL"],
  media: ["Rasm", "EXIF", "Metadata", "Hash"],
};

function storyVisualMarkup(category) {
  const slug = category.slug;
  if (slug === "crypto") return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>BLOCKCHAIN TRACE</span><b>LIVE</b></div><div class="visual-title">0xE8F0...2434</div><div class="visual-sub">ETHEREUM · WALLET</div><div class="visual-flow"><i></i><i></i><i></i><span class="root">WALLET A</span><span class="left">EXCHANGE</span><span class="right">WALLET B</span></div></div>`;
  if (slug === "telegram") return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>TELEGRAM LOOKUP</span><b>PUBLIC</b></div><div class="visual-title">@username</div><div class="visual-sub">USER ID · CHANNEL · OPEN TRACE</div><div class="visual-list"><span><i></i>Profile identifier<b>MATCH</b></span><span><i></i>Public channels<b>04</b></span><span><i></i>Related links<b>07</b></span></div></div>`;
  if (slug === "network") return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>DOMAIN INTELLIGENCE</span><b>RDAP</b></div><div class="visual-title">example.uz</div><div class="visual-sub">DNS · ASN · WHOIS · HOSTING</div><div class="visual-metrics"><span>IP<b>185.xxx.xxx.xxx</b></span><span>ASN<b>ASxxxxx</b></span><span>DNS<b>4 records</b></span><span>STATUS<b>ACTIVE</b></span></div></div>`;
  if (slug === "mobile-threats") return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>THREAT ANALYSIS</span><b>SCAN</b></div><div class="visual-title">sample.apk</div><div class="visual-sub">SHA-256 · URL · PERMISSIONS</div><div class="visual-metrics"><span>PERMISSIONS<b>18</b></span><span>HOSTS<b>07</b></span><span>SIGNATURES<b>02</b></span><span>RISK<b>REVIEW</b></span></div></div>`;
  if (slug === "media") return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>DIGITAL EVIDENCE</span><b>EXIF</b></div><div class="visual-title">evidence_01.jpg</div><div class="visual-sub">IMAGE · FILE · METADATA</div><div class="visual-metrics"><span>HASH<b>8f5a...39c</b></span><span>METADATA<b>14 fields</b></span><span>CREATED<b>10:42 UTC</b></span><span>STATUS<b>VERIFIED</b></span></div></div>`;
  if (slug === "search") return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>OPEN WEB SEARCH</span><b>INDEX</b></div><div class="visual-title">"exact phrase"</div><div class="visual-sub">GOOGLE · YANDEX · BING · 2GIS</div><div class="visual-list"><span><i></i>Indexed source<b>01</b></span><span><i></i>Archived record<b>02</b></span><span><i></i>Related entity<b>03</b></span></div></div>`;
  return `<div class="visual-ui" data-no-transliterate><div class="visual-head"><span>IDENTITY PIVOT</span><b>OSINT</b></div><div class="visual-title">username</div><div class="visual-sub">ALIAS · PROFILE · EMAIL</div><div class="visual-list"><span><i></i>Social profile<b>MATCH</b></span><span><i></i>Reused nickname<b>05</b></span><span><i></i>Related domain<b>02</b></span></div></div>`;
}

const storyMedia = {
  crypto: "crypto.webp",
  telegram: "telegram-search.webp",
  username: "username.webp",
  search: "search.webp",
  network: "network.webp",
  "mobile-threats": "mobile-threats.webp",
  media: "media.webp",
};

function storyMediaMarkup(category) {
  const file = storyMedia[category.slug] || "search.webp";
  return `<figure class="story-media"><img src="/static/media/${file}" alt="${display(category.name)} yo'nalishiga oid amaliy tekshiruv muhiti" loading="lazy" decoding="async"></figure>`;
}

function renderStories() {
  if (!elements.storyList) return;
  const fragment = document.createDocumentFragment();
  const total = state.categories.length;
  state.categories.forEach((category, index) => {
    const article = document.createElement("article");
    article.className = `story-panel reveal-on-scroll${index % 2 === 1 ? " reverse" : ""}`;
    article.dataset.story = category.slug;
    article.id = `direction-${category.slug}`;
    article.style.setProperty("--story-index", String(index + 1));

    const count = document.createElement("span");
    count.className = "story-count";
    count.textContent = `${String(index + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}`;
    count.dataset.noTransliterate = "true";

    const copy = document.createElement("div");
    copy.className = "story-copy";
    const sequence = document.createElement("p");
    sequence.className = "story-index story-reveal story-delay-1";
    sequence.textContent = display(`${String(index + 1).padStart(2, "0")} · ${category.tool_count} ta vosita`);
    const heading = document.createElement("h3");
    heading.className = "story-reveal story-delay-1";
    heading.textContent = display(category.name);
    const description = document.createElement("p");
    description.className = "story-description story-reveal story-delay-2";
    description.textContent = display(category.description);
    const link = document.createElement("a");
    link.className = "story-link story-reveal story-delay-3";
    link.href = `/category/${category.slug}`;
    link.innerHTML = `${display("Yo'nalishdagi vositalarni ko'rish")} ${uiIcons.svg("arrowRight", "", 16)}`;
    const facts = document.createElement("ul");
    facts.className = "story-facts story-reveal story-delay-4";
    (storyTags[category.slug] || category.tags.slice(0, 4)).forEach((item) => {
      const fact = document.createElement("li");
      fact.textContent = display(item);
      facts.append(fact);
    });
    copy.append(sequence, heading, description, link, facts);

    const visual = document.createElement("div");
    visual.className = "story-visual story-reveal";
    visual.innerHTML = storyMediaMarkup(category);
    article.append(count, copy, visual);
    fragment.append(article);
  });
  elements.storyList.replaceChildren(fragment);
}

function renderMarquee() {
  if (!elements.marqueeRows) return;
  elements.marqueeRows.replaceChildren();
  if (!state.tools.length) return;
  const rows = [[], [], []];
  state.tools.forEach((tool, index) => rows[index % rows.length].push(tool));
  rows.forEach((tools, rowIndex) => {
    const row = document.createElement("div");
    row.className = `marquee-row${rowIndex % 2 === 1 ? " reverse" : ""}`;
    const buildTrack = () => {
      const track = document.createElement("div");
      track.className = "marquee-track";
      tools.forEach((tool) => {
        const link = document.createElement("a");
        link.className = "marquee-item";
        link.href = tool.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        const name = document.createElement("b");
        name.textContent = tool.name;
        name.dataset.noTransliterate = "true";
        link.append(name);
        track.append(link);
      });
      return track;
    };
    row.append(buildTrack(), buildTrack());
    elements.marqueeRows.append(row);
  });
}

function setupScrollMotion() {
  const targets = document.querySelectorAll(".reveal-on-scroll");
  if (matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    targets.forEach((target) => target.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -12%", threshold: .08 });
  targets.forEach((target) => observer.observe(target));
}

function setupHeroStreams() {
  const host = document.querySelector("#hero-streams");
  if (!host) return;
  const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+-=[]{}<>?/";
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let columns = [];
  let frame = 0;
  let lastUpdate = 0;
  let isVisible = true;
  let resizeTimer = 0;
  const randomCharacter = () => characters[Math.floor(Math.random() * characters.length)];

  const build = () => {
    host.replaceChildren();
    columns = [];
    const width = Math.max(host.clientWidth, window.innerWidth);
    const height = Math.max(host.clientHeight, 420);
    const columnCount = Math.min(36, Math.max(10, Math.ceil(width / 38)));
    const symbolCount = Math.ceil(height / 19) + 5;
    const fragment = document.createDocumentFragment();
    for (let index = 0; index < columnCount; index += 1) {
      if (index % 13 === 7) continue;
      const column = document.createElement("span");
      column.className = "stream-column";
      column.style.left = `${(index / Math.max(1, columnCount - 1)) * 100}%`;
      column.style.opacity = String(.36 + Math.random() * .34);
      const symbols = [];
      for (let row = 0; row < symbolCount; row += 1) {
        const symbol = document.createElement("i");
        symbol.className = "stream-symbol";
        symbol.textContent = randomCharacter();
        column.append(symbol);
        symbols.push(symbol);
      }
      columns.push({ symbols, position: -Math.floor(Math.random() * symbolCount), speed: .68 + Math.random() * .65, previous: -20 });
      fragment.append(column);
    }
    host.append(fragment);
  };

  const paintColumn = (column) => {
    for (let offset = 0; offset < 4; offset += 1) column.symbols[column.previous - offset]?.classList.remove("is-head", "trail-1", "trail-2", "trail-3");
    const head = Math.floor(column.position);
    column.symbols[head]?.classList.add("is-head");
    column.symbols[head - 1]?.classList.add("trail-1");
    column.symbols[head - 2]?.classList.add("trail-2");
    column.symbols[head - 3]?.classList.add("trail-3");
    column.previous = head;
    column.position += .48 * column.speed;
    if (Math.random() < .06) column.symbols[Math.floor(Math.random() * column.symbols.length)].textContent = randomCharacter();
    if (column.position > column.symbols.length + 4) {
      column.position = -Math.floor(4 + Math.random() * 18);
      column.speed = .68 + Math.random() * .65;
    }
  };

  const animate = (time) => {
    if (isVisible && !document.hidden && time - lastUpdate >= 50) {
      columns.forEach(paintColumn);
      lastUpdate = time;
    }
    frame = requestAnimationFrame(animate);
  };

  build();
  if (!reducedMotion) {
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([entry]) => { isVisible = entry.isIntersecting; }, { threshold: 0 }).observe(host);
    }
    frame = requestAnimationFrame(animate);
  } else {
    host.classList.add("is-static");
  }
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(build, 160);
  }, { passive: true });
  window.addEventListener("pagehide", () => cancelAnimationFrame(frame), { once: true });
}

function setupSmoothScroll() {
  const wrapper = document.querySelector("#smooth-wrapper");
  const content = document.querySelector("#smooth-content");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const mobileViewport = matchMedia("(max-width: 820px)");
  if (!wrapper || !content || reduceMotion.matches || mobileViewport.matches) return null;

  let currentScroll = window.scrollY;
  let targetScroll = window.scrollY;
  let frame = 0;
  let resizeObserver = null;
  let stickyMetrics = [];

  const headerHeight = () => document.querySelector(".site-header")?.getBoundingClientRect().height || 0;
  const applySmoothSticky = () => {
    const enabled = window.innerWidth > 900;
    stickyMetrics.forEach(({ card, top, max }) => {
      const offset = enabled ? Math.max(0, Math.min(max, currentScroll - top + 18)) : 0;
      card.style.setProperty("--smooth-sticky-y", `${offset.toFixed(2)}px`);
    });
  };
  const measureStickyCards = () => {
    const cards = [...content.querySelectorAll("#story-list .story-panel")];
    cards.forEach((card) => card.style.setProperty("--smooth-sticky-y", "0px"));
    if (!cards.length) {
      stickyMetrics = [];
      return;
    }
    const contentTop = content.getBoundingClientRect().top;
    const list = cards[0].closest(".story-list");
    const listBottom = list.getBoundingClientRect().bottom - contentTop;
    stickyMetrics = cards.map((card) => {
      const rect = card.getBoundingClientRect();
      const top = rect.top - contentTop;
      return { card, top, max: Math.max(0, listBottom - top - rect.height) };
    });
    applySmoothSticky();
  };
  const setBodyHeight = () => {
    document.body.style.height = `${Math.ceil(content.scrollHeight + headerHeight())}px`;
    measureStickyCards();
  };
  const scrollToElement = (element, offset = 14) => {
    if (!element) return;
    const top = Math.max(0, currentScroll + element.getBoundingClientRect().top - headerHeight() - offset);
    window.scrollTo({ top, behavior: "auto" });
  };
  const renderFrame = () => {
    targetScroll = window.scrollY;
    currentScroll += (targetScroll - currentScroll) * 0.075;
    if (Math.abs(targetScroll - currentScroll) < 0.05) currentScroll = targetScroll;
    wrapper.style.transform = `translate3d(0, ${-currentScroll}px, 0)`;
    applySmoothSticky();
    frame = requestAnimationFrame(renderFrame);
  };

  document.documentElement.classList.add("smooth-scroll-enabled");
  setBodyHeight();
  window.addEventListener("resize", setBodyHeight, { passive: true });
  if ("ResizeObserver" in window) {
    resizeObserver = new ResizeObserver(setBodyHeight);
    resizeObserver.observe(content);
  }
  frame = requestAnimationFrame(renderFrame);

  const controller = {
    scrollToElement,
    refresh: setBodyHeight,
    destroy() {
      cancelAnimationFrame(frame);
      resizeObserver?.disconnect();
      window.removeEventListener("resize", setBodyHeight);
      wrapper.style.removeProperty("transform");
      stickyMetrics.forEach(({ card }) => card.style.removeProperty("--smooth-sticky-y"));
      stickyMetrics = [];
      document.body.style.removeProperty("height");
      document.documentElement.classList.remove("smooth-scroll-enabled");
    },
  };
  reduceMotion.addEventListener?.("change", (event) => {
    if (event.matches) controller.destroy();
  }, { once: true });
  mobileViewport.addEventListener?.("change", (event) => {
    if (event.matches) controller.destroy();
  }, { once: true });
  return controller;
}

function scrollToContent(element) {
  if (!element) return;
  if (smoothScrollController) smoothScrollController.scrollToElement(element);
  else element.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
}

function directSearchHref(tool, detection, rawQuery) {
  const acceptedTypes = acceptedIndicatorTypes(detection);
  if (!detection || !rawQuery || !acceptedTypes.some((type) => (tool.input_types || []).includes(type))) return null;
  const cleaned = detection.type === "telegram-username" ? compactTelegramQuery(rawQuery) : rawQuery.trim();
  if (tool.slug === "rdap") {
    if (detection.type === "ip") return `https://rdap.org/ip/${encodeURIComponent(cleaned)}`;
    if (detection.type === "asn") return `https://rdap.org/autnum/${encodeURIComponent(cleaned.replace(/^AS\s*/i, ""))}`;
    return `https://rdap.org/domain/${encodeURIComponent(cleaned)}`;
  }
  if (tool.slug === "urlscan") {
    const field = detection.type === "ip" ? "page.ip" : detection.type === "url" ? "page.url" : "page.domain";
    return `https://urlscan.io/search/#${field}:${encodeURIComponent(cleaned)}`;
  }
  if (!tool.query_url_template?.includes("{query}")) return null;
  return tool.query_url_template.replaceAll("{query}", encodeURIComponent(cleaned));
}

function fileToolCompatible(tool, detection = detectSelectedFile()) {
  if (!detection) return false;
  const inputTypes = tool.input_types || [];
  if (inputTypes.includes(detection.type)) return true;
  if (["exif-tools", "virustotal-files"].includes(tool.slug)) return true;
  if (tool.slug === "virustotal-url") return false;
  return Boolean(state.selectedFileHash && inputTypes.includes("file-hash") && directSearchHref(tool, { type: "file-hash", label: "Fayl hashi" }, state.selectedFileHash));
}

function toolSearchAction(tool) {
  const detection = currentDetection();
  if (state.selectedFile) {
    const hashDetection = { type: "file-hash", label: "Fayl hashi", categories: ["media", "mobile-threats", "search"] };
    const hashHref = state.selectedFileHash ? directSearchHref(tool, hashDetection, state.selectedFileHash) : null;
    if (hashHref) return { href: hashHref, direct: true, mode: "hash" };
    return { href: tool.url, direct: false, mode: "upload" };
  }
  const directHref = directSearchHref(tool, detection, state.query);
  return { href: directHref || tool.url, direct: Boolean(directHref), mode: directHref ? "query" : "open" };
}

function toolHref(tool) {
  return toolSearchAction(tool).href;
}

function recommendedTools() {
  const query = normalize(state.query);
  const detected = currentDetection();
  if (!query && !state.selectedFile) return [];
  const acceptedTypes = acceptedIndicatorTypes(detected);
  const preferredCategories = (detected?.categories || []).filter((slug) => slug !== "search");
  const pool = state.category ? state.tools.filter((tool) => tool.category_slug === state.category.slug) : state.tools;
  const matches = pool
    .map((tool) => {
      const inputTypes = tool.input_types || [];
      const textMatch = Boolean(query) && allSearchText(tool).includes(query);
      const nameMatch = Boolean(query) && (normalize(tool.name).includes(query) || normalize(tool.slug) === query);
      const inputMatch = state.selectedFile ? fileToolCompatible(tool, detected) : acceptedTypes.some((type) => inputTypes.includes(type));
      const primaryFileMatch = Boolean(state.selectedFile && inputTypes.includes(detected?.type));
      const hashMatch = Boolean(state.selectedFileHash && inputTypes.includes("file-hash"));
      const categoryIndex = detected?.categories.indexOf(tool.category_slug) ?? -1;
      const categoryMatch = categoryIndex >= 0;
      const specializedMatch = preferredCategories.includes(tool.category_slug);
      const action = toolSearchAction(tool);
      let score = 0;
      if (textMatch) score += 100;
      if (nameMatch) score += 140;
      if (inputMatch) score += state.selectedFile ? 70 : 80;
      if (primaryFileMatch) score += 55;
      if (hashMatch) score += 18;
      if (categoryMatch) score += (detected.categories.length - categoryIndex) * 10;
      if (specializedMatch) score += 120;
      if (action.direct) score += 35;
      if (tool.featured) score += 8;
      if (tool.access === "free") score += 4;
      return { tool, score, inputMatch, textMatch, nameMatch, specializedMatch, action };
    })
    .filter((entry) => entry.inputMatch || entry.textMatch || (!state.selectedFile && entry.specializedMatch && detected));

  const exactToolMatches = matches.filter((entry) => entry.nameMatch);
  const specializedMatches = matches.filter((entry) => entry.specializedMatch);
  const scopedMatches = exactToolMatches.length ? exactToolMatches : specializedMatches.length ? specializedMatches : matches;
  const actionableMatches = exactToolMatches.length || specializedMatches.length
    ? scopedMatches
    : scopedMatches.filter((entry) => state.selectedFile || entry.action.direct || (entry.textMatch && !entry.inputMatch));

  return actionableMatches
    .sort((a, b) => b.score - a.score || a.tool.sort_order - b.tool.sort_order || a.tool.name.localeCompare(b.tool.name))
    .slice(0, 6);
}

function renderRecommendations(detected) {
  const recommendations = recommendedTools();
  elements.heroSection?.classList.toggle("has-recommendations", recommendations.length > 0);
  elements.recommendations.classList.toggle("hidden", recommendations.length === 0);
  elements.recommendationList.replaceChildren();
  if (!recommendations.length) return;
  elements.recommendationContext.textContent = display(`${recommendations.length} ta mos vosita · ${detected?.label || "qidiruv natijasi"}`);

  const fragment = document.createDocumentFragment();
  recommendations.forEach(({ tool, inputMatch, action }) => {
    const link = document.createElement("a");
    link.className = `recommendation-item${action.direct ? " is-direct" : " is-upload"}`;
    link.href = action.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `${tool.name} — ${display("tashqi OSINT vositasini ochish")}`);

    const icon = document.createElement("span");
    icon.className = "recommendation-icon";
    const image = document.createElement("img");
    image.alt = "";
    const text = document.createElement("b");
    icon.append(image, text);
    const visual = iconSystem.resolve(tool, "tool");
    icon.dataset.iconTheme = visual.theme;
    iconSystem.mount(icon, image, text, visual);

    const copy = document.createElement("span");
    copy.className = "recommendation-copy";
    const name = document.createElement("b");
    name.textContent = tool.name;
    const reason = document.createElement("span");
    if (action.mode === "hash") reason.textContent = display("SHA-256 bo'yicha bevosita qidirish");
    else if (action.mode === "query") reason.textContent = display(`${detected.label} bo'yicha bevosita qidirish`);
    else if (action.mode === "upload") reason.textContent = display("Faylni ochilgan sahifada yuklash");
    else reason.textContent = display(inputMatch ? `${detected.label} uchun` : tool.category_name);
    copy.append(name, reason);

    const arrow = document.createElement("span");
    arrow.className = "recommendation-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.innerHTML = uiIcons.svg("external", "", 16);
    link.append(icon, copy, arrow);
    if (action.mode === "upload") {
      link.addEventListener("click", () => showFileFeedback(`${tool.name} ochildi. Maxfiylikni saqlash uchun tanlangan faylni ochilgan sahifada o'zingiz yuklang.`));
    }
    fragment.append(link);
  });
  elements.recommendationList.append(fragment);
}

function renderToolCard(tool, index) {
  const card = elements.toolTemplate.content.firstElementChild.cloneNode(true);
  const link = card.querySelector(".card-main-link");
  link.href = toolHref(tool);
  link.setAttribute("aria-label", `${tool.name} — ${display("tashqi OSINT vositasini ochish")}`);
  card.dataset.toolId = tool.id;
  card.querySelector(".card-index").textContent = String(index + 1).padStart(2, "0");
  card.querySelector("h3").textContent = tool.name;
  const access = accessLabels[tool.access] || tool.access;
  const accessBadge = card.querySelector(".access-badge");
  const accessLabel = display(tool.login_required ? `${access} · Login talab etiladi` : access);
  const accessIcon = tool.login_required ? "users" : tool.access === "free" ? "check" : "shield";
  accessBadge.innerHTML = uiIcons.svg(accessIcon, "", 17);
  accessBadge.setAttribute("aria-label", accessLabel);
  accessBadge.title = accessLabel;
  card.querySelector(".details-button b").textContent = display("Batafsil");
  card.querySelector(".card-description").textContent = display(tool.description);
  applyCardVisual(card, tool, "tool");
  card.querySelector(".details-button").addEventListener("click", (event) => openDetails(tool, "tool", event.currentTarget));
  [...tool.networks, ...tool.tags].slice(0, 4).forEach((tag) => card.querySelector(".card-tags").append(createTag(tag)));
  return card;
}

function clearToolCarouselTimers() {
  toolCarouselTimers.forEach((timer) => window.clearInterval(timer));
  toolCarouselTimers = [];
}

function carouselLoopWidth(carousel) {
  const sets = carousel.querySelectorAll(".tool-carousel-set");
  return sets.length > 1 ? sets[1].offsetLeft - sets[0].offsetLeft : carousel.scrollWidth;
}

function moveToolCarousel(carousel, direction) {
  if (!carousel || window.innerWidth > 820) return;
  const loopWidth = carouselLoopWidth(carousel);
  const card = carousel.querySelector(".feature-card");
  const gap = Number.parseFloat(getComputedStyle(carousel.querySelector(".tool-carousel-set")).gap) || 14;
  const step = (card?.getBoundingClientRect().width || carousel.clientWidth * .86) + gap;
  if (direction > 0 && carousel.scrollLeft + step >= loopWidth - 2) {
    carousel.scrollTo({ left: 0, behavior: "auto" });
  } else if (direction < 0 && carousel.scrollLeft <= 2) {
    carousel.scrollTo({ left: loopWidth, behavior: "auto" });
  }
  carousel.scrollBy({ left: direction * step, behavior: "smooth" });
}

function createToolCarouselControls(carousel, category) {
  const controls = document.createElement("div");
  controls.className = "tool-carousel-controls";
  const previous = document.createElement("button");
  previous.type = "button";
  previous.setAttribute("aria-label", display(`${category.name}: oldingi vosita`));
  previous.innerHTML = uiIcons.svg("arrowLeft", "", 18);
  const next = document.createElement("button");
  next.type = "button";
  next.setAttribute("aria-label", display(`${category.name}: keyingi vosita`));
  next.innerHTML = uiIcons.svg("arrowRight", "", 18);
  previous.addEventListener("click", () => moveToolCarousel(carousel, -1));
  next.addEventListener("click", () => moveToolCarousel(carousel, 1));
  controls.append(previous, next);
  return controls;
}

function renderToolGroup(category, tools, groupIndex) {
  const section = document.createElement("section");
  section.className = "tool-group";
  section.setAttribute("aria-labelledby", `tool-group-${category.slug}`);

  const header = document.createElement("header");
  header.className = "tool-group-header";
  const title = document.createElement("div");
  title.className = "tool-group-title";
  const counter = document.createElement("p");
  counter.textContent = display(`${String(groupIndex + 1).padStart(2, "0")} · ${tools.length} ta vosita`);
  const heading = document.createElement("h3");
  heading.id = `tool-group-${category.slug}`;
  if (state.category) {
    heading.textContent = display(category.name);
  } else {
    const link = document.createElement("a");
    link.href = `/category/${category.slug}`;
    link.textContent = display(category.name);
    heading.append(link);
  }
  title.append(counter, heading);

  header.append(title);

  const orderedTools = [...tools].sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name));
  if (state.category) {
    const grid = document.createElement("div");
    grid.className = "tool-grid";
    orderedTools.forEach((tool, index) => grid.append(renderToolCard(tool, index)));
    section.append(header, grid);
    return section;
  }

  section.classList.add("has-tool-carousel");
  const carousel = document.createElement("div");
  carousel.className = "tool-carousel";
  carousel.setAttribute("aria-label", display(`${category.name} vositalari karuseli`));
  const track = document.createElement("div");
  track.className = `tool-carousel-track${groupIndex % 2 ? " reverse" : ""}`;
  track.style.setProperty("--carousel-duration", `${Math.max(28, orderedTools.length * 6)}s`);

  const buildSet = (duplicate = false) => {
    const set = document.createElement("div");
    set.className = "tool-carousel-set";
    if (duplicate) set.setAttribute("aria-hidden", "true");
    orderedTools.forEach((tool, index) => {
      const card = renderToolCard(tool, index);
      if (duplicate) card.querySelectorAll("a, button").forEach((control) => control.setAttribute("tabindex", "-1"));
      set.append(card);
    });
    return set;
  };
  track.append(buildSet(), buildSet(true));
  carousel.append(track);
  header.append(createToolCarouselControls(carousel, category));
  section.append(header, carousel);
  return section;
}

function renderToolGroups(items) {
  const fragment = document.createDocumentFragment();
  const categories = state.category ? [state.category] : state.categories;
  let groupIndex = 0;
  categories.forEach((category) => {
    const tools = items.filter((tool) => tool.category_slug === category.slug);
    if (!tools.length) return;
    fragment.append(renderToolGroup(category, tools, groupIndex));
    groupIndex += 1;
  });
  elements.grid.replaceChildren(fragment);
  setupToolCarouselVisibility();
}

function setupToolCarouselVisibility() {
  clearToolCarouselTimers();
  toolCarouselObserver?.disconnect();
  const carousels = elements.grid.querySelectorAll(".tool-carousel");
  if (!carousels.length) return;
  if (!("IntersectionObserver" in window)) {
    carousels.forEach((carousel) => carousel.classList.add("is-running"));
    return;
  }
  toolCarouselObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => entry.target.classList.toggle("is-running", entry.isIntersecting));
  }, { rootMargin: "120px 0px", threshold: .01 });
  carousels.forEach((carousel) => toolCarouselObserver.observe(carousel));
  if (window.innerWidth <= 820 && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    carousels.forEach((carousel) => {
      const timer = window.setInterval(() => {
        if (!document.hidden && carousel.classList.contains("is-running") && !carousel.matches(":hover") && !carousel.contains(document.activeElement)) {
          moveToolCarousel(carousel, 1);
        }
      }, 4600);
      toolCarouselTimers.push(timer);
    });
  }
}

function defaultDetails(item, kind) {
  if (kind === "category") {
    const capabilities = {
      crypto: [
        "Kriptoaktiv hamyon balansi, tranzaksiyalar tarixi va mablag'lar harakatini tekshirish.",
        "Tranzaksiya hashi asosida jo'natuvchi, qabul qiluvchi, vaqt, summa va komissiyaga oid ma'lumotlarni aniqlash.",
        "Token, smart-kontrakt va tegishli blokcheyn tarmog'iga doir ma'lumotlarni tekshirish.",
        "Hamyonlar o'rtasidagi ehtimoliy o'zaro bog'liqlik hamda mablag'lar yo'nalishini grafik shaklda tahlil qilish.",
        "Firibgarlik, sanksiyaviy cheklov yoki boshqa xavf belgilarini bir nechta ochiq manba orqali qiyosiy tekshirish.",
      ],
      telegram: [
        "Telegram username, public ID, kanal yoki guruh havolasi asosida ochiq profil ma'lumotlarini aniqlash.",
        "Kanal tavsifi, faollik belgilari, ochiq postlar va tashqi havolalarni tekshirish.",
        "Postlar soni, ko'rishlar, auditoriya dinamikasi hamda faollik vaqtlarini tahlil qilish.",
        "Username va ochiq kontent asosida boshqa akkaunt, sayt yoki ijtimoiy tarmoq profillariga oid tekshiruv yo'nalishlarini belgilash.",
        "Ahamiyatli post, profil va metadata ma'lumotlarini sana-vaqt ko'rsatkichi bilan qayd etish.",
      ],
      username: [
        "Username qaysi ochiq platformalarda qo'llanilganini aniqlash.",
        "Mos nickname, avatar va profil tavsiflari orqali ehtimoliy bog'liq akkauntlarni aniqlash.",
        "Alias va username o'zgarishlari bo'yicha qo'shimcha tekshiruv yo'nalishlarini shakllantirish.",
        "Ochiq profil havolalari, faollik izlari va bog'langan domenlarni qiyosiy tekshirish.",
      ],
      search: [
        "Shaxs nomi, username, telefon raqami, email, IP manzil, domen, URL yoki boshqa kalit so'z bo'yicha indekslangan ochiq sahifalarni qidirish.",
        "Qidiruv operatorlari yordamida natijalarni muayyan domen, fayl turi, sana yoki aniq ibora bo'yicha aniqlashtirish.",
        "Google Search, Yandex Search va Microsoft Bing natijalarini o'zaro qiyoslash orqali qo'shimcha manbalarni aniqlash.",
        "2GIS orqali tashkilot nomi, manzil yoki telefon raqami bo'yicha ochiq xarita va katalog yozuvlarini tekshirish.",
        "Ahamiyatli natijaning sarlavhasi, URL manzili, qidiruv so'rovi hamda tekshiruv sanasi va vaqtini qayd etish.",
      ],
      network: [
        "IP, domen va URL bo'yicha WHOIS, DNS, ASN, hosting hamda sertifikat ma'lumotlarini tekshirish.",
        "IP yoki domen reputatsiyasi, ehtimoliy zararli faollik va abuse hisobotlarini aniqlash.",
        "Subdomenlar, tarixiy DNS yozuvlari va bir infratuzilmaga bog'langan boshqa aktivlarni aniqlash.",
        "Ochiq portlar, servislar va internet tarmog'iga chiqarilgan qurilmalar bo'yicha texnik ma'lumotlarni olish.",
        "URL yo'naltirish zanjiri, sahifa tasviri va tashqi tarmoq so'rovlarini tekshirish.",
      ],
      "mobile-threats": [
        "Shubhali URL manzili bo'yicha reputatsiya, yo'naltirish zanjiri va fishing belgilarini tekshirish.",
        "APK yoki AAB paketini statik tahlil qilib, ruxsatlar, imzo va ichki komponentlarga oid ma'lumotlarni aniqlash.",
        "Fayl hashini zararli dasturlar va threat-intelligence bazalari orqali qiyosiy tekshirish.",
        "Ilovaning tashqi domenlari, IP manzillari va tarmoq so'rovlariga oid ochiq ma'lumotlarni aniqlash.",
        "Aniqlangan xavf belgilarini tekshiruv vaqti, manba URL manzili hamda hash qiymati bilan qayd etish.",
      ],
      media: [
        "Rasmni reverse image search orqali dastlabki yoki o'xshash ochiq manbalarda aniqlash.",
        "EXIF va fayl metadata ma'lumotlari asosida qurilma, sana, dastur yoki joylashuv belgilarini tekshirish.",
        "Rasm tahriri, siqilish farqlari va ehtimoliy manipulyatsiya belgilarini aniqlash.",
        "Video kadrlarini alohida tasvir ko'rinishida ajratish va tekshirish.",
        "Fayl hashini zararli dasturlar va threat-intelligence bazalari orqali tekshirish.",
      ],
    };
    const actions = capabilities[item.slug] || [
      "Mavjud indikatorni ochiq manbalar orqali tekshirish va bog'liq raqamli ma'lumotlarni aniqlash.",
      "Bir nechta vosita natijalarini qiyoslash orqali tekshiruv versiyasini aniqlashtirish.",
      "Ahamiyatli natijalarni manba havolasi hamda sana-vaqt ko'rsatkichi bilan qayd etish.",
    ];
    return `Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:\n${actions.map((action) => `- ${action}`).join("\n")}\n\nTekshiruvni amalga oshirish tartibi:\n- Tekshiruv predmetiga oid dastlabki indikator turini belgilang.\n- Dastlab tezkor tekshiruv vositasidan, so'ng kengaytirilgan tahlil vositasidan foydalaning.\n- Ahamiyatli natijalarni kamida ikkita mustaqil ochiq manba orqali qiyosiy tekshiring.\n- Manbaning URL manzili, tekshiruv sanasi va vaqti hamda aniqlangan holatni qayd eting.`;
  }

  const inputs = (item.input_types || []).join(", ") || "ochiq indikator";
  const networks = (item.networks || []).join(", ") || item.category_name || "OSINT";
  const inputActions = {
    wallet: "Kriptoaktiv hamyon balansi, tranzaksiyalar tarixi va bog'liq manzillarni tekshirish.",
    "tx-hash": "Tranzaksiya vaqti, summasi, holati, jo'natuvchi va qabul qiluvchiga oid ma'lumotlarni aniqlash.",
    contract: "Smart-kontrakt, token va kontrakt chaqiruvlariga oid ma'lumotlarni tekshirish.",
    "telegram-username": "Telegram username bo'yicha public profil, kanal yoki guruh ma'lumotlarini aniqlash.",
    "telegram-channel": "Kanal postlari, auditoriya va faollik ko'rsatkichlarini tahlil qilish.",
    "telegram-id": "Mavjud public IDni boshqa ochiq Telegram ma'lumotlari bilan qiyosiy tekshirish.",
    username: "Username qo'llanilgan ochiq profil va platformalarni aniqlash.",
    email: "Email reputatsiyasi, ma'lumotlar sizib chiqishi va bog'liq public akkauntlarni tekshirish.",
    phone: "Telefon raqami formati, mamlakat kodi va ochiq manbalardagi bog'lanishlarni tekshirish.",
    name: "Shaxs nomi bo'yicha indekslangan ochiq sahifa va ehtimoliy bog'liq public profillarni qidirish.",
    address: "Manzil va unga bog'liq public tashkilot yoki joy ma'lumotlarini tekshirish.",
    ip: "IP geolokatsiyasi, ASN, hosting, reputatsiya va abuse belgilarini tekshirish.",
    asn: "ASN va unga biriktirilgan tarmoq diapazoni hamda ro'yxatga olish ma'lumotlarini tekshirish.",
    domain: "Domen WHOIS, DNS, sertifikat, subdomen va tarixiy infratuzilma ma'lumotlarini tekshirish.",
    url: "URL reputatsiyasi, redirect zanjiri, sahifa tasviri va tarmoq so'rovlarini tekshirish.",
    image: "Rasm manbasi, o'xshash nusxalar, metadata va tahrir belgilarini aniqlash.",
    file: "Fayl metadata ma'lumotlari va texnik xususiyatlarini tekshirish.",
    document: "Hujjat muallifi, dastur, yaratilgan sana va boshqa metadata ma'lumotlarini aniqlash.",
    video: "Video kadrlarini ajratish hamda manba va vizual mosliklarni tekshirish.",
    "file-hash": "Fayl hashini malware va threat-intelligence bazalari orqali tekshirish.",
    keyword: "Kalit so'z orqali ochiq post, profil yoki texnik manbalarni aniqlash.",
    certificate: "TLS sertifikati va unga bog'langan domen yoki infratuzilmani tekshirish.",
  };
  const actions = [...new Set((item.input_types || []).map((type) => inputActions[type]).filter(Boolean))];
  if (!actions.length) actions.push(item.description || "Ochiq manbadagi mavjud ma'lumotni tekshirish.");
  if (item.query_url_template) actions.push("Kiritilgan indikatorni mazkur vositada bevosita tekshiruv so'rovi sifatida ochish.");
  return `${item.name} vositasi yordamida quyidagi ma'lumotlarni aniqlash yoki tekshirish mumkin:\n${actions.map((action) => `- ${action}`).join("\n")}\n\nTekshiriladigan ma'lumot turlari:\n- ${inputs}\n\nTegishli tarmoq yoki xizmat:\n- ${networks}\n\nNatijalarni qayd etish tartibi:\n- Tekshiruv sanasi va vaqti, kiritilgan indikator hamda natija manzilini qayd eting.\n- Aniqlangan identifikator, sana, summa yoki boshqa texnik belgilarni alohida qayd eting.\n- Natijalarni boshqa mustaqil manbalar va tekshiruv materiallari bilan qiyoslang.`;
}

function renderDetailsText(value) {
  elements.detailsContent.replaceChildren();
  const lines = String(value || "").replace(/\r/g, "").split("\n");
  let paragraph = [];
  let list = null;

  const flushParagraph = () => {
    if (!paragraph.length) return;
    const node = document.createElement("p");
    node.textContent = paragraph.join(" ");
    elements.detailsContent.append(node);
    paragraph = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      list = null;
      return;
    }
    if (/^#{1,3}\s+/.test(line) || (line.endsWith(":") && line.length < 80)) {
      flushParagraph();
      list = null;
      const heading = document.createElement("h3");
      heading.textContent = display(line.replace(/^#{1,3}\s+/, "").replace(/:$/, ""));
      elements.detailsContent.append(heading);
      return;
    }
    if (/^-\s+/.test(line)) {
      flushParagraph();
      if (!list) {
        list = document.createElement("ul");
        elements.detailsContent.append(list);
      }
      const item = document.createElement("li");
      item.textContent = display(line.replace(/^-\s+/, ""));
      list.append(item);
      return;
    }
    list = null;
    paragraph.push(display(line));
  });
  flushParagraph();
}

function openDetails(item, kind, trigger) {
  detailsReturnFocus = trigger;
  const visual = iconSystem.resolve(item, kind);
  const icon = elements.detailsModal.querySelector(".details-icon");
  icon.dataset.iconTheme = visual.theme;
  iconSystem.mount(
    icon,
    elements.detailsModal.querySelector(".details-icon-image"),
    elements.detailsModal.querySelector(".details-icon-text"),
    visual,
  );
  elements.detailsKind.textContent = display(kind === "category" ? "TEKSHIRUV YO'NALISHI" : "OSINT VOSITASI");
  elements.detailsTitle.textContent = kind === "tool" ? item.name : display(item.name);
  elements.detailsSummary.textContent = display(item.description);
  renderDetailsText(item.details || defaultDetails(item, kind));
  elements.detailsMeta.replaceChildren();
  const meta = kind === "category" ? item.tags : [...(item.input_types || []), ...(item.networks || []), ...(item.tags || [])];
  [...new Set(meta)].slice(0, 10).forEach((label) => elements.detailsMeta.append(createTag(label)));

  elements.detailsAction.innerHTML = `${display(kind === "category" ? "Yo'nalishdagi vositalarni ko'rish" : "Tashqi vositani ochish")} ${uiIcons.svg(kind === "category" ? "arrowRight" : "external", "", 16)}`;
  elements.detailsAction.href = kind === "category" ? `/category/${item.slug}` : toolHref(item);
  if (kind === "tool") {
    elements.detailsAction.target = "_blank";
    elements.detailsAction.rel = "noopener noreferrer";
  } else {
    elements.detailsAction.removeAttribute("target");
    elements.detailsAction.removeAttribute("rel");
  }
  elements.detailsModal.classList.remove("hidden");
  document.body.classList.add("modal-open");
  requestAnimationFrame(() => elements.detailsDialog.focus());
}

function closeDetails() {
  elements.detailsModal.classList.add("hidden");
  document.body.classList.remove("modal-open");
  detailsReturnFocus?.focus();
  detailsReturnFocus = null;
}

function currentCategorySlug() {
  const match = window.location.pathname.match(/^\/category\/([a-z0-9-]+)\/?$/i);
  return match ? match[1] : null;
}

function currentGuideRoute() {
  return /^\/guide\/?$/i.test(window.location.pathname);
}

const guideSteps = [
  {
    number: "01",
    tabTitle: "Индикаторни киритинг",
    tabDescription: "Username, домен, IP манзил ёки крипто ҳамён манзилини киритинг.",
    header: "01 · Индикаторни киритиш",
    title: "Қидирув майдонига маълумотни киритинг",
    description: "Текширмоқчи бўлган объектинингизни асосий қидирув майдонига ёзинг ёки қўйинг. Масалан: @username, example.uz ёки IP манзил.",
    tip: "Мисол: Telegram аккаунти учун @username форматида киритинг.",
  },
  {
    number: "02",
    tabTitle: "Йўналишни аниқланг",
    tabDescription: "Нима текшираётганингизга қараб керакли йўналишни танланг.",
    header: "02 · Йўналишни танлаш",
    title: "Объект турига мос йўналишни танланг",
    description: "Индикаторга қараб текширув турини танланг. Telegram аккаунти, IP/домен ёки криптоактив учун алоҳида йўналишлардан фойдаланилади.",
    tip: "Нотўғри йўналиш танланса, керакли воситалар рўйхати мос келмаслиги мумкин.",
  },
  {
    number: "03",
    tabTitle: "Восита орқали текширинг",
    tabDescription: "Тавсия қилинган воситани очинг ва текширувни давом эттиринг.",
    header: "03 · Воситани очиш",
    title: "Тавсия қилинган восита билан текширинг",
    description: "Тизим кўрсатган воситалардан бирини танланг. Ҳар бир восита маълум турдаги индикаторни қўшимча текшириш учун хизмат қилади.",
    tip: "Масалан, домен ва файлларни VirusTotal орқали, Ethereum манзилларини Etherscan орқали текшириш мумкин.",
  },
];

function guideDemoMarkup(index) {
  const bar = '<div class="demo-browser-bar" aria-hidden="true"><i></i><i></i><i></i></div>';
  if (index === 0) {
    return `<div class="demo-browser">${bar}<div class="demo-browser-body"><label class="demo-label">${display("Индикатор")}</label><div class="demo-input-row"><span data-no-transliterate>@example_user</span><button type="button" tabindex="-1">${display("Текшириш")}</button></div><span class="guide-pointer" aria-hidden="true">↗</span></div></div>`;
  }
  if (index === 1) {
    return `<div class="demo-browser">${bar}<div class="demo-browser-body"><span class="demo-label">${display("Йўналиш")}</span><div class="demo-choice-grid"><span class="demo-choice is-active">Telegram</span><span class="demo-choice">${display("IP ва домен")}</span><span class="demo-choice">${display("Криптоактив")}</span></div><span class="guide-pointer" aria-hidden="true">↗</span></div></div>`;
  }
  return `<div class="demo-browser">${bar}<div class="demo-browser-body"><span class="demo-label">${display("Тавсия қилинган воситалар")}</span><div class="demo-tool-list"><span class="demo-tool"><span data-no-transliterate>VirusTotal</span><b>${display("ОЧИШ")} ↗</b></span><span class="demo-tool"><span data-no-transliterate>Etherscan</span><b>${display("ОЧИШ")} ↗</b></span><span class="demo-tool"><span data-no-transliterate>urlscan.io</span><b>${display("ОЧИШ")} ↗</b></span></div><span class="guide-pointer" aria-hidden="true">↗</span></div></div>`;
}

function renderGuideStep(index, focusPanel = false) {
  guideStepIndex = Math.max(0, Math.min(guideSteps.length - 1, index));
  const step = guideSteps[guideStepIndex];
  elements.guideTabs.querySelectorAll(".guide-tab").forEach((tab, tabIndex) => {
    const active = tabIndex === guideStepIndex;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  elements.guideDetailIndex.textContent = display(step.header);
  elements.guideDetailTitle.textContent = display(step.title);
  elements.guideDetailDescription.textContent = display(step.description);
  elements.guideTip.textContent = display(step.tip);
  elements.guideDemo.innerHTML = guideDemoMarkup(guideStepIndex);
  elements.guidePrevious.disabled = guideStepIndex === 0;
  elements.guideNext.textContent = display(guideStepIndex === guideSteps.length - 1 ? "Бошидан кўриш ↻" : "Кейинги →");
  elements.guideStatus.textContent = `${guideStepIndex + 1} / ${guideSteps.length}`;
  if (focusPanel) elements.guidePanel.focus({ preventScroll: true });
}

function renderGuidePage() {
  if (!elements.guidePage) return;
  elements.guidePage.classList.remove("hidden");
  elements.guideEyebrow.textContent = display("Тизимдан фойдаланиш");
  elements.guideTitle.textContent = display("Текширувни уч қадамда бошланг");
  elements.guideDescription.textContent = display("Қадам устига босинг — пастда айнан шу амални қандай бажариш кераклиги қисқа анимация ва изоҳ билан кўрсатилади.");
  elements.guideTabs.replaceChildren();
  guideSteps.forEach((step, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "guide-tab";
    button.id = `guide-tab-${index + 1}`;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-controls", "guide-panel");
    button.innerHTML = `<span>${step.number}</span><strong>${display(step.tabTitle)}</strong><small>${display(step.tabDescription)}</small>`;
    button.addEventListener("click", () => renderGuideStep(index));
    button.addEventListener("keydown", (event) => {
      const keyIndex = { ArrowLeft: index - 1, ArrowRight: index + 1, Home: 0, End: guideSteps.length - 1 }[event.key];
      if (keyIndex === undefined) return;
      event.preventDefault();
      const target = Math.max(0, Math.min(guideSteps.length - 1, keyIndex));
      renderGuideStep(target);
      elements.guideTabs.querySelectorAll(".guide-tab")[target].focus();
    });
    elements.guideTabs.append(button);
  });
  elements.guidePrevious.onclick = () => renderGuideStep(guideStepIndex - 1, true);
  elements.guideNext.onclick = () => renderGuideStep(guideStepIndex === guideSteps.length - 1 ? 0 : guideStepIndex + 1, true);
  renderGuideStep(0);
  document.title = `${display("Qo'llanma")} — OSINT`;
}

function setupPage() {
  const guide = currentGuideRoute();
  const slug = currentCategorySlug();
  state.category = slug ? state.categories.find((item) => item.slug === slug) : null;
  document.documentElement.classList.toggle("category-route", Boolean(slug));
  document.documentElement.classList.toggle("guide-route", guide);
  document.body.classList.toggle("category-view", Boolean(slug));
  document.body.classList.toggle("guide-view", guide);
  elements.guidePage?.classList.toggle("hidden", !guide);
  elements.categoryIntro?.classList.toggle("hidden", !slug || guide);

  if (guide) {
    buildCategoryFilters();
    renderGuidePage();
    return;
  }

  if (slug && !state.category) {
    elements.title.textContent = display("Tekshiruv yo'nalishi aniqlanmadi");
    elements.subtitle.textContent = display("Bosh sahifaga qayting va mavjud OSINT tekshiruv yo'nalishlaridan birini tanlang.");
    elements.back.classList.remove("hidden");
    if (elements.filters) elements.filters.innerHTML = "";
    render();
    return;
  }

  if (state.category) {
    elements.heroKicker.textContent = display("TANLANGAN TEKSHIRUV YO'NALISHI");
    elements.title.textContent = display(state.category.name);
    elements.subtitle.textContent = display(state.category.description);
    elements.back.classList.remove("hidden");
    elements.sectionEyebrow.textContent = display("YO'NALISH DOIRASIDAGI VOSITALAR");
    elements.sectionTitle.textContent = display("Tekshiruv uchun OSINT vositalari");
    document.title = `${display(state.category.name)} — OSINT`;
    buildToolFilters();
  } else {
    elements.heroKicker.textContent = display("OSINT KATALOGI");
    elements.sectionEyebrow.textContent = display("OSINT VOSITALARI");
    elements.sectionTitle.textContent = display("Tekshiruv uchun ochiq manbalar katalogi");
    buildCategoryFilters();
  }
}

function buildCategoryFilters() {
  if (!elements.filters) return;
  elements.filters.innerHTML = "";
  const options = [{ slug: "all", name: "Barcha yo'nalishlar" }, ...state.categories.map((category) => ({ slug: category.slug, name: category.name.split(" va ")[0] }))];
  options.forEach((option) => elements.filters.append(createFilterButton(option.slug, option.name)));
}

function buildToolFilters() {
  if (!elements.filters) return;
  const categoryTools = state.tools.filter((tool) => tool.category_slug === state.category.slug);
  const tags = [...new Set(categoryTools.flatMap((tool) => [...tool.networks, ...tool.tags]))].slice(0, 12);
  elements.filters.innerHTML = "";
  [{ slug: "all", name: "Barcha vositalar", technical: false }, ...tags.map((tag) => ({ slug: normalize(tag), name: tag, technical: true }))]
    .forEach((option) => elements.filters.append(createFilterButton(option.slug, option.name, option.technical)));
}

function createFilterButton(slug, label, preserveTechnicalLabel = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `filter-chip${state.activeFilter === slug ? " active" : ""}`;
  button.dataset.filter = slug;
  button.textContent = preserveTechnicalLabel ? label : display(label);
  button.addEventListener("click", () => {
    if (currentGuideRoute()) {
      window.location.assign(slug === "all" ? "/#catalog" : `/category/${slug}`);
      return;
    }
    state.activeFilter = slug;
    elements.filters.querySelectorAll(".filter-chip").forEach((chip) => chip.classList.toggle("active", chip.dataset.filter === slug));
    render();
  });
  return button;
}

function visibleCategories() {
  const query = normalize(state.query);
  const detected = detectIndicator(state.query);
  const hasDirectTextMatch = Boolean(query) && (
    state.categories.some((category) => normalize([category.name, category.description, category.details, ...category.tags].join(" ")).includes(query)) ||
    state.tools.some((tool) => allSearchText(tool).includes(query))
  );
  return state.categories.filter((category) => {
    if (state.activeFilter !== "all" && category.slug !== state.activeFilter) return false;
    if (!query) return true;
    const categoryMatch = normalize([category.name, category.description, category.details, ...category.tags].join(" ")).includes(query);
    const matchingTool = state.tools.some((tool) => tool.category_slug === category.slug && allSearchText(tool).includes(query));
    const indicatorMatch = !hasDirectTextMatch && detected?.categories.includes(category.slug);
    return categoryMatch || matchingTool || indicatorMatch;
  });
}

function visibleTools() {
  const query = normalize(state.query);
  const detected = currentDetection();
  const acceptedTypes = acceptedIndicatorTypes(detected);
  const pool = state.category ? state.tools.filter((tool) => tool.category_slug === state.category.slug) : state.tools;
  const hasDirectTextMatch = Boolean(query) && pool.some((tool) => allSearchText(tool).includes(query));
  return state.tools.filter((tool) => {
    if (state.category && tool.category_slug !== state.category.slug) return false;
    if (state.activeFilter !== "all") {
      if (!state.category && tool.category_slug !== state.activeFilter) return false;
      if (state.category) {
        const toolTags = [...tool.tags, ...tool.networks].map(normalize);
        if (!toolTags.includes(state.activeFilter)) return false;
      }
    }
    if (state.selectedFile) return fileToolCompatible(tool, detected);
    if (!query) return true;
    const textMatch = allSearchText(tool).includes(query);
    const inputMatch = !hasDirectTextMatch && acceptedTypes.some((type) => tool.input_types.includes(type));
    return textMatch || inputMatch;
  });
}

function render() {
  renderSelectedFile();
  if (currentGuideRoute()) {
    const detected = currentDetection();
    elements.detected.classList.toggle("hidden", !detected);
    if (detected) elements.detected.textContent = display(`${state.selectedFile ? "Tanlangan fayl turi" : "Aniqlangan indikator turi"}: ${detected.label}`);
    renderRecommendations(detected);
    elements.clear.classList.toggle("hidden", !state.query && !state.selectedFile);
    smoothScrollController?.refresh();
    return;
  }
  const items = visibleTools();
  renderToolGroups(items);
  elements.count.textContent = display(`${items.length} ta mos yozuv`);
  elements.empty.classList.toggle("hidden", items.length !== 0);
  elements.grid.classList.toggle("hidden", items.length === 0);
  const catalogIsEmpty = state.tools.length === 0 && !state.query && !state.selectedFile;
  elements.emptyTitle.textContent = display(catalogIsEmpty ? "Katalogga ma'lumot kiritilmagan" : "So'rov bo'yicha natija aniqlanmadi");
  elements.emptyCopy.textContent = display(catalogIsEmpty ? "Tekshiruv yo'nalishlari va OSINT vositalari boshqaruv paneli orqali kiritiladi." : "Kiritilgan ma'lumotni tekshiring yoki boshqa tekshiruv mezonini tanlang.");
  elements.reset.classList.toggle("hidden", catalogIsEmpty);

  const detected = currentDetection();
  elements.detected.classList.toggle("hidden", !detected);
  if (detected) elements.detected.textContent = display(`${state.selectedFile ? "Tanlangan fayl turi" : "Aniqlangan indikator turi"}: ${detected.label}`);
  renderRecommendations(detected);
  elements.clear.classList.toggle("hidden", !state.query && !state.selectedFile);
  smoothScrollController?.refresh();
}

function resetSearch() {
  state.query = "";
  state.activeFilter = "all";
  elements.search.value = "";
  clearSelectedFile();
  hideFileFeedback();
  const url = new URL(window.location.href);
  url.searchParams.delete("q");
  history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  setupPage();
  render();
  elements.search.focus();
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("osint-theme", next);
  elements.themeToggle.setAttribute("aria-label", display(next === "dark" ? "Oq rang rejimini yoqish" : "Tantanali moviy rang rejimini yoqish"));
  window.dispatchEvent(new CustomEvent("osint-theme-change", { detail: { theme: next } }));
}

function setContactMenuVisible(visible) {
  elements.contactMenu?.classList.toggle("hidden", !visible);
  elements.contactButton.setAttribute("aria-expanded", String(visible));
}

function setMobileMenuVisible(visible) {
  if (!elements.mobileMenuToggle || !elements.primaryNav) return;
  elements.primaryNav.classList.toggle("is-open", visible);
  elements.mobileMenuToggle.setAttribute("aria-expanded", String(visible));
  elements.mobileMenuToggle.setAttribute("aria-label", display(visible ? "Asosiy menyuni yopish" : "Asosiy menyuni ochish"));
}

function configureBotLinks() {
  const isAvailable = Boolean(state.botConfig.enabled && state.botConfig.url);
  if (elements.contactTelegram) {
    elements.contactTelegram.classList.toggle("is-disabled", !isAvailable);
    elements.contactTelegram.setAttribute("aria-disabled", String(!isAvailable));
    if (isAvailable) {
      elements.contactTelegram.href = state.botConfig.url;
      elements.contactTelegram.target = "_blank";
      elements.contactTelegram.rel = "noopener noreferrer";
      elements.contactTelegram.removeAttribute("tabindex");
    } else {
      elements.contactTelegram.removeAttribute("href");
      elements.contactTelegram.removeAttribute("target");
      elements.contactTelegram.setAttribute("tabindex", "-1");
    }
  }
  if (elements.contactTelegramMeta) elements.contactTelegramMeta.textContent = display(isAvailable ? "Telegram orqali murojaat yuborish" : "Bot sozlanmagan");
  if (elements.assistantLink) {
    elements.assistantLink.classList.toggle("is-disabled", !isAvailable);
    elements.assistantLink.setAttribute("aria-disabled", String(!isAvailable));
    if (isAvailable) {
      elements.assistantLink.href = state.botConfig.url;
      elements.assistantLink.target = "_blank";
      elements.assistantLink.rel = "noopener noreferrer";
    } else {
      elements.assistantLink.removeAttribute("href");
      elements.assistantLink.removeAttribute("target");
    }
  }
}

async function initialize() {
  i18n.initControls();
  i18n.localizeStatic(document.body);
  uiIcons.mountAll(document);
  if (currentGuideRoute()) elements.heroSection?.remove();
  else setupHeroStreams();
  elements.themeToggle.setAttribute("aria-label", display(document.documentElement.dataset.theme === "dark" ? "Oq rang rejimini yoqish" : "Tantanali moviy rang rejimini yoqish"));
  document.querySelector("#year").textContent = new Date().getFullYear();
  const urlQuery = new URLSearchParams(window.location.search).get("q") || "";
  elements.search.value = urlQuery;
  state.query = urlQuery;
  smoothScrollController = setupSmoothScroll();

  try {
    const [categoriesResponse, toolsResponse, botResponse] = await Promise.all([fetch("/api/categories"), fetch("/api/tools"), fetch("/api/bot/config")]);
    if (!categoriesResponse.ok || !toolsResponse.ok) throw new Error("Katalog ma'lumotlarini olish imkoni bo'lmadi");
    state.categories = await categoriesResponse.json();
    state.tools = await toolsResponse.json();
    if (botResponse.ok) state.botConfig = await botResponse.json();
    configureBotLinks();
    if (!currentCategorySlug() && !currentGuideRoute()) {
      renderMarquee();
      renderStories();
    }
    setupPage();
    render();
    setupScrollMotion();
    smoothScrollController?.refresh();
    if (window.location.hash) requestAnimationFrame(() => scrollToContent(document.querySelector(window.location.hash)));
  } catch (error) {
    elements.grid.innerHTML = `<div class="empty-state"><span>!</span><h3>${display("Katalog ma'lumotlari yuklanmadi")}</h3><p>${display("Tizim holatini tekshiring va sahifani qayta yuklang.")}</p></div>`;
    elements.count.textContent = display("Tizim xatosi");
  }
}

let searchRenderTimer = 0;
elements.search.addEventListener("input", (event) => {
  if (event.target.value && state.selectedFile) clearSelectedFile();
  hideFileFeedback();
  state.query = event.target.value;
  window.clearTimeout(searchRenderTimer);
  searchRenderTimer = window.setTimeout(render, 80);
});
elements.search.addEventListener("keydown", (event) => {
  if (event.key === "Escape") resetSearch();
  if (event.key === "Enter") {
    event.preventDefault();
    window.clearTimeout(searchRenderTimer);
    state.query = elements.search.value.trim();
    if (currentGuideRoute()) {
      const query = state.query ? `?q=${encodeURIComponent(state.query)}` : "";
      window.location.assign(`/${query}#catalog`);
      return;
    }
    const url = new URL(window.location.href);
    if (state.query) url.searchParams.set("q", state.query);
    else url.searchParams.delete("q");
    history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    render();
    scrollToContent(document.querySelector("#catalog"));
  }
});
elements.fileButton.addEventListener("click", () => elements.fileInput.click());
elements.fileInput.addEventListener("change", (event) => selectEvidenceFile(event.target.files?.[0]));
elements.removeSelectedFile.addEventListener("click", () => {
  clearSelectedFile({ renderView: true });
  hideFileFeedback();
  elements.search.focus();
});

let searchDragDepth = 0;
elements.searchDropZone.addEventListener("dragenter", (event) => {
  event.preventDefault();
  searchDragDepth += 1;
  elements.searchDropZone.classList.add("is-dragover");
});
elements.searchDropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
});
elements.searchDropZone.addEventListener("dragleave", (event) => {
  event.preventDefault();
  searchDragDepth = Math.max(0, searchDragDepth - 1);
  if (searchDragDepth === 0) elements.searchDropZone.classList.remove("is-dragover");
});
elements.searchDropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  searchDragDepth = 0;
  elements.searchDropZone.classList.remove("is-dragover");
  selectEvidenceFile(event.dataTransfer?.files?.[0]);
});
elements.clear.addEventListener("click", resetSearch);
elements.reset.addEventListener("click", resetSearch);
elements.themeToggle.addEventListener("click", toggleTheme);
elements.mobileMenuToggle?.addEventListener("click", (event) => {
  event.stopPropagation();
  const next = !elements.primaryNav.classList.contains("is-open");
  setContactMenuVisible(false);
  setMobileMenuVisible(next);
});
elements.primaryNav?.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setMobileMenuVisible(false)));
elements.contactButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setMobileMenuVisible(false);
  setContactMenuVisible(elements.contactMenu?.classList.contains("hidden"));
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".contact-wrap")) setContactMenuVisible(false);
  if (!event.target.closest("#primary-nav") && !event.target.closest("#mobile-menu-toggle")) setMobileMenuVisible(false);
});
document.addEventListener("click", (event) => {
  const anchor = event.target.closest("a[href*='#']");
  if (!anchor || anchor.target === "_blank") return;
  const url = new URL(anchor.href, window.location.href);
  if (url.origin !== window.location.origin || url.pathname !== window.location.pathname || !url.hash) return;
  const target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
  if (!target) return;
  event.preventDefault();
  history.pushState({}, "", `${url.pathname}${url.search}${url.hash}`);
  scrollToContent(target);
});
document.querySelectorAll("[data-close-details]").forEach((button) => button.addEventListener("click", closeDetails));
window.addEventListener("beforeunload", releaseSelectedFilePreview);
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  setContactMenuVisible(false);
  setMobileMenuVisible(false);
  if (!elements.detailsModal.classList.contains("hidden")) closeDetails();
});
window.addEventListener("resize", () => {
  if (window.innerWidth > 820) setMobileMenuVisible(false);
}, { passive: true });

initialize();
