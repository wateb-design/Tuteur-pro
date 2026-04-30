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



# ── Progression des cours ─────────────────────────────────────────

def sauvegarder_diagnostic(eleve_id, theme, score, niveau):
    """Enregistre le résultat du diagnostic pour une matière."""
    # On vérifie si une ligne existe déjà pour cet élève/thème
    res = requests.get(
        f"{supabase_url()}/rest/v1/progression_cours",
        headers=headers(),
        params={
            "select":   "id",
            "eleve_id": f"eq.{eleve_id}",
            "theme":    f"eq.{theme}",
            "chapitre": "eq.__diagnostic__"
        }
    )
    existe = res.json()

    if existe:
        # Mise à jour si déjà existant
        requests.patch(
            f"{supabase_url()}/rest/v1/progression_cours",
            headers=headers(),
            params={
                "eleve_id": f"eq.{eleve_id}",
                "theme":    f"eq.{theme}",
                "chapitre": "eq.__diagnostic__"
            },
            json={
                "score_diag":     score,
                "niveau_detecte": niveau,
                "date_debut":     "now()"
            }
        )
    else:
        # Insertion nouvelle ligne
        requests.post(
            f"{supabase_url()}/rest/v1/progression_cours",
            headers=headers(),
            json={
                "eleve_id":       eleve_id,
                "theme":          theme,
                "chapitre":       "__diagnostic__",
                "score_diag":     score,
                "niveau_detecte": niveau,
                "cours_vu":       False
            }
        )

def get_niveau_detecte(eleve_id, theme):
    """Récupère le niveau détecté lors du diagnostic."""
    res = requests.get(
        f"{supabase_url()}/rest/v1/progression_cours",
        headers=headers(),
        params={
            "select":   "niveau_detecte",
            "eleve_id": f"eq.{eleve_id}",
            "theme":    f"eq.{theme}",
            "chapitre": "eq.__diagnostic__"
        }
    )
    data = res.json()
    if data:
        return data[0]["niveau_detecte"]
    return None  # Pas encore de diagnostic

def marquer_cours_vu(eleve_id, theme, chapitre, niveau):
    """Marque un chapitre comme vu par l'élève."""
    res = requests.get(
        f"{supabase_url()}/rest/v1/progression_cours",
        headers=headers(),
        params={
            "select":   "id",
            "eleve_id": f"eq.{eleve_id}",
            "theme":    f"eq.{theme}",
            "chapitre": f"eq.{chapitre}"
        }
    )
    existe = res.json()

    if existe:
        requests.patch(
            f"{supabase_url()}/rest/v1/progression_cours",
            headers=headers(),
            params={
                "eleve_id": f"eq.{eleve_id}",
                "theme":    f"eq.{theme}",
                "chapitre": f"eq.{chapitre}"
            },
            json={"cours_vu": True}
        )
    else:
        requests.post(
            f"{supabase_url()}/rest/v1/progression_cours",
            headers=headers(),
            json={
                "eleve_id":       eleve_id,
                "theme":          theme,
                "chapitre":       chapitre,
                "niveau_detecte": niveau,
                "cours_vu":       True
            }
        )

def marquer_quiz_reussi(eleve_id, theme, chapitre):
    """Marque le quiz d'un chapitre comme réussi."""
    requests.patch(
        f"{supabase_url()}/rest/v1/progression_cours",
        headers=headers(),
        params={
            "eleve_id": f"eq.{eleve_id}",
            "theme":    f"eq.{theme}",
            "chapitre": f"eq.{chapitre}"
        },
        json={
            "quiz_reussi":      True,
            "date_completion":  "now()"
        }
    )

def get_progression_cours(eleve_id, theme):
    """Retourne tous les chapitres vus pour une matière."""
    res = requests.get(
        f"{supabase_url()}/rest/v1/progression_cours",
        headers=headers(),
        params={
            "select":   "chapitre,cours_vu,quiz_reussi,niveau_detecte",
            "eleve_id": f"eq.{eleve_id}",
            "theme":    f"eq.{theme}"
        }
    )
    return res.json()

def get_stats_cours(eleve_id):
    """Retourne le nombre de chapitres vus et quiz réussis."""
    res = requests.get(
        f"{supabase_url()}/rest/v1/progression_cours",
        headers=headers(),
        params={
            "select":    "cours_vu,quiz_reussi",
            "eleve_id":  f"eq.{eleve_id}",
            "cours_vu":  "eq.true"
        }
    )
    data = res.json()
    return {
        "chapitres_vus":  len(data),
        "quiz_reussis":   sum(1 for d in data if d["quiz_reussi"])
    }
