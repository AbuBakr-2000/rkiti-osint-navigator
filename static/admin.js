const adminState = { categories: [], tools: [], requests: [], botUsers: [], activeRequest: null, panel: "tools", emptyPromptShown: false };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const views = { login: $("#login-view"), dashboard: $("#dashboard-view") };
const modal = $("#modal");
const requestModal = $("#request-modal");
const toolForm = $("#tool-form");
const categoryForm = $("#category-form");
const requestReplyForm = $("#request-reply-form");
const i18n = window.OSINT_I18N;
const display = (value) => i18n.display(value);
const iconSystem = window.OSINT_ICONS;
const uiIcons = window.OSINT_UI_ICONS;

async function api(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || "So'rov bajarilmadi.");
  return payload;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = display(message);
  node.classList.remove("hidden");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => node.classList.add("hidden"), 2600);
}

function splitList(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

function slugify(value) {
  return i18n.toLatin(value).toLocaleLowerCase("uz").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function recordIcon() {
  return '<span class="record-icon"><img class="icon-image" alt=""><b class="icon-text">OS</b></span>';
}

function recordTemplate(item, type) {
  const tags = type === "tool" ? [...item.networks, ...item.tags] : item.tags;
  const title = type === "tool" ? item.name : display(item.name);
  const subtitle = type === "tool"
    ? `${escapeHtml(display(item.category_name))} · <span data-no-transliterate>${escapeHtml(item.url)}</span>`
    : `${escapeHtml(display(`${item.tool_count} ta OSINT vositasi`))} · <span data-no-transliterate>/category/${escapeHtml(item.slug)}</span>`;
  return `
    <article class="record" data-id="${item.id}" data-kind="${type}">
      <div class="record-heading">${recordIcon()}<div><h3 ${type === "tool" ? "data-no-transliterate" : ""}>${escapeHtml(title)}</h3><p>${subtitle}</p></div></div>
      <div class="record-tags">${tags.slice(0, 3).map((tag) => `<span>${escapeHtml(type === "tool" ? tag : display(tag))}</span>`).join("")}${item.featured ? `<span class="priority-status">${display(type === "category" ? "Birinchi qatorda" : "Ustuvor")}</span>` : ""}<span class="details-status ${item.details ? "" : "empty"}">${display(item.details ? "Tafsilot kiritilgan" : "Avtomatik tafsilot")}</span><span class="status ${item.enabled ? "" : "off"}">${display(item.enabled ? "E'lon qilingan" : "Yashirilgan")}</span></div>
      <div class="record-actions">
        <button class="icon-button" data-edit="${type}" data-id="${item.id}" title="${display("Tahrirlash")}" aria-label="${display("Tahrirlash")}">${uiIcons.svg("pencil", "", 14)}</button>
        <button class="icon-button danger" data-delete="${type}" data-id="${item.id}" title="${display("O'chirish")}" aria-label="${display("O'chirish")}">${uiIcons.svg("trash", "", 14)}</button>
      </div>
    </article>`;
}

const requestStatusLabels = {
  new: "Yangi",
  in_progress: "Ko'rib chiqilmoqda",
  answered: "Javob berilgan",
  closed: "Yopilgan",
};

function requesterName(item) {
  const name = [item.first_name, item.last_name].filter(Boolean).join(" ").trim();
  return name || (item.username ? `@${item.username}` : `Telegram ID: ${item.telegram_user_id}`);
}

function requestTemplate(item) {
  return `
    <article class="request-record">
      <div><h3 data-no-transliterate>${escapeHtml(item.request_code)}</h3><p>${escapeHtml(display(requesterName(item)))}${item.username ? ` · <span data-no-transliterate>@${escapeHtml(item.username)}</span>` : ""}</p></div>
      <div class="request-meta"><span class="request-status status-${escapeHtml(item.status)}">${escapeHtml(display(requestStatusLabels[item.status] || item.status))}</span><span>${escapeHtml(display(`${item.evidence_count} ta dalil`))}</span><span>${escapeHtml(display(`${item.reply_count} ta javob`))}</span></div>
      <button class="icon-button" type="button" data-open-request="${item.id}" title="${display("Ko'rib chiqish")}" aria-label="${display("Ko'rib chiqish")}">${uiIcons.svg("eye", "", 15)}</button>
    </article>`;
}

function botUserTemplate(item) {
  const identity = requesterName(item);
  return `
    <article class="request-record">
      <div><h3>${escapeHtml(display(identity))}</h3><p><span data-no-transliterate>Telegram ID: ${escapeHtml(item.telegram_user_id)}</span>${item.username ? ` · <span data-no-transliterate>@${escapeHtml(item.username)}</span>` : ""}</p></div>
      <div class="request-meta"><span>${escapeHtml(display(`${item.request_count} ta murojaat`))}</span><span>${escapeHtml(display(item.last_seen_at || ""))}</span></div>
      <div class="user-actions">
        <button class="user-toggle ${item.approved ? "active" : ""}" type="button" data-user-toggle="approved" data-user-id="${item.telegram_user_id}">${display(item.approved ? "Tasdiqlangan" : "Tasdiqlash")}</button>
        <button class="user-toggle ${item.blocked ? "blocked" : ""}" type="button" data-user-toggle="blocked" data-user-id="${item.telegram_user_id}">${display(item.blocked ? "Bloklangan" : "Bloklash")}</button>
      </div>
    </article>`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function render() {
  const search = i18n.toLatin($("#tool-search").value).trim().toLocaleLowerCase("uz");
  const categoryId = $("#category-filter").value;
  const tools = adminState.tools.filter((tool) => {
    const source = i18n.toLatin(`${tool.name} ${tool.description} ${tool.details} ${tool.tags.join(" ")}`).toLocaleLowerCase("uz");
    const matchesSearch = !search || source.includes(search);
    return matchesSearch && (!categoryId || String(tool.category_id) === categoryId);
  });
  $("#tool-list").innerHTML = tools.length ? tools.map((item) => recordTemplate(item, "tool")).join("") : `<div class="empty-records">${display("Mos vosita topilmadi.")}</div>`;
  $("#category-list").innerHTML = adminState.categories.length ? adminState.categories.map((item) => recordTemplate(item, "category")).join("") : `<div class="empty-records">${display("Tekshiruv yo'nalishi kiritilmagan.")}</div>`;
  const requestSearch = i18n.toLatin($("#request-search").value).trim().toLocaleLowerCase("uz");
  const requestStatus = $("#request-status-filter").value;
  const requests = adminState.requests.filter((item) => {
    const source = i18n.toLatin(`${item.request_code} ${item.first_name} ${item.last_name} ${item.username} ${item.telegram_user_id} ${item.category_name}`).toLocaleLowerCase("uz");
    return (!requestSearch || source.includes(requestSearch)) && (!requestStatus || item.status === requestStatus);
  });
  $("#request-list").innerHTML = requests.length ? requests.map(requestTemplate).join("") : `<div class="empty-records">${display("Mos murojaat topilmadi.")}</div>`;
  const userSearch = i18n.toLatin($("#bot-user-search").value).trim().toLocaleLowerCase("uz");
  const users = adminState.botUsers.filter((item) => i18n.toLatin(`${item.first_name} ${item.last_name} ${item.username} ${item.telegram_user_id}`).toLocaleLowerCase("uz").includes(userSearch));
  $("#bot-user-list").innerHTML = users.length ? users.map(botUserTemplate).join("") : `<div class="empty-records">${display("Bot foydalanuvchilari mavjud emas.")}</div>`;
  hydrateRecordIcons();
  uiIcons.mountAll(document);
}

function hydrateRecordIcons() {
  $$(".record[data-kind]").forEach((record) => {
    const collection = record.dataset.kind === "tool" ? adminState.tools : adminState.categories;
    const item = collection.find((entry) => entry.id === Number(record.dataset.id));
    if (!item) return;
    const icon = record.querySelector(".record-icon");
    const visual = iconSystem.resolve(item, record.dataset.kind);
    icon.dataset.iconTheme = visual.theme;
    iconSystem.mount(icon, icon.querySelector(".icon-image"), icon.querySelector(".icon-text"), visual);
  });
}

function populateCategorySelects() {
  const options = adminState.categories.map((category) => `<option value="${category.id}">${escapeHtml(display(category.name))}</option>`).join("");
  $("#category-filter").innerHTML = `<option value="">${display("Barcha tekshiruv yo'nalishlari")}</option>${options}`;
  toolForm.elements.category_id.innerHTML = options;
}

async function loadData() {
  [adminState.categories, adminState.tools, adminState.requests, adminState.botUsers] = await Promise.all([
    api("/api/admin/categories"),
    api("/api/admin/tools"),
    api("/api/admin/requests"),
    api("/api/admin/bot-users"),
  ]);
  $("#nav-tool-count").textContent = adminState.tools.length;
  $("#nav-category-count").textContent = adminState.categories.length;
  $("#nav-request-count").textContent = adminState.requests.filter((item) => ["new", "in_progress"].includes(item.status)).length;
  $("#nav-user-count").textContent = adminState.botUsers.length;
  populateCategorySelects();
  render();
  if (!adminState.categories.length) {
    setPanel("categories");
    if (!adminState.emptyPromptShown) {
      adminState.emptyPromptShown = true;
      toast("Avval tekshiruv yo'nalishini kiriting.");
    }
  }
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("osint-theme", next);
  $$('[data-theme-action]').forEach((button) => button.setAttribute("aria-label", display(next === "dark" ? "Oq rang rejimini yoqish" : "Tantanali moviy rang rejimini yoqish")));
}

function setView(authenticated) {
  views.login.classList.toggle("hidden", authenticated);
  views.dashboard.classList.toggle("hidden", !authenticated);
}

function setPanel(panel) {
  adminState.panel = panel;
  $("#tools-panel").classList.toggle("hidden", panel !== "tools");
  $("#categories-panel").classList.toggle("hidden", panel !== "categories");
  $("#requests-panel").classList.toggle("hidden", panel !== "requests");
  $("#bot-users-panel").classList.toggle("hidden", panel !== "bot-users");
  $$(".nav-button").forEach((button) => button.classList.toggle("active", button.dataset.panel === panel));
  const copy = {
    tools: ["OSINT vositalari", "Yangi OSINT vositasini kiriting yoki mavjud yozuvni tahrirlang."],
    categories: ["Tekshiruv yo'nalishlari", "Katalogdagi tekshiruv yo'nalishlarini boshqaring."],
    requests: ["Tergovchi murojaatlari", "Bot orqali yuborilgan dalillarni ko'rib chiqing va javobni bevosita Telegram orqali yuboring."],
    "bot-users": ["Bot foydalanuvchilari", "Botdan foydalanuvchilarni tasdiqlang yoki zarur hollarda bloklang."],
  }[panel];
  $("#dashboard-title").textContent = display(copy[0]);
  $("#dashboard-description").textContent = display(copy[1]);
  $(".dashboard-header-actions").classList.toggle("hidden", !["tools", "categories"].includes(panel));
  $("#new-item-button").innerHTML = `${uiIcons.svg("plus", "", 15)} ${display(panel === "tools" ? "Yangi OSINT vositasi" : "Yangi tekshiruv yo'nalishi")}`;
}

function openModal(type, item = null) {
  modal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
  const isTool = type === "tool";
  toolForm.classList.toggle("hidden", !isTool);
  categoryForm.classList.toggle("hidden", isTool);
  $("#form-error").classList.add("hidden");
  $("#modal-title").textContent = item
    ? `${isTool ? item.name : display(item.name)} ${display("yozuvini tahrirlash")}`
    : display(isTool ? "Yangi OSINT vositasi" : "Yangi tekshiruv yo'nalishi");
  const form = isTool ? toolForm : categoryForm;
  form.reset();
  form.elements.id.value = item?.id || "";
  form.elements.enabled.checked = item ? item.enabled : true;

  if (item) {
    Object.entries(item).forEach(([key, value]) => {
      const field = form.elements[key];
      if (!field) return;
      if (field.type === "checkbox") field.checked = Boolean(value);
      else field.value = Array.isArray(value) ? value.join(", ") : value ?? "";
    });
  }
  updateFormIconPreview(form, type);
  requestAnimationFrame(() => form.elements.name?.focus());
}

function updateFormIconPreview(form, type) {
  const item = Object.fromEntries(new FormData(form).entries());
  if (type === "tool") {
    const category = adminState.categories.find((entry) => String(entry.id) === String(item.category_id));
    item.category_slug = category?.slug || "";
  }
  const preview = $(type === "tool" ? "#tool-icon-preview" : "#category-icon-preview");
  const visual = iconSystem.resolve(item, type);
  preview.dataset.iconTheme = visual.theme;
  iconSystem.mount(preview, preview.querySelector(".icon-image"), preview.querySelector(".icon-text"), visual);
}

function closeModal() {
  modal.classList.add("hidden");
  document.body.style.overflow = "";
}

function evidenceLabel(kind) {
  return ({ image: "Rasm", video: "Video", audio: "Audio", voice: "Ovozli xabar", document: "Fayl", apk: "APK/AAB", url: "URL", domain: "Domen", ip: "IP manzil", wallet: "Kriptoaktiv hamyon", "tx-hash": "Tranzaksiya hashi", "file-hash": "Fayl hashi", "telegram-id": "Telegram ID", "telegram-username": "Telegram username", email: "Email", phone: "Telefon raqami", username: "Username", text: "Matn" }[kind] || kind);
}

function renderRequestDetail(item) {
  const evidence = item.evidence.map((entry) => {
    const value = entry.value || entry.file_name || entry.caption || "Fayl";
    const download = entry.telegram_file_id ? `<a class="evidence-download" href="/api/admin/evidence/${entry.id}/download">${display("Yuklab olish")}</a>` : "";
    return `<article class="evidence-item"><div class="evidence-item-head"><b>${escapeHtml(display(evidenceLabel(entry.kind)))}</b>${download}</div><p data-no-transliterate>${escapeHtml(value)}</p>${entry.caption && entry.caption !== value ? `<p>${escapeHtml(display(entry.caption))}</p>` : ""}</article>`;
  }).join("") || `<div class="empty-records">${display("Dalil mavjud emas.")}</div>`;
  const replies = item.replies.map((reply) => `<article class="reply-item"><div class="reply-item-head"><b>${escapeHtml(display(reply.kind === "text" ? "Matnli javob" : reply.file_name || "Fayl"))}</b><span class="request-status status-${reply.delivery_status === "sent" ? "answered" : "new"}">${escapeHtml(display(reply.delivery_status === "sent" ? "Yuborilgan" : reply.delivery_status === "failed" ? "Yuborilmadi" : "Navbatda"))}</span></div>${reply.body ? `<p>${escapeHtml(display(reply.body))}</p>` : ""}${reply.error ? `<p>${escapeHtml(display(reply.error))}</p>` : ""}${reply.delivery_status === "failed" ? `<button class="icon-button" type="button" data-retry-reply="${reply.id}">${display("Qayta yuborish")}</button>` : ""}</article>`).join("") || `<div class="empty-records">${display("Hozircha javob yuborilmagan.")}</div>`;
  $("#request-modal-title").textContent = item.request_code;
  $("#request-detail").innerHTML = `
    <div class="request-overview">
      <div class="request-stat"><b>${display("Foydalanuvchi")}</b><span>${escapeHtml(display(requesterName(item)))}</span></div>
      <div class="request-stat"><b>Telegram ID</b><span data-no-transliterate>${escapeHtml(item.telegram_user_id)}</span></div>
      <div class="request-stat"><b>${display("Yo'nalish")}</b><span>${escapeHtml(display(item.category_name || "Boshqa turdagi dalil"))}</span></div>
      <div class="request-stat"><b>${display("Qabul qilingan vaqt")}</b><span data-no-transliterate>${escapeHtml(item.submitted_at || item.created_at)}</span></div>
    </div>
    <div class="request-detail-grid">
      <section class="request-box"><h3>${display(`Dalillar · ${item.evidence.length}`)}</h3><div class="evidence-list">${evidence}</div></section>
      <section class="request-box"><h3>${display(`Yuborilgan javoblar · ${item.replies.length}`)}</h3><div class="reply-list">${replies}</div></section>
    </div>
    <section class="request-box">
      <label>${display("Murojaat holati")}<select id="request-detail-status"><option value="new">${display("Yangi")}</option><option value="in_progress">${display("Ko'rib chiqilmoqda")}</option><option value="answered">${display("Javob berilgan")}</option><option value="closed">${display("Yopilgan")}</option></select></label>
      <label>${display("Ichki izoh")}<textarea id="request-detail-summary" rows="3" placeholder="Bu izoh faqat administrator panelida saqlanadi.">${escapeHtml(item.summary || "")}</textarea></label>
    </section>`;
  $("#request-detail-status").value = item.status;
  uiIcons.mountAll($("#request-detail"));
}

async function openRequest(requestId) {
  const item = await api(`/api/admin/requests/${requestId}`);
  adminState.activeRequest = item;
  renderRequestDetail(item);
  requestReplyForm.reset();
  $("#request-form-error").classList.add("hidden");
  requestModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeRequestModal() {
  requestModal.classList.add("hidden");
  adminState.activeRequest = null;
  if (modal.classList.contains("hidden")) document.body.style.overflow = "";
}

async function saveRequestState() {
  if (!adminState.activeRequest) return;
  await api(`/api/admin/requests/${adminState.activeRequest.id}`, {
    method: "PUT",
    body: JSON.stringify({ status: $("#request-detail-status").value, summary: $("#request-detail-summary").value }),
  });
  await loadData();
  await openRequest(adminState.activeRequest.id);
  toast("Murojaat holati va ichki izoh saqlandi.");
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({ name: file.name, type: file.type || "application/octet-stream", data: reader.result });
    reader.onerror = () => reject(new Error(`${file.name} faylini o'qib bo'lmadi.`));
    reader.readAsDataURL(file);
  });
}

async function sendRequestReply(event) {
  event.preventDefault();
  if (!adminState.activeRequest) return;
  const submit = requestReplyForm.querySelector('[type="submit"]');
  submit.disabled = true;
  $("#request-form-error").classList.add("hidden");
  try {
    const files = [...requestReplyForm.elements.files.files];
    const encodedFiles = await Promise.all(files.map(readFileAsDataUrl));
    const result = await api(`/api/admin/requests/${adminState.activeRequest.id}/reply`, {
      method: "POST",
      body: JSON.stringify({ text: requestReplyForm.elements.text.value, files: encodedFiles }),
    });
    requestReplyForm.reset();
    await loadData();
    await openRequest(adminState.activeRequest.id);
    toast(result.errors?.length
      ? `${result.created} ta javob saqlandi; ${result.delivered} tasi yuborildi. Yuborilmagan qismlarni qayta jo'nating.`
      : `${result.delivered} ta javob qismi Telegram orqali yuborildi.`);
  } catch (error) {
    $("#request-form-error").textContent = display(error.message);
    $("#request-form-error").classList.remove("hidden");
  } finally {
    submit.disabled = false;
  }
}

async function toggleBotUser(userId, field) {
  const user = adminState.botUsers.find((item) => String(item.telegram_user_id) === String(userId));
  if (!user) return;
  const payload = { approved: Boolean(user.approved), blocked: Boolean(user.blocked) };
  payload[field] = !payload[field];
  if (field === "blocked" && payload.blocked) payload.approved = false;
  if (field === "approved" && payload.approved) payload.blocked = false;
  await api(`/api/admin/bot-users/${userId}`, { method: "PUT", body: JSON.stringify(payload) });
  await loadData();
  toast("Bot foydalanuvchisi holati yangilandi.");
}

function formPayload(form, type) {
  const data = Object.fromEntries(new FormData(form).entries());
  data.enabled = form.elements.enabled.checked;
  data.tags = splitList(data.tags);
  if (type === "tool") {
    data.category_id = Number(data.category_id);
    data.input_types = splitList(data.input_types);
    data.networks = splitList(data.networks);
    data.featured = form.elements.featured.checked;
    data.login_required = form.elements.login_required.checked;
  } else {
    data.featured = form.elements.featured.checked;
  }
  return data;
}

async function saveForm(form, type) {
  const data = formPayload(form, type);
  const id = data.id;
  delete data.id;
  const endpoint = type === "tool" ? "/api/admin/tools" : "/api/admin/categories";
  try {
    const result = await api(id ? `${endpoint}/${id}` : endpoint, { method: id ? "PUT" : "POST", body: JSON.stringify(data) });
    closeModal();
    await loadData();
    toast(result.backup_written === false
      ? "Ma'lumot saqlandi, ammo JSON backup yaratilmadi."
      : id ? "Kiritilgan o'zgarishlar saqlandi." : "Yangi katalog yozuvi saqlandi.");
  } catch (error) {
    $("#form-error").textContent = display(error.message);
    $("#form-error").classList.remove("hidden");
  }
}

async function removeItem(type, id) {
  const items = type === "tool" ? adminState.tools : adminState.categories;
  const item = items.find((entry) => entry.id === Number(id));
  const extra = type === "category" ? " Mazkur yo'nalishga biriktirilgan vositalar ham o'chiriladi." : "";
  if (!window.confirm(display(`“${item?.name || "Katalog yozuvi"}” yozuvini o'chirishni tasdiqlaysizmi?${extra}`))) return;
  const endpoint = type === "tool" ? "/api/admin/tools" : "/api/admin/categories";
  const result = await api(`${endpoint}/${id}`, { method: "DELETE" });
  await loadData();
  toast(result.backup_written === false
    ? "Yozuv o'chirildi, ammo JSON backup yaratilmadi."
    : "Katalog yozuvi o'chirildi.");
}

async function exportCatalog() {
  const button = $("#export-catalog-button");
  button.disabled = true;
  try {
    const catalog = await api("/api/admin/catalog/export");
    const blob = new Blob([`${JSON.stringify(catalog, null, 2)}\n`], { type: "application/json;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `osint-catalog-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
    toast("Katalog JSON faylga eksport qilindi.");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
}

async function importCatalog(file) {
  if (!file) return;
  if (file.size > 1_000_000) throw new Error("JSON fayl hajmi 1 MB dan oshmasin.");

  let catalog;
  try {
    catalog = JSON.parse(await file.text());
  } catch {
    throw new Error("Tanlangan fayl to'g'ri JSON formatida emas.");
  }
  if (catalog?.format !== "osint-navigator-catalog" || catalog?.version !== 1) {
    throw new Error("Tanlangan fayl OSINT Navigator katalogining 1-versiya eksporti emas.");
  }

  const categories = Array.isArray(catalog.categories) ? catalog.categories.length : 0;
  const tools = Array.isArray(catalog.tools) ? catalog.tools.length : 0;
  const confirmed = window.confirm(display(
    `Import joriy katalogni to'liq almashtiradi. Faylda ${categories} ta kategoriya va ${tools} ta vosita mavjud. Davom etasizmi?`
  ));
  if (!confirmed) return;

  const button = $("#import-catalog-button");
  button.disabled = true;
  try {
    const result = await api("/api/admin/catalog/import", {
      method: "POST",
      body: JSON.stringify({ ...catalog, confirm_replace: true }),
    });
    await loadData();
    toast(result.backup_written === false
      ? "Katalog import qilindi, ammo JSON backup yaratilmadi."
      : `${result.categories} ta kategoriya va ${result.tools} ta vosita import qilindi.`);
  } finally {
    button.disabled = false;
  }
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget).entries());
  try {
    await api("/api/admin/login", { method: "POST", body: JSON.stringify(data) });
    $("#login-error").classList.add("hidden");
    setView(true);
    await loadData();
  } catch (error) {
    $("#login-error").textContent = display(error.message);
    $("#login-error").classList.remove("hidden");
  }
});

$("#logout-button").addEventListener("click", async () => {
  await api("/api/admin/logout", { method: "POST", body: "{}" });
  setView(false);
});

$("#export-catalog-button").addEventListener("click", exportCatalog);
$("#import-catalog-button").addEventListener("click", () => $("#import-catalog-input").click());
$("#import-catalog-input").addEventListener("change", async (event) => {
  const input = event.currentTarget;
  try {
    await importCatalog(input.files?.[0]);
  } catch (error) {
    toast(error.message);
  } finally {
    input.value = "";
  }
});

$$(".nav-button").forEach((button) => button.addEventListener("click", () => setPanel(button.dataset.panel)));
$("#new-item-button").addEventListener("click", () => {
  if (!["tools", "categories"].includes(adminState.panel)) return;
  if (adminState.panel === "tools" && !adminState.categories.length) {
    setPanel("categories");
    openModal("category");
    return;
  }
  openModal(adminState.panel === "tools" ? "tool" : "category");
});
$$('[data-close-modal]').forEach((button) => button.addEventListener("click", closeModal));
$$('[data-close-request-modal]').forEach((button) => button.addEventListener("click", closeRequestModal));
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (!requestModal.classList.contains("hidden")) closeRequestModal();
  else if (!modal.classList.contains("hidden")) closeModal();
});
$("#tool-search").addEventListener("input", render);
$("#category-filter").addEventListener("change", render);
$("#request-search").addEventListener("input", render);
$("#request-status-filter").addEventListener("change", render);
$("#bot-user-search").addEventListener("input", render);
$("#save-request-button").addEventListener("click", () => saveRequestState().catch((error) => toast(error.message)));
requestReplyForm.addEventListener("submit", sendRequestReply);
$$('[data-theme-action]').forEach((button) => button.addEventListener("click", toggleTheme));

