"""
generate_seed_data.py -- Bo sinh du lieu mo phong SRRM MVP
Theo luat: Luat_Sinh_Du_Lieu_SRRM.md
Chay: python scripts/generate_seed_data.py
Dau ra: eval/seeds/*.csv, eval/seeds/*.json, eval/ground_truth.csv

Toi uu hieu suat:
- Phase 1-4: giong cu
- Phase 5: vectorized numpy cho demand sampling;
  chi Python-loop tren nhung OD-trip co D>0 va so luong khach thuc su.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np

# ------------------------------------------------------------------
# 0. Cau hinh chung
# ------------------------------------------------------------------
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS_DIR = os.path.join(ROOT, "eval", "seeds")
EVAL_DIR  = os.path.join(ROOT, "eval")
os.makedirs(SEEDS_DIR, exist_ok=True)
os.makedirs(EVAL_DIR, exist_ok=True)

SIM_START = date(2024, 1, 1)
SIM_END   = date(2025, 12, 31)

BOOKING_WINDOW    = 60    # ngay truoc chuyen
NEGBINOM_R        = 12    # over-dispersion
WTP_MEDIAN_RATIO  = 1.15
WTP_SIGMA         = 0.25
FIXED_FEE         = 20_000
PRICE_PER_KM      = {"ngoi_mem": 670, "giuong_nam_k6": 760}
CANCEL_RATE       = 0.07
BROWSE_MULTIPLIER = 1.7
DISTANCE_THRESHOLD_KM = 400
SHORT_HAUL_SHARES = {"ngoi_mem": 0.70, "giuong_nam_k6": 0.30}
LONG_HAUL_SHARES  = {"ngoi_mem": 0.35, "giuong_nam_k6": 0.65}

# ------------------------------------------------------------------
# 1. Catalog co dinh
# ------------------------------------------------------------------
STATIONS = [
    {"id":  1, "code": "HAN", "name": "Ha Noi",                  "km":    0, "is_hub": True,  "pop": 1.00, "display_order":  1},
    {"id":  2, "code": "PHL", "name": "Phu Ly",                  "km":   56, "is_hub": False, "pop": 0.25, "display_order":  2},
    {"id":  3, "code": "NDI", "name": "Nam Dinh",                "km":   87, "is_hub": False, "pop": 0.40, "display_order":  3},
    {"id":  4, "code": "NBH", "name": "Ninh Binh",               "km":  115, "is_hub": False, "pop": 0.30, "display_order":  4},
    {"id":  5, "code": "THH", "name": "Thanh Hoa",               "km":  175, "is_hub": False, "pop": 0.50, "display_order":  5},
    {"id":  6, "code": "VIH", "name": "Vinh",                    "km":  319, "is_hub": True,  "pop": 0.50, "display_order":  6},
    {"id":  7, "code": "DHO", "name": "Dong Hoi",                "km":  522, "is_hub": False, "pop": 0.30, "display_order":  7},
    {"id":  8, "code": "DHA", "name": "Dong Ha",                 "km":  622, "is_hub": False, "pop": 0.25, "display_order":  8},
    {"id":  9, "code": "HUE", "name": "Hue",                     "km":  688, "is_hub": True,  "pop": 0.60, "display_order":  9},
    {"id": 10, "code": "DAN", "name": "Da Nang",                 "km":  791, "is_hub": True,  "pop": 0.90, "display_order": 10},
    {"id": 11, "code": "TAK", "name": "Tam Ky",                  "km":  865, "is_hub": False, "pop": 0.35, "display_order": 11},
    {"id": 12, "code": "QNG", "name": "Quang Ngai",              "km":  928, "is_hub": False, "pop": 0.35, "display_order": 12},
    {"id": 13, "code": "DTR", "name": "Dieu Tri (Quy Nhon)",     "km": 1096, "is_hub": False, "pop": 0.45, "display_order": 13},
    {"id": 14, "code": "TYH", "name": "Tuy Hoa",                 "km": 1198, "is_hub": False, "pop": 0.30, "display_order": 14},
    {"id": 15, "code": "NTG", "name": "Nha Trang",               "km": 1315, "is_hub": True,  "pop": 0.70, "display_order": 15},
    {"id": 16, "code": "TPC", "name": "Thap Cham",               "km": 1408, "is_hub": False, "pop": 0.25, "display_order": 16},
    {"id": 17, "code": "BTH", "name": "Binh Thuan (Muong Man)",  "km": 1551, "is_hub": False, "pop": 0.30, "display_order": 17},
    {"id": 18, "code": "LKH", "name": "Long Khanh",              "km": 1637, "is_hub": False, "pop": 0.20, "display_order": 18},
    {"id": 19, "code": "BHO", "name": "Bien Hoa",                "km": 1694, "is_hub": False, "pop": 0.40, "display_order": 19},
    {"id": 20, "code": "SGO", "name": "Sai Gon",                 "km": 1726, "is_hub": True,  "pop": 1.00, "display_order": 20},
]
STATION_BY_ID   = {s["id"]: s for s in STATIONS}
STATION_BY_CODE = {s["code"]: s for s in STATIONS}
HUB_IDS         = {s["id"] for s in STATIONS if s["is_hub"]}

TRAINS     = [{"id": 1, "code": "SE1", "name": "Thong Nhat SE1", "is_active": True}]
SEAT_TYPES = [
    {"code": "ngoi_mem",      "name": "Ngoi mem dieu hoa",   "is_active": True, "capacity_per_trip": 192},
    {"code": "giuong_nam_k6", "name": "Giuong nam khoang 6", "is_active": True, "capacity_per_trip": 252},
]
SEAT_CAP     = {st["code"]: st["capacity_per_trip"] for st in SEAT_TYPES}
SEAT_CONFIGS = {
    "ngoi_mem":      {"coaches": 3, "per_coach": 64},
    "giuong_nam_k6": {"coaches": 6, "per_coach": 42},
}
FARE_CLASSES = [{"code": "standard", "name": "Pho thong", "is_active": True}]

# Gio chay tinh tu HN (gio thap phan)
STATION_HOUR_OFFSET = {
    "HAN":  0.0,  "PHL":  0.75, "NDI":  1.25, "NBH":  1.75, "THH":  3.0,
    "VIH":  5.58, "DHO": 10.0,  "DHA": 11.5,  "HUE": 12.67, "DAN": 15.42,
    "TAK": 17.0,  "QNG": 18.5,  "DTR": 22.5,  "TYH": 25.0,  "NTG": 26.0,
    "TPC": 26.5,  "BTH": 29.5,  "LKH": 30.5,  "BHO": 31.0,  "SGO": 31.42,
}

# ------------------------------------------------------------------
# 2. Lich
# ------------------------------------------------------------------
FIXED_HOLIDAYS = {(1,1), (4,30), (5,1), (9,2)}
TET_DATES = {2024: date(2024, 2, 10), 2025: date(2025, 1, 29)}
TET_WINDOW = 10

TOURIST_HUB_IDS = {STATION_BY_CODE["DAN"]["id"], STATION_BY_CODE["NTG"]["id"]}
BOTTLENECK_SEQ  = 9   # seq_no cua chặng Hue->DaN (STATIONS[8]->STATIONS[9])


def build_calendar(start: date, end: date) -> List[dict]:
    rows = []
    d = start
    while d <= end:
        is_holiday = (d.month, d.day) in FIXED_HOLIDAYS
        is_tet = any(abs((d - td).days) <= TET_WINDOW for td in TET_DATES.values())
        m = d.month
        season = "summer" if m in (6,7,8) else ("winter" if m in (12,1,2) else
                  ("spring" if m in (3,4,5) else "autumn"))
        weather = ("rainy_central" if m in (10,11,12) else
                   ("hot_dry" if m in (6,7,8) else "mild"))
        rows.append({
            "service_date": d.isoformat(),
            "is_holiday":   is_holiday,
            "is_tet":       is_tet,
            "season":       season,
            "weather":      weather,
            "local_event":  None,
            "created_at":   "2024-01-01T00:00:00+07:00",
            "updated_at":   "2024-01-01T00:00:00+07:00",
        })
        d += timedelta(days=1)
    return rows


# ------------------------------------------------------------------
# 3. Gia co so
# ------------------------------------------------------------------
def base_price(seat_type: str, distance_km: float) -> int:
    p = FIXED_FEE + PRICE_PER_KM[seat_type] * distance_km
    return int(round(p / 1000) * 1000)


# ------------------------------------------------------------------
# 4. Demand model (numpy-ready)
# ------------------------------------------------------------------
F_DOW = np.array([0.85, 0.80, 0.85, 1.10, 1.45, 1.20, 1.50])  # Mon=0..Sun=6


def _f_season(d: date, origin_id: int, dest_id: int) -> float:
    m = d.month
    tourist = (origin_id in TOURIST_HUB_IDS or dest_id in TOURIST_HUB_IDS)
    if m in (6, 7, 8) and tourist:
        return 1.35
    if m in (2, 3, 4):
        return 0.85
    return 1.0


def _f_holiday(d: date, origin_id: int, dest_id: int) -> float:
    for yr, tet_date in TET_DATES.items():
        delta = (d - tet_date).days
        if -TET_WINDOW <= delta <= TET_WINDOW:
            base = 3.0
            han_id = STATION_BY_CODE["HAN"]["id"]
            sgo_id = STATION_BY_CODE["SGO"]["id"]
            if delta < 0 and origin_id == han_id:
                return base * 1.4
            if delta > 0 and origin_id == sgo_id:
                return base * 1.4
            return base
    if (d.month, d.day) in FIXED_HOLIDAYS:
        return 1.8
    return 1.0


def _pair_boost(origin_id: int, dest_id: int, traverses_bn: bool) -> float:
    han_id = STATION_BY_CODE["HAN"]["id"]
    vih_id = STATION_BY_CODE["VIH"]["id"]
    if {origin_id, dest_id} == {han_id, vih_id}:
        return 1.6
    if traverses_bn:
        return 1.5
    return 1.0


def _seat_share(distance_km: float, seat_type: str) -> float:
    shares = SHORT_HAUL_SHARES if distance_km <= DISTANCE_THRESHOLD_KM else LONG_HAUL_SHARES
    return shares[seat_type]


def compute_lambda(origin: dict, dest: dict, dist: float,
                   seat_type: str, traverses_bn: bool, d: date, K: float) -> float:
    base_od = (origin["pop"] * dest["pop"]
               * math.exp(-dist / 800)
               * _pair_boost(origin["id"], dest["id"], traverses_bn)
               * _seat_share(dist, seat_type))
    return max(K * base_od * F_DOW[d.weekday()]
               * _f_season(d, origin["id"], dest["id"])
               * _f_holiday(d, origin["id"], dest["id"]), 0.0)


def sample_demand_batch(lambdas: np.ndarray) -> np.ndarray:
    """NegBinom vectorized. Tra ve mang so nguyen >= 0."""
    r = NEGBINOM_R
    result = np.zeros(len(lambdas), dtype=np.int32)
    pos = lambdas > 0
    if pos.any():
        lam_pos = lambdas[pos]
        p = r / (r + lam_pos)
        result[pos] = rng.negative_binomial(r, p)
    return result


def booking_curve_weights(n_days: int, service_date: date) -> np.ndarray:
    t = np.arange(n_days, 0, -1, dtype=float)  # t=60..1
    w = np.exp(-t / 15.0)
    for yr, tet_date in TET_DATES.items():
        delta_tet = (tet_date - service_date).days
        if 0 < delta_tet <= 60:
            w += 0.5 * np.exp(-((t - 45) ** 2) / (2 * 64.0))
    w /= w.sum()
    return w


def calibrate_K(active_od: list, ref_date: date, target_load: float = 0.65) -> float:
    seg_lam: Dict[int, float] = {}
    for od in active_od:
        origin = STATION_BY_ID[od["origin_station_id"]]
        dest   = STATION_BY_ID[od["destination_station_id"]]
        lam1   = compute_lambda(origin, dest, od["distance_km"],
                                od["seat_type"], od["traverses_bn"], ref_date, K=1.0)
        for seq in od["segment_seqs"]:
            seg_lam[seq] = seg_lam.get(seq, 0.0) + lam1
    if not seg_lam:
        return 1.0
    avg_lam = sum(seg_lam.values()) / len(seg_lam)
    avg_cap = (SEAT_CAP["ngoi_mem"] + SEAT_CAP["giuong_nam_k6"]) / 2
    return (target_load * avg_cap) / avg_lam if avg_lam > 0 else 1.0


# ------------------------------------------------------------------
# 5. I/O helpers
# ------------------------------------------------------------------
def write_json(path: str, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {os.path.basename(path)} ({len(data)} rows)")


def write_csv(path: str, data: list):
    if not data:
        print(f"  [WARN] {os.path.basename(path)} empty, skipped")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)
    print(f"  [OK] {os.path.basename(path)} ({len(data)} rows)")


def write_csv_rows(path: str, fieldnames: List[str], rows):
    """Ghi CSV tu iterator/list de tiet kiem RAM."""
    count = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
            count += 1
    print(f"  [OK] {os.path.basename(path)} ({count} rows)")
    return count


# ------------------------------------------------------------------
# 6. Main
# ------------------------------------------------------------------
def main():
    print("=== SRRM Data Generator ===")
    print(f"Seed: {RANDOM_SEED}, Period: {SIM_START} -> {SIM_END}")

    # -------- Phase 1: Catalog --------
    print("\n[1/6] Catalog...")
    write_json(os.path.join(SEEDS_DIR, "stations.json"), [
        {k: v for k, v in s.items() if k not in ("km", "is_hub", "pop")}
        for s in STATIONS
    ])
    write_json(os.path.join(SEEDS_DIR, "trains.json"), TRAINS)
    write_json(os.path.join(SEEDS_DIR, "seat_types.json"), [
        {k: v for k, v in st.items() if k != "capacity_per_trip"}
        for st in SEAT_TYPES
    ])
    write_json(os.path.join(SEEDS_DIR, "fare_classes.json"), FARE_CLASSES)

    # -------- Phase 2: Calendar --------
    print("\n[2/6] Calendar...")
    cal_rows = build_calendar(SIM_START, SIM_END)
    write_csv(os.path.join(SEEDS_DIR, "calendar_features.csv"), cal_rows)
    sim_dates = [date.fromisoformat(r["service_date"]) for r in cal_rows]
    n_days = len(sim_dates)

    # -------- Phase 3: Trips / Segments / Seats / Capacities / Inventory --------
    print("\n[3/6] Trips / Segments / Seats / Capacities / Inventory...")
    trips            = []
    segments_all     = []
    seats_all        = []
    seg_capacities   = []
    seg_inventory    = []

    trip_id    = 1
    segment_id = 1
    seat_id    = 1

    # trip_segment_map[trip_id][seq_no] = segment_id
    trip_segment_map: Dict[int, Dict[int, int]] = {}
    trip_date_map:    Dict[int, date] = {}

    for d in sim_dates:
        dep_base = datetime(d.year, d.month, d.day, 22, 20)
        dep_str  = dep_base.strftime("%Y-%m-%dT%H:%M:%S+07:00")
        arr_str  = (dep_base + timedelta(hours=31.42)).strftime("%Y-%m-%dT%H:%M:%S+07:00")

        trips.append({
            "id": trip_id, "train_id": 1,
            "service_date": d.isoformat(),
            "origin_station_id": STATIONS[0]["id"],
            "destination_station_id": STATIONS[-1]["id"],
            "departure_at": dep_str, "arrival_at": arr_str,
            "status": "completed" if d < date.today() else "scheduled",
            "created_at": dep_str, "updated_at": dep_str,
        })
        trip_date_map[trip_id] = d
        trip_segment_map[trip_id] = {}

        for seq in range(len(STATIONS) - 1):
            s_from = STATIONS[seq]
            s_to   = STATIONS[seq + 1]
            dist   = float(s_to["km"] - s_from["km"])
            dep_dt = dep_base + timedelta(hours=STATION_HOUR_OFFSET[s_from["code"]])
            arr_dt = dep_base + timedelta(hours=STATION_HOUR_OFFSET[s_to["code"]])

            segments_all.append({
                "id": segment_id, "trip_id": trip_id,
                "sequence_no": seq + 1,
                "origin_station_id": s_from["id"],
                "destination_station_id": s_to["id"],
                "departure_at": dep_dt.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "arrival_at":   arr_dt.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "distance_km":  dist,
                "created_at":   dep_dt.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
            })
            trip_segment_map[trip_id][seq + 1] = segment_id

            for st in SEAT_TYPES:
                seg_capacities.append({
                    "segment_id": segment_id, "seat_type": st["code"],
                    "capacity": st["capacity_per_trip"],
                    "created_at": dep_str, "updated_at": dep_str,
                })
                seg_inventory.append({
                    "segment_id": segment_id, "seat_type": st["code"],
                    "remaining": st["capacity_per_trip"],
                    "updated_at": dep_str,
                })
            segment_id += 1

        for st in SEAT_TYPES:
            cfg = SEAT_CONFIGS[st["code"]]
            for coach in range(1, cfg["coaches"] + 1):
                for sn in range(1, cfg["per_coach"] + 1):
                    seats_all.append({
                        "id": seat_id, "trip_id": trip_id,
                        "coach_no": f"{coach:02d}", "seat_no": f"{sn:02d}",
                        "seat_type": st["code"], "status": "available",
                        "created_at": dep_str,
                    })
                    seat_id += 1
        trip_id += 1

    write_csv(os.path.join(SEEDS_DIR, "trips.csv"),              trips)
    write_csv(os.path.join(SEEDS_DIR, "segments.csv"),           segments_all)
    write_csv(os.path.join(SEEDS_DIR, "seats.csv"),              seats_all)
    write_csv(os.path.join(SEEDS_DIR, "segment_capacities.csv"), seg_capacities)
    write_csv(os.path.join(SEEDS_DIR, "segment_inventory.csv"),  seg_inventory)
    print(f"  trips={len(trips)}, segments={len(segments_all)}, seats={len(seats_all)}")

    # Seat pool: (trip_id, seat_type) -> list of seat_ids (reversed for pop)
    seat_pool: Dict[Tuple[int, str], List[int]] = {}
    for seat in seats_all:
        key = (seat["trip_id"], seat["seat_type"])
        seat_pool.setdefault(key, []).append(seat["id"])
    # Reverse so pop() gives lowest id first
    for v in seat_pool.values():
        v.reverse()

    # -------- Phase 4: OD Products --------
    print("\n[4/6] OD Products...")
    od_template = []
    for i in range(len(STATIONS)):
        for j in range(i + 1, len(STATIONS)):
            s_from = STATIONS[i]; s_to = STATIONS[j]
            dist   = float(s_to["km"] - s_from["km"])
            seqs   = list(range(i + 1, j + 1))
            tbn    = BOTTLENECK_SEQ in seqs
            for st in SEAT_TYPES:
                od_template.append({
                    "origin_station_id":      s_from["id"],
                    "destination_station_id": s_to["id"],
                    "distance_km":            dist,
                    "seat_type":              st["code"],
                    "traverses_bn":           tbn,
                    "segment_seqs":           seqs,
                    "fare_class":             "standard",
                })

    # Calibrate K
    ref_date = date(2024, 3, 19)  # Thu 3, thang 3, khong le
    K = calibrate_K(od_template, ref_date, target_load=0.65)
    print(f"  K = {K:.4f}")

    # Loc OD
    def base_od_k1(od: dict) -> float:
        o = STATION_BY_ID[od["origin_station_id"]]
        d_ = STATION_BY_ID[od["destination_station_id"]]
        return (o["pop"] * d_["pop"]
                * math.exp(-od["distance_km"] / 800)
                * _pair_boost(o["id"], d_["id"], od["traverses_bn"])
                * _seat_share(od["distance_km"], od["seat_type"]))

    threshold_b = 0.5 / K if K > 0 else 0.001
    active_od = []
    for od in od_template:
        has_hub = (od["origin_station_id"] in HUB_IDS or
                   od["destination_station_id"] in HUB_IDS)
        if has_hub or base_od_k1(od) >= threshold_b:
            active_od.append(od)
    print(f"  Active OD/trip: {len(active_od)} / {len(od_template)}")

    # Sinh od_products cho tat ca trips
    od_products        = []
    od_product_segs    = []
    od_product_id      = 1
    # trip_od_map[tid][(orig, dest, st)] = od_product_id
    trip_od_map: Dict[int, Dict[Tuple, int]] = {}

    for trip in trips:
        tid = trip["id"]
        trip_od_map[tid] = {}
        seg_map = trip_segment_map[tid]
        ts = trip["departure_at"]
        for od in active_od:
            bp = base_price(od["seat_type"], od["distance_km"])
            od_products.append({
                "id": od_product_id, "trip_id": tid,
                "origin_station_id":      od["origin_station_id"],
                "destination_station_id": od["destination_station_id"],
                "seat_type":   od["seat_type"],
                "fare_class":  od["fare_class"],
                "base_price":  bp,
                "distance_km": od["distance_km"],
                "is_active":   True,
                "created_at":  ts, "updated_at": ts,
            })
            key = (od["origin_station_id"], od["destination_station_id"], od["seat_type"])
            trip_od_map[tid][key] = od_product_id
            for seq in od["segment_seqs"]:
                sid = seg_map.get(seq)
                if sid:
                    od_product_segs.append({"od_product_id": od_product_id, "segment_id": sid})
            od_product_id += 1

    write_csv(os.path.join(SEEDS_DIR, "od_products.csv"),         od_products)
    write_csv(os.path.join(SEEDS_DIR, "od_product_segments.csv"), od_product_segs)
    print(f"  od_products={len(od_products)}, od_product_segments={len(od_product_segs)}")

    # -------- Phase 5: Simulation (vectorized demand sampling) --------
    print("\n[5/6] Simulation...")

    N_OD   = len(active_od)
    N_DAYS = len(sim_dates)

    # Pre-compute scalar features per OD
    od_bp    = np.array([base_price(od["seat_type"], od["distance_km"]) for od in active_od], dtype=np.int64)
    od_seqs  = [od["segment_seqs"] for od in active_od]   # list of lists

    # Pre-compute calendar features per day
    dow_arr     = np.array([d.weekday() for d in sim_dates], dtype=np.int32)  # (N_DAYS,)
    f_dow_arr   = F_DOW[dow_arr]                                                # (N_DAYS,)

    # Inventory: (trip_id, seq_no, seat_type) -> remaining
    # Dung dict de tiet kiem RAM (chi co N_DAYS*19*2 ~ 27K entries)
    inventory: Dict[Tuple[int, int, str], int] = {}
    for trip in trips:
        tid = trip["id"]
        for seq in range(1, 20):
            for st in SEAT_TYPES:
                inventory[(tid, seq, st["code"])] = st["capacity_per_trip"]

    # ---- Batch sample demand matrix (N_OD x N_DAYS) ----
    print("  Sampling demand matrix...")
    # Tinh lambda matrix (N_OD, N_DAYS)
    lambda_mat = np.zeros((N_OD, N_DAYS), dtype=np.float32)
    for oi, od in enumerate(active_od):
        origin = STATION_BY_ID[od["origin_station_id"]]
        dest   = STATION_BY_ID[od["destination_station_id"]]
        dist   = od["distance_km"]
        st     = od["seat_type"]
        tbn    = od["traverses_bn"]
        base_od_val = (origin["pop"] * dest["pop"]
                       * math.exp(-dist / 800)
                       * _pair_boost(origin["id"], dest["id"], tbn)
                       * _seat_share(dist, st))
        # f_season va f_holiday phai tinh tung ngay
        fsh = np.array([_f_season(d, origin["id"], dest["id"]) for d in sim_dates], dtype=np.float32)
        fhol = np.array([_f_holiday(d, origin["id"], dest["id"]) for d in sim_dates], dtype=np.float32)
        lambda_mat[oi] = K * base_od_val * f_dow_arr.astype(np.float32) * fsh * fhol

    print(f"  Lambda matrix: {lambda_mat.shape}, mean={lambda_mat.mean():.3f}")

    # Sample demand D[N_OD, N_DAYS]
    demand_mat = np.zeros((N_OD, N_DAYS), dtype=np.int32)
    flat_lam = lambda_mat.ravel()
    r = NEGBINOM_R
    pos_mask = flat_lam > 0
    if pos_mask.any():
        lam_pos = flat_lam[pos_mask]
        p_arr   = r / (r + lam_pos)
        demand_mat.ravel()[pos_mask] = rng.negative_binomial(r, p_arr)

    total_demand = int(demand_mat.sum())
    nonzero_cells = int((demand_mat > 0).sum())
    print(f"  Total demand: {total_demand:,}, non-zero OD-trips: {nonzero_cells:,}")

    # ---- Process each OD-trip with D>0 ----
    # Ghi truc tiep ra file bang generator de tiet kiem RAM
    booking_fields = [
        "id", "booking_code", "od_product_id", "seat_id", "status",
        "channel", "booked_price", "booked_at", "expires_at",
        "cancelled_at", "refunded_at", "created_at", "updated_at",
    ]
    search_fields = [
        "id", "searched_at", "origin_station_id", "destination_station_id",
        "seat_type", "service_date", "result", "od_product_id", "channel", "created_at",
    ]
    gt_fields = [
        "trip_id", "service_date", "origin_station_id", "destination_station_id",
        "seat_type", "lambda_true", "demand_uncensored", "wtp_median", "wtp_sigma", "base_price",
    ]

    bk_path = os.path.join(SEEDS_DIR, "bookings.csv")
    sl_path = os.path.join(SEEDS_DIR, "search_logs.csv")
    gt_path = os.path.join(EVAL_DIR,  "ground_truth.csv")

    bk_f  = open(bk_path, "w", newline="", encoding="utf-8")
    sl_f  = open(sl_path, "w", newline="", encoding="utf-8")
    gt_f  = open(gt_path, "w", newline="", encoding="utf-8")
    bk_w  = csv.DictWriter(bk_f, fieldnames=booking_fields);   bk_w.writeheader()
    sl_w  = csv.DictWriter(sl_f, fieldnames=search_fields);    sl_w.writeheader()
    gt_w  = csv.DictWriter(gt_f, fieldnames=gt_fields);        gt_w.writeheader()

    booking_id    = 1
    search_log_id = 1
    n_bookings    = 0
    n_searches    = 0

    # Load stats (chặng Hue-DaN = seq=9)
    bottleneck_sold: Dict[Tuple[int,str], int] = {}  # (trip_id, seat_type) -> sold

    for di, d in enumerate(sim_dates):
        if di % 60 == 0:
            pct = 100 * di / N_DAYS
            print(f"  Day {di+1}/{N_DAYS} ({pct:.0f}%)... bookings={n_bookings:,}", flush=True)

        service_date_str = d.isoformat()
        trip_id_cur      = trips[di]["id"]
        seg_map          = trip_segment_map[trip_id_cur]
        dep_str          = trips[di]["departure_at"]

        # Pre-compute booking curve weights for this day
        bw = booking_curve_weights(BOOKING_WINDOW, d)

        for oi, od in enumerate(active_od):
            D = int(demand_mat[oi, di])
            lam = float(lambda_mat[oi, di])

            # Ground truth
            bp = int(od_bp[oi])
            gt_w.writerow({
                "trip_id":           trip_id_cur,
                "service_date":      service_date_str,
                "origin_station_id": od["origin_station_id"],
                "destination_station_id": od["destination_station_id"],
                "seat_type":         od["seat_type"],
                "lambda_true":       round(lam, 4),
                "demand_uncensored": D,
                "wtp_median":        int(round(WTP_MEDIAN_RATIO * bp)),
                "wtp_sigma":         WTP_SIGMA,
                "base_price":        bp,
            })

            if D == 0:
                continue

            seat_type    = od["seat_type"]
            seqs         = od["segment_seqs"]
            od_key       = (od["origin_station_id"], od["destination_station_id"], seat_type)
            od_prod_id   = trip_od_map[trip_id_cur].get(od_key)
            seat_pool_key = (trip_id_cur, seat_type)

            # Phân bo D khach theo booking curve -> arrival_per_day (60 phan tu)
            arrivals = rng.multinomial(D, bw)  # len=60; idx=0 la 60 ngay truoc

            for t_idx in range(BOOKING_WINDOW):
                n_arr = int(arrivals[t_idx])
                if n_arr == 0:
                    continue
                lead_days  = BOOKING_WINDOW - t_idx
                book_date  = d - timedelta(days=lead_days)
                if book_date < SIM_START:
                    continue
                book_str   = book_date.isoformat() + "T12:00:00+07:00"
                weekday    = book_date.weekday()

                # Gia hien thi: tinh 1 gia cho tat ca khach trong ngay do
                factor = 1.0
                if lead_days < 7:    factor += 0.15
                if weekday in (4,6): factor += 0.10
                noise = float(rng.uniform(-0.15, 0.20))
                factor += noise
                disp_price = max(int(round(bp * factor / 1000) * 1000), 10_000)

                # Check ton kho chung cho t_idx nay
                can_book = all(
                    inventory.get((trip_id_cur, seq, seat_type), 0) > 0
                    for seq in seqs
                )

                if not can_book:
                    # Tat ca n_arr khach gap sold_out
                    for _ in range(n_arr):
                        sl_w.writerow({
                            "id": search_log_id,
                            "searched_at": book_str,
                            "origin_station_id": od["origin_station_id"],
                            "destination_station_id": od["destination_station_id"],
                            "seat_type": seat_type,
                            "service_date": service_date_str,
                            "result": "sold_out",
                            "od_product_id": od_prod_id,
                            "channel": "web",
                            "created_at": book_str,
                        })
                        search_log_id += 1; n_searches += 1
                    continue

                # WTP batch cho n_arr khach
                mu_log = math.log(WTP_MEDIAN_RATIO * bp)
                wtps   = rng.lognormal(mu_log, WTP_SIGMA, size=n_arr)
                buys   = wtps >= disp_price

                for ki in range(n_arr):
                    if buys[ki] and inventory.get((trip_id_cur, seqs[0], seat_type), 0) > 0:
                        # Kiem tra lai ton kho (co the het sau vai khach dau)
                        still_ok = all(
                            inventory.get((trip_id_cur, seq, seat_type), 0) > 0
                            for seq in seqs
                        )
                        if not still_ok:
                            result = "sold_out"
                        else:
                            result = "found"
                            # Gan ghe
                            pool = seat_pool.get(seat_pool_key, [])
                            assigned = pool.pop() if pool else None
                            # Xac dinh trang thai
                            status = "confirmed"
                            cancelled_at = None
                            if float(rng.random()) < CANCEL_RATE:
                                status = "cancelled"
                                cl = int(rng.integers(1, max(lead_days, 2)))
                                cd = book_date + timedelta(days=cl)
                                cd = min(cd, d - timedelta(days=1))
                                cancelled_at = cd.isoformat() + "T10:00:00+07:00"

                            bk_w.writerow({
                                "id": booking_id,
                                "booking_code": f"BK{booking_id:08d}",
                                "od_product_id": od_prod_id,
                                "seat_id": assigned,
                                "status": status,
                                "channel": "web",
                                "booked_price": disp_price,
                                "booked_at": book_str,
                                "expires_at": None,
                                "cancelled_at": cancelled_at,
                                "refunded_at": None,
                                "created_at": book_str,
                                "updated_at": book_str,
                            })
                            booking_id += 1; n_bookings += 1

                            # Tru ton kho neu confirmed
                            if status == "confirmed":
                                for seq in seqs:
                                    k_ = (trip_id_cur, seq, seat_type)
                                    inventory[k_] = max(0, inventory.get(k_, 0) - 1)
                                # Load stats bottleneck
                                if BOTTLENECK_SEQ in seqs:
                                    bk_ = (trip_id_cur, seat_type)
                                    bottleneck_sold[bk_] = bottleneck_sold.get(bk_, 0) + 1
                    else:
                        result = "found"

                    sl_w.writerow({
                        "id": search_log_id,
                        "searched_at": book_str,
                        "origin_station_id": od["origin_station_id"],
                        "destination_station_id": od["destination_station_id"],
                        "seat_type": seat_type,
                        "service_date": service_date_str,
                        "result": result,
                        "od_product_id": od_prod_id,
                        "channel": "web",
                        "created_at": book_str,
                    })
                    search_log_id += 1; n_searches += 1

            # Browsing searches
            browse_n = int(rng.integers(
                max(int(D * (BROWSE_MULTIPLIER - 0.3)), 0),
                max(int(D * BROWSE_MULTIPLIER) + 1, 1)
            ))
            for _ in range(browse_n):
                bl = int(rng.integers(1, BOOKING_WINDOW + 1))
                bd = d - timedelta(days=bl)
                if bd < SIM_START:
                    continue
                bs = bd.isoformat() + "T09:00:00+07:00"
                sl_w.writerow({
                    "id": search_log_id,
                    "searched_at": bs,
                    "origin_station_id": od["origin_station_id"],
                    "destination_station_id": od["destination_station_id"],
                    "seat_type": seat_type,
                    "service_date": service_date_str,
                    "result": "found",
                    "od_product_id": od_prod_id,
                    "channel": "web",
                    "created_at": bs,
                })
                search_log_id += 1; n_searches += 1

    bk_f.close(); sl_f.close(); gt_f.close()
    print(f"\n  [OK] bookings.csv ({n_bookings:,} rows)")
    print(f"  [OK] search_logs.csv ({n_searches:,} rows)")
    print(f"  [OK] ground_truth.csv ({N_OD * N_DAYS:,} rows)")

    # -------- Phase 6: Load stats --------
    print("\n[6/6] Load statistics (bottleneck Hue-DaN seq=9)...")
    weekday_trips_sample = [t for t in trips if date.fromisoformat(t["service_date"]).weekday() == 1][:5]
    for trip in weekday_trips_sample:
        tid = trip["id"]
        for st in SEAT_TYPES:
            cap  = SEAT_CAP[st["code"]]
            sold = bottleneck_sold.get((tid, st["code"]), 0)
            pct  = 100 * sold / cap
            print(f"  Trip {tid} ({trip['service_date']}) seq9 {st['code']}: {sold}/{cap} ({pct:.0f}%)")

    print("\n[DONE]")
    print(f"  Seeds dir   : {SEEDS_DIR}")
    print(f"  Ground truth: {gt_path}")
    print(f"  Total bookings : {n_bookings:,}")
    print(f"  Total searches : {n_searches:,}")


if __name__ == "__main__":
    main()
