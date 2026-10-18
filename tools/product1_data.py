"""Select an offline campaign without touching the production source data."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    path = Path(os.environ.get('NEON_CAMPAIGN', ROOT/'assets/levels/product1-campaign.json'))
    raw = path.read_bytes()
    campaign = json.loads(raw)
    levels = campaign['levels']
    explicit_bounds = os.environ.get('NEON_CAMPAIGN_BOUNDS')
    if explicit_bounds or not all('visual_size' in level for level in levels):
        bounds_path = Path(explicit_bounds or ROOT/'assets/levels/product1-bounds.json')
        bounds = json.loads(bounds_path.read_text())
        assert bounds['campaign_sha256'] == hashlib.sha256(raw).hexdigest()
    else:
        # New campaigns carry their authored rectangle beside the rows. Read
        # this metadata directly: no stale sidecar and no campaign rewriting.
        bounds = dict(levels=[dict(number=level['number'],visual_size=level['visual_size'],
                          rows_sha256=hashlib.sha256('\n'.join(level['rows']).encode()).hexdigest())
                          for level in levels])
    assert 1 <= len(levels) <= 60 and len(bounds['levels']) == len(levels)
    for n, (level, rect) in enumerate(zip(levels, bounds['levels']), 1):
        assert level['number'] == rect['number'] == n
        assert level['area'] in (1,2,3,4)
        assert rect['rows_sha256'] == hashlib.sha256('\n'.join(level['rows']).encode()).hexdigest()
        w,h = rect['visual_size']
        assert 3 <= w <= 16 and 3 <= h <= 8
        assert len(level['rows']) == 8 and all(len(r)==16 for r in level['rows'])
        assert all(c=='#' for y,r in enumerate(level['rows']) for x,c in enumerate(r) if x>=w or y>=h)
        level['visual_size'] = [w,h]
    return raw, levels
