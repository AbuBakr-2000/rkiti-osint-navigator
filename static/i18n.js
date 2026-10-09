(function () {
  const STORAGE_KEY = "osint-language";
  const language = localStorage.getItem(STORAGE_KEY) === "latin" ? "latin" : "cyrillic";
  const protectedPattern = /(https?:\/\/[^\s]+|[\w.+-]+@[\w.-]+\.\w+|\b(?:username|email|hash|login|slug|metadata|favicon|hosting|redirect)[A-Za-z'’ʻʼ-]*\b|\b(?:MobSF\s+Live|MobSF|Koodous|VirusTotal\s+URL|VirusTotal\s+Files|Kropiva\s+UA\s+Bot|TGShield|Fun\s+Xeyes\s+Bot|Instant\s+Username\s+Search|Google\s+Search|Yandex\s+Search|Microsoft\s+Bing|Wayback\s+Machine|ICANN\s+Lookup|Fingerprint\.to|IDCrawl|RDAP\.org|DNSDumpster|urlscan\.io|Google|Yandex|Bing|2GIS|Reverse\s+image\s+search|Smart\s+contract|smart-kontrakt|Multi-chain|Quick\s+check|Social\s+media|Open\s+source|Threat\s+intel|Threat\s+intelligence|threat-intelligence|File\s+hash|user\s+ID|ID|e-mail|tx-hash|file-hash|wallet|blockchain|transaction|Telegram|Android|Phishing|APK|AAB|Bitcoin|Ethereum|Etherscan|TRON|Monero|OSINT|COBE|WebGL|BTC|ETH|EVM|TRC20|XMR|IP|IPv4|IPv6|URL|DNS|EXIF|API|CLI|WHOIS|RDAP|ASN|CIDR|rDNS|VPN|TOR|CVE|CVSS|EPSS|BCH|LTC|TLS|ELA|SHA256|PDF|CSV|JSON|HTTP|HTTPS|OAuth|SSO|MFA|TX|TG|admin|auto|text|Explorer|Graph|Free|Public|Direct|Analytics|Channel|Catalog|Search|Messages|Accounts|Fast|Report|Availability|Domains|Analysis|Internet|Reputation|Screenshot|Requests|Ports|Devices|Hosts|Certificates|History|Subdomains|Mapping|Records|Registration|Ownership|Abuse|Context|Scanner|Breach|Exposure|Discovery|Verification|Identity|Pivot|Risk|Images|Visual|Forensics|Documents|Frames|Files|Malware|Balance|Cluster|Privacy|Attribution|Tracing|Token|Phone|Wallet|Web|Social|Nickname)\b)/gi;
  const additionalProtectedPattern = /(Telegram\s+(?:Desktop|bot)|Kropiva\s+UA\s+Bot|Fun\s+Xeyes\s+Bot|Google\s+Lens|Yandex\s+Images|TGStat|OXT\.me|EXIF\.tools|FotoForensics|crt\.sh|Arkham\s+Intelligence|MetaSleuth|TRONSCAN|Bitcoin\s+Who's\s+Who|Lyzem|Blockscan|Blockchair|External\s+(?:redirect|service)|Manual\s+verification|Reverse\s+search|Static\s+analysis|Dynamic\s+analysis|APK\s+repository|Malware\s+research|Indexed\s+data|Network\s+requests|Certificate\s+Transparency|Structured\s+data|People\s+search|Natural\s+Earth|Wikimedia\s+Commons|\.UZ\b|\b(?:Bot|iOS|Map|Places|Organizations|Registry|Archive|Repository|Research|Uzbekistan|UTC|GPLv3|SHA-256)\b)/gi;

  function preserveTechnical(text, transform) {
    const saved = [];
    const saveToken = (token) => {
      saved.push(token);
      return `\uE000${saved.length - 1}\uE001`;
    };
    const protectedText = String(text ?? "")
      .replace(additionalProtectedPattern, saveToken)
      .replace(protectedPattern, saveToken);
    return transform(protectedText).replace(/\uE000(\d+)\uE001/g, (_, index) => saved[Number(index)]);
  }

  function latinToCyrillic(value) {
    return preserveTechnical(value, (input) => {
      const digraphs = [
        [/o[‘'’`]z/gi, "ўз"],
        [/o[‘'’`]/gi, "ў"],
        [/g[‘'’`]/gi, "ғ"],
        [/ksiya/gi, "кция"],
        [/tsiya/gi, "ция"],
        [/ts/gi, "ц"],
        [/sh/gi, "ш"],
        [/ch/gi, "ч"],
        [/yo/gi, "ё"],
        [/yu/gi, "ю"],
        [/ya/gi, "я"],
        [/ye/gi, "е"],
        [/ng/gi, "нг"],
      ];
      let text = input;
      for (const [pattern, replacement] of digraphs) {
        text = text.replace(pattern, (match) => {
          if (match === match.toUpperCase()) return replacement.toUpperCase();
          if (match[0] === match[0].toUpperCase()) return replacement[0].toUpperCase() + replacement.slice(1);
          return replacement;
        });
      }
      const map = {
        a: "а", b: "б", d: "д", e: "е", f: "ф", g: "г", h: "ҳ", i: "и", j: "ж",
        k: "к", l: "л", m: "м", n: "н", o: "о", p: "п", q: "қ", r: "р", s: "с",
        t: "т", u: "у", v: "в", x: "х", y: "й", z: "з", c: "с", w: "в",
      };
      return [...text].map((char) => {
        const lower = char.toLowerCase();
        if (!map[lower]) return /[‘'’`]/.test(char) ? "ъ" : char;
        return char === char.toUpperCase() ? map[lower].toUpperCase() : map[lower];
      }).join("");
    });
  }

  function cyrillicToLatin(value) {
    return preserveTechnical(value, (input) => {
      const map = {
        а: "a", б: "b", в: "v", г: "g", ғ: "g‘", д: "d", е: "e", ё: "yo", ж: "j",
        з: "z", и: "i", й: "y", к: "k", қ: "q", л: "l", м: "m", н: "n", о: "o",
        п: "p", р: "r", с: "s", т: "t", у: "u", ў: "o‘", ф: "f", х: "x", ҳ: "h",
        ц: "s", ч: "ch", ш: "sh", щ: "sh", ъ: "", ы: "i", ь: "", э: "e", ю: "yu", я: "ya",
      };
      return [...String(input)].map((char) => {
        const lower = char.toLowerCase();
        if (map[lower] === undefined) return char;
        const result = map[lower];
        return char === char.toUpperCase() && result ? result[0].toUpperCase() + result.slice(1) : result;
      }).join("");
    });
  }

  function display(value) {
    return language === "cyrillic" ? latinToCyrillic(value) : cyrillicToLatin(value);
  }

  function localizeStatic(root) {
    document.documentElement.lang = language === "cyrillic" ? "uz-Cyrl" : "uz-Latn";
    if (language !== "cyrillic") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const parent = node.parentElement;
      if (!parent || parent.closest("script, style, code, [data-no-transliterate]")) return;
      if (/[A-Za-z]/.test(node.nodeValue || "")) node.nodeValue = latinToCyrillic(node.nodeValue);
    });
    root.querySelectorAll("[placeholder], [title], [aria-label]").forEach((element) => {
      if (element.closest("[data-no-transliterate]")) return;
      for (const attribute of ["placeholder", "title", "aria-label"]) {
        if (element.hasAttribute(attribute)) element.setAttribute(attribute, latinToCyrillic(element.getAttribute(attribute)));
      }
    });
    document.title = latinToCyrillic(document.title);
  }

  function initControls() {
    const savedScroll = Number(sessionStorage.getItem("osint-language-scroll") || "");
    if (Number.isFinite(savedScroll) && savedScroll > 0) {
      sessionStorage.removeItem("osint-language-scroll");
      window.addEventListener("load", () => requestAnimationFrame(() => window.scrollTo({ top: savedScroll, behavior: "auto" })), { once: true });
    }
    document.querySelectorAll("#language-toggle, [data-language-toggle]").forEach((button) => {
      button.dataset.noTransliterate = "true";
      button.innerHTML = `<span class="language-option ${language === "latin" ? "active" : ""}">UZ</span><span class="language-separator">/</span><span class="language-option ${language === "cyrillic" ? "active" : ""}">ЎЗ</span>`;
      button.setAttribute("aria-label", language === "cyrillic" ? "UZ yozuviga o'tish" : "ЎЗ ёзувига ўтиш");
      button.addEventListener("click", () => {
        sessionStorage.setItem("osint-language-scroll", String(window.scrollY));
        localStorage.setItem(STORAGE_KEY, language === "cyrillic" ? "latin" : "cyrillic");
        window.location.reload();
      });
    });
  }

  window.OSINT_I18N = {
    language,
    display,
    toCyrillic: latinToCyrillic,
    toLatin: cyrillicToLatin,
    localizeStatic,
    initControls,
  };
})();
