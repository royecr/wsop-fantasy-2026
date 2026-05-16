"""
PokerNews scraper — fetches live coverage from PokerNews WSOP tour pages.
Provides chip counts and live updates not yet on WSOP.com.
"""
import re
import json
import time
import logging
from urllib.parse import urljoin
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE = 'https://www.pokernews.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
}
TIMEOUT = 25

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('pokernews')


def http_get(url: str) -> str:
    log.info(f'GET {url}')
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    log.info(f'  -> {r.status_code} {len(r.text):,} bytes')
    r.raise_for_status()
    return r.text


def scrape_wsop_hub() -> dict:
    """Fetch the main WSOP coverage hub page and extract event links."""
    url = f'{BASE}/tours/wsop/2026-wsop/'
    try:
        html = http_get(url)
    except Exception:
        # Fallback to generic tour URL
        try:
            html = http_get(f'{BASE}/tours/wsop/')
        except Exception as e:
            log.error(f'Both PokerNews URLs failed: {e}')
            return {'events': [], 'errors': [str(e)]}

    soup = BeautifulSoup(html, 'html.parser')
    events = []
    # Look for links to event coverage pages
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(' ', strip=True)
        if not text:
            continue
        # Common patterns: "/news/2026/05/event-1-..." or "/tours/wsop/2026-wsop/event-X-..."
        if re.search(r'/(news|tours)/.*event[\s-]+\d+', href, re.IGNORECASE) or 'wsop' in href.lower():
            m = re.search(r'event[\s-]+(\d+)', href + ' ' + text, re.IGNORECASE)
            if m:
                events.append({
                    'event_no': int(m.group(1)),
                    'title': text[:120],
                    'url': urljoin(BASE, href),
                })
    # Dedup
    seen = {}
    for e in events:
        if e['event_no'] not in seen:
            seen[e['event_no']] = e
    return {'events': sorted(seen.values(), key=lambda x: x['event_no']), 'errors': []}


def scrape_chip_counts(event_url: str) -> list:
    """Fetch an event coverage page and parse chip counts table."""
    try:
        html = http_get(event_url)
    except Exception as e:
        log.error(f'Failed to fetch {event_url}: {e}')
        return []

    soup = BeautifulSoup(html, 'html.parser')
    chips = []
    # Look for chip-counts tables — typically rank, name, chips
    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        if len(rows) < 3:
            continue
        # Check headers
        headers_text = (rows[0].get_text(' ', strip=True) or '').lower()
        if 'player' not in headers_text and 'name' not in headers_text:
            continue
        for row in rows[1:]:
            cells = [c.get_text(' ', strip=True) for c in row.find_all('td')]
            if len(cells) < 2:
                continue
            # Pos, name, chips, maybe BB
            pos_m = re.match(r'^(\d+)$', cells[0])
            pos = int(pos_m.group(1)) if pos_m else None
            name = cells[1] if pos else cells[0]
            chips_str = next((c for c in cells if '$' not in c and re.search(r'\d[\d,]+', c)), '')
            chips_val = int(re.sub(r'[^\d]', '', chips_str)) if chips_str else 0
            chips.append({'pos': pos, 'name': name, 'chips': chips_val})
    log.info(f'  Parsed {len(chips)} chip-count entries')
    return chips


def scrape_all() -> dict:
    out = {
        'source': 'pokernews.com',
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'events': [],
        'errors': [],
    }
    hub = scrape_wsop_hub()
    out['errors'].extend(hub.get('errors', []))
    for ev in hub['events'][:20]:  # cap at 20 to be polite
        try:
            time.sleep(0.5)
            chips = scrape_chip_counts(ev['url'])
            out['events'].append({**ev, 'chip_counts': chips})
        except Exception as e:
            out['errors'].append(f'event {ev.get("event_no")}: {e}')
    return out


if __name__ == '__main__':
    data = scrape_all()
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str)[:3000])
    print(f'\n...total: {len(data["events"])} events, {len(data["errors"])} errors')
