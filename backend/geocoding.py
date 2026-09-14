import time
import httpx
from typing import Optional, Tuple

# In-memory geocode cache for instant response & demo safety
GEOCODE_CACHE = {
    "mihan": (21.0925, 79.0472, "MIHAN / Outer Ring Road, Nagpur"),
    "sadar": (21.1580, 79.0850, "Sadar, Nagpur, Maharashtra"),
    "hingna": (21.0700, 78.9950, "Hingna MIDC, Nagpur, Maharashtra"),
    "civil lines": (21.1550, 79.0700, "Civil Lines, Nagpur, Maharashtra"),
    "seminary": (21.1620, 79.0550, "Seminary Hills, Nagpur, Maharashtra"),
    "seminary hills": (21.1620, 79.0550, "Seminary Hills, Nagpur, Maharashtra"),
    "ambazari": (21.1300, 79.0450, "Ambazari Lake & Catchment, Nagpur"),
    "jamtha": (21.0150, 79.0300, "Jamtha / VCA Stadium, Nagpur, Maharashtra"),
    "vnit": (21.1260, 79.0500, "VNIT Campus, Ambazari Road, Nagpur"),
    "manish nagar": (21.0935, 79.0684, "Manish Nagar, Nagpur, Maharashtra"),
    "gittikhadan": (21.1750, 79.0350, "Gittikhadan, Nagpur, Maharashtra"),
    "wardha road": (21.0850, 79.0620, "Wardha Road, Nagpur, Maharashtra"),
    "dharampeth": (21.1440, 79.0620, "Dharampeth, Nagpur, Maharashtra"),
    "ramdaspeth": (21.1380, 79.0740, "Ramdaspeth, Nagpur, Maharashtra"),
    "dhantoli": (21.1340, 79.0820, "Dhantoli, Nagpur, Maharashtra"),
    "manewada": (21.1080, 79.0960, "Manewada, Nagpur, Maharashtra"),
    "sitabuldi": (21.1460, 79.0830, "Sitabuldi, Nagpur, Maharashtra"),
    "cotton market": (21.1460, 79.0920, "Cotton Market / Central Station, Nagpur"),
    "kamptee": (21.2220, 79.1980, "Kamptee, Nagpur District, Maharashtra"),
    "it park": (21.1240, 79.0510, "IT Park / Gayatri Nagar, Nagpur"),
    "nandanvan": (21.1340, 79.1250, "Nandanvan, Nagpur, Maharashtra"),
    "koradi": (21.2480, 79.0980, "Koradi Thermal Precinct, Nagpur"),
    "butibori": (20.9300, 78.9800, "Butibori Industrial Area, Nagpur"),
    "besa": (21.0850, 79.0900, "Besa / Pipla, Nagpur, Maharashtra"),
    "khamla": (21.1150, 79.0600, "Khamla, Nagpur, Maharashtra"),
    "trimurti nagar": (21.1180, 79.0450, "Trimurti Nagar, Nagpur, Maharashtra"),
    "pratap nagar": (21.1150, 79.0520, "Pratap Nagar, Nagpur, Maharashtra"),
    "shankar nagar": (21.1350, 79.0600, "Shankar Nagar, Nagpur, Maharashtra"),
    "mahal": (21.1440, 79.1120, "Mahal, Old City, Nagpur"),
    "gandhibagh": (21.1520, 79.1050, "Gandhibagh / Itwari, Nagpur"),
    "itwari": (21.1550, 79.1120, "Itwari / Gandhibagh Commercial Hub, Nagpur"),
    "mankapur": (21.1900, 79.0800, "Mankapur Sports Complex, Nagpur"),
    "pardi": (21.1480, 79.1620, "Pardi / Bhandara Road, Nagpur"),
    "kalamna": (21.1750, 79.1450, "Kalamna Market, Nagpur"),
    "jaripatka": (21.1850, 79.1000, "Jaripatka, North Nagpur"),
    "chhatrapati nagar": (21.1120, 79.0680, "Chhatrapati Nagar, Wardha Road, Nagpur"),
}

_last_request_time = 0.0

async def geocode_location(location_name: str) -> Tuple[float, float, str]:
    """
    Geocodes a location name to (lat, lng, display_name).
    Uses in-memory cache, landmark defaults, and OpenStreetMap Nominatim API with rate-limiting.
    """
    global _last_request_time
    q_norm = location_name.strip().lower()

    # 1. Check exact/partial match in cache
    for key, (lat, lng, display) in GEOCODE_CACHE.items():
        if key in q_norm or q_norm in key:
            return lat, lng, display

    # 2. Rate-limit enforcement for Nominatim (max 1 req/sec)
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    # 3. Build query biased towards Nagpur / Maharashtra
    query = location_name
    if "nagpur" not in q_norm and "maharashtra" not in q_norm:
        query = f"{location_name}, Nagpur, Maharashtra"

    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "NagpurEarthWatch-UrbanIntelligence/1.0 (HackathonDemo; contact: demo@nagpurearthwatch.org)"
    }
    params = {
        "q": query,
        "format": "json",
        "limit": "1",
        "countrycodes": "in",
        "viewbox": "78.8,21.3,79.3,21.0",
        "bounded": "0"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            _last_request_time = time.time()

            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    item = data[0]
                    lat = float(item["lat"])
                    lng = float(item["lon"])
                    display_name = item.get("display_name", location_name)
                    # Cache result
                    GEOCODE_CACHE[q_norm] = (lat, lng, display_name)
                    return lat, lng, display_name
    except Exception as e:
        print(f"Nominatim geocoding warning: {e}. Falling back to default Nagpur centroid.")

    # 4. Fallback if outside or Nominatim fails
    default_lat, default_lng = 21.1458, 79.0882
    fallback_display = f"{location_name}, Nagpur"
    GEOCODE_CACHE[q_norm] = (default_lat, default_lng, fallback_display)
    return default_lat, default_lng, fallback_display
