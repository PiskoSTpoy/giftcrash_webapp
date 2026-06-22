#!/usr/bin/env python3
"""Собирает единый АВТОНОМНЫЙ статический HTML-файл базы знаний.

Весь Markdown-контент заранее отрисовывается в HTML на этапе сборки,
поэтому готовый файл НЕ требует JavaScript, сервера или интернета —
он открывается двойным кликом в любом браузере и в превью на телефоне.
Навигация — оглавление со ссылками-якорями; поиск — встроенный в браузер
(Ctrl/Cmd+F).

Запуск:  python3 build-standalone.py
Результат: arkona-baza-znaniy.html
"""
import html as html_mod
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "arkona-baza-znaniy.html")

# Порядок и группировка разделов (4 блока × 12 разделов + главная).
NAV = [
    ("", [("00-home", "Главная")]),
    ("Люди", [
        ("people/01-o-kompanii", "1. О компании"),
        ("people/05-dolzhnostnye", "★ Должностные инструкции"),
        ("people/02-hr-i-naem", "9. HR и найм"),
        ("people/03-kpi", "10. KPI компании"),
        ("people/04-obuchenie", "11. База обучения"),
    ]),
    ("Процессы", [
        ("processes/01-prodazhi", "2. Продажи"),
        ("processes/02-dispetcherizaciya", "3. Диспетчеризация техники"),
        ("processes/03-buhgalteriya", "8. Бухгалтерия"),
    ]),
    ("Клиенты и техника", [
        ("assets/01-avtopark", "4. Автопарк"),
        ("assets/02-klienty", "5. Клиенты"),
        ("assets/03-postavshchiki", "6. Поставщики техники"),
    ]),
    ("Управление", [
        ("management/01-finansy", "7. Финансы"),
        ("management/02-shablony", "12. Стандартные шаблоны"),
        ("management/03-otchety-strategiya", "Отчёты, планирование, стратегия"),
    ]),
]


def anchor(page_id):
    return "sec-" + page_id.replace("/", "-")


def esc(s):
    return html_mod.escape(s, quote=False)


def inline(text):
    """Инлайн-разметка: код, ссылки, жирный, курсив."""
    t = esc(text)
    t = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", t)

    def link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith("#"):
            href = "#" + anchor(href[1:])
        return f'<a href="{href}">{label}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(^|[^*])\*([^*]+)\*", r"\1<em>\2</em>", t)
    return t


def render_markdown(md):
    lines = md.replace("\r\n", "\n").split("\n")
    html = []
    i, n = 0, len(lines)

    def is_block_start(s):
        return bool(re.match(r"(#{1,4}\s|>|\s*[-*]\s|\s*\d+\.\s|```|---+\s*$|\s*\|)", s))

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # Код-блок
        if line.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            html.append(f"<pre><code>{esc(chr(10).join(buf))}</code></pre>")
            continue

        # Горизонтальная линия
        if re.match(r"^---+\s*$", line):
            html.append("<hr>"); i += 1; continue

        # Заголовки
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            html.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); i += 1; continue

        # Цитата
        if re.match(r"^>\s?", line):
            buf = []
            while i < n and re.match(r"^>\s?", lines[i]):
                buf.append(re.sub(r"^>\s?", "", lines[i])); i += 1
            html.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue

        # Таблица
        if re.match(r"^\s*\|.*\|\s*$", line) and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            def cells(r):
                return [c.strip() for c in r.strip().strip("|").split("|")]
            headers = cells(line)
            i += 2
            body = []
            while i < n and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                body.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(lines[i])) + "</tr>")
                i += 1
            html.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in headers) +
                        "</tr></thead><tbody>" + "".join(body) + "</tbody></table>")
            continue

        # Маркированный список
        if re.match(r"^\s*[-*]\s+", line):
            buf = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(re.sub(r"^\s*[-*]\s+", "", lines[i])); i += 1
            html.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
            continue

        # Нумерованный список
        if re.match(r"^\s*\d+\.\s+", line):
            buf = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                buf.append(re.sub(r"^\s*\d+\.\s+", "", lines[i])); i += 1
            html.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ol>")
            continue

        # Параграф
        buf = [line]; i += 1
        while i < n and lines[i].strip() and not is_block_start(lines[i]):
            buf.append(lines[i]); i += 1
        html.append(f"<p>{inline(' '.join(buf))}</p>")

    return "".join(html)


