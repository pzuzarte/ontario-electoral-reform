#!/usr/bin/env python3
"""
Ontario Electoral Reform Analysis
Compares FPTP with PR, MMP, AMS systems across 60 years of Ontario elections.

Output: index.html (fully self-contained)
"""

import json
import math
import os
import re
import warnings
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ════════════════════════════════════════════════════════════════════════════
# CURATED DATA
# ════════════════════════════════════════════════════════════════════════════

ONTARIO_ELECTIONS = [
    {"year": 1963, "seats": 108, "results": {"PC": (44.0, 77), "Liberal": (33.6, 24), "NDP": (22.4, 7)}},
    {"year": 1967, "seats": 117, "results": {"PC": (42.0, 69), "Liberal": (31.9, 28), "NDP": (26.0, 20)}},
    {"year": 1971, "seats": 117, "results": {"PC": (44.5, 78), "Liberal": (27.8, 20), "NDP": (27.2, 19)}},
    {"year": 1975, "seats": 125, "results": {"PC": (36.1, 51), "Liberal": (34.3, 36), "NDP": (28.9, 38)}},
    {"year": 1977, "seats": 125, "results": {"PC": (39.7, 58), "Liberal": (31.5, 34), "NDP": (28.0, 33)}},
    {"year": 1981, "seats": 125, "results": {"PC": (44.4, 70), "Liberal": (33.8, 34), "NDP": (21.1, 21)}},
    {"year": 1985, "seats": 125, "results": {"PC": (36.9, 52), "Liberal": (38.0, 48), "NDP": (23.8, 25)}},
    {"year": 1987, "seats": 130, "results": {"PC": (24.7, 16), "Liberal": (47.3, 95), "NDP": (25.7, 19)}},
    {"year": 1990, "seats": 130, "results": {"PC": (23.5, 20), "Liberal": (32.4, 36), "NDP": (37.6, 74)}},
    {"year": 1995, "seats": 130, "results": {"PC": (44.8, 82), "Liberal": (31.1, 30), "NDP": (20.6, 17), "Others": (3.5, 1)}},
    {"year": 1999, "seats": 103, "results": {"PC": (44.9, 59), "Liberal": (39.9, 35), "NDP": (12.5, 9)}},
    {"year": 2003, "seats": 103, "results": {"PC": (34.7, 24), "Liberal": (46.5, 72), "NDP": (14.7, 7), "Green": (2.8, 0)}},
    {"year": 2007, "seats": 107, "results": {"PC": (31.6, 26), "Liberal": (42.2, 71), "NDP": (16.8, 10), "Green": (8.0, 0)}},
    {"year": 2011, "seats": 107, "results": {"PC": (35.5, 37), "Liberal": (37.6, 53), "NDP": (22.7, 17), "Green": (2.9, 0)}},
    {"year": 2014, "seats": 107, "results": {"PC": (31.2, 28), "Liberal": (38.7, 58), "NDP": (23.8, 21), "Green": (4.8, 0)}},
    {"year": 2018, "seats": 124, "results": {"PC": (40.5, 76), "Liberal": (19.6, 7), "NDP": (33.6, 40), "Green": (4.6, 1)}},
    {"year": 2022, "seats": 124, "results": {"PC": (40.8, 83), "Liberal": (23.8, 8), "NDP": (23.7, 31), "Green": (6.0, 1), "Others": (5.7, 1)}},
]

FEDERAL_ONTARIO = [
    {"year": 2000, "seats": 103, "results": {"Liberal": (51.5, 100), "Alliance": (23.6, 2), "NDP": (8.3, 1), "PC": (14.4, 0)}},
    {"year": 2004, "seats": 106, "results": {"Liberal": (44.7, 75), "Conservative": (31.5, 24), "NDP": (18.1, 7), "Green": (4.4, 0)}},
    {"year": 2006, "seats": 106, "results": {"Liberal": (39.9, 54), "Conservative": (35.1, 40), "NDP": (19.4, 12), "Green": (4.7, 0)}},
    {"year": 2008, "seats": 106, "results": {"Conservative": (39.2, 51), "Liberal": (33.8, 38), "NDP": (18.2, 17), "Green": (8.0, 0)}},
    {"year": 2011, "seats": 106, "results": {"Conservative": (44.4, 73), "Liberal": (25.3, 11), "NDP": (25.6, 22), "Green": (3.8, 0)}},
    {"year": 2015, "seats": 121, "results": {"Liberal": (44.8, 80), "Conservative": (35.1, 33), "NDP": (16.6, 8), "Green": (2.8, 0)}},
    {"year": 2019, "seats": 121, "results": {"Liberal": (41.5, 79), "Conservative": (33.2, 36), "NDP": (16.8, 6), "Green": (6.2, 0), "PPC": (1.6, 0)}},
    {"year": 2021, "seats": 121, "results": {"Liberal": (39.3, 78), "Conservative": (34.9, 37), "NDP": (17.9, 5), "Green": (2.2, 1), "PPC": (5.4, 0)}},
]

ONTARIO_REGIONS_2022 = {
    "Toronto":            {"seats": 25, "votes": {"PC": 15.0, "Liberal": 35.0, "NDP": 43.0, "Green": 7.0}},
    "GTA 905 Belt":       {"seats": 35, "votes": {"PC": 45.0, "Liberal": 25.0, "NDP": 24.0, "Green": 6.0}},
    "Eastern / Ottawa":   {"seats": 15, "votes": {"PC": 39.0, "Liberal": 30.0, "NDP": 21.0, "Green": 10.0}},
    "Northern Ontario":   {"seats": 12, "votes": {"PC": 34.0, "Liberal": 15.0, "NDP": 44.0, "Green": 7.0}},
    "Central Ontario":    {"seats": 10, "votes": {"PC": 54.0, "Liberal": 18.0, "NDP": 19.0, "Green": 9.0}},
    "Hamilton / Niagara": {"seats": 14, "votes": {"PC": 40.0, "Liberal": 15.0, "NDP": 37.0, "Green": 8.0}},
    "Southwestern ON":    {"seats": 13, "votes": {"PC": 49.0, "Liberal": 17.0, "NDP": 26.0, "Green": 8.0}},
}

# ════════════════════════════════════════════════════════════════════════════
# RIDING-LEVEL DATA LOADING
# ════════════════════════════════════════════════════════════════════════════

def classify_riding(population):
    """Classify a riding by population into urban/suburban/rural type."""
    if population < 80000:
        return "Remote/Northern"
    elif population < 110000:
        return "Rural / Small City"
    elif population < 125000:
        return "Suburban"
    else:
        return "Urban / High-Growth"


RIDING_TYPE_COLORS = {
    "Remote/Northern":   "#9333EA",  # purple
    "Rural / Small City": "#F4831F", # orange
    "Suburban":          "#003F7F",  # blue
    "Urban / High-Growth": "#D00000", # red
}


def load_riding_data():
    """Load riding-level GeoJSON, election results and populations.

    Returns (geojson, results, populations) or (None, None, None) on failure.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    geojson_path  = os.path.join(script_dir, "ontario_ridings.geojson")
    results_path  = os.path.join(script_dir, "ontario_election_2022.json")
    pop_path      = os.path.join(script_dir, "ontario_riding_populations.json")

    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        with open(pop_path, "r", encoding="utf-8") as f:
            populations = json.load(f)
        print(f"  [ok] Loaded riding data: {len(geojson['features'])} ridings, "
              f"{len(results)} results, {len(populations)} populations")
        return geojson, results, populations
    except FileNotFoundError as e:
        print(f"  [skip] Riding data file missing: {e}")
        return None, None, None
    except Exception as e:
        print(f"  [skip] Riding data load failed: {e}")
        return None, None, None


def get_riding_centroids(geojson):
    """Compute centroid lon/lat for each riding feature (simple coordinate mean)."""
    centroids = {}
    for feature in geojson.get("features", []):
        name = feature["properties"].get("name", "")
        geom = feature.get("geometry", {})
        geom_type = geom.get("type", "")
        coords_flat = []

        if geom_type == "Polygon":
            rings = geom.get("coordinates", [])
            if rings:
                coords_flat = rings[0]  # exterior ring
        elif geom_type == "MultiPolygon":
            polys = geom.get("coordinates", [])
            for poly in polys:
                if poly:
                    coords_flat.extend(poly[0])  # exterior ring of each polygon

        if coords_flat:
            lons = [c[0] for c in coords_flat]
            lats = [c[1] for c in coords_flat]
            centroids[name] = (sum(lons) / len(lons), sum(lats) / len(lats))

    return centroids


# ════════════════════════════════════════════════════════════════════════════
# PARTY COLORS & STYLE
# ════════════════════════════════════════════════════════════════════════════

PARTY_COLORS = {
    "PC":           "#003F7F",
    "Liberal":      "#D00000",
    "NDP":          "#F4831F",
    "Green":        "#3D9B35",
    "Others":       "#6B7280",
    "Alliance":     "#6B7280",
    "Conservative": "#003F7F",
    "PPC":          "#4B0082",
}

BG       = "#0D1117"
BG_CARD  = "#161B22"
BG_CARD2 = "#1C2128"
BORDER   = "#30363D"
TEXT     = "#E6EDF3"
MUTED    = "#8B949E"
GRID     = "#2D333B"

BASE_LAYOUT = dict(
    paper_bgcolor=BG_CARD,
    plot_bgcolor=BG,
    font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", color=TEXT, size=13),
    title_font=dict(size=16, color=TEXT),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
               tickfont=dict(color="#CDD9E5")),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
               tickfont=dict(color="#CDD9E5")),
    legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1,
                font=dict(color=TEXT)),
    margin=dict(t=70, b=55, l=65, r=30),
    hoverlabel=dict(bgcolor="#2D333B", bordercolor=GRID, font=dict(color=TEXT, size=13)),
)

H = 480


def lay(**kwargs):
    out = dict(BASE_LAYOUT)
    for k, v in kwargs.items():
        if k in ("xaxis", "yaxis") and k in out:
            merged = dict(out[k])
            merged.update(v)
            out[k] = merged
        else:
            out[k] = v
    return out


def to_html(fig):
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "responsive": True},
    )


def pcolor(party):
    return PARTY_COLORS.get(party, "#6B7280")


def hex_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ════════════════════════════════════════════════════════════════════════════
# ELECTORAL SYSTEM SIMULATORS
# ════════════════════════════════════════════════════════════════════════════

def dhondt(votes_dict, total_seats, threshold=5.0):
    """Closed-list d'Hondt allocation with threshold."""
    eligible = {p: v for p, v in votes_dict.items() if v >= threshold}
    if not eligible:
        return {p: 0 for p in votes_dict}
    seats = {p: 0 for p in eligible}
    for _ in range(total_seats):
        quotients = {p: eligible[p] / (seats[p] + 1) for p in eligible}
        winner = max(quotients, key=quotients.get)
        seats[winner] += 1
    result = {p: 0 for p in votes_dict}
    result.update(seats)
    return result


def sainte_lague(votes_dict, total_seats, threshold=5.0):
    """Closed-list Sainte-Laguë allocation with threshold."""
    eligible = {p: v for p, v in votes_dict.items() if v >= threshold}
    if not eligible:
        return {p: 0 for p in votes_dict}
    seats = {p: 0 for p in eligible}
    for _ in range(total_seats):
        quotients = {p: eligible[p] / (2 * seats[p] + 1) for p in eligible}
        winner = max(quotients, key=quotients.get)
        seats[winner] += 1
    result = {p: 0 for p in votes_dict}
    result.update(seats)
    return result


def regional_pr_dhondt(regions_data, threshold=5.0):
    """Regional List PR d'Hondt using ONTARIO_REGIONS_2022."""
    totals = {}
    for region, info in regions_data.items():
        alloc = dhondt(info["votes"], info["seats"], threshold)
        for p, s in alloc.items():
            totals[p] = totals.get(p, 0) + s
    return totals


