import requests
from datetime import datetime, timedelta
from config import get_secret

BASE_URL = "https://intervals.icu/api/v1"

def _get_auth():
    api_key = get_secret("INTERVALS_API_KEY")
    return ("API_KEY", api_key)

def _get_athlete_id():
    return get_secret("INTERVALS_ATHLETE_ID")

def is_configured() -> bool:
    return bool(_get_athlete_id() and get_secret("INTERVALS_API_KEY"))

def get_wellness_summary() -> dict:
    """Récupère les métriques de forme (CTL, ATL, TSB, FC repos) du jour."""
    athlete_id = _get_athlete_id()
    if not is_configured():
        return {"ok": False, "error": "Clés Intervals.icu manquantes."}

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/athlete/{athlete_id}/wellness?oldest={week_ago}&newest={today}"

    try:
        r = requests.get(url, auth=_get_auth(), timeout=10)
        r.raise_for_status()
        records = r.json()
        if not records:
            return {"ok": True, "ctl": 0.0, "atl": 0.0, "tsb": 0.0, "resting_hr": None}
        latest = records[-1]
        ctl = float(latest.get("ctl") or 0.0)
        atl = float(latest.get("atl") or 0.0)
        tsb = round(ctl - atl, 1)
        return {
            "ok": True,
            "date": latest.get("id", today),
            "ctl": round(ctl, 1),
            "atl": round(atl, 1),
            "tsb": tsb,
            "resting_hr": latest.get("restingHR"),
            "hrv": latest.get("hrv")
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_recent_activities(days: int = 14) -> list:
    """Récupère les séances effectuées sur les X derniers jours."""
    athlete_id = _get_athlete_id()
    if not is_configured():
        return []

    newest = datetime.now().strftime("%Y-%m-%d")
    oldest = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/athlete/{athlete_id}/activities?oldest={oldest}&newest={newest}"

    try:
        r = requests.get(url, auth=_get_auth(), timeout=10)
        r.raise_for_status()
        raw = r.json()
        activities = []
        for a in raw:
            if not a.get("type"):
                continue
            dist_km = round((a.get("distance") or 0) / 1000.0, 2)
            dur_min = round((a.get("moving_time") or 0) / 60.0, 1)
            activities.append({
                "date": (a.get("start_date_local") or "")[:10],
                "name": a.get("name", "Séance"),
                "type": a.get("type", "Run"),
                "distance_km": dist_km,
                "duration_min": dur_min,
                "load": a.get("icu_training_load", 0),
                "avg_hr": a.get("average_heartrate")
            })
        return activities
    except Exception:
        return []

def get_upcoming_events(days: int = 14) -> list:
    """Récupère les entraînements planifiés et les notes dans le calendrier Intervals.icu."""
    athlete_id = _get_athlete_id()
    if not is_configured():
        return []

    oldest = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    newest = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/athlete/{athlete_id}/events?oldest={oldest}&newest={newest}"

    try:
        r = requests.get(url, auth=_get_auth(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

def push_event_to_intervals(date_str: str, name: str, description: str, category: str = "WORKOUT", sport_type: str = "Run") -> dict:
    """Envoie un entraînement structuré ou une note du Coach directement dans le calendrier Intervals.icu."""
    athlete_id = _get_athlete_id()
    if not is_configured():
        return {"ok": False, "error": "Clés Intervals.icu non configurées."}

    url = f"{BASE_URL}/athlete/{athlete_id}/events"
    payload = {
        "category": category,
        "start_date_local": f"{date_str}T00:00:00",
        "name": name,
        "description": description,
    }
    if category == "WORKOUT":
        payload["type"] = sport_type

    try:
        r = requests.post(url, auth=_get_auth(), json=payload, timeout=10)
        r.raise_for_status()
        return {"ok": True, "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
