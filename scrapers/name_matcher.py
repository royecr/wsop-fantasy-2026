"""
Name matcher — maps English names from WSOP/PokerNews HTML to our Hebrew player roster.
The 230-player roster has both Hebrew (name_he) and English (name_en) names.
"""
import json
import re
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parent.parent
PLAYERS_FILE = ROOT / 'data' / 'players.json'


def normalize_name(s: str) -> str:
    """Normalize for comparison: lowercase, strip punctuation/whitespace."""
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r"[\.,'\"`]", '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def load_roster():
    """Load 230-player roster and build lookup indexes."""
    with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
        players = json.load(f)
    by_en = {}
    by_he = {}
    for p in players:
        en = (p.get('e') or '').strip()
        he = p.get('h', '').strip()
        if en:
            by_en[normalize_name(en)] = p
            # Also index "First Last" reversed combinations
            parts = en.split()
            if len(parts) >= 2:
                by_en[normalize_name(parts[-1] + ' ' + ' '.join(parts[:-1]))] = p
                by_en[normalize_name(parts[-1])] = p  # last name only
        if he:
            by_he[normalize_name(he)] = p
    return players, by_en, by_he


def find_player(query: str, players=None, by_en=None, by_he=None):
    """Find a player by English or Hebrew name, with fuzzy fallback."""
    if players is None:
        players, by_en, by_he = load_roster()
    q = normalize_name(query)
    if not q:
        return None
    # Exact English
    if q in by_en:
        return by_en[q]
    # Exact Hebrew
    if q in by_he:
        return by_he[q]
    # Fuzzy English (>= 0.85 ratio)
    best = None
    best_score = 0.85
    for k, p in by_en.items():
        score = SequenceMatcher(None, q, k).ratio()
        if score > best_score:
            best = p
            best_score = score
    if best:
        return best
    # Fuzzy Hebrew
    for k, p in by_he.items():
        score = SequenceMatcher(None, q, k).ratio()
        if score > best_score:
            best = p
            best_score = score
    return best


if __name__ == '__main__':
    players, by_en, by_he = load_roster()
    print(f'Loaded {len(players)} players')
    # Test some lookups
    for q in ['Phil Hellmuth', 'Phil Ivey', 'Daniel Negreanu', 'phil hellmuth', 'jeremy ausmus', 'Shaun Deeb']:
        p = find_player(q, players, by_en, by_he)
        if p:
            print(f"  {q!r:30} -> {p['h']} ({p['e']}) [{p['cat']}, ${p['pr']}M]")
        else:
            print(f"  {q!r:30} -> NOT FOUND")
