"""
Main entry point — orchestrates all scrapers and produces:
  data/live_results.json   - aggregated player points + per-event details
  data/last_update.json    - metadata about the latest run

Runs from GitHub Actions on schedule. Designed to be idempotent and safe to fail:
- If a source fails, others continue
- If parsing yields nothing, still writes a valid file (so the dashboard never breaks)
- Always logs verbosely so the workflow run is debuggable
"""
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timezone

import wsop_scraper
import pokernews_scraper
from name_matcher import load_roster, find_player, normalize_name
from compute_points import compute_event_points

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('build')

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)


def classify_event_type(event: dict) -> str:
    """Map a WSOP event to our scoring categories."""
    name = (event.get('name') or '').lower()
    buy_in = event.get('buy_in', 0)
    if 'main event' in name and '$10' in name:
        return 'main_event'
    if 'heads' in name and 'up' in name and buy_in >= 25000:
        return 'hu_25k'
    if buy_in >= 10000:
        return 'expensive'
    return 'standard'


def aggregate_player_points(wsop_data: dict, pokernews_data: dict) -> dict:
    """
    Combine scraper outputs into per-player point totals.
    Returns: {
      'players': { 'name_he': { 'points': N, 'events': [...], 'last_event': str } },
      'events': [...],
      'summary': {...}
    }
  """
    players, by_en, by_he = load_roster()
    player_points = {}  # name_he -> { points: float, events: [...] }
    all_events = []

    # Process WSOP.com events (authoritative for final results)
    for ev in wsop_data.get('events', []):
        event_type = classify_event_type(ev)
        ev_record = {
            'event_no': ev.get('event_no'),
            'name': ev.get('name'),
            'buy_in': ev.get('buy_in'),
            'entries': ev.get('entries', 0),
            'type': event_type,
            'status': ev.get('status', 'unknown'),
            'source': 'wsop.com',
            'finishes_matched': 0,
            'finishes_total': len(ev.get('finishes', [])),
        }
        for f in ev.get('finishes', []):
            name = f.get('name', '')
            pos = f.get('pos')
            if not name or not pos:
                continue
            player = find_player(name, players, by_en, by_he)
            if not player:
                continue
            ev_record['finishes_matched'] += 1
            pts = compute_event_points({
                'type': event_type,
                'pos': pos,
                'entries': ev.get('entries', 0),
                'buy_in': ev.get('buy_in', 0),
            })
            entry = player_points.setdefault(player['h'], {
                'name_he': player['h'],
                'name_en': player.get('e', ''),
                'category': player['cat'],
                'price': player['pr'],
                'points': 0,
                'events': [],
                'last_update': datetime.now(timezone.utc).isoformat(),
            })
            entry['points'] += pts
            entry['events'].append({
                'event_no': ev.get('event_no'),
                'event_name': ev.get('name'),
                'pos': pos,
                'points': pts,
                'prize': f.get('prize'),
            })
        all_events.append(ev_record)

    # Process PokerNews chip counts as in_progress info (no points yet)
    chip_info = {}  # name_he -> [{event, chips}, ...]
    for ev in pokernews_data.get('events', []):
        for c in ev.get('chip_counts', []):
            name = c.get('name', '')
            chips = c.get('chips', 0)
            if not name:
                continue
            player = find_player(name, players, by_en, by_he)
            if not player:
                continue
            chip_info.setdefault(player['h'], []).append({
                'event_no': ev.get('event_no'),
                'event_title': ev.get('title', ''),
                'chips': chips,
                'source': 'pokernews.com',
            })

    # Attach chip counts to player records
    for name_he, chips in chip_info.items():
        if name_he not in player_points:
            player = next((p for p in players if p['h'] == name_he), None)
            if player:
                player_points[name_he] = {
                    'name_he': player['h'],
                    'name_en': player.get('e', ''),
                    'category': player['cat'],
                    'price': player['pr'],
                    'points': 0,
                    'events': [],
                    'last_update': datetime.now(timezone.utc).isoformat(),
                }
        if name_he in player_points:
            player_points[name_he]['live_chips'] = chips

    return {
        'players': player_points,
        'events': all_events,
        'summary': {
            'total_events_seen': len(all_events),
            'total_players_with_points': sum(1 for p in player_points.values() if p['points'] > 0),
            'total_players_with_chips': len(chip_info),
        }
    }


def main():
    started = time.time()
    log.info('=== WSOP Fantasy 2026 Live Scraper ===')

    sources = []

    # 1. WSOP.com
    wsop_data = {'events': [], 'errors': ['not run']}
    try:
        wsop_data = wsop_scraper.scrape_all()
        sources.append({
            'name': 'WSOP.com',
            'ok': True,
            'events': len(wsop_data.get('events', [])),
            'errors': len(wsop_data.get('errors', [])),
        })
    except Exception as e:
        log.exception('WSOP scraper failed')
        sources.append({'name': 'WSOP.com', 'ok': False, 'error': str(e)})

    # 2. PokerNews
    pn_data = {'events': [], 'errors': ['not run']}
    try:
        pn_data = pokernews_scraper.scrape_all()
        sources.append({
            'name': 'PokerNews',
            'ok': True,
            'events': len(pn_data.get('events', [])),
            'errors': len(pn_data.get('errors', [])),
        })
    except Exception as e:
        log.exception('PokerNews scraper failed')
        sources.append({'name': 'PokerNews', 'ok': False, 'error': str(e)})

    # 3. Aggregate
    log.info('Aggregating per-player points...')
    aggregated = aggregate_player_points(wsop_data, pn_data)

    # 4. Write outputs
    elapsed = time.time() - started
    last_update = {
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'duration_seconds': round(elapsed, 1),
        'sources': sources,
        'summary': aggregated['summary'],
    }

    out_file = DATA_DIR / 'live_results.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            'last_update': last_update,
            'events': aggregated['events'],
            'players': aggregated['players'],
        }, f, ensure_ascii=False, indent=2)
    log.info(f'Wrote {out_file} ({out_file.stat().st_size:,} bytes)')

    meta_file = DATA_DIR / 'last_update.json'
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(last_update, f, ensure_ascii=False, indent=2)
    log.info(f'Wrote {meta_file}')

    log.info(f'Done in {elapsed:.1f}s. {aggregated["summary"]}')


if __name__ == '__main__':
    main()
