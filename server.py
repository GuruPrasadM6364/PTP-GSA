# Simple Flask backend to provide IP-based location + real nearby renewable metrics
# - Calls ipapi.co to resolve IP -> lat/lon
# - Calls Open-Meteo to fetch recent hourly shortwave_radiation & windspeed_10m
# - Returns JSON with location and nearby "communities" (actual measured data, not mocked)
#
# Requirements:
#   pip install flask flask-cors requests
#
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import math
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)

IPAPI_URL = "https://ipapi.co/{ip}/json/"
IPAPI_NOARG = "https://ipapi.co/json/"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def haversine_km(a_lat, a_lon, b_lat, b_lon):
    R = 6371.0
    to_rad = math.pi / 180.0
    dlat = (b_lat - a_lat) * to_rad
    dlon = (b_lon - a_lon) * to_rad
    alat = a_lat * to_rad
    blat = b_lat * to_rad
    h = math.sin(dlat/2)**2 + math.cos(alat) * math.cos(blat) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(h), math.sqrt(1-h))

def fetch_ip_location(ip):
    try:
        if not ip:
            r = requests.get(IPAPI_NOARG, timeout=6)
        else:
            url = IPAPI_URL.format(ip=ip)
            r = requests.get(url, timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.warning("ipapi lookup failed: %s", e)
    return None

def fetch_open_meteo(lat, lon, start_date, end_date):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "shortwave_radiation,windspeed_10m",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC"
    }
    r = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def compute_averages(om_json):
    hourly = om_json.get("hourly", {})
    sr = hourly.get("shortwave_radiation") or []
    ws = hourly.get("windspeed_10m") or []
    def avg(arr):
        vals = [v for v in arr if v is not None]
        return sum(vals) / len(vals) if vals else None
    return {
        "avg_shortwave": avg(sr),
        "avg_windspeed": avg(ws),
        "data_points": len(sr) if sr else 0
    }

@app.route("/api/community", methods=["GET"])
def community():
    # allow optional explicit lat/lon override (from client)
    lat_arg = request.args.get("lat")
    lon_arg = request.args.get("lon")
    ip_override = request.args.get("ip")  # optional ip override for testing

    detected = {"ip": None, "city": "", "region": "", "country": "", "latitude": None, "longitude": None}

    if lat_arg is not None and lon_arg is not None:
        # use provided coordinates directly
        try:
            lat = float(lat_arg)
            lon = float(lon_arg)
            detected.update({
                "ip": ip_override or request.remote_addr,
                "city": "Manual",
                "region": "",
                "country": "",
                "latitude": lat,
                "longitude": lon
            })
        except ValueError:
            return jsonify({"error": "Invalid lat/lon parameters"}), 400
    else:
        # resolve location from IP (use ip_override if provided)
        ip = ip_override
        if not ip:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
            if "," in ip:
                ip = ip.split(",")[0].strip()
        use_noarg = ip in ("127.0.0.1", "::1", "localhost", "")

        ipapi_resp = fetch_ip_location(None if use_noarg else ip)
        if not ipapi_resp:
            return jsonify({"error": "Failed to resolve location from IP"}), 502

        # ipapi may use keys 'latitude'/'longitude' or 'lat'/'lon'
        lat = ipapi_resp.get("latitude") or ipapi_resp.get("lat")
        lon = ipapi_resp.get("longitude") or ipapi_resp.get("lon")
        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:
            return jsonify({"error": "Location response missing coordinates", "raw": ipapi_resp}), 502

        detected.update({
            "ip": ip,
            "city": ipapi_resp.get("city", ""),
            "region": ipapi_resp.get("region", ""),
            "country": ipapi_resp.get("country_name", ipapi_resp.get("country", "")),
            "latitude": lat,
            "longitude": lon
        })

    # request last 7 days (end_date = yesterday)
    end = datetime.utcnow().date() - timedelta(days=1)
    start = end - timedelta(days=6)
    start_s = start.isoformat()
    end_s = end.isoformat()

    # prepare list of points: center + three nearby offsets (~5km)
    offsets = [(0,0), (0.05,0.0), (-0.05,0.06), (0.04,-0.05)]
    communities = []
    for i, (dlat, dlon) in enumerate(offsets):
        qlat = float(detected["latitude"]) + dlat
        qlon = float(detected["longitude"]) + dlon
        try:
            om = fetch_open_meteo(qlat, qlon, start_s, end_s)
            avgs = compute_averages(om)
            dist = haversine_km(float(detected["latitude"]), float(detected["longitude"]), qlat, qlon)
            communities.append({
                "name": "Your community" if i==0 else f"Nearby {i}",
                "latitude": round(qlat, 6),
                "longitude": round(qlon, 6),
                "distance_km": round(dist, 2),
                "avg_shortwave_W_m2": avgs["avg_shortwave"],
                "avg_windspeed_m_s": avgs["avg_windspeed"],
                "data_points": avgs["data_points"]
            })
        except Exception as e:
            logging.exception("Open-Meteo fetch failed for %s,%s", qlat, qlon)
            communities.append({
                "name": "Nearby "+str(i),
                "latitude": round(qlat,6),
                "longitude": round(qlon,6),
                "error": str(e)
            })

    result = {
        "detected": detected,
        "period": {"start_date": start_s, "end_date": end_s},
        "communities": communities
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)