def sim_mmp(votes_dict, total_seats, actual_fptp_seats, list_fraction=0.5):
    """
    Mixed-Member Proportional: half seats FPTP (estimated), half list top-up.
    Overhang seats allowed.
    """
    fptp_count = math.floor(total_seats * (1 - list_fraction))
    list_count  = total_seats - fptp_count

    # Estimate FPTP seats as actual × (fptp_count / total_seats)
    scale = fptp_count / total_seats
    fptp_seats = {}
    for p, s in actual_fptp_seats.items():
        fptp_seats[p] = round(s * scale)

    # Proportional allocation for total seats by d'Hondt
    proportional = dhondt(votes_dict, total_seats, threshold=5.0)

    # Top-up: give each party max(0, proportional - fptp) from list seats
    result = dict(fptp_seats)
    remaining = list_count
    top_up_needed = {}
    for p in proportional:
        need = max(0, proportional[p] - fptp_seats.get(p, 0))
        top_up_needed[p] = need

    total_needed = sum(top_up_needed.values())
    if total_needed > 0:
        for p, need in top_up_needed.items():
            allocated = round(need * remaining / total_needed) if total_needed else 0
            result[p] = result.get(p, 0) + allocated

    return result


def sim_ams(votes_dict, total_seats, actual_fptp_seats):
    """AMS: 2/3 FPTP seats, 1/3 list seats."""
    return sim_mmp(votes_dict, total_seats, actual_fptp_seats, list_fraction=1/3)


def simulate_all_systems(election):
    """Returns dict of system_name -> {party: seats}."""
    year = election["year"]
    total = election["seats"]
    results = election["results"]

    votes_dict = {p: v for p, (v, s) in results.items()}
    fptp_dict  = {p: s for p, (v, s) in results.items()}

    systems = {}
    systems["FPTP"] = fptp_dict
    systems["List PR d'Hondt"]     = dhondt(votes_dict, total, threshold=5.0)
    systems["List PR Sainte-Laguë"] = sainte_lague(votes_dict, total, threshold=5.0)
    systems["MMP"]  = sim_mmp(votes_dict, total, fptp_dict, list_fraction=0.5)
    systems["AMS"]  = sim_ams(votes_dict, total, fptp_dict)

    # Regional PR only for 2022
    if year == 2022:
        systems["Regional PR d'Hondt"] = regional_pr_dhondt(ONTARIO_REGIONS_2022, threshold=5.0)
    else:
        # Province-wide d'Hondt as proxy
        systems["Regional PR d'Hondt"] = dhondt(votes_dict, total, threshold=5.0)

    return systems


# ════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ════════════════════════════════════════════════════════════════════════════

def gallagher_index(votes_dict, seats_dict, total_seats):
    """Gallagher index: sqrt(0.5 * sum((v_i - s_i)^2)), v/s as percentages."""
    all_parties = set(votes_dict) | set(seats_dict)
    total_votes = sum(votes_dict.values())
    sq_sum = 0.0
    for p in all_parties:
        v_pct = 100.0 * votes_dict.get(p, 0) / total_votes if total_votes else 0
        s_pct = 100.0 * seats_dict.get(p, 0) / total_seats if total_seats else 0
        sq_sum += (v_pct - s_pct) ** 2
    return math.sqrt(0.5 * sq_sum)


def wasted_votes_pct(election):
    """Fraction of votes cast for non-winning parties (FPTP approximation)."""
    results = election["results"]
    winner = max(results, key=lambda p: results[p][1])
    winner_votes_pct, winner_seats = results[winner]
    total_votes_pct = sum(v for v, s in results.values())
    wasted = total_votes_pct - winner_votes_pct
    return 100.0 * wasted / total_votes_pct if total_votes_pct else 0


def is_false_majority(election):
    """True if winner got <50% of votes but >50% of seats."""
    results = election["results"]
    total_seats = election["seats"]
    winner = max(results, key=lambda p: results[p][1])
    v_pct, seats = results[winner]
    return v_pct < 50.0 and seats > total_seats / 2


def compute_all_gallagher(election):
    """Gallagher index for all 6 systems for one election."""
    total = election["seats"]
    votes_dict = {p: v for p, (v, s) in election["results"].items()}
    systems = simulate_all_systems(election)
    out = {}
    for sys_name, seats_dict in systems.items():
        out[sys_name] = gallagher_index(votes_dict, seats_dict, total)
    return out


# ════════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ════════════════════════════════════════════════════════════════════════════

GEOJSON_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geojson_cache.json")

def fetch_geojson():
    """Try fetching Ontario riding GeoJSON from OpenNorth Represent API."""
    if not HAS_REQUESTS:
        print("  [skip] requests not available for GeoJSON fetch")
        return None

    cache_path = GEOJSON_CACHE
    if os.path.exists(cache_path):
        print("  [cache] Loading GeoJSON from geojson_cache.json")
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"  [cache warn] Could not read cache: {e}")

    print("  Fetching Ontario riding boundaries from OpenNorth Represent API…")
    base = "https://represent.opennorth.ca/boundaries/ontario-electoral-districts-representation-act-2015/"
    try:
        resp = requests.get(base, params={"limit": 200}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        objects = data.get("objects", [])
        if not objects:
            print("  [warn] No boundary objects returned")
            return None

        features = []
        for i, obj in enumerate(objects[:10]):  # Limit for performance
            try:
                boundary_url = obj.get("url", "")
                if not boundary_url:
                    continue
                shape_url = f"https://represent.opennorth.ca{boundary_url}shape"
                sr = requests.get(shape_url, timeout=15)
                sr.raise_for_status()
                shape = sr.json()
                features.append({
                    "type": "Feature",
                    "properties": {"name": obj.get("name", "")},
                    "geometry": shape,
                })
                if (i + 1) % 5 == 0:
                    print(f"    fetched {i+1}/{len(objects)} shapes…")
            except Exception as e:
                print(f"  [warn] Shape fetch failed for {obj.get('name','?')}: {e}")
                continue

        if not features:
            return None

        geojson = {"type": "FeatureCollection", "features": features}
        with open(cache_path, "w") as f:
            json.dump(geojson, f)
        print(f"  [ok] Cached {len(features)} riding shapes to geojson_cache.json")
        return geojson

    except Exception as e:
        print(f"  [fail] GeoJSON fetch failed: {e}")
        return None


def fetch_riding_results():
    """Try fetching 2022 riding-level results from Elections Ontario."""
    if not HAS_REQUESTS:
        return None

    urls = [
        "https://results.elections.on.ca/api/elections/2022/district-results",
        "https://results.elections.on.ca/api/elections?year=2022",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, (list, dict)) and data:
                print(f"  [ok] Riding results from {url}")
                return data
        except Exception as e:
            print(f"  [fail] {url}: {e}")
    return None


# ════════════════════════════════════════════════════════════════════════════
# DERIVED DATASETS
# ════════════════════════════════════════════════════════════════════════════

def build_election_stats():
    """Pre-compute stats for all Ontario elections."""
    stats = []
    for e in ONTARIO_ELECTIONS:
        votes_dict = {p: v for p, (v, s) in e["results"].items()}
        fptp_dict  = {p: s for p, (v, s) in e["results"].items()}
        winner = max(fptp_dict, key=fptp_dict.get)
        g_systems = compute_all_gallagher(e)
        stats.append({
            "year": e["year"],
            "seats": e["seats"],
            "winner": winner,
            "winner_votes": votes_dict[winner],
            "winner_seats": fptp_dict[winner],
            "gallagher": g_systems,
            "wasted": wasted_votes_pct(e),
            "false_majority": is_false_majority(e),
            "votes": votes_dict,
            "fptp_seats": fptp_dict,
            "systems": simulate_all_systems(e),
        })
    return stats


# ════════════════════════════════════════════════════════════════════════════
# CHARTS
# ════════════════════════════════════════════════════════════════════════════

MAIN_PARTIES = ["PC", "Liberal", "NDP"]
PARTY_LABELS = {"PC": "PC", "Liberal": "Liberal", "NDP": "NDP", "Green": "Green"}

ANNOTATIONS_2022 = {1987: "Liberal sweep", 1990: "NDP majority", 1995: "Harris revolution", 2022: "PC supermajority"}


def chart_vote_seat_gap(stats):
    """Dual-line chart per major party: vote % (dashed) vs seat % (solid)."""
    years = [s["year"] for s in stats]
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=["PC — Vote % vs Seat %", "Liberal — Vote % vs Seat %", "NDP — Vote % vs Seat %"],
        vertical_spacing=0.1,
        shared_xaxes=True,
    )
    for row, party in enumerate(MAIN_PARTIES, start=1):
        vote_pcts = []
        seat_pcts = []
        for s in stats:
            total = s["seats"]
            v = s["votes"].get(party, 0)
            sv = s["fptp_seats"].get(party, 0)
            vote_pcts.append(v)
            seat_pcts.append(100.0 * sv / total if total else 0)

        color = pcolor(party)
        # Vote %
        fig.add_trace(go.Scatter(
            x=years, y=vote_pcts, mode="lines+markers", name=f"{party} Vote %",
            line=dict(color=color, width=2, dash="dash"),
            marker=dict(size=6, color=color),
            hovertemplate=f"<b>{party} Vote</b>: %{{y:.1f}}%<extra></extra>",
            legendgroup=party, showlegend=(row == 1),
        ), row=row, col=1)
        # Seat %
        fig.add_trace(go.Scatter(
            x=years, y=seat_pcts, mode="lines+markers", name=f"{party} Seat %",
            line=dict(color=color, width=3),
            fill="tonexty", fillcolor=hex_rgba(color, 0.08),
            marker=dict(size=7, color=color, symbol="square"),
            hovertemplate=f"<b>{party} Seats</b>: %{{y:.1f}}%<extra></extra>",
            legendgroup=party, showlegend=(row == 1),
        ), row=row, col=1)

        # Annotations
        for yr, label in ANNOTATIONS_2022.items():
            if yr in years:
                idx = years.index(yr)
                fig.add_vline(x=yr, line_width=1, line_dash="dot",
                              line_color="rgba(255,255,255,0.15)", row=row, col=1)

    for i in range(1, 4):
        fig.update_yaxes(title_text="% of Total", gridcolor=GRID, zerolinecolor=GRID,
                         tickfont=dict(color="#CDD9E5"), row=i, col=1)
    fig.update_xaxes(gridcolor=GRID, tickfont=dict(color="#CDD9E5"))

    fig.update_layout(
        paper_bgcolor=BG_CARD, plot_bgcolor=BG,
        font=dict(family="Inter, sans-serif", color=TEXT),
        height=750,
        title=dict(text="<b>Vote Share vs Seat Share</b> — FPTP Distortion by Party (1963–2022)", font=dict(size=16, color=TEXT)),
        legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1, font=dict(color=TEXT)),
        margin=dict(t=80, b=55, l=65, r=30),
        hoverlabel=dict(bgcolor="#2D333B", bordercolor=GRID, font=dict(color=TEXT, size=13)),
    )
    # Annotation for major elections
    fig.add_annotation(x=1987, y=1.06, xref="x", yref="paper",
                       text="'87 sweep", showarrow=False,
                       font=dict(color=MUTED, size=10), bgcolor="rgba(0,0,0,0)")
    return to_html(fig)


