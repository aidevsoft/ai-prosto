# ИИ — просто

Публичная часть проекта @ai.prosto.official.

- `site/` — сайт на GitHub Pages: бесплатная шпаргалка, библиотека запросов из рилсов, гайды.
- `tg/queue/` — очередь постов канала [@about_ai_easy](https://t.me/about_ai_easy); правила — `tg/RULES.md`.
- `tools/tg_publish.py` — публикатор (Bot API, только стандартная библиотека). Запускается `.github/workflows/tg.yml` каждые 10 минут.

Секрет `TG_BOT_TOKEN` хранится только в GitHub Secrets.
