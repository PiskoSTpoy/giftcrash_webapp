/* ============================================================
   База знаний «Аркона» — навигация, роутинг, рендер Markdown, поиск.
   Чистый ванильный JS, без зависимостей. Контент живёт в /content/*.md
   ============================================================ */

// ---- Структура: 4 верхних блока → разделы (12 тем) ----
const NAV = [
    {
        title: "Люди",
        items: [
            { id: "people/01-o-kompanii",   num: "1", title: "О компании" },
            { id: "people/05-dolzhnostnye", num: "2", title: "Должностные инструкции" },
            { id: "people/02-hr-i-naem",    num: "3", title: "HR и найм" },
            { id: "people/03-kpi",          num: "4", title: "KPI компании" },
            { id: "people/04-obuchenie",    num: "5", title: "База обучения" },
        ]
    },
    {
        title: "Процессы",
        items: [
            { id: "processes/01-prodazhi",          num: "6", title: "Продажи" },
            { id: "processes/02-dispetcherizaciya",  num: "7", title: "Диспетчеризация техники" },
            { id: "processes/03-buhgalteriya",       num: "8", title: "Бухгалтерия" },
        ]
    },
    {
        title: "Клиенты и техника",
        items: [
            { id: "assets/01-avtopark",      num: "9",  title: "Автопарк" },
            { id: "assets/02-klienty",       num: "10", title: "Клиенты" },
            { id: "assets/03-postavshchiki", num: "11", title: "Поставщики техники" },
        ]
    },
    {
        title: "Управление",
        items: [
            { id: "management/01-finansy",            num: "12", title: "Финансы" },
            { id: "management/02-shablony",           num: "13", title: "Стандартные шаблоны" },
            { id: "management/03-otchety-strategiya", num: "14", title: "Отчёты, планирование, стратегия" },
        ]
    },
];

const HOME = { id: "00-home", title: "Главная" };

// Плоский индекс id → {title, block}
const PAGE_INDEX = {};
PAGE_INDEX[HOME.id] = { title: HOME.title, block: "" };
NAV.forEach(b => b.items.forEach(it => PAGE_INDEX[it.id] = { title: it.title, block: b.title }));

// ---------------------------------------------------------------
// Минималистичный Markdown → HTML рендер (заголовки, списки,
// таблицы, цитаты, код, жирный/курсив, ссылки, hr).
// ---------------------------------------------------------------
function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(text) {
    // экранируем, затем восстанавливаем разметку
    let t = escapeHtml(text);
    t = t.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);
    t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, txt, href) => `<a href="${href}">${txt}</a>`);
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
    return t;
}

