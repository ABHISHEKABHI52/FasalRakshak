"""WKT helpers for field locations (docs/07 §9 — PostGIS geography(Point,4326)).

Points are exchanged with clients as {lat, lng} and stored as WKT. On PostgreSQL the
stored value is cast to geography by GeoAlchemy2; on SQLite (tests/dev) the WKT text
is stored as-is. Longitude always precedes latitude inside WKT (OGC order).
"""

import re

_WKT_POINT = re.compile(
    r"POINT\s*\(\s*(?P<x>-?\d+(?:\.\d+)?)\s+(?P<y>-?\d+(?:\.\d+)?)\s*\)", re.IGNORECASE
)


def make_point_wkt(lat: float, lng: float) -> str:
    """Build an EWKT point from client latitude/longitude (validated upstream)."""
    return f"SRID=4326;POINT({lng} {lat})"


def parse_point_wkt(value: str | None) -> tuple[float, float] | None:
    """Parse stored WKT/EWKT into (lat, lng); returns None when absent or unparseable."""
    if not value or not isinstance(value, str):
        return None
    match = _WKT_POINT.search(value)
    if match is None:
        return None
    lng = float(match.group("x"))
    lat = float(match.group("y"))
    return lat, lng