def chart_gallagher_history(stats):
    """Bar chart: Gallagher index per election, colored by winner."""
    years = [s["year"] for s in stats]
    gi = [s["gallagher"]["FPTP"] for s in stats]
    colors = [pcolor(s["winner"]) for s in stats]
    winner_labels = [s["winner"] for s in stats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=gi,
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Gallagher Index: %{y:.2f}<extra></extra>",
        name="Gallagher Index",
        text=[f"{v:.1f}" for v in gi],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
    ))

    for threshold, label, dash_color in [
        (5,  "Low (5)",      "rgba(61,155,53,0.6)"),
        (10, "Moderate (10)", "rgba(244,131,31,0.6)"),
        (15, "High (15)",     "rgba(208,0,0,0.6)"),
    ]:
        fig.add_hline(y=threshold, line_dash="dash", line_color=dash_color,
                      line_width=1.5,
                      annotation_text=label,
                      annotation_position="right",
                      annotation_font=dict(color=MUTED, size=11))

    # Annotate 2022
    idx_2022 = years.index(2022)
    fig.add_annotation(
        x=2022, y=gi[idx_2022] + 0.8,
        text=f"<b>2022: {gi[idx_2022]:.1f}</b>",
        showarrow=True, arrowhead=2, arrowcolor=MUTED,
        font=dict(color=TEXT, size=12), bgcolor=BG_CARD2, bordercolor=BORDER,
    )

    fig.update_layout(**lay(
        title="<b>Gallagher Disproportionality Index</b> — Ontario Elections 1963–2022",
        height=H,
        xaxis=dict(title="Election Year", tickmode="array", tickvals=years, tickangle=-45),
        yaxis=dict(title="Gallagher Index (higher = more disproportional)"),
        showlegend=False,
    ))
    return to_html(fig)


def chart_wasted_votes(stats):
    """Area/bar chart of wasted votes per election."""
    years = [s["year"] for s in stats]
    wasted = [s["wasted"] for s in stats]
    # Theoretical PR minimum ≈ 2.5% (threshold/2)
    pr_min = 2.5

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=wasted,
        marker_color=[pcolor(s["winner"]) for s in stats],
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Wasted Votes: %{y:.1f}%<extra></extra>",
        name="Wasted Votes (FPTP)",
        text=[f"{v:.0f}%" for v in wasted],
        textposition="outside",
        textfont=dict(color=TEXT, size=10),
    ))
    fig.add_hline(y=pr_min, line_dash="dot", line_color=pcolor("Green"),
                  line_width=2,
                  annotation_text="List PR theoretical minimum (~2.5%)",
                  annotation_position="right",
                  annotation_font=dict(color=pcolor("Green"), size=11))

    fig.update_layout(**lay(
        title="<b>Wasted Votes per Election</b> — Ontario FPTP 1963–2022<br>"
              "<sup>Votes cast for non-winning parties as % of total vote</sup>",
        height=H,
        xaxis=dict(title="Election Year", tickmode="array", tickvals=years, tickangle=-45),
        yaxis=dict(title="Wasted Votes (%)", ticksuffix="%"),
        showlegend=False,
    ))
    return to_html(fig)


def chart_false_majorities(stats):
    """Horizontal bar chart: winner's vote % vs 50% threshold."""
    years = [str(s["year"]) for s in stats]
    vote_pcts = [s["winner_votes"] for s in stats]
    colors = [
        "#D00000" if s["false_majority"] else "#3D9B35"
        for s in stats
    ]
    labels = [
        f"{'FALSE MAJORITY' if s['false_majority'] else 'Legitimate'}" for s in stats
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=vote_pcts, y=years, orientation="h",
        marker_color=colors,
        hovertemplate="<b>%{y}</b><br>Winner's Vote %: %{x:.1f}%<br><extra></extra>",
        text=[f"{v:.1f}%" for v in vote_pcts],
        textposition="inside",
        textfont=dict(color="#ffffff", size=11),
        name="Winner's Vote %",
    ))
    fig.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.5)",
                  line_width=2,
                  annotation_text="50% threshold",
                  annotation_position="top",
                  annotation_font=dict(color=MUTED, size=11))

    false_count = sum(1 for s in stats if s["false_majority"])
    fig.update_layout(**lay(
        title=f"<b>False Majority Elections</b> — Winner's Vote Share vs 50% Threshold<br>"
              f"<sup>{false_count} of {len(stats)} elections had a false majority (red bars)</sup>",
        height=H + 100,
        xaxis=dict(title="Winner's Vote % (red = false majority, green = majority of votes)", ticksuffix="%"),
        yaxis=dict(title="", autorange="reversed"),
        showlegend=False,
    ))
    return to_html(fig), false_count


def chart_seat_comparison_2022(stats):
    """Grouped horizontal bar chart: seats under all systems for 2022."""
    s2022 = next(s for s in stats if s["year"] == 2022)
    systems = s2022["systems"]
    votes_2022 = s2022["votes"]
    total_2022 = s2022["seats"]

    sys_order = ["FPTP", "List PR d'Hondt", "List PR Sainte-Laguë",
                 "Regional PR d'Hondt", "MMP", "AMS"]
    parties = ["PC", "Liberal", "NDP", "Green", "Others"]

    fig = go.Figure()
    for sys_name in sys_order:
        seats_dict = systems.get(sys_name, {})
        seat_vals = [seats_dict.get(p, 0) for p in parties]
        fig.add_trace(go.Bar(
            y=parties, x=seat_vals, orientation="h", name=sys_name,
            hovertemplate=f"<b>{sys_name}</b><br>%{{y}}: %{{x}} seats<extra></extra>",
        ))

    # Reference lines for proportional vote %
    for p in parties:
        v = votes_2022.get(p, 0)
        prop_seats = total_2022 * v / 100
        fig.add_vline(x=prop_seats, line_dash="dot", line_color=hex_rgba(pcolor(p), 0.4),
                      line_width=1.5)

    fig.update_layout(**lay(
        title="<b>2022 Seat Comparison Across Electoral Systems</b><br>"
              "<sup>Dotted lines = proportional seat share based on vote %</sup>",
        height=550,
        barmode="group",
        xaxis=dict(title="Seats"),
        yaxis=dict(title=""),
        legend=dict(**BASE_LAYOUT["legend"]),
    ))
    return to_html(fig)


def chart_gallagher_by_system(stats):
    """Grouped bar chart: Gallagher index by system for each election year."""
    years = [s["year"] for s in stats]
    sys_order = ["FPTP", "List PR d'Hondt", "List PR Sainte-Laguë",
                 "MMP", "AMS", "Regional PR d'Hondt"]
    sys_colors = ["#6B7280", "#003F7F", "#4CC9F0", "#F4831F", "#D00000", "#3D9B35"]

    fig = go.Figure()
    for sys_name, color in zip(sys_order, sys_colors):
        gi_vals = [s["gallagher"].get(sys_name, 0) for s in stats]
        fig.add_trace(go.Bar(
            x=years, y=gi_vals, name=sys_name, marker_color=color,
            hovertemplate=f"<b>{sys_name}</b><br>%{{x}}: %{{y:.2f}}<extra></extra>",
        ))

    fig.update_layout(**lay(
        title="<b>Gallagher Index by Electoral System</b> — All Ontario Elections 1963–2022",
        height=H,
        barmode="group",
        xaxis=dict(title="Election Year", tickmode="array", tickvals=years, tickangle=-45),
        yaxis=dict(title="Gallagher Index"),
        legend=dict(**BASE_LAYOUT["legend"]),
    ))
    return to_html(fig)


def chart_regional_bar(stats):
    """Regional bar chart fallback: 2022 results by region."""
    regions = list(ONTARIO_REGIONS_2022.keys())
    parties = ["PC", "Liberal", "NDP", "Green"]

    fig = go.Figure()
    for party in parties:
        vote_shares = [ONTARIO_REGIONS_2022[r]["votes"].get(party, 0) for r in regions]
        fig.add_trace(go.Bar(
            x=regions, y=vote_shares, name=party,
            marker_color=pcolor(party),
            hovertemplate=f"<b>{party}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(**lay(
        title="<b>2022 Ontario Election — Regional Vote Shares (FPTP)</b>",
        height=H,
        barmode="group",
        xaxis=dict(title="Region", tickangle=-20),
        yaxis=dict(title="Vote Share (%)", ticksuffix="%"),
        legend=dict(**BASE_LAYOUT["legend"]),
    ))
    return to_html(fig)


def chart_regional_pr_bar(stats):
    """Regional PR d'Hondt seat allocation by region."""
    regions = list(ONTARIO_REGIONS_2022.keys())
    parties = ["PC", "Liberal", "NDP", "Green"]

    fig = go.Figure()
    for party in parties:
        seat_vals = []
        for r in regions:
            info = ONTARIO_REGIONS_2022[r]
            alloc = dhondt(info["votes"], info["seats"], threshold=5.0)
            seat_vals.append(alloc.get(party, 0))
        fig.add_trace(go.Bar(
            x=regions, y=seat_vals, name=party,
            marker_color=pcolor(party),
            hovertemplate=f"<b>{party}</b><br>%{{x}}: %{{y}} seats<extra></extra>",
            text=seat_vals, textposition="inside",
            textfont=dict(color="#ffffff", size=10),
        ))

    fig.update_layout(**lay(
        title="<b>2022 Ontario — Regional List PR d'Hondt Seat Allocation</b><br>"
              "<sup>Seats allocated within each region by d'Hondt with 5% threshold</sup>",
        height=H,
        barmode="stack",
        xaxis=dict(title="Region", tickangle=-20),
        yaxis=dict(title="Seats"),
        legend=dict(**BASE_LAYOUT["legend"]),
    ))
    return to_html(fig)


def chart_systems_table_html(stats):
    """Build a styled HTML table for 2022 systems comparison."""
    s2022 = next(s for s in stats if s["year"] == 2022)
    systems_data = s2022["systems"]
    votes_2022 = s2022["votes"]
    total = s2022["seats"]

    sys_order = ["FPTP", "List PR d'Hondt", "List PR Sainte-Laguë",
                 "Regional PR d'Hondt", "MMP", "AMS"]

    rows_html = ""
    for sys_name in sys_order:
        seats = systems_data.get(sys_name, {})
        gi = gallagher_index(votes_2022, seats, total)
        pc_s  = seats.get("PC", 0)
        lib_s = seats.get("Liberal", 0)
        ndp_s = seats.get("NDP", 0)
        grn_s = seats.get("Green", 0)
        pc_maj = "Yes" if pc_s > total / 2 else "No"
        maj_cls = "style='color:#D00000'" if pc_maj == "Yes" else "style='color:#3D9B35'"
        rows_html += f"""
        <tr>
          <td><strong>{sys_name}</strong></td>
          <td style="color:{pcolor('PC')}">{pc_s}</td>
          <td style="color:{pcolor('Liberal')}">{lib_s}</td>
          <td style="color:{pcolor('NDP')}">{ndp_s}</td>
          <td style="color:{pcolor('Green')}">{grn_s}</td>
          <td>{gi:.2f}</td>
          <td {maj_cls}>{pc_maj}</td>
        </tr>"""

    # Reference row: vote %
    rows_html = f"""
        <tr style="border-bottom:2px solid #30363D;color:#8B949E;">
          <td><em>Vote % (reference)</em></td>
          <td style="color:{pcolor('PC')}">{votes_2022.get('PC',0):.1f}%</td>
          <td style="color:{pcolor('Liberal')}">{votes_2022.get('Liberal',0):.1f}%</td>
          <td style="color:{pcolor('NDP')}">{votes_2022.get('NDP',0):.1f}%</td>
          <td style="color:{pcolor('Green')}">{votes_2022.get('Green',0):.1f}%</td>
          <td>—</td>
          <td>—</td>
        </tr>""" + rows_html

    return f"""
    <div class="table-responsive">
      <table class="summary-table">
        <thead>
          <tr>
            <th>System</th>
            <th style="color:{pcolor('PC')}">PC Seats</th>
            <th style="color:{pcolor('Liberal')}">Liberal Seats</th>
            <th style="color:{pcolor('NDP')}">NDP Seats</th>
            <th style="color:{pcolor('Green')}">Green Seats</th>
            <th>Gallagher Index</th>
            <th>PC Majority?</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>"""