document.addEventListener("click", (event) => {
  const request = event.target.closest("[data-open-request]");
  if (request) openRequest(request.dataset.openRequest).catch((error) => toast(error.message));
  const userToggle = event.target.closest("[data-user-toggle]");
  if (userToggle) toggleBotUser(userToggle.dataset.userId, userToggle.dataset.userToggle).catch((error) => toast(error.message));
  const retry = event.target.closest("[data-retry-reply]");
  if (retry) {
    const activeId = adminState.activeRequest?.id;
    api(`/api/admin/replies/${retry.dataset.retryReply}/deliver`, { method: "POST", body: "{}" })
      .then(loadData).then(() => activeId && openRequest(activeId)).then(() => toast("Javob qayta yuborildi."))
      .catch((error) => toast(error.message));
  }
  const edit = event.target.closest("[data-edit]");
  if (edit) {
    const items = edit.dataset.edit === "tool" ? adminState.tools : adminState.categories;
    openModal(edit.dataset.edit, items.find((item) => item.id === Number(edit.dataset.id)));
  }
  const remove = event.target.closest("[data-delete]");
  if (remove) removeItem(remove.dataset.delete, remove.dataset.id).catch((error) => toast(error.message));
});

toolForm.elements.name.addEventListener("input", () => {
  if (!toolForm.elements.id.value) toolForm.elements.slug.value = slugify(toolForm.elements.name.value);
  updateFormIconPreview(toolForm, "tool");
});
categoryForm.elements.name.addEventListener("input", () => {
  if (!categoryForm.elements.id.value) categoryForm.elements.slug.value = slugify(categoryForm.elements.name.value);
  updateFormIconPreview(categoryForm, "category");
});
toolForm.elements.icon.addEventListener("input", () => updateFormIconPreview(toolForm, "tool"));
toolForm.elements.url.addEventListener("input", () => updateFormIconPreview(toolForm, "tool"));
toolForm.elements.slug.addEventListener("input", () => updateFormIconPreview(toolForm, "tool"));
toolForm.elements.category_id.addEventListener("change", () => updateFormIconPreview(toolForm, "tool"));
categoryForm.elements.icon.addEventListener("input", () => updateFormIconPreview(categoryForm, "category"));
categoryForm.elements.slug.addEventListener("input", () => updateFormIconPreview(categoryForm, "category"));
toolForm.addEventListener("submit", (event) => { event.preventDefault(); saveForm(toolForm, "tool"); });
categoryForm.addEventListener("submit", (event) => { event.preventDefault(); saveForm(categoryForm, "category"); });

(async function initializeAdmin() {
  i18n.initControls();
  i18n.localizeStatic(document.body);
  uiIcons.mountAll(document);
  try {
    const session = await api("/api/admin/session");
    setView(session.authenticated);
    if (session.authenticated) await loadData();
  } catch {
    setView(false);
  }
})();
