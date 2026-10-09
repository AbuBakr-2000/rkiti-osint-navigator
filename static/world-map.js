(() => {
  const host = document.querySelector("#world-map");
  if (!host || /^\/guide\/?$/i.test(window.location.pathname)) return;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 1000;
  const HEIGHT = 520;
  const MAX_LATITUDE = 84;
  let resizeObserver = null;

  function createSvgElement(name, attributes = {}) {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }

  function project([longitude, latitude]) {
    const safeLatitude = Math.max(-MAX_LATITUDE, Math.min(MAX_LATITUDE, latitude));
    const x = ((longitude + 180) / 360) * WIDTH;
    const radians = safeLatitude * Math.PI / 180;
    const mercator = Math.log(Math.tan(Math.PI / 4 + radians / 2));
    const y = (1 - mercator / Math.PI) / 2 * HEIGHT;
    return [x, y];
  }

  function ringPath(ring) {
    if (!Array.isArray(ring) || ring.length < 2) return "";
    let path = "";
    let previousLongitude = null;
    ring.forEach((coordinate, index) => {
      const [x, y] = project(coordinate);
      const longitude = coordinate[0];
      const crossesDateLine = previousLongitude !== null && Math.abs(longitude - previousLongitude) > 180;
      path += `${index === 0 || crossesDateLine ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
      previousLongitude = longitude;
    });
    return `${path}Z`;
  }

  function geometryPath(geometry) {
    if (!geometry) return "";
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.type === "MultiPolygon" ? geometry.coordinates : [];
    return polygons.map((polygon) => polygon.map(ringPath).join("")).join("");
  }

  function drawGrid(svg) {
    const grid = createSvgElement("g", { class: "world-map-grid", "aria-hidden": "true" });
    for (let longitude = -150; longitude <= 150; longitude += 30) {
      const points = [];
      for (let latitude = -75; latitude <= 75; latitude += 3) points.push(project([longitude, latitude]));
      grid.append(createSvgElement("path", { d: points.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join("") }));
    }
    for (let latitude = -60; latitude <= 60; latitude += 30) {
      const points = [];
      for (let longitude = -180; longitude <= 180; longitude += 4) points.push(project([longitude, latitude]));
      grid.append(createSvgElement("path", { d: points.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join("") }));
    }
    svg.append(grid);
  }

  function drawSignals(svg) {
    const signals = createSvgElement("g", { class: "world-map-signals", "aria-hidden": "true" });
    const origin = project([69.2401, 41.2995]);
    const targets = [[12.4964, 41.9028], [-0.1276, 51.5072], [77.209, 28.6139]];
    targets.forEach((target, index) => {
      const point = project(target);
      const midX = (origin[0] + point[0]) / 2;
      const midY = Math.min(origin[1], point[1]) - (34 + index * 8);
      signals.append(createSvgElement("path", {
        class: "world-map-route",
        d: `M${origin[0].toFixed(2)},${origin[1].toFixed(2)} Q${midX.toFixed(2)},${midY.toFixed(2)} ${point[0].toFixed(2)},${point[1].toFixed(2)}`,
      }));
      signals.append(createSvgElement("circle", { class: "world-map-node", cx: point[0], cy: point[1], r: 3.4 }));
    });
    signals.append(createSvgElement("circle", { class: "world-map-node world-map-node-origin", cx: origin[0], cy: origin[1], r: 5 }));
    svg.append(signals);
  }

  function renderMap(collection) {
    const svg = createSvgElement("svg", {
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      preserveAspectRatio: "xMidYMid meet",
      focusable: "false",
      "aria-hidden": "true",
    });
    drawGrid(svg);
    const countries = createSvgElement("g", { class: "world-map-countries" });
    collection.features.forEach((feature) => {
      const pathData = geometryPath(feature.geometry);
      if (!pathData) return;
      const code = feature.properties?.ADM0_A3 || feature.properties?.SOV_A3 || "";
      const country = createSvgElement("path", { d: pathData, "data-country": code });
      if (code === "UZB") country.classList.add("is-origin");
      countries.append(country);
    });
    svg.append(countries);
    drawSignals(svg);
    host.replaceChildren(svg);
    host.classList.add("is-ready");
  }

  function updateDensity() {
    const width = host.getBoundingClientRect().width;
    host.dataset.density = width < 520 ? "compact" : "regular";
  }

  fetch("/static/world-110m.geojson", { cache: "force-cache" })
    .then((response) => {
      if (!response.ok) throw new Error(`Map data: ${response.status}`);
      return response.json();
    })
    .then(renderMap)
    .catch(() => {
      host.classList.add("is-unavailable");
      host.innerHTML = '<p role="status">Xarita ma\'lumotlarini yuklash imkoni bo\'lmadi.</p>';
    });

  if ("ResizeObserver" in window) {
    resizeObserver = new ResizeObserver(updateDensity);
    resizeObserver.observe(host);
  }
  updateDensity();

  window.addEventListener("pagehide", () => resizeObserver?.disconnect(), { once: true });
})();
