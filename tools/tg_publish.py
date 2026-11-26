"""Publish due posts from tg/queue/*.md to the Telegram channel via Bot API. Runs in GitHub Actions every 10 minutes.

Post file: front matter (at: "YYYY-MM-DD HH:MM" Asia/Tbilisi, optional photo: path in repo, optional preview: true,
optional expires_h: hours, optional pin: true) + body in Telegram HTML (<b>, <i>, <a href>, <code>, <pre>, <blockquote>).
State: tg/posted.json {file: {message_id, posted_at} | {skipped: reason}}. Env: TG_BOT_TOKEN, TG_CHAT (default @about_ai_easy).
  python tools/tg_publish.py            # publish due
  python tools/tg_publish.py --dry      # show what is due, send nothing
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE, STATE = ROOT / 'tg' / 'queue', ROOT / 'tg' / 'posted.json'
TBILISI = timezone(timedelta(hours=4))
EXPIRES_H = 12


def parse(path: Path):
    text = path.read_text(encoding='utf-8')
    _, fm, body = text.split('---\n', 2)
    meta = dict(line.split(':', 1) for line in fm.strip().splitlines() if ':' in line)
    meta = {k.strip(): v.strip().strip('"') for k, v in meta.items()}
    meta['at'] = datetime.strptime(meta['at'], '%Y-%m-%d %H:%M').replace(tzinfo=TBILISI)
    return meta, body.strip()


def call(token, method, fields, photo: Path | None = None):
    url = f'https://api.telegram.org/bot{token}/{method}'
    if photo is None:
        req = urllib.request.Request(url, data=json.dumps(fields).encode(), headers={'Content-Type': 'application/json'})
    else:
        boundary = uuid.uuid4().hex
        parts = []
        for k, v in fields.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        ctype = mimetypes.guess_type(photo.name)[0] or 'image/jpeg'
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{photo.name}"\r\n'
                     f'Content-Type: {ctype}\r\n\r\n'.encode() + photo.read_bytes() + b'\r\n')
        parts.append(f'--{boundary}--\r\n'.encode())
        req = urllib.request.Request(url, data=b''.join(parts), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b'{}') | {'ok': False, 'http': e.code}


def main() -> int:
    dry = '--dry' in sys.argv
    token = os.environ.get('TG_BOT_TOKEN') or os.environ.get('TG_AIPROSTO_BOT_TOKEN')
    chat = os.environ.get('TG_CHAT', '@about_ai_easy')
    if not token and not dry:
        print('::warning::TG_BOT_TOKEN не задан — публикация выключена')
        return 0
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    now, failed = datetime.now(TBILISI), 0
    for path in sorted(QUEUE.glob('*.md')):
        if path.name in state:
            continue
        meta, body = parse(path)
        if meta.get('skip') == 'true':
            continue
        if meta['at'] > now:
            continue
        late = (now - meta['at']).total_seconds() / 3600
        if late > float(meta.get('expires_h', EXPIRES_H)):
            state[path.name] = {'skipped': f'опоздал на {late:.1f} ч'}
            print('SKIP', path.name, state[path.name]['skipped'])
            continue
        print('DUE', path.name, meta['at'].isoformat())
        if dry:
            continue
        photo = ROOT / meta['photo'] if meta.get('photo') else None
        if photo:
            r = call(token, 'sendPhoto', {'chat_id': chat, 'caption': body, 'parse_mode': 'HTML'}, photo)
        else:
            r = call(token, 'sendMessage', {'chat_id': chat, 'text': body, 'parse_mode': 'HTML',
                                            'link_preview_options': {'is_disabled': meta.get('preview') != 'true'}})
        if r.get('ok'):
            state[path.name] = {'message_id': r['result']['message_id'], 'posted_at': now.isoformat(timespec='seconds')}
            print('POSTED', path.name, r['result']['message_id'])
            if meta.get('pin') == 'true':
                call(token, 'pinChatMessage', {'chat_id': chat, 'message_id': r['result']['message_id'],
                                               'disable_notification': True})
        else:
            failed += 1
            print(f"::error::{path.name}: {r.get('description')}")
    if not dry:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
