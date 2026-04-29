import streamlit as st
import requests

# ── Helpers REST Supabase ─────────────────────────────────────────
# On appelle l'API REST Supabase directement avec requests.
# Plus fiable que le client officiel sur Python 3.14.
def supabase_url():
    return st.secrets["SUPABASE_URL"].rstrip("/")

def headers():
    return {
        "apikey":        st.secrets["SUPABASE_KEY"],
        "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation"
    }

def init_db():
    # Les tables sont créées dans Supabase SQL Editor
    # Cette fonction vérifie juste que les secrets sont présents
    try:
        _ = st.secrets["SUPABASE_URL"]
        _ = st.secrets["SUPABASE_KEY"]
    except Exception as e:
        st.error(f"Secrets manquants : {e}")

# ── Élèves ────────────────────────────────────────────────────────

def inserer_eleve(prenom, email, password_hash):
    try:
        res = requests.post(
            f"{supabase_url()}/rest/v1/eleves",
            headers=headers(),
            json={
                "prenom":        prenom,
                "email":         email,
                "mot_de_passe":  password_hash
            }
        )
        return res.status_code in [200, 201]
    except Exception:
        return False

def get_eleve_par_email(email, password_hash):
    if not email or not password_hash:
        return None
    try:
        res = requests.get(
            f"{supabase_url()}/rest/v1/eleves",
            headers=headers(),
            params={
                "select": "id,prenom",
                "email":         f"eq.{email}",
                "mot_de_passe":  f"eq.{password_hash}"
            }
        )
        data = res.json()
        if data:
            return data[0]["id"], data[0]["prenom"]
        return None
    except Exception as e:
        st.error(f"Erreur : {e}")
        return None

# ── Résultats ─────────────────────────────────────────────────────

def inserer_resultat(eleve_id, theme, niveau, reussi, temps=0):
    requests.post(
        f"{supabase_url()}/rest/v1/resultats",
        headers=headers(),
        json={
            "eleve_id": eleve_id,
            "theme":    theme,
            "niveau":   niveau,
            "reussi":   reussi,
            "temps":    temps
        }
    )

def get_resultats_eleve(eleve_id):
    res = requests.get(
        f"{supabase_url()}/rest/v1/resultats",
        headers=headers(),
        params={
            "select":   "theme,niveau,reussi,temps,date",
            "eleve_id": f"eq.{eleve_id}",
            "order":    "date.desc"
        }
    )
    return [
        (r["theme"], r["niveau"], r["reussi"], r["temps"], r["date"])
        for r in res.json()
    ]

def get_stats_eleve(eleve_id):
    res = requests.get(
        f"{supabase_url()}/rest/v1/resultats",
        headers=headers(),
        params={
            "select":   "reussi",
            "eleve_id": f"eq.{eleve_id}"
        }
    )
    data    = res.json()
    total   = len(data)
    reussis = sum(r["reussi"] for r in data) if data else 0
    taux    = round(reussis / total * 100) if total > 0 else 0
    return {"total": total, "reussis": reussis, "taux": taux}

def get_stats_par_theme(eleve_id):
    res = requests.get(
        f"{supabase_url()}/rest/v1/resultats",
        headers=headers(),
        params={
            "select":   "theme,reussi",
            "eleve_id": f"eq.{eleve_id}"
        }
    )
    themes = {}
    for r in res.json():
        t = r["theme"]
        if t not in themes:
            themes[t] = {"total": 0, "reussis": 0}
        themes[t]["total"]   += 1
        themes[t]["reussis"] += r["reussi"]
    return [(t, v["total"], v["reussis"]) for t, v in themes.items()]
