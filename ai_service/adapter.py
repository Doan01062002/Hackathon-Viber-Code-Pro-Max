"""Adapter: đọc 21 bảng CSV/JSON (bộ seeds) -> bảng `history` tổng hợp cho Forecaster.
Đây là phần của AI (feature engineering), không phải backend.

Dùng:  from ai_service import adapter; hist = adapter.load_history("out/seeds")
"""
from __future__ import annotations
import os, json
import pandas as pd

from . import config as C, datagen

HUB_CODES = {"HAN", "VIH", "HUE", "DAN", "NTG", "SGO"}
HUE_ID, DAN_ID = 9, 10   # id ga Huế / Đà Nẵng -> chặng nút cổ chai ở giữa


def load_history(seeds_dir: str) -> pd.DataFrame:
    p = lambda f: os.path.join(seeds_dir, f)
    od = pd.read_csv(p("od_products.csv"))
    trips = pd.read_csv(p("trips.csv"))[["id", "service_date"]].rename(columns={"id": "trip_id"})
    bk = pd.read_csv(p("bookings.csv"))
    sl = pd.read_csv(p("search_logs.csv"))
    cal = pd.read_csv(p("calendar_features.csv"))
    stations = json.load(open(p("stations.json"), encoding="utf-8"))
    hub_ids = {s["id"] for s in stations if s["code"] in HUB_CODES}

    trips["service_date"] = pd.to_datetime(trips["service_date"])
    od = od.merge(trips, on="trip_id")
    od["service_date"] = pd.to_datetime(od["service_date"])
    GKEY = ["origin_station_id", "destination_station_id", "seat_type", "service_date"]

    # --- nhu cầu đã bán từ bookings ---
    odx = od.rename(columns={"id": "od_product_id"})[
        ["od_product_id", "origin_station_id", "destination_station_id", "seat_type", "service_date"]]
    b = bk[["od_product_id", "booked_price"]].merge(odx, on="od_product_id")
    bagg = b.groupby(GKEY).agg(bookings=("booked_price", "size"),
                               shown_price=("booked_price", "mean")).reset_index()

    # --- nhu cầu bị cắt (sold_out) từ search_logs ---
    sl["service_date"] = pd.to_datetime(sl["service_date"])
    so = (sl[sl["result"] == "sold_out"]
          .groupby(GKEY).size().reset_index(name="soldout"))

    # --- thuộc tính cố định mỗi OD vật lý ---
    phys = od.groupby(["origin_station_id", "destination_station_id", "seat_type"]).agg(
        base_price=("base_price", "median"), distance_km=("distance_km", "median")).reset_index()
    dates = pd.DataFrame({"service_date": sorted(od["service_date"].unique())})
    grid = phys.merge(dates, how="cross")   # đủ (OD × ngày), gồm cả ngày cầu = 0

    h = (grid.merge(bagg, on=GKEY, how="left")
             .merge(so, on=GKEY, how="left"))
    h["bookings"] = h["bookings"].fillna(0).astype(int)
    h["soldout"] = h["soldout"].fillna(0).astype(int)
    h["shown_price"] = h["shown_price"].fillna(h["base_price"])

    # --- đặc trưng lịch ---
    cal["service_date"] = pd.to_datetime(cal["service_date"])
    def _b(s): return s.astype(str).str.lower().isin(["true", "1"]).astype(int)
    cal["is_holiday"] = _b(cal["is_holiday"]); cal["is_tet"] = _b(cal["is_tet"])
    # thời tiết / khuyến mãi (nếu seed có cột; không thì suy từ tháng/để 0)
    cal["is_rainy"] = (cal["weather"].astype(str).str.lower().str.contains("rain")
                       if "weather" in cal else False)
    cal["is_rainy"] = cal["is_rainy"].fillna(False).astype(int)
    cal["promo"] = (cal["local_event"].astype(str).str.lower().str.contains("promo")
                    if "local_event" in cal else False)
    cal["promo"] = cal["promo"].fillna(False).astype(int)
    h = h.merge(cal[["service_date", "is_holiday", "is_tet", "is_rainy", "promo"]],
                on="service_date", how="left")
    for c in ["is_holiday", "is_tet", "is_rainy", "promo"]:
        h[c] = h[c].fillna(0).astype(int)

    h["dow"] = h["service_date"].dt.weekday
    h["month"] = h["service_date"].dt.month
    h["is_summer"] = h["month"].isin([6, 7, 8]).astype(int)
    # mùa mưa miền Trung: nếu seed không đánh dấu thời tiết thì suy từ tháng
    h.loc[h["is_rainy"] == 0, "is_rainy"] = h["month"].isin(list(C.RAINY_MONTHS)).astype(int)
    # chiều đi/về Tết (days_to_tet, pre/post) tính từ ngày
    tc = h["service_date"].map(lambda x: datagen.tet_context(x.date()))
    h["days_to_tet"] = tc.map(lambda z: z[0])
    h["is_pre_tet"] = tc.map(lambda z: z[1])
    h["is_post_tet"] = tc.map(lambda z: z[2])
    h["is_hub_o"] = h["origin_station_id"].isin(hub_ids).astype(int)
    h["is_hub_d"] = h["destination_station_id"].isin(hub_ids).astype(int)
    h["crosses_bottleneck"] = ((h["origin_station_id"] <= HUE_ID) &
                               (h["destination_station_id"] >= DAN_ID)).astype(int)

    # --- pop (độ hút ga) suy từ lượng đặt lịch sử (thay cho tham số sinh) ---
    vo = b.groupby("origin_station_id").size(); vo = vo / vo.max()
    vd = b.groupby("destination_station_id").size(); vd = vd / vd.max()
    h["pop_o"] = h["origin_station_id"].map(vo).fillna(0.1)
    h["pop_d"] = h["destination_station_id"].map(vd).fillna(0.1)

    # --- id OD vật lý + willing (cho ước lượng co giãn) ---
    h["od_id"] = h.groupby(["origin_station_id", "destination_station_id", "seat_type"]).ngroup()
    h["willing"] = h["bookings"] + h["soldout"]
    return h


def load_bookings_leadtime(seeds_dir: str) -> pd.DataFrame:
    """Đọc bookings + trips -> bảng [trip_id, lead_time] để fit booking curve.
    lead_time = số ngày từ lúc đặt (booked_at) tới ngày chạy (service_date)."""
    p = lambda f: os.path.join(seeds_dir, f)
    bk = pd.read_csv(p("bookings.csv"))
    od = pd.read_csv(p("od_products.csv"))[["id", "trip_id"]].rename(columns={"id": "od_product_id"})
    trips = pd.read_csv(p("trips.csv"))[["id", "service_date"]].rename(columns={"id": "trip_id"})
    b = bk[["od_product_id", "booked_at"]].merge(od, on="od_product_id").merge(trips, on="trip_id")
    b["service_date"] = pd.to_datetime(b["service_date"]).dt.tz_localize(None)
    b["booked_at"] = pd.to_datetime(b["booked_at"], utc=True, errors="coerce").dt.tz_localize(None)
    b = b.dropna(subset=["booked_at"])
    b["lead_time"] = (b["service_date"] - b["booked_at"]).dt.days.clip(lower=0)
    return b[["trip_id", "lead_time"]]