def chart_historical_govt(stats):
    """Stacked bar: seat composition FPTP vs MMP for all elections."""
    years = [s["year"] for s in stats]
    parties = ["PC", "Liberal", "NDP", "Green", "Others"]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["FPTP — Actual Seat Composition", "MMP — Simulated Seat Composition"],
        shared_xaxes=True,
        vertical_spacing=0.12,
    )

    for row, sys_name in enumerate(["FPTP", "MMP"], start=1):
        for party in parties:
            seat_vals = []
            for s in stats:
                seat_dict = s["systems"].get(sys_name, {})
                seat_vals.append(seat_dict.get(party, 0))
            fig.add_trace(go.Bar(
                x=years, y=seat_vals, name=party,
                marker_color=pcolor(party),
                hovertemplate=f"<b>{party}</b> ({sys_name}): %{{y}} seats<extra></extra>",
                legendgroup=party,
                showlegend=(row == 1),
            ), row=row, col=1)

        # 50% majority line
        majority_lines = [s["seats"] / 2 for s in stats]
        fig.add_trace(go.Scatter(
            x=years, y=majority_lines, mode="lines",
            line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dot"),
            name="Majority threshold", showlegend=(row == 1),
            hoverinfo="skip",
        ), row=row, col=1)

    fig.update_layout(
        paper_bgcolor=BG_CARD, plot_bgcolor=BG,
        font=dict(family="Inter, sans-serif", color=TEXT),
        height=700,
        barmode="stack",
        title=dict(text="<b>60 Years Reimagined</b> — FPTP vs MMP Seat Composition (1963–2022)",
                   font=dict(size=16, color=TEXT)),
        legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1,
                    font=dict(color=TEXT)),
        margin=dict(t=80, b=55, l=65, r=30),
        hoverlabel=dict(bgcolor="#2D333B", bordercolor=GRID, font=dict(color=TEXT)),
    )
    fig.update_xaxes(gridcolor=GRID, tickfont=dict(color="#CDD9E5"),
                     tickmode="array", tickvals=years, tickangle=-45)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color="#CDD9E5"),
                     title_text="Seats")
    return to_html(fig)


def chart_federal_ontario_gallagher():
    """Gallagher index for federal elections in Ontario."""
    years = []
    gi_vals = []
    colors = []

    for e in FEDERAL_ONTARIO:
        votes_dict = {p: v for p, (v, s) in e["results"].items()}
        seats_dict  = {p: s for p, (v, s) in e["results"].items()}
        gi = gallagher_index(votes_dict, seats_dict, e["seats"])
        years.append(e["year"])
        gi_vals.append(gi)
        winner = max(seats_dict, key=seats_dict.get)
        colors.append(pcolor(winner))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=gi_vals, marker_color=colors,
        hovertemplate="<b>Federal %{x}</b><br>Gallagher: %{y:.2f}<extra></extra>",
        text=[f"{v:.1f}" for v in gi_vals],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
    ))
    for y, label, col in [(5, "Low", "rgba(61,155,53,0.6)"),
                           (10, "Moderate", "rgba(244,131,31,0.6)"),
                           (15, "High", "rgba(208,0,0,0.6)")]:
        fig.add_hline(y=y, line_dash="dash", line_color=col, line_width=1.5,
                      annotation_text=label, annotation_position="right",
                      annotation_font=dict(color=MUTED, size=10))

    fig.update_layout(**lay(
        title="<b>Federal Elections in Ontario</b> — Gallagher Disproportionality Index 2000–2021",
        height=H,
        xaxis=dict(title="Election Year", tickmode="array", tickvals=years),
        yaxis=dict(title="Gallagher Index"),
        showlegend=False,
    ))
    return to_html(fig)


def chart_federal_vote_seat():
    """Vote % vs Seat % for Liberal and Conservative in federal Ontario."""
    parties_fed = [
        ("Liberal",      "#D00000"),
        ("Conservative", "#003F7F"),
        ("Alliance",     "#6B7280"),
    ]

    fig = go.Figure()
    for party, color in parties_fed:
        years_list, vote_pcts, seat_pcts = [], [], []
        for e in FEDERAL_ONTARIO:
            if party in e["results"]:
                v, s = e["results"][party]
                total = e["seats"]
                years_list.append(e["year"])
                vote_pcts.append(v)
                seat_pcts.append(100.0 * s / total)

        if not years_list:
            continue
        fig.add_trace(go.Scatter(
            x=years_list, y=vote_pcts, mode="lines+markers", name=f"{party} Vote %",
            line=dict(color=color, width=2, dash="dash"),
            marker=dict(size=6),
            hovertemplate=f"<b>{party} Vote</b>: %{{y:.1f}}%<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=years_list, y=seat_pcts, mode="lines+markers", name=f"{party} Seat %",
            line=dict(color=color, width=3),
            fill="tonexty", fillcolor=hex_rgba(color, 0.06),
            marker=dict(size=7, symbol="square"),
            hovertemplate=f"<b>{party} Seats</b>: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(**lay(
        title="<b>Federal Ontario — Vote % vs Seat %</b> — Liberal & Conservative 2000–2021",
        height=H,
        xaxis=dict(title="Federal Election Year"),
        yaxis=dict(title="Percentage (%)", ticksuffix="%"),
        legend=dict(**BASE_LAYOUT["legend"]),
    ))
    return to_html(fig)


def chart_pr_systems_explainer():
    """Radar/spider chart comparing 6 electoral systems on 6 dimensions."""
    # Curated scores 0-100
    systems_scores = {
        "FPTP": {
            "Proportionality": 15,
            "Local Representation": 95,
            "Simplicity": 95,
            "Govt Stability": 85,
            "Minority Voice": 20,
            "Voter Choice": 30,
        },
        "List PR d'Hondt": {
            "Proportionality": 85,
            "Local Representation": 20,
            "Simplicity": 65,
            "Govt Stability": 55,
            "Minority Voice": 85,
            "Voter Choice": 70,
        },
        "List PR Sainte-Laguë": {
            "Proportionality": 90,
            "Local Representation": 20,
            "Simplicity": 60,
            "Govt Stability": 50,
            "Minority Voice": 90,
            "Voter Choice": 70,
        },
        "Regional PR d'Hondt": {
            "Proportionality": 75,
            "Local Representation": 60,
            "Simplicity": 60,
            "Govt Stability": 60,
            "Minority Voice": 70,
            "Voter Choice": 65,
        },
        "MMP": {
            "Proportionality": 80,
            "Local Representation": 70,
            "Simplicity": 50,
            "Govt Stability": 60,
            "Minority Voice": 80,
            "Voter Choice": 75,
        },
        "AMS": {
            "Proportionality": 65,
            "Local Representation": 80,
            "Simplicity": 55,
            "Govt Stability": 70,
            "Minority Voice": 65,
            "Voter Choice": 65,
        },
    }

    categories = ["Proportionality", "Local Representation", "Simplicity",
                  "Govt Stability", "Minority Voice", "Voter Choice"]
    sys_colors = {
        "FPTP": "#6B7280",
        "List PR d'Hondt": "#003F7F",
        "List PR Sainte-Laguë": "#4CC9F0",
        "Regional PR d'Hondt": "#3D9B35",
        "MMP": "#F4831F",
        "AMS": "#D00000",
    }

    fig = go.Figure()
    for sys_name, scores in systems_scores.items():
        vals = [scores[c] for c in categories]
        vals_closed = vals + [vals[0]]
        cats_closed = categories + [categories[0]]
        color = sys_colors[sys_name]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed, theta=cats_closed,
            fill="toself", fillcolor=hex_rgba(color, 0.1),
            line=dict(color=color, width=2),
            name=sys_name,
            hovertemplate=f"<b>{sys_name}</b><br>%{{theta}}: %{{r}}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor=BG_CARD, plot_bgcolor=BG,
        polar=dict(
            bgcolor=BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=GRID, tickfont=dict(color=MUTED, size=10),
                linecolor=GRID,
            ),
            angularaxis=dict(
                gridcolor=GRID, linecolor=GRID,
                tickfont=dict(color=TEXT, size=12),
            ),
        ),
        font=dict(family="Inter, sans-serif", color=TEXT),
        title=dict(text="<b>Electoral System Scorecard</b> — Curated Comparative Dimensions",
                   font=dict(size=16, color=TEXT)),
        legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1,
                    font=dict(color=TEXT)),
        height=580,
        margin=dict(t=80, b=55, l=65, r=65),
        hoverlabel=dict(bgcolor="#2D333B", bordercolor=GRID, font=dict(color=TEXT)),
    )
    return to_html(fig)


# ════════════════════════════════════════════════════════════════════════════
# RIDING-LEVEL CHARTS
# ════════════════════════════════════════════════════════════════════════════

def chart_population_disparity(results, populations, geojson):
    """Histogram + box plot of riding populations by type."""
    ridings = list(populations.keys())
    pops    = [populations[r] for r in ridings]
    types   = [classify_riding(p) for p in pops]

    type_order = ["Remote/Northern", "Rural / Small City", "Suburban", "Urban / High-Growth"]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Population Distribution by Riding Type",
                        "Population Spread by Riding Type"],
        column_widths=[0.6, 0.4],
    )

    # ── Left: histogram coloured by riding type ──────────────
    bin_size = 10000
    for rt in type_order:
        color = RIDING_TYPE_COLORS[rt]
        rt_pops = [p for p, t in zip(pops, types) if t == rt]
        if not rt_pops:
            continue
        fig.add_trace(go.Histogram(
            x=rt_pops,
            name=rt,
            marker_color=color,
            opacity=0.75,
            xbins=dict(start=0, end=max(pops) + bin_size, size=bin_size),
            hovertemplate=f"<b>{rt}</b><br>Population: %{{x}}<br>Count: %{{y}}<extra></extra>",
        ), row=1, col=1)

    mean_pop   = sum(pops) / len(pops)
    median_pop = sorted(pops)[len(pops) // 2]
    fig.add_vline(x=mean_pop,   line_dash="dash",  line_color="#00F5D4",
                  line_width=1.5, row=1, col=1,
                  annotation_text=f"Mean {mean_pop/1000:.0f}k",
                  annotation_font=dict(color="#00F5D4", size=11))
    fig.add_vline(x=median_pop, line_dash="dot",   line_color="#FFD60A",
                  line_width=1.5, row=1, col=1,
                  annotation_text=f"Median {median_pop/1000:.0f}k",
                  annotation_font=dict(color="#FFD60A", size=11),
                  annotation_position="bottom right")

    # ── Right: box plots ──────────────────────────────────────
    for rt in type_order:
        color  = RIDING_TYPE_COLORS[rt]
        rt_pops = [p for p, t in zip(pops, types) if t == rt]
        if not rt_pops:
            continue
        fig.add_trace(go.Box(
            y=rt_pops,
            name=rt,
            marker_color=color,
            line_color=color,
            fillcolor=hex_rgba(color, 0.2),
            hovertemplate=f"<b>{rt}</b><br>Population: %{{y}}<extra></extra>",
            showlegend=False,
        ), row=1, col=2)

    fig.update_layout(
        paper_bgcolor=BG_CARD, plot_bgcolor=BG,
        font=dict(family="Inter, sans-serif", color=TEXT),
        height=480,
        barmode="stack",
        title=dict(text="<b>Riding Population Inequality — How Much Is Your Vote Worth?</b>",
                   font=dict(size=16, color=TEXT)),
        legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1,
                    font=dict(color=TEXT)),
        margin=dict(t=80, b=55, l=65, r=30),
        hoverlabel=dict(bgcolor="#2D333B", bordercolor=GRID, font=dict(color=TEXT, size=13)),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color="#CDD9E5"))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color="#CDD9E5"))
    fig.update_xaxes(title_text="Population", row=1, col=1)
    fig.update_yaxes(title_text="Number of Ridings", row=1, col=1)
    fig.update_yaxes(title_text="Population", row=1, col=2)
    return to_html(fig)


