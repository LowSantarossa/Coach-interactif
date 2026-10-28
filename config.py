import os
import streamlit as st

def get_secret(key: str) -> str:
    """Récupère une clé depuis Streamlit Cloud (Secrets) ou les variables d'environnement."""
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.getenv(key, "").strip()

# Coordonnées exactes de Granby, QC
GRANBY_LAT = 45.4001
GRANBY_LON = -72.7329

# Profil de l'athlète transmis au Coach IA et au générateur de séances
ATHLETE_CONTEXT = """
Profil de l'athlète :
- Homme, 44 ans, basé à Granby (Québec).
- Course sur route et trail (4 à 6 séances/semaine, distances de 5 km à 21+ km).
- Record personnel (RP) sur Demi-Marathon : 1h57m30s (allure ~5:34/km). Expérience sur relais ultra trail (Bromont Ultra).
- Montre : Garmin Forerunner 965 (utilise PacePro, SatIQ et les zones de fréquence cardiaque Karvonen / FC Réserve).
- Chaussures route : Saucony Endorphin Speed 5. Bâtons de trail : 115 cm (Komperdell / Salomon).
- Équipement Home Gym disponible :
  * Tapis de course Horizon T202
  * Cage à squat (Power cage) GOIMU C1-V4 avec barre et poids (1 pouce)
  * Système de poulie haute et basse (câbles)
  * Banc de musculation pliable
- Autres sports : Badminton (niveau intermédiaire-avancé, style puissant), Golf.
"""
