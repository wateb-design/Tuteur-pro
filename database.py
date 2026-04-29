import streamlit as st
from supabase import create_client

# ── Connexion à Supabase ──────────────────────────────────────────
# Le client officiel Supabase est plus simple que psycopg2.
# Il utilise l'API REST — pas de driver PostgreSQL nécessaire.
@st.cache_resource
def get_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

# ── Initialisation ────────────────────────────────────────────────
# Les tables sont créées directement dans Supabase SQL Editor.
# Cette fonction vérifie juste que la connexion fonctionne.
def init_db():
    try:
        get_client()
    except Exception as e:
        st.error(f"Erreur de connexion Supabase : {e}")

# ── Élèves ────────────────────────────────────────────────────────

def inserer_eleve(prenom, email, password_hash):
    try:
        get_client().table("eleves").insert({
            "prenom":        prenom,
            "email":         email,
            "mot_de_passe":  password_hash   # ← changé
        }).execute()
        return True
    except Exception:
        return False

def get_eleve_par_email(email, password_hash):
    res = get_client().table("eleves").select("id, prenom").eq(
        "email", email
    ).eq("mot_de_passe", password_hash).execute()  # ← changé
    if res.data:
        return res.data[0]["id"], res.data[0]["prenom"]
    return None

# ── Résultats ─────────────────────────────────────────────────────

def inserer_resultat(eleve_id, theme, niveau, reussi, temps=0):
    get_client().table("resultats").insert({
        "eleve_id": eleve_id,
        "theme":    theme,
        "niveau":   niveau,
        "reussi":   reussi,
        "temps":    temps
    }).execute()

def get_resultats_eleve(eleve_id):
    res = get_client().table("resultats").select(
        "theme, niveau, reussi, temps, date"
    ).eq("eleve_id", eleve_id).order("date", desc=True).execute()
    # On retourne une liste de tuples comme avant
    # pour ne pas modifier exercices.py et progression.py
    return [
        (r["theme"], r["niveau"], r["reussi"], r["temps"], r["date"])
        for r in res.data
    ]

def get_stats_eleve(eleve_id):
    res = get_client().table("resultats").select(
        "reussi"
    ).eq("eleve_id", eleve_id).execute()
    total   = len(res.data)
    reussis = sum(r["reussi"] for r in res.data) if res.data else 0
    taux    = round(reussis / total * 100) if total > 0 else 0
    return {"total": total, "reussis": reussis, "taux": taux}

def get_stats_par_theme(eleve_id):
    res = get_client().table("resultats").select(
        "theme, reussi"
    ).eq("eleve_id", eleve_id).execute()

    # On regroupe manuellement par thème
    themes = {}
    for r in res.data:
        t = r["theme"]
        if t not in themes:
            themes[t] = {"total": 0, "reussis": 0}
        themes[t]["total"]   += 1
        themes[t]["reussis"] += r["reussi"]

    # Retourne le même format que l'ancienne version SQLite :
    # [(theme, total, reussis), ...]
    return [(t, v["total"], v["reussis"]) for t, v in themes.items()]