def chart_votes_per_seat(results):
    """Horizontal bar: actual party votes received ÷ seats won per party in 2022.

    Uses province-wide vote share from the curated ONTARIO_ELECTIONS data
    (not total turnout in won ridings, which was the previous incorrect approach).
    """
    # Total valid votes cast across all 124 ridings (from riding-level data)
    total_votes = sum(info.get("votes", 0) for info in results.values())

    # Province-wide vote share + seats from curated 2022 data
    election_2022 = next(e for e in ONTARIO_ELECTIONS if e["year"] == 2022)

    rows = []
    for party, (vote_pct, seats) in election_2022["results"].items():
        if seats == 0:
            continue
        party_votes_received = (vote_pct / 100) * total_votes
        vps = party_votes_received / seats
        rows.append((party, vps, seats, vote_pct))

    # Sort descending — most inefficient (highest cost per seat) at top
    rows.sort(key=lambda r: r[1], reverse=True)

    parties_sorted  = [r[0] for r in rows]
    vps_sorted      = [r[1] for r in rows]
    colors_sorted   = [pcolor(p) for p in parties_sorted]
    annotations_txt = [f"{r[3]:.1f}% of votes → {r[2]} seat{'s' if r[2]!=1 else ''}" for r in rows]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=parties_sorted,
        x=vps_sorted,
        orientation="h",
        marker_color=colors_sorted,
        text=annotations_txt,
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="<b>%{y}</b><br>Votes received per seat won: %{x:,.0f}<extra></extra>",
        name="Votes per seat",
    ))

    # Reference line at the "perfectly proportional" cost
    # (total votes / total seats = what each seat costs if equal)
    fair_cost = total_votes / election_2022["seats"]
    fig.add_vline(
        x=fair_cost,
        line_dash="dot", line_color="rgba(255,255,255,0.35)",
        annotation_text=f"Proportional ideal: {fair_cost:,.0f}",
        annotation_position="top",
        annotation_font=dict(color=MUTED, size=11),
    )

    fig.update_layout(**lay(
        title="<b>Cost of a Seat — Votes Received per Seat Won (2022)</b><br>"
              "<sup>Party's province-wide votes ÷ seats won. "
              "The dashed line shows the cost under perfect proportionality.</sup>",
        height=H,
        xaxis=dict(title="Votes Received per Seat Won", tickformat=","),
        yaxis=dict(title=""),
        showlegend=False,
    ))
    return to_html(fig)


def chart_population_seat_bias(results, populations):
    """Scatter: riding population vs votes cast, coloured by winning party."""
    fig = go.Figure()

    parties_in_data = sorted(set(
        info.get("party", "Others") for info in results.values()
    ))

    all_pops   = []
    all_votes  = []
    all_colors = []

    for party in parties_in_data:
        xs, ys = [], []
        for riding, info in results.items():
            if info.get("party", "Others") != party:
                continue
            pop   = populations.get(riding)
            votes = info.get("votes", 0)
            if pop is None:
                continue
            xs.append(pop)
            ys.append(votes)
            all_pops.append(pop)
            all_votes.append(votes)
            all_colors.append(pcolor(party))

        if not xs:
            continue
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers",
            name=party,
            marker=dict(color=pcolor(party), size=8, opacity=0.75,
                        line=dict(color=BG_CARD, width=0.5)),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Population: %{x:,}<br>"
                "Votes cast: %{y:,}<extra></extra>"
            ),
            text=[r for r, info in results.items()
                  if info.get("party", "Others") == party
                  and populations.get(r) is not None],
        ))

    # Linear trend line
    if len(all_pops) >= 2:
        n    = len(all_pops)
        xbar = sum(all_pops) / n
        ybar = sum(all_votes) / n
        num  = sum((x - xbar) * (y - ybar) for x, y in zip(all_pops, all_votes))
        den  = sum((x - xbar) ** 2 for x in all_pops)
        slope    = num / den if den else 0
        intercept = ybar - slope * xbar
        x_min, x_max = min(all_pops), max(all_pops)
        fig.add_trace(go.Scatter(
            x=[x_min, x_max],
            y=[slope * x_min + intercept, slope * x_max + intercept],
            mode="lines",
            name="Trend",
            line=dict(color="#00F5D4", width=2, dash="dash"),
            hoverinfo="skip",
        ))

    fig.update_layout(**lay(
        title="<b>Population vs Votes Cast by Riding — 2022</b><br>"
              "<sup>Each point = one riding. Colour = winning party.</sup>",
        height=H,
        xaxis=dict(title="Riding Population (2016 Census)", tickformat=","),
        yaxis=dict(title="Total Valid Votes Cast", tickformat=","),
        legend=dict(**BASE_LAYOUT["legend"]),
    ))
    return to_html(fig)


CHOROPLETH_COLORSCALE = [
    [0/4,           "#003F7F"],
    [1/4 - 0.0001,  "#003F7F"],  # PC - blue
    [1/4,           "#F4831F"],
    [2/4 - 0.0001,  "#F4831F"],  # NDP - orange
    [2/4,           "#D00000"],
    [3/4 - 0.0001,  "#D00000"],  # Liberal - red
    [3/4,           "#3D9B35"],
    [4/4,           "#3D9B35"],  # Green - green (also Others/Ind)
]

PARTY_Z = {"PC": 0, "NDP": 1, "Liberal": 2, "Green": 3, "Independent": 3, "Others": 3}


def chart_map_choropleth(results, geojson):
    """Choropleth map of 2022 Ontario election results by riding."""
    locations = []
    z_vals    = []

    for feature in geojson.get("features", []):
        name = feature["properties"].get("name", "")
        info = results.get(name)
        if info is None:
            continue
        party = info.get("party", "Others")
        z = PARTY_Z.get(party, 3) / 4.0
        locations.append(name)
        z_vals.append(z)

    fig = go.Figure()
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=locations,
        z=z_vals,
        featureidkey="properties.name",
        colorscale=CHOROPLETH_COLORSCALE,
        zmin=0,
        zmax=1,
        showscale=False,
        marker=dict(opacity=0.85, line=dict(width=0.5, color="#30363D")),
        hovertemplate=(
            "<b>%{location}</b><br>"
            "Winner: %{customdata[0]}<extra></extra>"
        ),
        customdata=[[results[loc]["party"]] for loc in locations],
        name="",
    ))

    # Manual legend via invisible scatter traces
    legend_parties = [("PC", "#003F7F"), ("NDP", "#F4831F"),
                      ("Liberal", "#D00000"), ("Green", "#3D9B35")]
    for party_name, color in legend_parties:
        fig.add_trace(go.Scattermapbox(
            lat=[None], lon=[None],
            mode="markers",
            marker=dict(size=12, color=color),
            name=party_name,
            showlegend=True,
        ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=49.5, lon=-84.5),
            zoom=4.2,
        ),
        paper_bgcolor=BG_CARD,
        font=dict(family="Inter, sans-serif", color=TEXT),
        height=600,
        title=dict(
            text="<b>2022 Ontario Election — FPTP Results by Riding (Geographic Map)</b>",
            font=dict(size=16, color=TEXT),
        ),
        legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1,
                    font=dict(color=TEXT)),
        margin=dict(t=70, b=10, l=10, r=10),
    )
    return to_html(fig)


def chart_map_bubble(results, geojson):
    """Bubble map — 'Land Doesn't Vote, People Do' visualization."""
    centroids = get_riding_centroids(geojson)

    # Group ridings by party
    party_data = {}
    for riding, info in results.items():
        party = info.get("party", "Others")
        votes = info.get("votes", 0)
        centroid = centroids.get(riding)
        if centroid is None:
            continue
        if party not in party_data:
            party_data[party] = {"lons": [], "lats": [], "sizes": [], "names": [], "votes": []}
        lon, lat = centroid
        size = math.sqrt(votes) / 12
        party_data[party]["lons"].append(lon)
        party_data[party]["lats"].append(lat)
        party_data[party]["sizes"].append(size)
        party_data[party]["names"].append(riding)
        party_data[party]["votes"].append(votes)

    fig = go.Figure()
    for party, data in sorted(party_data.items()):
        color = pcolor(party)
        fig.add_trace(go.Scattermapbox(
            lat=data["lats"],
            lon=data["lons"],
            mode="markers",
            name=party,
            marker=dict(
                size=data["sizes"],
                color=color,
                opacity=0.75,
                sizemode="diameter",
            ),
            text=data["names"],
            customdata=list(zip(data["votes"], [party] * len(data["votes"]))),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Party: %{customdata[1]}<br>"
                "Votes: %{customdata[0]:,}<extra></extra>"
            ),
        ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=49.5, lon=-84.5),
            zoom=4.2,
        ),
        paper_bgcolor=BG_CARD,
        font=dict(family="Inter, sans-serif", color=TEXT),
        height=600,
        title=dict(
            text="<b>2022 Ontario Election — Votes Cast per Riding (Bubble = Votes, Colour = Winner)</b>",
            font=dict(size=16, color=TEXT),
        ),
        legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor=GRID, borderwidth=1,
                    font=dict(color=TEXT)),
        margin=dict(t=70, b=10, l=10, r=10),
        annotations=[dict(
            text="Each bubble's area is proportional to votes cast. Small bubbles in large "
                 "geographic areas show rural over-representation.",
            x=0.01, y=0.01, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color=MUTED),
            bgcolor="rgba(13,17,23,0.7)",
            bordercolor=BORDER,
            borderwidth=1,
            borderpad=6,
        )],
    )
    return to_html(fig)


# ════════════════════════════════════════════════════════════════════════════
# HTML ASSEMBLY
# ════════════════════════════════════════════════════════════════════════════

PLACEHOLDER_DIV = ("<div style='padding:40px;color:#8B949E;text-align:center;"
                   "font-size:14px'>Chart unavailable — data files not found.</div>")


def _riding_maps_section(riding_charts):
    """Build the Ontario Riding Maps chapter HTML."""
    rc = riding_charts or {}
    choropleth_html = rc.get("map_choropleth", PLACEHOLDER_DIV)
    bubble_html     = rc.get("map_bubble",     PLACEHOLDER_DIV)

    return f"""
<section id="riding-maps" class="chapter-section">
  <div class="chapter-hero">
    <h2>Ontario Riding Maps &middot; 2022</h2>
    <p>Two complementary views of the same election result: the geographic view (where land
    area dominates the picture) and the democratic view (where each bubble represents actual
    votes cast). Together they reveal a core structural tension in FPTP geography.</p>
  </div>
</section>

<section id="riding-maps-choropleth" class="rpt-section">
  <div class="sec-hdr">
    <div>
      <div class="chapter-label">Ontario Riding Maps &middot; 2022</div>
      <h2 class="sec-title">The Geographic View — land area dominates</h2>
    </div>
    <span class="src-badge">Source: Elections Ontario 2022</span>
  </div>
  <p class="sec-desc">
    Each riding is shaded by its winning party. Because many rural and northern ridings cover
    enormous geographic areas, the PC party (which dominates outside Toronto and Northern Ontario)
    appears to dominate the map — despite winning only 40.8% of the popular vote.
  </p>
  <div class="chart-card" style="height:620px;overflow:hidden">{choropleth_html}</div>
</section>
<div class="divider"></div>

<section id="riding-maps-bubble" class="rpt-section">
  <div class="sec-hdr">
    <div>
      <div class="chapter-label">Ontario Riding Maps &middot; 2022</div>
      <h2 class="sec-title">The Democratic View — each bubble = votes cast</h2>
    </div>
    <span class="src-badge">Source: Elections Ontario 2022</span>
  </div>
  <blockquote style="background:rgba(0,245,212,0.06);border-left:3px solid #00F5D4;
    padding:16px 20px;border-radius:0 8px 8px 0;font-size:18px;font-style:italic;
    color:#E6EDF3;margin:20px 0;">
    Land Doesn&rsquo;t Vote &mdash; People Do
  </blockquote>
  <p class="sec-desc">
    Bubble size is proportional to total valid votes cast in that riding. Small bubbles
    sitting inside large geographic areas (Northern and rural Ontario) reveal that those
    ridings return exactly one MPP despite far fewer voters than dense urban ridings — giving
    each ballot disproportionate weight.
  </p>
  <div class="chart-card" style="height:620px;overflow:hidden">{bubble_html}</div>
</section>
<div class="divider"></div>"""


