import streamlit as st
from datetime import datetime, date
import plotly.graph_objects as go
from google import genai

from config import get_secret, ATHLETE_CONTEXT
from meteo_granby import get_weather_granby
from api_intervals import (
    is_configured,
    get_wellness_summary,
    get_recent_activities,
    get_upcoming_events,
    push_event_to_intervals,
)
from workout_builder import build_running_workout_text, build_home_gym_workout_text

st.set_page_config(
    page_title="Coach Interactif",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏃‍♂️ Coach Interactif — Granby")

# Chargement des données contextuelles en cache léger
@st.cache_data(ttl=600)
def load_dashboard_data():
    weather = get_weather_granby()
    wellness = get_wellness_summary()
    activities = get_recent_activities(days=14)
    events = get_upcoming_events(days=14)
    return weather, wellness, activities, events

weather, wellness, activities, events = load_dashboard_data()

# Navigation par onglets (très pratique sur mobile Pixel 10 Pro XL comme sur PC)
tab_accueil, tab_builder, tab_coach, tab_agenda = st.tabs([
    "🏠 Accueil & Forme",
    "🛠️ Créer une Séance",
    "🤖 Coach IA",
    "📅 Agenda Intervals.icu"
])

# ==========================================
# ONGLET 1 : ACCUEIL, MÉTÉO & ÉTAT DE FORME
# ==========================================
with tab_accueil:
    col_meteo, col_forme = st.columns([1, 1])

    with col_meteo:
        st.subheader("🌦️ Météo en direct à Granby")
        if weather.get("ok"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Température", f"{weather['temp']} °C", f"Ressenti {weather['feels_like']} °C")
            c2.metric("Vent", f"{weather['wind']} km/h")
            c3.metric("Humidité", f"{weather['humidity']} %")
            st.info(f"**{weather['description']}** — {weather['conseil']}")
        else:
            st.warning("Météo indisponible momentanément.")

    with col_forme:
        st.subheader("⚡ État de forme (Intervals.icu)")
        if wellness.get("ok"):
            f1, f2, f3 = st.columns(3)
            f1.metric("Condition (CTL)", wellness.get("ctl", 0))
            f2.metric("Fatigue (ATL)", wellness.get("atl", 0))
            tsb = wellness.get("tsb", 0)
            statut_tsb = "Frais / Prêt" if tsb >= 0 else ("Charge optimale" if tsb >= -20 else "Fatigue élevée")
            f3.metric("Forme (TSB)", tsb, statut_tsb)
            if wellness.get("resting_hr"):
                st.caption(f"❤️ FC au repos récente : **{wellness['resting_hr']} bpm** | HRV : **{wellness.get('hrv') or 'N/A'}**")
        else:
            st.warning("Connecte tes clés Intervals.icu dans les Secrets pour voir ta forme en direct.")

    st.divider()
    st.subheader("📈 Dernières activités (14 jours)")
    if activities:
        # Graphique rapide des distances ou charges
        dates = [a["date"] for a in reversed(activities)]
        loads = [a["load"] or 0 for a in reversed(activities)]
        names = [f"{a['name']} ({a['distance_km']} km)" for a in reversed(activities)]

        fig = go.Figure(data=[go.Bar(x=dates, y=loads, text=names, textposition="auto")])
        fig.update_layout(
            title="Charge d'entraînement par séance (Load)",
            xaxis_title="Date",
            yaxis_title="Charge (ICU Load)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        for act in activities[:6]:
            st.write(f"• **{act['date']}** — **{act['name']}** ({act['type']}) : `{act['distance_km']} km` en `{act['duration_min']} min` | Charge : `{act['load']}`")
    else:
        st.info("Aucune activité récente trouvée sur les 14 derniers jours.")

    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# ONGLET 2 : CRÉATEUR D'ENTRAÎNEMENT
# ==========================================
with tab_builder:
    st.subheader("🛠️ Programmer et envoyer une séance vers Intervals.icu & Garmin")

    type_seance = st.radio(
        "Type de séance :",
        ["🏃‍♂️ Course (Route / Trail / Tapis Horizon T202)", "🏋️‍♂️ Musculation Home Gym (Cage GOIMU / Poulies)"],
        horizontal=True
    )

    col_d1, col_d2 = st.columns(2)
    date_seance = col_d1.date_input("Date prévue", value=date.today())

    if "Course" in type_seance:
        nom_defaut = "Fractionné Seuil"
        nom_seance = col_d2.text_input("Nom de la séance", value=nom_defaut)

        c1, c2, c3 = st.columns(3)
        warmup = c1.number_input("Échauffement (min)", min_value=5, max_value=45, value=15)
        reps = c2.number_input("Nombre de répétitions", min_value=1, max_value=30, value=5)
        cooldown = c3.number_input("Retour au calme (min)", min_value=5, max_value=30, value=10)

        c4, c5, c6 = st.columns(3)
        work_dur = c4.text_input("Durée ou distance de l'effort (ex: 4m ou 1km)", value="4m")
        work_target = c5.text_input("Cible (ex: 85-90% HR ou 5:15/km Pace)", value="85-90% HR")
        rest_dur = c6.text_input("Récupération entre séries (ex: 2m)", value="2m")

        notes_run = st.text_area("Notes (ex: Saucony Endorphin Speed 5, ou inclinaison 1% sur tapis Horizon T202)", value="")
        texte_final = build_running_workout_text(warmup, reps, work_dur, work_target, rest_dur, cooldown, notes_run)
        sport_code = "Run"

    else:
        nom_seance = col_d2.text_input("Nom de la séance", value="Renforcement Course & Puissance")
        focus = st.selectbox("Focus du jour", [
            "Bas du corps & Prévention Trail (Squats, Fentes, Mollets)",
            "Haut du corps & Tirage Poulie (Dos, Épaules, Gainage)",
            "Full Body Fonctionnel & Explosivité"
        ])
        duree_gym = st.slider("Durée estimée (min)", 20, 90, 45, step=5)
        exos_defaut = (
            "Squat barre libre (Cage GOIMU) : 4 x 8 reps (RPE 8)\n"
            "Fentes bulgares sur banc : 3 x 10 reps par jambe\n"
            "Tirage horizontal poulie basse : 4 x 12 reps\n"
            "Face pull poulie haute : 3 x 15 reps\n"
            "Gainage planche + abdos poulie haute : 3 séries"
        )
        exos_texte = st.text_area("Exercices (un par ligne)", value=exos_defaut, height=150)
        notes_gym = st.text_input("Notes complémentaires", value="Repos 90s entre les séries.")
        liste_exos = [l.strip() for l in exos_texte.split("\n") if l.strip()]
        texte_final = build_home_gym_workout_text(focus, duree_gym, liste_exos, notes_gym)
        sport_code = "WeightTraining"

    st.markdown("**Aperçu du code envoyé à Intervals.icu :**")
    st.code(texte_final, language="text")

    if st.button("🚀 Envoyer dans mon calendrier Intervals.icu", type="primary"):
        res = push_event_to_intervals(
            date_str=date_seance.strftime("%Y-%m-%d"),
            name=nom_seance,
            description=texte_final,
            category="WORKOUT",
            sport_type=sport_code
        )
        if res.get("ok"):
            st.success(f"Séance « {nom_seance} » ajoutée au {date_seance} sur Intervals.icu !")
            st.cache_data.clear()
        else:
            st.error(f"Erreur lors de l'envoi : {res.get('error')}")

# ==========================================
# ONGLET 3 : COACH IA (GEMINI)
# ==========================================
with tab_coach:
    st.subheader("🤖 Discussion avec ton Coach IA")

    gemini_key = get_secret("GEMINI_API_KEY")
    if not gemini_key:
        st.warning("Ajoute ta clé `GEMINI_API_KEY` dans les Secrets Streamlit pour activer le Coach IA.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Affichage de l'historique de la session
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt_user = st.chat_input("Pose une question à ton coach (ex: Que me conseilles-tu comme séance aujourd'hui selon ma fatigue et la météo ?)")

        if prompt_user:
            st.session_state.messages.append({"role": "user", "content": prompt_user})
            with st.chat_message("user"):
                st.markdown(prompt_user)

            # Construction du contexte temps réel pour Gemini
            contexte_live = f"""
{ATHLETE_CONTEXT}

Données en direct aujourd'hui ({datetime.now().strftime('%Y-%m-%d')}) :
- Météo à Granby : {weather.get('temp')}°C (Ressenti {weather.get('feels_like')}°C), {weather.get('description')}, Vent {weather.get('wind')} km/h. {weather.get('conseil')}
- État de forme Intervals.icu : Condition (CTL) = {wellness.get('ctl')}, Fatigue (ATL) = {wellness.get('atl')}, Forme (TSB) = {wellness.get('tsb')}, FC Repos = {wellness.get('resting_hr')} bpm.
- 5 dernières activités : {activities[:5]}

Instructions de style :
- Parle de façon directe, naturelle et motivante, comme un collègue autour d'un café.
- Évite le jargon inutile et les formules toutes faites.
- Donne des conseils précis (allures, zones Karvonen, choix entre extérieur et tapis Horizon T202, ou exercices sur la cage GOIMU).
"""
            with st.chat_message("assistant"):
                with st.spinner("Analyse de tes données en cours..."):
                    try:
                     client = genai.Client(api_key=gemini_key)
                     full_prompt = f"{contexte_live}\n\nQuestion de l'athlète : {prompt_user}"

                     # Détection automatique du modèle actif sur ton compte Google
                     modeles_a_tester = [
                         "gemini-3-flash-preview",
                         "gemini-2.0-flash",
                         "gemini-1.5-flash"
                     ]
                     for m in client.models.list():
                         nom_m = m.name.replace("models/", "")
                         if "flash" in nom_m and "2.5" not in nom_m and nom_m not in modeles_a_tester:
                             modeles_a_tester.insert(0, nom_m)

                     reply = None
                     derniere_erreur = ""
                     for nom_modele in modeles_a_tester:
                         try:
                             response = client.models.generate_content(
                                 model=nom_modele,
                                 contents=full_prompt
                             )
                             reply = response.text
                             break
                         except Exception as err:
                             derniere_erreur = str(err)
                             continue

                     if reply:
                         st.markdown(reply)
                         st.session_state.messages.append({"role": "assistant", "content": reply})
                     else:
                         st.error(f"Aucun modèle disponible : {derniere_erreur}")
                 except Exception as e:
                     st.error(f"Erreur d'appel Gemini : {e}")

        # Bouton pour sauvegarder la dernière recommandation du coach directement dans Intervals.icu
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            if st.button("📌 Sauvegarder ce conseil en Note du jour sur Intervals.icu"):
                derniere_rep = st.session_state.messages[-1]["content"]
                res = push_event_to_intervals(
                    date_str=date.today().strftime("%Y-%m-%d"),
                    name="Note Coach IA",
                    description=derniere_rep,
                    category="NOTE"
                )
                if res.get("ok"):
                    st.success("Note enregistrée dans ton calendrier Intervals.icu ! Accessible sur ton PC et ton Pixel.")
                    st.cache_data.clear()
                else:
                    st.error(f"Erreur : {res.get('error')}")

# ==========================================
# ONGLET 4 : AGENDA & NOTES INTERVALS.ICU
# ==========================================
with tab_agenda:
    st.subheader("📅 Mes séances planifiées et notes sauvegardées")
    if events:
        for ev in events:
            d_ev = (ev.get("start_date_local") or "")[:10]
            cat = ev.get("category", "")
            nom = ev.get("name", "Événement")
            desc = ev.get("description", "")
            icone = "📝" if cat == "NOTE" else "🏃‍♂️"
            with st.expander(f"{icone} {d_ev} — {nom} ({cat})"):
                st.text(desc or "Aucun détail.")
    else:
        st.info("Aucun entraînement ou note planifié pour les prochains jours.")
