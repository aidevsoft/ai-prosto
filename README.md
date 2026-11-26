# ИИ — просто

Публичная часть проекта @ai.prosto.official.

- `site/` — черновик сайта в репозитории. Боевая витрина — Тильда, не GitHub Pages.
- `tg/queue/` — очередь постов канала [@about_ai_easy](https://t.me/about_ai_easy); правила — `tg/RULES.md`.
- `tools/tg_publish.py` — публикатор (Bot API, только стандартная библиотека). Каждые 10 минут его запускает cron на Almaty, не GitHub Actions.

Токен бота только на сервере, в репозиторий не класть. Состояние канала — `CONTEXT.md` в проекте, раздел «Telegram».
