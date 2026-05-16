"""
WSOP.com scraper — fetches live tournament data from the official WSOP site.

Strategy:
1. Fetch the tournament listings page (/tournaments/)
2. Parse each event: number, name, buy-in, status, dates, entries
3. For completed/in-progress events, fetch results page and extract finishes
4. Output structured dict per event

This scraper is intentionally defensive — it logs raw HTML statistics so we
can diagnose when WSOP changes their page structure.
"""
import re
import json
import time
import logging
from urllib.parse import urljoin
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE = 'https://www.wsop.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
}
TIMEOUT = 25

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('wsop')


def http_get(url: str) -> str:
    log.info(f'GET {url}')
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    log.info(f'  -> {r.status_code} {len(r.text):,} bytes')
    r.raise_for_status()
    return r.text


def parse_money(s: str) -> int:
    """Extract integer dollar amount from a string like '$1,500' or '10K'."""
    if not s:
        return 0
    s = s.replace(',', '').replace('$', '').strip().upper()
    m = re.match(r'^(\d+(?:\.\d+)?)\s*K$', s)
    if m:
        return int(float(m.group(1)) * 1000)
    m = re.match(r'^(\d+(?:\.\d+)?)\s*M$', s)
    if m:
        return int(float(m.group(1)) * 1_000_000)
    m = re.match(r'^(\d+)$', s)
    if m:
        return int(m.group(1))
    return 0


def parse_int(s: str) -> int:
    if not s:
        return 0
    s = s.replace(',', '').strip()
    m = re.search(r'\d+', s)
    return int(m.group()) if m else 0


def scrape_tournaments_listing() -> list:
    """
    Returns a list of event dicts:
      { 'event_no': int, 'name': str, 'buy_in': int, 'url': str, 'status': str, 'entries': int }
    Best effort — uses multiple heuristics since WSOP HTML may vary.
    """
    url = f'{BASE}/tournaments/?circuit=2026'
    try:
        html = http_get(url)
    except Exception as e:
        log.error(f'Failed to fetch tournaments listing: {e}')
        return []

    soup = BeautifulSoup(html, 'html.parser')
    events = []

    # Strategy 1: look for tournament tables with class hints
    candidate_rows = soup.find_all('tr')
    for row in candidate_rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 3:
            continue
        text = ' '.join(c.get_text(' ', strip=True) for c in cells)
        # Look for patterns like "Event #1" or numbers + dollar signs
        ev_match = re.search(r'event\s*#?\s*(\d+)', text, re.IGNORECASE)
        money_match = re.search(r'\$(\d[\d,]*)', text)
        if not ev_match or not money_match:
            continue
        ev_no = int(ev_match.group(1))
        buy_in = parse_money(money_match.group(0))
        # Try to extract event name (text between Event# and $)
        name_match = re.search(r'event\s*#?\s*\d+[:\s]*([^$]+?)(?=\$)', text, re.IGNORECASE)
        name = name_match.group(1).strip(' -:') if name_match else f'Event #{ev_no}'
        # Find the link
        link = row.find('a', href=True)
        ev_url = urljoin(BASE, link['href']) if link else url
        events.append({
            'event_no': ev_no,
            'name': name,
            'buy_in': buy_in,
            'url': ev_url,
            'status': 'unknown',
            'entries': 0,
        })

    # Strategy 2: look for div-based event cards
    if not events:
        for div in soup.find_all('div'):
            txt = div.get_text(' ', strip=True)
            if not txt:
                continue
            m = re.search(r'Event\s*#?\s*(\d+).*?\$([\d,]+)', txt[:200])
            if m:
                ev_no = int(m.group(1))
                buy_in = parse_money(m.group(2))
                link = div.find('a', href=True)
                events.append({
                    'event_no': ev_no,
                    'name': txt[:120].split('Event')[1] if 'Event' in txt[:200] else '',
                    'buy_in': buy_in,
                    'url': urljoin(BASE, link['href']) if link else url,
                    'status': 'unknown',
                    'entries': 0,
                })

    # Dedup by event_no
    seen = {}
    for e in events:
        if e['event_no'] not in seen:
            seen[e['event_no']] = e
    events = sorted(seen.values(), key=lambda x: x['event_no'])

    log.info(f'Found {len(events)} events on WSOP.com listing')
    return events


def scrape_event_results(event_url: str) -> dict:
    """
    For a specific event URL, fetch the results page and extract finishes.
    Returns: { 'entries': int, 'finishes': [{'pos': int, 'name': str, 'prize': int}], 'status': str }
    """
    try:
        html = http_get(event_url)
    except Exception as e:
        log.error(f'Failed to fetch event {event_url}: {e}')
        return {'entries': 0, 'finishes': [], 'status': 'error'}

    soup = BeautifulSoup(html, 'html.parser')
    finishes = []
    entries = 0
    status = 'unknown'

    # Look for entries count
    txt = soup.get_text(' ', strip=True)
    m = re.search(r'(\d[\d,]*)\s+entries', txt, re.IGNORECASE)
    if m:
        entries = parse_int(m.group(1))

    # Look for results table — typically a table with rank, name, prize columns
    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        if len(rows) < 3:
            continue
        for row in rows[1:]:  # skip header
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            cell_texts = [c.get_text(' ', strip=True) for c in cells]
            # First cell should be position (numeric)
            pos_match = re.match(r'^(\d+)$', cell_texts[0])
            if not pos_match:
                continue
            pos = int(pos_match.group(1))
            # Find name - usually 2nd column
            name = cell_texts[1] if len(cell_texts) > 1 else ''
            # Strip "United States" etc. trailing country
            name = re.sub(r'\s*(United States|Canada|Germany|UK|France|Israel|Brazil|Russia|Spain|Italy|Portugal|Belgium|Bulgaria|Belarus|Argentina|Japan|China|Australia|Mexico)\s*$', '', name)
            prize = 0
            for c in cell_texts[2:]:
                if '$' in c:
                    prize = parse_money(c.split()[0] if c.split() else c)
                    break
            if name:
                finishes.append({'pos': pos, 'name': name.strip(), 'prize': prize})

    if finishes:
        status = 'complete' if entries and len(finishes) >= entries * 0.10 else 'in_progress'

    log.info(f'  Event has {entries} entries, parsed {len(finishes)} finishes (status: {status})')
    return {'entries': entries, 'finishes': finishes, 'status': status}


def scrape_all() -> dict:
    """Main entry point. Returns aggregated scraper output."""
    out = {
        'source': 'wsop.com',
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'events': [],
        'errors': [],
    }
    try:
        events = scrape_tournaments_listing()
    except Exception as e:
        out['errors'].append(f'listing: {e}')
        return out

    for ev in events:
        try:
            # Throttle to be polite
            time.sleep(0.5)
            details = scrape_event_results(ev['url'])
            ev.update(details)
            out['events'].append(ev)
        except Exception as e:
            out['errors'].append(f'event {ev.get("event_no")}: {e}')

    return out


if __name__ == '__main__':
    data = scrape_all()
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str)[:3000])
    print(f'\n...total: {len(data["events"])} events, {len(data["errors"])} errors')
