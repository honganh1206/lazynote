"""Pure window-geometry helpers. Ported from the original geometry.ts.

No PySide6 imports — unit-testable under plain pytest.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

MIN_WIDTH = 360
MIN_HEIGHT = 360


@dataclass
class Geometry:
    x: int
    y: int
    width: int
    height: int


def is_on_screen(g: Geometry, m: Geometry) -> bool:
    """True if the window overlaps the monitor by >= 50px on both axes."""
    overlap_x = max(0, min(g.x + g.width, m.x + m.width) - max(g.x, m.x))
    overlap_y = max(0, min(g.y + g.height, m.y + m.height) - max(g.y, m.y))
    return overlap_x >= 50 and overlap_y >= 50


def parse_geometry(raw: str | None) -> Geometry | None:
    """Parse persisted geometry JSON; None if missing/malformed. Clamps to minimums."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if not all(isinstance(data.get(k), (int, float)) for k in ("x", "y", "width", "height")):
        return None
    return Geometry(
        x=int(data["x"]),
        y=int(data["y"]),
        width=max(int(data["width"]), MIN_WIDTH),
        height=max(int(data["height"]), MIN_HEIGHT),
    )