def read(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as f:
        return f.read()


CSS = """
:root{--brand:#1f4e79;--brand-light:#2f6aa6;--accent:#f0a500;--bg:#f4f6f9;--panel:#fff;--text:#1f2733;--muted:#6b7785;--border:#e2e7ee}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:var(--text);background:var(--bg);line-height:1.6}
header.top{position:sticky;top:0;z-index:5;background:var(--brand);color:#fff;padding:12px 18px;box-shadow:0 2px 8px rgba(0,0,0,.12)}
header.top .logo{font-weight:800;letter-spacing:2px;font-size:18px}
header.top .sub{font-size:12px;opacity:.85}
.wrap{max-width:900px;margin:0 auto;padding:18px clamp(14px,4vw,32px) 80px}
.toc{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:18px 20px;margin:18px 0}
.toc h2{margin:0 0 10px;font-size:18px;color:var(--brand)}
.toc .block{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);font-weight:700;margin:14px 0 6px}
.toc a{display:inline-block;text-decoration:none;color:var(--brand-light);padding:4px 0}
.toc ul{margin:0;padding-left:18px}
.hint{background:#fff8e8;border:1px solid #f0d68a;color:#5b4b1f;border-radius:10px;padding:10px 14px;margin:14px 0;font-size:14px}
section.doc{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:clamp(18px,4vw,40px);margin:18px 0;scroll-margin-top:70px}
.toplink{display:block;text-align:right;font-size:13px;color:var(--muted);text-decoration:none;margin-top:10px}
h1{font-size:28px;margin:0 0 8px;color:var(--brand)}
h2{font-size:21px;margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--border)}
h3{font-size:17px;margin:22px 0 8px;color:var(--brand-light)}
h4{font-size:14px;margin:16px 0 6px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
p{margin:10px 0}ul,ol{margin:10px 0;padding-left:24px}li{margin:4px 0}a{color:var(--brand-light)}
code{background:#eef1f5;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace;font-size:13px}
pre{background:#1f2733;color:#e6e9ef;padding:14px 16px;border-radius:8px;overflow-x:auto}
pre code{background:transparent;padding:0;color:inherit}
blockquote{margin:14px 0;padding:8px 16px;border-left:4px solid var(--accent);background:#fff8e8;color:#5b4b1f;border-radius:0 6px 6px 0}
hr{border:none;border-top:1px solid var(--border);margin:26px 0}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px}
th,td{border:1px solid var(--border);padding:9px 12px;text-align:left;vertical-align:top}
th{background:var(--bg);font-weight:700}tr:nth-child(even) td{background:#fafbfc}
"""


def main():
    pages = {}
    base = os.path.join(HERE, "content")
    for root, _, files in os.walk(base):
        for name in files:
            if name.endswith(".md"):
                full = os.path.join(root, name)
                pid = os.path.relpath(full, base)[:-3].replace(os.sep, "/")
                with open(full, encoding="utf-8") as f:
                    pages[pid] = f.read()

    # Оглавление
    toc = ['<nav class="toc"><h2>Содержание</h2>']
    for block, items in NAV:
        if block:
            toc.append(f'<div class="block">{esc(block)}</div>')
        toc.append("<ul>")
        for pid, title in items:
            toc.append(f'<li><a href="#{anchor(pid)}">{esc(title)}</a></li>')
        toc.append("</ul>")
    toc.append("</nav>")

    # Разделы
    sections = []
    for block, items in NAV:
        for pid, _title in items:
            if pid not in pages:
                continue
            body = render_markdown(pages[pid])
            sections.append(
                f'<section class="doc" id="{anchor(pid)}">{body}'
                f'<a class="toplink" href="#top">↑ Наверх к содержанию</a></section>'
            )

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>База знаний — Аркона</title>
<style>{CSS}</style>
</head>
<body>
<a id="top"></a>
<header class="top">
  <div class="logo">АРКОНА</div>
  <div class="sub">База знаний компании · единый файл</div>
</header>
<div class="wrap">
  <div class="hint">📖 Это автономный файл — работает без интернета и сервера. Навигация — по ссылкам в «Содержании». Поиск по тексту — встроенный в браузер: <strong>Ctrl+F</strong> (на iPhone: «Поделиться» → «Найти на странице»).</div>
  {''.join(toc)}
  {''.join(sections)}
</div>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Готово: {OUT} ({os.path.getsize(OUT)//1024} КБ, разделов: {len(sections)})")


if __name__ == "__main__":
    main()
