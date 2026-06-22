#!/usr/bin/env python3
"""Собирает единый автономный HTML-файл базы знаний.

Встраивает CSS, JS и весь Markdown-контент в один файл, который
открывается двойным кликом без локального сервера и без интернета.

Запуск:  python3 build-standalone.py
Результат: arkona-baza-znaniy.html
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "arkona-baza-znaniy.html")


def read(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as f:
        return f.read()


def collect_content():
    content = {}
    base = os.path.join(HERE, "content")
    for root, _, files in os.walk(base):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, base)[:-3].replace(os.sep, "/")
            with open(full, encoding="utf-8") as f:
                content[rel] = f.read()
    return content


def main():
    css = read("kb.css")
    js = read("kb.js")
    content = collect_content()

    # Безопасно встраиваем JSON в <script> (экранируем закрывающий тег).
    data = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>База знаний — Аркона</title>
    <style>
{css}
    </style>
</head>
<body>
    <header id="topbar">
        <button id="menu-toggle" aria-label="Меню">☰</button>
        <a class="brand" href="#home">
            <span class="logo">АРКОНА</span>
            <span class="brand-sub">База знаний</span>
        </a>
        <div class="search-box">
            <input type="search" id="search" placeholder="Поиск по базе знаний…" autocomplete="off">
            <ul id="search-results"></ul>
        </div>
    </header>

    <div id="layout">
        <nav id="sidebar"></nav>
        <main id="content">
            <article id="doc">Загрузка…</article>
            <footer id="doc-footer"></footer>
        </main>
    </div>

    <script>
    // Весь контент базы знаний встроен в файл — сервер и интернет не нужны.
    window.KB_CONTENT = {data};
    </script>
    <script>
{js}
    </script>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = os.path.getsize(OUT) // 1024
    print(f"Готово: {OUT} ({size_kb} КБ, разделов: {len(content)})")


if __name__ == "__main__":
    main()