def _population_disparity_section(riding_charts):
    """Build the Riding Population Disparities chapter HTML."""
    rc = riding_charts or {}
    pop_disp_html = rc.get("population_disparity", PLACEHOLDER_DIV)
    vps_html      = rc.get("votes_per_seat",       PLACEHOLDER_DIV)
    scatter_html  = rc.get("population_seat_bias",  PLACEHOLDER_DIV)

    return f"""
<section id="population-disparity" class="chapter-section">
  <div class="chapter-hero">
    <h2>Riding Population Disparities</h2>
    <p>Every riding returns exactly one MPP regardless of population size. A riding with
    60,000 residents has the same legislative representation as one with 180,000. This chapter
    quantifies how unequal the value of a vote is across Ontario&rsquo;s 124 ridings.</p>
  </div>
</section>

{make_section("population-disparity-chart","Population Disparities",
  "Riding Population Inequality — How Much Is Your Vote Worth?",
  "Each bar represents ridings grouped by population bracket and classified by type: "
  "Remote/Northern (&lt;80k), Rural/Small City (80k–110k), Suburban (110k–125k), and "
  "Urban/High-Growth (&gt;125k). The vertical lines mark the mean and median riding population. "
  "Because every riding returns one MPP, a voter in a smaller riding has proportionally "
  "more legislative power.",
  pop_disp_html,
  "Elections Ontario · Statistics Canada 2016 Census")}
<div class="divider"></div>

{make_section("votes-per-seat","Population Disparities",
  "Cost of a Seat — How Many Votes Did It Take? (2022)",
  "Total valid votes cast in ridings won by each party, divided by seats won. This &ldquo;cost "
  "per seat&rdquo; reveals that under FPTP, a vote for the party that wins densely contested "
  "ridings is far less efficient than a vote for the party that sweeps low-competition ridings. "
  "Parties winning geographically concentrated or low-turnout ridings pay far fewer votes "
  "per seat.",
  vps_html,
  "Elections Ontario · Statistics Canada 2016 Census")}
<div class="divider"></div>

{make_section("population-seat-bias","Population Disparities",
  "Population vs Votes Cast by Riding — 2022",
  "Each point is one riding. The x-axis is total riding population (2016 Census) and the "
  "y-axis is total valid votes cast in 2022. The trend line confirms that smaller-population "
  "ridings generally have fewer votes — yet each still returns one MPP, giving those voters "
  "disproportionate legislative weight.",
  scatter_html,
  "Elections Ontario · Statistics Canada 2016 Census")}
<div class="divider"></div>"""


def make_section(sid, chapter, title, desc, chart_html, source=""):
    badge = (f'<span class="src-badge">Source: {source}</span>' if source else "")
    return f"""
<section id="{sid}" class="rpt-section">
  <div class="sec-hdr">
    <div>
      <div class="chapter-label">{chapter}</div>
      <h2 class="sec-title">{title}</h2>
    </div>
    {badge}
  </div>
  <p class="sec-desc">{desc}</p>
  <div class="chart-card">{chart_html}</div>
</section>"""


def build_html(charts, stats, false_count, systems_table_html, riding_charts=None):
    today = datetime.now().strftime("%B %d, %Y")
    gen_year = datetime.now().year

    # Gallagher 2022 FPTP
    s2022 = next(s for s in stats if s["year"] == 2022)
    gi_2022 = s2022["gallagher"]["FPTP"]
    wasted_2022 = s2022["wasted"]

    nav_items = [
        ("hero",              "Overview"),
        ("the-problem",       "Ch.1 · The Problem"),
        ("vote-seat-gap",     "Vote vs Seat Gap"),
        ("gallagher-history", "Gallagher History"),
        ("wasted-votes",      "Wasted Votes"),
        ("false-majorities",  "False Majorities"),
        ("election-2022",     "Ch.2 · 2022 Election"),
        ("map-fptp",          "2022 FPTP Map"),
        ("seat-comparison",   "Seat Comparison"),
        ("systems-table",     "Systems Table"),
        ("alt-systems",       "Ch.3 · Alt. Systems"),
        ("systems-explainer", "System Explainer"),
        ("map-regional-pr",   "Regional PR"),
        ("gallagher-by-sys",  "Gallagher by System"),
        ("reimagined",        "Ch.4 · 60 Years"),
        ("historical-govt",   "Historical Govts"),
        ("federal",           "Ch.5 · Federal"),
        ("federal-vote-seat", "Federal Vote/Seat"),
        ("federal-gallagher", "Federal Gallagher"),
        ("scorecard",         "Ch.6 · Scorecard"),
        ("pr-explainer",      "PR Scorecard"),
        ("population-disparity", "Population Disparities"),
        ("methodology",       "Ch.7 · Methodology"),
    ]
    nav_html = "\n".join(
        f'    <a href="#{sid}" class="nav-link">{lbl}</a>'
        for sid, lbl in nav_items
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ontario Electoral Reform Analysis</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js" charset="utf-8"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0D1117;--bg-card:#161B22;--bg-card2:#1C2128;
  --border:#30363D;--text:#E6EDF3;--muted:#8B949E;
  --pc:#003F7F;--lib:#D00000;--ndp:#F4831F;--grn:#3D9B35;
  --font:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);font-family:var(--font);
  font-size:15px;line-height:1.6;display:flex;min-height:100vh}}

/* ── Sidebar ── */
#sidebar{{width:230px;min-width:230px;background:var(--bg-card);
  border-right:1px solid var(--border);height:100vh;position:sticky;
  top:0;overflow-y:auto;padding:24px 0;flex-shrink:0;
  scrollbar-width:thin;scrollbar-color:var(--border) transparent}}
.sb-title{{font-size:11px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);padding:0 20px 14px}}
.nav-link{{display:block;padding:7px 20px;color:var(--muted);
  text-decoration:none;font-size:13px;
  border-left:2px solid transparent;transition:all .15s}}
.nav-link:hover{{color:var(--text);background:rgba(255,255,255,.04);
  border-left-color:var(--ndp)}}
.nav-link.active{{color:var(--ndp);border-left-color:var(--ndp);
  background:rgba(244,131,31,.06);font-weight:500}}

/* ── Main ── */
#main{{flex:1;overflow-y:auto;height:100vh}}

/* ── Hero ── */
.hero{{background:linear-gradient(135deg,#0D1117 0%,#161B22 60%,#0D1117 100%);
  border-bottom:1px solid var(--border);padding:60px 48px 44px;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 900px 500px at 75% 50%,rgba(244,131,31,.05) 0%,transparent 70%),
             radial-gradient(ellipse 600px 400px at 15% 90%,rgba(208,0,0,.04) 0%,transparent 70%);
  pointer-events:none}}
.hero-eyebrow{{font-size:12px;font-weight:600;letter-spacing:.15em;
  text-transform:uppercase;color:var(--ndp);margin-bottom:14px}}
.hero h1{{font-size:44px;font-weight:700;letter-spacing:-.5px;
  line-height:1.15;margin-bottom:16px}}
.hero h1 span{{background:linear-gradient(90deg,var(--pc),var(--ndp),var(--grn));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.hero-sub{{font-size:16px;color:var(--muted);max-width:700px;margin-bottom:40px;line-height:1.75}}
.hero-sub strong{{color:var(--text)}}

/* ── Hero stat cards ── */
.hero-stats{{display:flex;gap:18px;flex-wrap:wrap}}
.hstat{{background:var(--bg-card2);border:1px solid var(--border);
  border-radius:10px;padding:22px 28px;flex:1;min-width:200px}}
.hstat-num{{font-size:36px;font-weight:700;letter-spacing:-1px;margin-bottom:4px}}
.hstat-label{{font-size:13px;color:var(--muted)}}

/* ── Content ── */
.content{{padding:0 48px 80px;max-width:1320px}}

/* ── Sections ── */
.rpt-section{{padding:52px 0 0}}
.sec-hdr{{display:flex;align-items:flex-start;gap:14px;margin-bottom:8px;
  justify-content:space-between;flex-wrap:wrap}}
.chapter-label{{font-size:11px;font-weight:600;letter-spacing:.12em;
  text-transform:uppercase;color:var(--ndp);margin-bottom:4px}}
.sec-title{{font-size:24px;font-weight:700;letter-spacing:-.3px}}
.src-badge{{font-size:11px;font-weight:500;color:var(--muted);
  background:var(--bg-card2);border:1px solid var(--border);
  border-radius:20px;padding:3px 10px;white-space:nowrap;margin-top:6px}}
.sec-desc{{color:var(--muted);font-size:14px;max-width:820px;
  margin-bottom:20px;line-height:1.75}}
.chart-card{{background:var(--bg-card);border:1px solid var(--border);
  border-radius:12px;padding:8px;overflow:hidden}}
.divider{{height:1px;background:var(--border);margin-top:52px}}

/* ── Chapter headers ── */
.chapter-section{{padding:52px 0 0}}
.chapter-hero{{background:var(--bg-card2);border:1px solid var(--border);
  border-left:4px solid var(--ndp);border-radius:0 10px 10px 0;
  padding:20px 28px;margin-bottom:0}}
.chapter-hero h2{{font-size:20px;font-weight:700;margin-bottom:6px}}
.chapter-hero p{{color:var(--muted);font-size:13px;max-width:700px}}

/* ── Summary Table ── */
.table-responsive{{background:var(--bg-card);border:1px solid var(--border);
  border-radius:12px;overflow-x:auto}}
.summary-table{{width:100%;border-collapse:collapse;font-size:13px}}
.summary-table th{{background:var(--bg-card2);color:var(--muted);
  font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  padding:12px 16px;text-align:left;border-bottom:1px solid var(--border)}}
.summary-table td{{padding:11px 16px;border-bottom:1px solid rgba(48,54,61,.4);
  font-variant-numeric:tabular-nums}}
.summary-table tr:hover td{{background:rgba(255,255,255,.02)}}
.summary-table td:first-child{{font-weight:500;color:var(--text)}}

/* ── Methodology ── */
.meth-box{{background:var(--bg-card);border:1px solid var(--border);
  border-radius:12px;padding:32px}}
.meth-box h3{{font-size:15px;font-weight:600;margin-bottom:8px;color:var(--text)}}
.meth-box p,.meth-box li{{color:var(--muted);font-size:13px;line-height:1.85}}
.meth-box ul{{padding-left:20px;margin-top:6px}}
.meth-box p+h3,.meth-box ul+h3{{margin-top:24px}}
.src-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));
  gap:14px;margin-top:14px}}
.src-item{{background:var(--bg-card2);border:1px solid var(--border);
  border-radius:8px;padding:14px 16px}}
.src-name{{font-weight:600;font-size:13px;color:var(--text);margin-bottom:4px}}
.src-detail{{font-size:12px;color:var(--muted);line-height:1.7}}

/* ── Footer ── */
.rpt-footer{{border-top:1px solid var(--border);margin-top:64px;
  padding:22px 48px;color:var(--muted);font-size:12px;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}

/* ── Scrollbar ── */
::-webkit-scrollbar{{width:6px;height:6px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}

/* ── Mobile / collapsible nav ── */
#nav-toggle{{display:none;position:fixed;top:14px;left:14px;z-index:1001;
  background:var(--bg-card);border:1px solid var(--border);border-radius:8px;
  padding:8px 13px;color:var(--text);font-size:18px;line-height:1;
  cursor:pointer;transition:background .15s}}
