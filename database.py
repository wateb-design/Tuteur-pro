import streamlit as st
import requests
import json as _json

# ── Helpers REST Supabase ─────────────────────────────────────────
# On appelle l'API REST Supabase directement avec requests.
# Plus fiable que le client officiel sur Python 3.14.
def supabase_url():
    return st.secrets["SUPABASE_URL"].rstrip("/")

def headers(prefer="return=representation"):
    return {
        "apikey":        st.secrets["SUPABASE_KEY"],
        "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}",
        "Content-Type":  "application/json",
        "Prefer":        prefer
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

def get_onboarding(eleve_id):
    """Vérifie si l'élève a déjà fait l'onboarding."""
    res = requests.get(
        f"{supabase_url()}/rest/v1/onboarding",
        headers=headers(),
        params={"eleve_id": f"eq.{eleve_id}"}
    )
    data = res.json()
    return data[0] if data else None

def sauvegarder_onboarding(eleve_id, scores, recommandation):
    """Sauvegarde les résultats du diagnostic initial."""
    onboarding = get_onboarding(eleve_id)
    if onboarding:
        requests.patch(
            f"{supabase_url()}/rest/v1/onboarding",
            headers=headers(),
            params={"eleve_id": f"eq.{eleve_id}"},
            json={
                "onboarding_fait": True,
                "scores":          scores,
                "recommandation":  recommandation
            }
        )
    else:
        requests.post(
            f"{supabase_url()}/rest/v1/onboarding",
            headers=headers(),
            json={
                "eleve_id":        eleve_id,
                "onboarding_fait": True,
                "scores":          scores,
                "recommandation":  recommandation
            }
        )

# ══════════════════════════════════════════════════════════════════
# COURS CONTENU
# ══════════════════════════════════════════════════════════════════

def get_cours_contenu(theme, chapitre, niveau):
    """Récupère le contenu d'un cours depuis Supabase.
    Retourne None si pas encore généré."""
    try:
        res = requests.get(
            f"{supabase_url()}/rest/v1/cours_contenu",
            headers=headers(),
            params={
                "select":   "contenu",
                "theme":    f"eq.{theme}",
                "chapitre": f"eq.{chapitre}",
                "niveau":   f"eq.{niveau}",
                "limit":    "1"
            }
        )
        data = res.json()
        return data[0]["contenu"] if data else None
    except Exception:
        return None

def sauvegarder_cours_contenu(theme, chapitre, niveau, contenu):
    """Sauvegarde le contenu généré par Groq en base.
    Utilise upsert pour éviter les doublons."""
    try:
        h = headers(prefer="resolution=merge-duplicates,return=representation")
        requests.post(
            f"{supabase_url()}/rest/v1/cours_contenu",
            headers=h,
            json={
                "theme":    theme,
                "chapitre": chapitre,
                "niveau":   niveau,
                "contenu":  contenu
            }
        )
    except Exception:
        pass  # On continue même si la sauvegarde échoue


# ══════════════════════════════════════════════════════════════════
# QUIZ CONTENU
# ══════════════════════════════════════════════════════════════════

def get_quiz_contenu(theme, chapitre, niveau):
    """Récupère un quiz depuis Supabase.
    Retourne None si pas encore généré."""
    try:
        res = requests.get(
            f"{supabase_url()}/rest/v1/quiz_contenu",
            headers=headers(),
            params={
                "select":   "question,choix,reponse,explication,savoir_faire_evalue",
                "theme":    f"eq.{theme}",
                "chapitre": f"eq.{chapitre}",
                "niveau":   f"eq.{niveau}",
                "limit":    "1"
            }
        )
        data = res.json()
        if not data:
            return None
        row = data[0]
        # choix est stocké en JSONB → déjà une liste Python
        choix = row["choix"] if isinstance(row["choix"], list) \
                else _json.loads(row["choix"])
        return {
            "question":            row["question"],
            "choix":               choix,
            "reponse":             row["reponse"],
            "explication":         row["explication"],
            "savoir_faire_evalue": row.get("savoir_faire_evalue", "")
        }
    except Exception:
        return None

def sauvegarder_quiz_contenu(theme, chapitre, niveau, quiz):
    """Sauvegarde un quiz généré par Groq en base."""
    try:
       h = headers(prefer="resolution=merge-duplicates,return=representation")
        requests.post(
            f"{supabase_url()}/rest/v1/quiz_contenu",
            headers=h,
            json={
                "theme":               theme,
                "chapitre":            chapitre,
                "niveau":              niveau,
                "question":            quiz["question"],
                "choix":               quiz["choix"],
                "reponse":             quiz["reponse"],
                "explication":         quiz.get("explication", ""),
                "savoir_faire_evalue": quiz.get("savoir_faire_evalue", "")
            }
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
# POOL D'EXERCICES
# ══════════════════════════════════════════════════════════════════

# Remplacez get_exercice_pool par cette version corrigée :

def get_exercice_pool(theme, chapitre, niveau, type_ex):
    try:
        res = requests.get(
            f"{supabase_url()}/rest/v1/exercices_contenu",
            headers=headers(),
            params={
                "select":   "id,titre,description,code_depart,solution,explication",
                "theme":    f"eq.{theme}",
                "chapitre": f"eq.{chapitre}",
                "niveau":   f"eq.{niveau}",
                "type_ex":  f"eq.{type_ex}",
                "utilise":  "eq.false",
                "limit":    "5"  # ← on prend 5 puis on pioche aléatoirement en Python
            }
        )
        data = res.json()

        if data:
            import random
            ex = random.choice(data)  # ← aléatoire côté Python
            requests.patch(
                f"{supabase_url()}/rest/v1/exercices_contenu",
                headers=headers(),
                params={"id": f"eq.{ex['id']}"},
                json={"utilise": True}
            )
            return {
                "titre":       ex["titre"],
                "description": ex["description"],
                "code_depart": ex.get("code_depart", ""),
                "solution":    ex["solution"],
                "explication": ex.get("explication", "")
            }

        # Pool épuisé → reset
        requests.patch(
            f"{supabase_url()}/rest/v1/exercices_contenu",
            headers=headers(),
            params={
                "theme":    f"eq.{theme}",
                "chapitre": f"eq.{chapitre}",
                "niveau":   f"eq.{niveau}",
                "type_ex":  f"eq.{type_ex}"
            },
            json={"utilise": False}
        )
        return None

    except Exception:
        return None

def sauvegarder_exercice_pool(theme, chapitre, niveau, type_ex, exercice):
    """Ajoute un exercice généré par Groq dans le pool."""
    try:
        requests.post(
            f"{supabase_url()}/rest/v1/exercices_contenu",
            headers=headers(),
            json={
                "theme":       theme,
                "chapitre":    chapitre,
                "niveau":      niveau,
                "type_ex":     type_ex,
                "titre":       exercice["titre"],
                "description": exercice["description"],
                "code_depart": exercice.get("code_depart", ""),
                "solution":    exercice["solution"],
                "explication": exercice.get("explication", ""),
                "utilise":     False
            }
        )
    except Exception:
        pass

def compter_exercices_pool(theme, chapitre, niveau, type_ex):
    """Retourne le nombre d'exercices disponibles dans le pool."""
    try:
        h = headers()
        h["Prefer"] = "count=exact"
        res = requests.get(
            f"{supabase_url()}/rest/v1/exercices_contenu",
            headers=h,
            params={
                "select":   "id",
                "theme":    f"eq.{theme}",
                "chapitre": f"eq.{chapitre}",
                "niveau":   f"eq.{niveau}",
                "type_ex":  f"eq.{type_ex}"
            }
        )
        count = int(res.headers.get("Content-Range", "0/0").split("/")[-1])
        return count
    except Exception:
        return 0


# ══════════════════════════════════════════════════════════════════
# QUESTIONS DE DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════

def get_diagnostic_questions(theme):
    """Récupère les questions de diagnostic pour une matière.
    Retourne None si pas encore générées."""
    try:
        res = requests.get(
            f"{supabase_url()}/rest/v1/diagnostic_questions",
            headers=headers(),
            params={
                "select":  "niveau,question,choix,reponse,explication",
                "theme":   f"eq.{theme}",
                "order":   "id.asc"
            }
        )
        data = res.json()
        if not data or len(data) < 3:
            return None
        # Reformater pour correspondre au format attendu
        questions = []
        for row in data:
            choix = row["choix"] if isinstance(row["choix"], list) \
                    else _json.loads(row["choix"])
            questions.append({
                "niveau":      row["niveau"],
                "question":    row["question"],
                "choix":       choix,
                "reponse":     row["reponse"],
                "explication": row["explication"]
            })
        return {"questions": questions}
    except Exception:
        return None

def sauvegarder_diagnostic_questions(theme, questions):
    """Sauvegarde les questions de diagnostic en base.
    Supprime les anciennes avant d'insérer les nouvelles."""
    try:
        # Supprimer les anciennes questions pour cette matière
        requests.delete(
            f"{supabase_url()}/rest/v1/diagnostic_questions",
            headers=headers(),
            params={"theme": f"eq.{theme}"}
        )
        # Insérer les nouvelles
        for q in questions:
            requests.post(
                f"{supabase_url()}/rest/v1/diagnostic_questions",
                headers=headers(),
                json={
                    "theme":       theme,
                    "niveau":      q["niveau"],
                    "question":    q["question"],
                    "choix":       q["choix"],
                    "reponse":     q["reponse"],
                    "explication": q.get("explication", "")
                }
            )
    except Exception:
        pass