function renderMarkdown(md) {
    const lines = md.replace(/\r\n/g, "\n").split("\n");
    let html = "";
    let i = 0;

    const flushList = (buf, ordered) => {
        if (!buf.length) return "";
        const tag = ordered ? "ol" : "ul";
        return `<${tag}>` + buf.map(li => `<li>${inline(li)}</li>`).join("") + `</${tag}>`;
    };

    while (i < lines.length) {
        let line = lines[i];

        // Пустая строка
        if (/^\s*$/.test(line)) { i++; continue; }

        // Кодовый блок ```
        if (/^```/.test(line)) {
            let code = [];
            i++;
            while (i < lines.length && !/^```/.test(lines[i])) { code.push(lines[i]); i++; }
            i++; // закрывающие ```
            html += `<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`;
            continue;
        }

        // Горизонтальная линия
        if (/^---+\s*$/.test(line)) { html += "<hr>"; i++; continue; }

        // Заголовки
        const h = line.match(/^(#{1,4})\s+(.*)$/);
        if (h) { const lvl = h[1].length; html += `<h${lvl}>${inline(h[2])}</h${lvl}>`; i++; continue; }

        // Цитата
        if (/^>\s?/.test(line)) {
            let quote = [];
            while (i < lines.length && /^>\s?/.test(lines[i])) { quote.push(lines[i].replace(/^>\s?/, "")); i++; }
            html += `<blockquote>${inline(quote.join(" "))}</blockquote>`;
            continue;
        }

        // Таблица (| ... | ... |)
        if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i + 1])) {
            const parseRow = r => r.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
            const headers = parseRow(line);
            i += 2; // пропускаем строку-разделитель
            let body = "";
            while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
                const cells = parseRow(lines[i]);
                body += "<tr>" + cells.map(c => `<td>${inline(c)}</td>`).join("") + "</tr>";
                i++;
            }
            html += "<table><thead><tr>" + headers.map(c => `<th>${inline(c)}</th>`).join("") +
                    "</tr></thead><tbody>" + body + "</tbody></table>";
            continue;
        }

        // Маркированный список
        if (/^\s*[-*]\s+/.test(line)) {
            let buf = [];
            while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) { buf.push(lines[i].replace(/^\s*[-*]\s+/, "")); i++; }
            html += flushList(buf, false);
            continue;
        }

        // Нумерованный список
        if (/^\s*\d+\.\s+/.test(line)) {
            let buf = [];
            while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) { buf.push(lines[i].replace(/^\s*\d+\.\s+/, "")); i++; }
            html += flushList(buf, true);
            continue;
        }

        // Параграф (склеиваем подряд идущие строки)
        let para = [line];
        i++;
        while (i < lines.length && !/^\s*$/.test(lines[i]) &&
               !/^(#{1,4}\s|>|\s*[-*]\s|\s*\d+\.\s|```|---+\s*$|\s*\|)/.test(lines[i])) {
            para.push(lines[i]); i++;
        }
        html += `<p>${inline(para.join(" "))}</p>`;
    }
    return html;
}

// ---------------------------------------------------------------
// Навигация
// ---------------------------------------------------------------
function buildSidebar() {
    const nav = document.getElementById("sidebar");
    let html = `<a class="nav-item" href="#${HOME.id}" data-id="${HOME.id}">🏠 Главная</a>`;
    NAV.forEach(block => {
        html += `<div class="nav-block"><div class="nav-block-title">${block.title}</div>`;
        block.items.forEach(it => {
            html += `<a class="nav-item" href="#${it.id}" data-id="${it.id}">` +
                    `<span class="nav-num">${it.num}.</span>${it.title}</a>`;
        });
        html += `</div>`;
    });
    nav.innerHTML = html;
}

function setActiveNav(id) {
    document.querySelectorAll(".nav-item").forEach(a => {
        a.classList.toggle("active", a.dataset.id === id);
    });
}

// ---------------------------------------------------------------
// Роутинг + загрузка контента
// ---------------------------------------------------------------
const docCache = {};

async function loadPage(id) {
    if (!PAGE_INDEX[id]) id = HOME.id;
    const doc = document.getElementById("doc");
    const footer = document.getElementById("doc-footer");
    setActiveNav(id);

    try {
        let md = docCache[id];
        if (md === undefined) {
            // Автономный режим: контент встроен в страницу (один HTML-файл).
            if (window.KB_CONTENT && window.KB_CONTENT[id] != null) {
                md = window.KB_CONTENT[id];
            } else {
                const res = await fetch(`content/${id}.md`);
                if (!res.ok) throw new Error(res.status);
                md = await res.text();
            }
            docCache[id] = md;
        }
        doc.innerHTML = renderMarkdown(md);
        const meta = PAGE_INDEX[id];
        footer.innerHTML = meta.block
            ? `Раздел: <strong>${meta.block}</strong> · Файл: <code>content/${id}.md</code>`
            : `Файл: <code>content/${id}.md</code>`;
        document.getElementById("content").scrollTop = 0;
        window.scrollTo(0, 0);
    } catch (e) {
        doc.innerHTML = `<h1>Не удалось загрузить страницу</h1>
            <p>Файл <code>content/${id}.md</code> не найден или сайт открыт без локального сервера.</p>
            <blockquote>Для просмотра запустите простой сервер в папке <code>knowledge-base/</code>:<br>
            <code>python3 -m http.server 8000</code> и откройте <code>http://localhost:8000</code>.</blockquote>`;
        footer.innerHTML = "";
    }
    closeSidebar();
}