#nav-toggle:hover{{background:var(--border)}}
#sidebar-overlay{{display:none;position:fixed;inset:0;
  background:rgba(0,0,0,.55);z-index:999;backdrop-filter:blur(2px)}}
#sidebar-overlay.open{{display:block}}

@media(max-width:768px){{
  body{{display:block}}
  #nav-toggle{{display:block}}
  #sidebar{{position:fixed;top:0;left:-250px;height:100vh;z-index:1000;
    width:230px;transition:left .25s ease;box-shadow:none}}
  #sidebar.open{{left:0;box-shadow:4px 0 24px rgba(0,0,0,.6)}}
  #main{{height:auto;overflow-y:unset}}
  .hero{{padding:64px 20px 32px}}
  .hero-stats{{flex-direction:column}}
  .content{{padding:0 16px 60px}}
  .sec-title{{font-size:18px}}
  .chart-card{{padding:4px}}
  .rpt-footer{{padding:20px;flex-direction:column;gap:4px}}
}}
</style>
</head>
<body>
<button id="nav-toggle" aria-label="Toggle navigation">&#9776;</button>
<div id="sidebar-overlay"></div>

<!-- SIDEBAR -->
<nav id="sidebar">
  <div class="sb-title">Navigation</div>
{nav_html}
</nav>

<!-- MAIN -->
<div id="main">

  <!-- HERO -->
  <section id="hero" class="hero">
    <div class="hero-eyebrow">Ontario Electoral Reform Analysis &middot; {gen_year}</div>
    <h1>60 Years of<br><span>Electoral Distortion</span></h1>
    <p class="hero-sub">
      A data-driven examination of how Ontario's First-Past-the-Post electoral system
      systematically distorts the relationship between <strong>votes cast</strong> and
      <strong>seats won</strong> &mdash; and what six alternative systems would have delivered
      across every election since 1963.
    </p>
    <div class="hero-stats">
      <div class="hstat" style="border-top:3px solid var(--ndp)">
        <div class="hstat-num" style="color:var(--ndp)">{gi_2022:.1f}</div>
        <div class="hstat-label">2022 Gallagher Index<br><em>(higher = more disproportional)</em></div>
      </div>
      <div class="hstat" style="border-top:3px solid var(--lib)">
        <div class="hstat-num" style="color:var(--lib)">{false_count} of 17</div>
        <div class="hstat-label">Elections with a False Majority<br><em>(&lt;50% of votes, &gt;50% of seats)</em></div>
      </div>
      <div class="hstat" style="border-top:3px solid var(--pc)">
        <div class="hstat-num" style="color:var(--pc)">{wasted_2022:.0f}%</div>
        <div class="hstat-label">Wasted Votes in 2022<br><em>(votes for non-winning parties)</em></div>
      </div>
    </div>
  </section>

  <!-- CONTENT -->
  <div class="content">

    <!-- ── CHAPTER 1 ── -->
    <section id="the-problem" class="chapter-section">
      <div class="chapter-hero">
        <h2>Chapter 1 &middot; The Problem</h2>
        <p>Ontario's FPTP system consistently translates votes into seats in a dramatically
        non-proportional way. This chapter quantifies the distortion across 60 years of elections.</p>
      </div>
    </section>

    {make_section("vote-seat-gap","Chapter 1 · The Problem",
      "Vote Share vs Seat Share by Party",
      "The gap between a party's share of the popular vote (dashed line) and its share of seats "
      "(solid line) illustrates FPTP's distortion. When seat % greatly exceeds vote %, votes are "
      "being amplified; when seat % is far below vote %, votes are being systematically wasted. "
      "Shaded area shows the magnitude of distortion.",
      charts["vote_seat_gap"],
      "Elections Ontario · Curated Historical Data")}
    <div class="divider"></div>

    {make_section("gallagher-history","Chapter 1 · The Problem",
      "Gallagher Disproportionality Index",
      f"The Gallagher Index measures the overall mismatch between vote shares and seat shares. "
      f"A score below 5 is considered low disproportionality; 5–10 is moderate; above 10 is high. "
      f"Ontario's 2022 score of {gi_2022:.1f} is among the highest in its history. Bars are "
      f"colored by the winning party.",
      charts["gallagher_history"],
      "Computed from Elections Ontario data")}
    <div class="divider"></div>

    {make_section("wasted-votes","Chapter 1 · The Problem",
      "Wasted Votes per Election",
      "In a FPTP system, every vote cast for a losing candidate is 'wasted' — it elects nobody. "
      "This chart shows the percentage of all votes that had no impact on the result. Under List PR, "
      "the theoretical minimum waste approaches the exclusion threshold divided by two (~2.5%). "
      "Ontario routinely wastes more than half of all ballots cast.",
      charts["wasted_votes"],
      "Computed from Elections Ontario data")}
    <div class="divider"></div>

    {make_section("false-majorities","Chapter 1 · The Problem",
      "False Majority Governments",
      "A 'false majority' occurs when a party wins more than half the seats — and therefore governs "
      "with unchecked legislative power — despite receiving less than half the popular vote. Red bars "
      "indicate false majorities; green bars indicate elections where the winner had genuine majority "
      "support.",
      charts["false_majorities"],
      "Computed from Elections Ontario data")}
    <div class="divider"></div>

    <!-- ── CHAPTER 2 ── -->
    <section id="election-2022" class="chapter-section">
      <div class="chapter-hero">
        <h2>Chapter 2 &middot; The 2022 Election</h2>
        <p>The 2022 Ontario election is a case study in FPTP distortion: the PC party won 83 of
        124 seats (67%) with only 40.8% of the popular vote. This chapter examines what a
        different system would have produced.</p>
      </div>
    </section>

    {make_section("map-fptp","Chapter 2 · 2022 Election",
      "2022 Ontario Election — Regional Results (FPTP)",
      "Regional vote shares for the 2022 Ontario election. The PC party dominated the 905 Belt "
      "and rural Ontario, while the NDP held Toronto and the North, and the Liberals were "
      "competitive in Eastern Ontario and Ottawa. Under FPTP, regional concentration translates "
      "into massive seat amplification for geographically distributed vote shares.",
      charts["map_fptp"],
      "Elections Ontario 2022 · Curated Regional Aggregates")}
    <div class="divider"></div>

    {make_section("seat-comparison","Chapter 2 · 2022 Election",
      "2022 Seat Comparison Across All Six Electoral Systems",
      "How many seats would each party have won in 2022 under each of six electoral systems? "
      "Dotted vertical lines show each party's proportional entitlement based on vote share. "
      "Under every proportional system, the PC majority disappears and the NDP and Liberals "
      "gain significantly — while the Greens, shut out under FPTP, win seats.",
      charts["seat_comparison"],
      "Computed simulations · Elections Ontario 2022")}
    <div class="divider"></div>

    <section id="systems-table" class="rpt-section">
      <div class="sec-hdr">
        <div>
          <div class="chapter-label">Chapter 2 &middot; 2022 Election</div>
          <h2 class="sec-title">Systems Summary Table — 2022</h2>
        </div>
      </div>
      <p class="sec-desc">
        Key outcome metrics for the 2022 Ontario election under each of the six simulated
        systems. Note how the Gallagher Index drops dramatically under any proportional system,
        and how the PC false majority disappears under PR, MMP, and AMS.
      </p>
      {systems_table_html}
    </section>
    <div class="divider"></div>

    <!-- ── CHAPTER 3 ── -->
    <section id="alt-systems" class="chapter-section">
      <div class="chapter-hero">
        <h2>Chapter 3 &middot; Alternative Systems</h2>
        <p>Six electoral systems are compared: FPTP, Closed List PR (d'Hondt and Sainte-Laguë),
        Regional List PR, MMP, and AMS (Additional Member System). Each balances proportionality,
        local representation, and simplicity differently.</p>
      </div>
    </section>

    {make_section("systems-explainer","Chapter 3 · Alternative Systems",
      "Electoral System Scorecard",
      "A radar chart comparing the six systems across six dimensions: proportionality "
      "(how well seats match votes), local representation (geographic accountability), "
      "simplicity (ease of voting and counting), government stability, minority voice "
      "(ability of smaller parties to win seats), and voter choice. Scores are curated "
      "based on international evidence.",
      charts["pr_explainer"],
      "International IDEA · Electoral Integrity Project · Curated Scores")}
    <div class="divider"></div>

    {make_section("map-regional-pr","Chapter 3 · Alternative Systems",
      "2022 Regional List PR — Seat Allocation by Region",
      "Under Regional List PR with d'Hondt allocation and a 5% threshold, seats within each "
      "of Ontario's seven geographic regions are allocated proportionally to regional vote shares. "
      "This system preserves regional identity while substantially improving proportionality — "
      "the NDP wins seats in Toronto, the Greens win seats across the province.",
      charts["map_regional_pr"],
      "Simulated from ONTARIO_REGIONS_2022 curated data")}
    <div class="divider"></div>

    {make_section("gallagher-by-sys","Chapter 3 · Alternative Systems",
      "Gallagher Index by System — All Elections",
      "How much does each system reduce disproportionality compared to FPTP across all 17 "
      "Ontario elections? Both List PR methods achieve the lowest Gallagher scores in virtually "
      "every election. MMP and AMS are intermediate — significantly more proportional than FPTP "
      "while retaining local seats. Regional PR performs well but not as well as province-wide PR.",
      charts["gallagher_by_sys"],
      "Computed simulations · Elections Ontario 1963–2022")}
    <div class="divider"></div>

    <!-- ── CHAPTER 4 ── -->
    <section id="reimagined" class="chapter-section">
      <div class="chapter-hero">
        <h2>Chapter 4 &middot; 60 Years Reimagined</h2>
        <p>If Ontario had used Mixed-Member Proportional from 1963 onward, how would government
        composition have differed? Fewer false majorities, more minority governments, and more
        frequent coalition-building.</p>
      </div>
    </section>

    {make_section("historical-govt","Chapter 4 · 60 Years Reimagined",
      "Historical Government Composition — FPTP vs MMP",
      "The upper panel shows actual seat composition under FPTP; the lower panel shows simulated "
      "composition under Mixed-Member Proportional. Under MMP, the 1987 Liberal sweep, 1990 NDP "
      "majority, 1995 Harris PC majority, and 2022 PC supermajority would all have been reduced "
      "to minority or coalition governments. The dotted line marks the majority threshold.",
      charts["historical_govt"],
      "Computed simulations · Elections Ontario 1963–2022")}
    <div class="divider"></div>

    <!-- ── CHAPTER 5 ── -->
    <section id="federal" class="chapter-section">
      <div class="chapter-hero">
        <h2>Chapter 5 &middot; Federal Context</h2>
        <p>The same distortions seen in Ontario provincial elections appear in federal elections
        within Ontario. The FPTP problem is not unique to Queen's Park — it is structural.</p>
      </div>
    </section>

    {make_section("federal-vote-seat","Chapter 5 · Federal Context",
      "Federal Elections in Ontario — Vote % vs Seat %",
      "Liberal and Conservative vote shares vs seat shares in federal elections within Ontario "
      "(2000–2021). The 2000 federal election — where the Liberals won 100 of 103 Ontario seats "
      "with 51.5% of the vote — is among the most lopsided FPTP outcomes in Canadian history. "
      "Conservative vote share consistently underperforms in seats during Liberal-era elections.",
      charts["federal_vote_seat"],
      "Elections Canada · Curated Federal Ontario Data")}
    <div class="divider"></div>

    {make_section("federal-gallagher","Chapter 5 · Federal Context",
      "Federal Elections in Ontario — Gallagher Index",
      "Gallagher disproportionality for every federal election in Ontario from 2000 to 2021. "
      "The 2000 election scores exceptionally high. Federal elections in Ontario show consistently "
      "elevated disproportionality similar to provincial elections, confirming that FPTP distortion "
      "is a structural property of the voting system, not a product of any specific election.",
      charts["federal_gallagher"],
      "Computed from Elections Canada data")}
    <div class="divider"></div>

    <!-- ── CHAPTER 6 ── -->
    <section id="scorecard" class="chapter-section">
      <div class="chapter-hero">
        <h2>Chapter 6 &middot; System Scorecard</h2>
        <p>No electoral system perfectly maximizes every desirable property. The radar chart
        reveals the trade-offs: FPTP excels at local representation and simplicity; PR systems
        excel at proportionality and minority voice; MMP attempts to balance both.</p>
      </div>
    </section>

    {make_section("pr-explainer","Chapter 6 · Scorecard",
      "Six Systems, Six Dimensions",
      "Comparative scorecard for the six simulated electoral systems. Each system is scored 0–100 "
      "on six normatively important dimensions. FPTP scores highest on simplicity and local "
      "representation but near-lowest on proportionality and minority voice. The two List PR "
      "variants score highest on proportionality and minority voice. MMP and AMS occupy the "
      "middle ground, sacrificing some proportionality for local representation.",
      charts["pr_explainer2"],
      "International IDEA · Curated Comparative Scores")}
    <div class="divider"></div>

    {_population_disparity_section(riding_charts)}

    <!-- ── CHAPTER 7 ── -->
    <section id="methodology" class="rpt-section">
      <div class="sec-hdr">
        <div>
          <div class="chapter-label">Chapter 7</div>
          <h2 class="sec-title">Methodology &amp; Data Sources</h2>
        </div>
      </div>
      <div class="meth-box">
        <h3>Electoral System Simulations</h3>
        <p><strong>FPTP:</strong> Actual historical results as reported by Elections Ontario.</p>
        <p><strong>Closed List PR — d'Hondt:</strong> Province-wide vote shares used to allocate
        seats via the d'Hondt highest-averages method with a 5% exclusion threshold.</p>
        <p><strong>Closed List PR — Sainte-Laguë:</strong> Same as d'Hondt but using the
        Sainte-Laguë divisor sequence (1, 3, 5, 7, …), which typically favours smaller parties
        slightly more than d'Hondt.</p>
        <p><strong>Regional List PR — d'Hondt:</strong> Ontario divided into seven geographic
        regions (2022 only); d'Hondt applied within each region using regional seat counts and
        vote shares, with a 5% regional threshold.</p>
        <p><strong>MMP (Mixed-Member Proportional):</strong> Half the seats allocated as FPTP
        constituency seats (estimated by scaling actual FPTP results by 0.5); the remaining half
        allocated as list seats to achieve province-wide proportionality via d'Hondt. Overhang
        seats are permitted.</p>
        <p><strong>AMS (Additional Member System):</strong> Same as MMP but with 2/3 constituency
        seats and 1/3 list seats.</p>

        <h3>Gallagher Index</h3>
        <p>The Gallagher Index of disproportionality is computed as:
        <em>G = √(0.5 × Σ(v<sub>i</sub> − s<sub>i</sub>)²)</em> where v<sub>i</sub> is the
        vote percentage and s<sub>i</sub> is the seat percentage for party i. Lower values
        indicate more proportional outcomes.</p>

        <h3>Wasted Votes</h3>
        <p>Defined as votes cast for all parties except the plurality winner, expressed as a
        percentage of total valid votes. This is an approximation — a precise calculation would
        also subtract surplus votes beyond what the winner needed, but plurality contest mechanics
        make this ill-defined.</p>

        <h3>False Majority</h3>
        <p>An election is classified as a "false majority" if the winning party received less
        than 50% of the popular vote but more than 50% of the seats in the legislature.</p>

        <h3>Data Sources</h3>
        <div class="src-grid">
          <div class="src-item">
            <div class="src-name">Elections Ontario</div>
            <div class="src-detail">Official provincial election results 1963–2022. Vote
            percentages and seat counts per party. Data embedded from published Elections Ontario
            historical results tables.</div>
          </div>
          <div class="src-item">
            <div class="src-name">Elections Canada</div>
            <div class="src-detail">Federal election results for Ontario ridings 2000–2021.
            Aggregated to provincial totals for comparability with provincial results.</div>
          </div>
          <div class="src-item">
            <div class="src-name">OpenNorth Represent API</div>
            <div class="src-detail">Ontario electoral district boundary GeoJSON. Fetched at
            runtime from represent.opennorth.ca; cached locally if available. If unavailable,
            regional bar charts are shown instead.</div>
          </div>
          <div class="src-item">
            <div class="src-name">International IDEA</div>
            <div class="src-detail">Comparative electoral systems data. System scorecard
            dimensions informed by IDEA's Electoral System Design database and academic
            literature on electoral reform.</div>
          </div>
        </div>

        <h3>Limitations</h3>
        <ul>
          <li>MMP and AMS simulations use scaled FPTP results to estimate constituency seats,
          not a genuine riding-level simulation. Real outcomes would differ if voters strategically
          adapted to the new system.</li>
          <li>Regional PR uses curated regional vote share aggregates for 2022, not individual
          riding data. Results are approximate.</li>
          <li>Historical elections prior to 1995 did not include a Green Party; Green vote shares
          are zero for those years.</li>
          <li>The "Others" category aggregates all minor parties and independents. Under PR,
          these would likely not all pass the threshold — the simulation allocates them no seats
          under systems with a 5% threshold.</li>
          <li>Voter behaviour would change under any new system (strategic voting, new parties,
          turnout effects). These simulations assume identical vote shares to the observed
          FPTP election.</li>
        </ul>
      </div>
    </section>

  </div><!-- /content -->

  <footer class="rpt-footer">
    <span>Ontario Electoral Reform Analysis &mdash; Generated {today}</span>
    <span>Data: Elections Ontario &middot; Elections Canada &middot; Statistics Canada</span>
  </footer>

</div><!-- /main -->

<script>
// ── Scrollspy ──────────────────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('#sidebar .nav-link');
const observer  = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      const id = e.target.getAttribute('id');
      navLinks.forEach(l =>
        l.classList.toggle('active', l.getAttribute('href') === '#' + id)
      );
    }}
  }});
}}, {{ rootMargin: '-15% 0px -65% 0px' }});
sections.forEach(s => observer.observe(s));

