"""
Compute fantasy points for each finish, using the OFFICIAL WSOP Fantasy League scoring system.
Mirrors the xlsx exactly. Public so the dashboard and scraper agree on numbers.
"""

# Standard tournaments (under $10K) — [regular, big_field_1000+]
SCORING_STANDARD = {
    'cash':   [1, 2],
    'ft_9_6': [3, 6],
    'ft_5_4': [5, 10],
    'third':  [7, 14],
    'second': [10, 20],
    'first':  [15, 30],
}

# Expensive tournaments ($10K+) — [<200, 200-399, 400-599, 600-799, 800-999, 1000+]
SCORING_EXPENSIVE = {
    'cash':   [1, 2, 2, 2, 2, 2],
    'ft_9_6': [3, 4, 5, 6, 6, 6],
    'ft_5_4': [5, 6, 7, 8, 9, 10],
    'third':  [7, 8, 9, 10, 11, 14],
    'second': [10, 11, 12, 13, 14, 20],
    'first':  [15, 16, 17, 18, 19, 30],
}

# Main Event
SCORING_MAIN_EVENT = {
    'cash': 3, 'day5': 4, 'day6': 6, 'day7': 8, 'day8': 10,
    'ft_9_7': 12, 'ft_6_4': 15, 'third': 20, 'second': 30, 'first': 50,
}

# $25K Heads-Up Championship
SCORING_HU = {
    'cash': 1, 'semi': 5, 'second': 10, 'first': 15,
}


def finish_category(pos: int) -> str:
    if pos == 1: return 'first'
    if pos == 2: return 'second'
    if pos == 3: return 'third'
    if pos in (4, 5): return 'ft_5_4'
    if 6 <= pos <= 9: return 'ft_9_6'
    return 'cash'


def entry_tier(entries: int) -> int:
    if entries < 200: return 0
    if entries < 400: return 1
    if entries < 600: return 2
    if entries < 800: return 3
    if entries < 1000: return 4
    return 5


def compute_event_points(event: dict) -> float:
    """
    event = {
      'type': 'standard' | 'expensive' | 'main_event' | 'hu_25k',
      'pos': int (1-based finish position; large number = busted in money but not FT),
      'entries': int,
      'buy_in': int (optional, used to auto-detect expensive),
      'day': int (Main Event day reached, optional),
      'semi': bool (HU semi-final flag, optional),
    }
    """
    t = event.get('type')
    pos = event.get('pos', 0)
    entries = event.get('entries', 0)
    buy_in = event.get('buy_in', 0)

    if t == 'main_event':
        if pos == 1: return SCORING_MAIN_EVENT['first']
        if pos == 2: return SCORING_MAIN_EVENT['second']
        if pos == 3: return SCORING_MAIN_EVENT['third']
        if 4 <= pos <= 6: return SCORING_MAIN_EVENT['ft_6_4']
        if 7 <= pos <= 9: return SCORING_MAIN_EVENT['ft_9_7']
        d = event.get('day', 0)
        if d >= 8: return SCORING_MAIN_EVENT['day8']
        if d >= 7: return SCORING_MAIN_EVENT['day7']
        if d >= 6: return SCORING_MAIN_EVENT['day6']
        if d >= 5: return SCORING_MAIN_EVENT['day5']
        return SCORING_MAIN_EVENT['cash']

    if t == 'hu_25k':
        if pos == 1: return SCORING_HU['first']
        if pos == 2: return SCORING_HU['second']
        if event.get('semi') or pos in (3, 4): return SCORING_HU['semi']
        return SCORING_HU['cash']

    # Standard vs Expensive
    if t == 'expensive' or (buy_in and buy_in >= 10000):
        cat = finish_category(pos)
        tier = entry_tier(entries)
        return SCORING_EXPENSIVE[cat][tier]

    # Standard
    cat = finish_category(pos)
    big = 1 if entries >= 1000 else 0
    return SCORING_STANDARD[cat][big]


if __name__ == '__main__':
    # Sanity tests against the xlsx
    print('Standard win in 500-entry tournament:', compute_event_points({'type': 'standard', 'pos': 1, 'entries': 500, 'buy_in': 1500}))
    print('Standard win in 5000-entry tournament:', compute_event_points({'type': 'standard', 'pos': 1, 'entries': 5000, 'buy_in': 1500}))
    print('$25K win, 300 entries:', compute_event_points({'type': 'expensive', 'pos': 1, 'entries': 300, 'buy_in': 25000}))
    print('Main Event win:', compute_event_points({'type': 'main_event', 'pos': 1, 'entries': 9000, 'buy_in': 10000}))
    print('Main Event day 6 bust:', compute_event_points({'type': 'main_event', 'pos': 80, 'entries': 9000, 'buy_in': 10000, 'day': 6}))
    print('$25K HU win:', compute_event_points({'type': 'hu_25k', 'pos': 1, 'entries': 60, 'buy_in': 25000}))
    print('$25K HU semi:', compute_event_points({'type': 'hu_25k', 'pos': 3, 'entries': 60, 'buy_in': 25000}))