function router() {
    const id = location.hash.replace(/^#/, "") || HOME.id;
    loadPage(id);
}

// ---------------------------------------------------------------
// Поиск (полнотекстовый по загруженным .md, ленивая индексация)
// ---------------------------------------------------------------
let searchIndex = null;

async function buildSearchIndex() {
    if (searchIndex) return searchIndex;
    searchIndex = [];
    const ids = Object.keys(PAGE_INDEX);
    await Promise.all(ids.map(async id => {
        try {
            let md = docCache[id];
            if (md === undefined) {
                if (window.KB_CONTENT && window.KB_CONTENT[id] != null) {
                    md = window.KB_CONTENT[id]; docCache[id] = md;
                } else {
                    const res = await fetch(`content/${id}.md`);
                    if (res.ok) { md = await res.text(); docCache[id] = md; }
                }
            }
            if (md) searchIndex.push({ id, title: PAGE_INDEX[id].title, block: PAGE_INDEX[id].block, text: md.toLowerCase() });
        } catch (e) { /* пропускаем */ }
    }));
    return searchIndex;
}

async function runSearch(q) {
    const box = document.getElementById("search-results");
    q = q.trim().toLowerCase();
    if (q.length < 2) { box.classList.remove("open"); box.innerHTML = ""; return; }
    const idx = await buildSearchIndex();
    const hits = [];
    idx.forEach(p => {
        const inTitle = p.title.toLowerCase().includes(q);
        const pos = p.text.indexOf(q);
        if (inTitle || pos >= 0) {
            let snippet = "";
            if (pos >= 0) {
                const start = Math.max(0, pos - 35);
                snippet = (start > 0 ? "…" : "") +
                    p.text.slice(start, pos + q.length + 45).replace(/\n/g, " ").replace(/[#*>|`-]/g, "") + "…";
            }
            hits.push({ ...p, snippet, score: (inTitle ? 100 : 0) + (pos >= 0 ? 10 : 0) });
        }
    });
    hits.sort((a, b) => b.score - a.score);
    if (!hits.length) {
        box.innerHTML = `<li class="sr-empty">Ничего не найдено по запросу «${q}»</li>`;
    } else {
        box.innerHTML = hits.slice(0, 12).map(h =>
            `<li><a href="#${h.id}"><strong>${h.title}</strong>` +
            `<span class="sr-section"> · ${h.block || "Главная"}</span>` +
            (h.snippet ? `<br><span class="sr-section">${h.snippet}</span>` : "") + `</a></li>`
        ).join("");
    }
    box.classList.add("open");
}

// ---------------------------------------------------------------
// Мобильное меню
// ---------------------------------------------------------------
function openSidebar() {
    document.getElementById("sidebar").classList.add("open");
    document.getElementById("backdrop")?.classList.add("open");
}
function closeSidebar() {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("backdrop")?.classList.remove("open");
}

// ---------------------------------------------------------------
// Инициализация
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    buildSidebar();

    // backdrop для мобильного меню
    const backdrop = document.createElement("div");
    backdrop.id = "backdrop";
    document.body.appendChild(backdrop);
    backdrop.addEventListener("click", closeSidebar);
    document.getElementById("menu-toggle").addEventListener("click", openSidebar);

    // поиск
    const search = document.getElementById("search");
    let t;
    search.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => runSearch(search.value), 180); });
    document.addEventListener("click", e => {
        if (!e.target.closest(".search-box")) document.getElementById("search-results").classList.remove("open");
    });
    document.getElementById("search-results").addEventListener("click", () => {
        document.getElementById("search-results").classList.remove("open");
        search.value = "";
    });

    window.addEventListener("hashchange", router);
    router();
});
