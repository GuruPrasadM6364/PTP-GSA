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

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

IPAPI_URL = "https://ipapi.co/{ip}/json/"
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
        url = IPAPI_URL.format(ip=ip)
        r = requests.get(url, timeout=6)
        if r.ok:
            return r.json()
    except Exception:
        pass
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
    r = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def compute_averages(om_json):
    # om_json.hourly.shortwave_radiation and windspeed_10m are arrays aligned by time
    hourly = om_json.get("hourly", {})
    sr = hourly.get("shortwave_radiation", [])
    ws = hourly.get("windspeed_10m", [])
    def avg(arr):
        if not arr: return None
        vals = [v for v in arr if v is not None]
        return sum(vals) / len(vals) if vals else None
    return {
        "avg_shortwave": avg(sr),
        "avg_windspeed": avg(ws),
        "data_points": len(sr) if sr else 0
    }

@app.route("/api/community", methods=["GET"])
def community():
    # allow optional ip override (useful during local testing)
    ip = request.args.get("ip")
    if not ip:
        # Try to get client IP from headers or remote_addr
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
        if "," in ip:
            ip = ip.split(",")[0].strip()
    # if still local loopback, let ipapi infer caller by using no-ip endpoint
    use_ipapi_noarg = ip in ("127.0.0.1", "::1", "localhost", "")

    # resolve location
    if use_ipapi_noarg:
        ipapi_resp = fetch_ip_location("")
        # ipapi.co/json/ is used when ip blank, fetch_ip_location will have tried ipapi with empty string -> may fail
        # fallback to ipapi.co/json/ directly
        if ipapi_resp is None:
            try:
                r = requests.get("https://ipapi.co/json/", timeout=6)
                ipapi_resp = r.json() if r.ok else None
            except Exception:
                ipapi_resp = None
    else:
        ipapi_resp = fetch_ip_location(ip)

    if not ipapi_resp:
        return jsonify({"error": "Failed to resolve location from IP"}), 502

    lat = ipapi_resp.get("latitude") or ipapi_resp.get("lat")
    lon = ipapi_resp.get("longitude") or ipapi_resp.get("lon")
    city = ipapi_resp.get("city", "")
    region = ipapi_resp.get("region", "")
    country = ipapi_resp.get("country_name", ipapi_resp.get("country", ""))

    if lat is None or lon is None:
        return jsonify({"error": "Location response missing coordinates", "raw": ipapi_resp}), 502

    # request last 7 days (end_date = yesterday)
    end = datetime.utcnow().date() - timedelta(days=1)
    start = end - timedelta(days=6)
    start_s = start.isoformat()
    end_s = end.isoformat()

    # prepare list of points: center + three nearby offsets (~5km)
    offsets = [(0,0), (0.05,0.0), (-0.05,0.06), (0.04,-0.05)]
    communities = []
    for i, (dlat, dlon) in enumerate(offsets):
        qlat = float(lat) + dlat
        qlon = float(lon) + dlon
        try:
            om = fetch_open_meteo(qlat, qlon, start_s, end_s)
            avgs = compute_averages(om)
            dist = haversine_km(float(lat), float(lon), qlat, qlon)
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
            communities.append({
                "name": "Nearby "+str(i),
                "latitude": round(qlat,6),
                "longitude": round(qlon,6),
                "error": str(e)
            })

    result = {
        "detected": {
            "ip": ip,
            "city": city,
            "region": region,
            "country": country,
            "latitude": float(lat),
            "longitude": float(lon)
        },
        "period": {"start_date": start_s, "end_date": end_s},
        "communities": communities
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)