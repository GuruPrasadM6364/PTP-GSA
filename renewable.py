"""Renewable helpers: fetch Open-Meteo daily irradiance and estimate simple PV yield.
Kept CLI / validation helpers from previous file.
"""
import logging
import re
import argparse
from datetime import datetime
try:
    import requests
except Exception:
    requests = None

logging.basicConfig(level=logging.INFO)

# --- simple validation / CLI utilities (kept) ---
def validate_phone(phone):
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_pincode(pincode):
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, pincode))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# --- PV prediction helpers (restored) ---
OPEN_METEO_DAILY = "https://api.open-meteo.com/v1/forecast"

# assumptions
PANEL_EFFICIENCY = 0.18
AREA_PER_KW = 6.0
PERFORMANCE_RATIO = 0.75

def fetch_daily_irradiance(lat, lon, start_date, end_date, timezone="UTC"):
    if requests is None:
        raise RuntimeError("requests not installed")
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "shortwave_radiation_sum",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone
    }
    r = requests.get(OPEN_METEO_DAILY, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def estimate_pv_yield_from_irradiance(irradiance_wh_m2):
    if irradiance_wh_m2 is None:
        return None
    kwh_per_kw = (irradiance_wh_m2 / 1000.0) * (PANEL_EFFICIENCY * AREA_PER_KW) * PERFORMANCE_RATIO
    return kwh_per_kw

def predict_generation(lat, lon, start_date, end_date):
    """
    Returns daily list with irradiance and estimated kWh per kW.
    """
    if requests is None:
        raise RuntimeError("requests not installed")
    om = fetch_daily_irradiance(lat, lon, start_date, end_date)
    daily = []
    dates = om.get("daily", {}).get("time", []) or []
    irr_list = om.get("daily", {}).get("shortwave_radiation_sum", []) or []
    total = 0.0
    count = 0
    for i, dt in enumerate(dates):
        irr = None
        try:
            irr = float(irr_list[i])
        except Exception:
            irr = None
        kwh = estimate_pv_yield_from_irradiance(irr) if irr is not None else None
        if kwh is not None:
            total += kwh
            count += 1
        daily.append({"date": dt, "irradiance_wh_m2": irr, "kwh_per_kw": round(kwh,3) if kwh is not None else None})
    avg = round(total / count, 3) if count else None
    return {"daily": daily, "average_kwh_per_kw_per_day": avg, "total_kwh_per_kw": round(total,3) if count else None}

# --- CLI wrapper to call predictive.run_prediction when needed (kept lightweight) ---
try:
    from predictive import run_prediction
except Exception:
    run_prediction = None

def cmd_predict(lat, lon, days=7):
    if run_prediction is None:
        raise RuntimeError("predictive.run_prediction not available")
    return run_prediction(lat, lon, days=days)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--days", type=int, default=7)
    args = p.parse_args()
    print(cmd_predict(args.lat, args.lon, args.days))