// ── Collapsible sidebar ────────────────────────────────────
const toggle  = document.getElementById('nav-toggle');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebar-overlay');

function openNav() {{
  sidebar.classList.add('open');
  overlay.classList.add('open');
  toggle.innerHTML = '&#x2715;';
}}
function closeNav() {{
  sidebar.classList.remove('open');
  overlay.classList.remove('open');
  toggle.innerHTML = '&#9776;';
}}

toggle.addEventListener('click', () =>
  sidebar.classList.contains('open') ? closeNav() : openNav()
);
overlay.addEventListener('click', closeNav);
navLinks.forEach(l => l.addEventListener('click', () => {{
  if (window.innerWidth <= 768) closeNav();
}}));
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "index.html")

    print("=" * 65)
    print("  Ontario Electoral Reform Analysis")
    print("  Comparing FPTP · List PR · MMP · AMS across 60 years")
    print("=" * 65)

    # ── Fetch external data ──────────────────────────────────
    print("\nFetching external data…")
    geojson_data = fetch_geojson()
    riding_results = fetch_riding_results()

    fetch_status = {
        "GeoJSON": "fetched" if geojson_data else "unavailable — using regional fallback",
        "Riding results": "fetched" if riding_results else "unavailable — using curated data",
    }

    # ── Load local riding data ───────────────────────────────
    print("\nLoading local riding data…")
    riding_geojson, riding_election, riding_populations = load_riding_data()

    # ── Compute statistics ───────────────────────────────────
    print("\nComputing election statistics…")
    stats = build_election_stats()
    s2022 = next(s for s in stats if s["year"] == 2022)
    gi_2022 = s2022["gallagher"]["FPTP"]
    wasted_2022 = s2022["wasted"]
    false_count = sum(1 for s in stats if s["false_majority"])

    print(f"  Gallagher 2022 (FPTP): {gi_2022:.2f}")
    print(f"  Wasted votes 2022: {wasted_2022:.1f}%")
    print(f"  False majorities: {false_count}/17")

    # ── Build all charts ─────────────────────────────────────
    print("\nBuilding charts…")
    charts = {}

    def build(key, label, fn, *args, **kwargs):
        print(f"  • {label}")
        try:
            result = fn(*args, **kwargs)
            charts[key] = result
        except Exception as e:
            print(f"    [warn] {label} failed: {e}")
            import traceback
            traceback.print_exc()
            charts[key] = f"<p style='color:#D00000;padding:24px'>Chart unavailable: {e}</p>"

    build("vote_seat_gap",  "Vote vs Seat Gap",         chart_vote_seat_gap,  stats)
    build("gallagher_history", "Gallagher History",     chart_gallagher_history, stats)
    build("wasted_votes",   "Wasted Votes",             chart_wasted_votes,   stats)

    fm_html, fc = chart_false_majorities(stats)
    charts["false_majorities"] = fm_html

    build("map_fptp",       "Regional FPTP Map (2022)", chart_regional_bar,   stats)
    build("seat_comparison","Seat Comparison 2022",     chart_seat_comparison_2022, stats)
    build("map_regional_pr","Regional PR Bar",          chart_regional_pr_bar, stats)
    build("gallagher_by_sys","Gallagher by System",     chart_gallagher_by_system, stats)
    build("historical_govt","Historical Govts",         chart_historical_govt, stats)
    build("federal_gallagher","Federal Gallagher",      chart_federal_ontario_gallagher)
    build("federal_vote_seat","Federal Vote/Seat",      chart_federal_vote_seat)
    build("pr_explainer",   "PR Systems Explainer",     chart_pr_systems_explainer)
    build("pr_explainer2",  "PR Systems Explainer (Ch6)", chart_pr_systems_explainer)

    # ── Riding-level charts ───────────────────────────────────
    riding_charts = {}
    if riding_geojson and riding_election and riding_populations:
        print("  Building riding-level charts…")
        def rbuild(key, label, fn, *args):
            print(f"    • {label}")
            try:
                riding_charts[key] = fn(*args)
            except Exception as e:
                print(f"      [warn] {label} failed: {e}")
                import traceback
                traceback.print_exc()
                riding_charts[key] = (
                    f"<p style='color:#D00000;padding:24px'>Chart unavailable: {e}</p>"
                )

        rbuild("population_disparity", "Population Disparity",
               chart_population_disparity, riding_election, riding_populations, riding_geojson)
        rbuild("votes_per_seat",        "Votes per Seat",
               chart_votes_per_seat, riding_election)
        rbuild("population_seat_bias",  "Population vs Votes Scatter",
               chart_population_seat_bias, riding_election, riding_populations)
    else:
        print("  [skip] Riding-level charts skipped (data files missing)")

    # ── Summary table ────────────────────────────────────────
    print("  • Systems table (2022)")
    systems_table_html = chart_systems_table_html(stats)

    # ── Assemble HTML ─────────────────────────────────────────
    print("\nAssembling HTML report…")
    html = build_html(charts, stats, false_count, systems_table_html,
                      riding_charts=riding_charts)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  SUMMARY")
    print("=" * 65)
    for k, v in fetch_status.items():
        icon = "[ok]" if "fetched" in v else "[—] "
        print(f"  {icon}  {k}: {v}")
    print(f"\n  Charts built: {len(charts)}")
    print(f"  Output:       {output_path}")
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  File size:    {size_kb:.0f} KB")
    print("=" * 65)


if __name__ == "__main__":
    main()
