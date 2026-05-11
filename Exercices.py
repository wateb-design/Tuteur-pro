import streamlit as st
import json
import re
import time
import random
from groq import Groq
from database import (
    inserer_resultat,
    get_stats_par_theme,
    get_onboarding,
    get_progression_exercices,
    init_progression_exercices,
    maj_progression_exercices,
    valider_niveau,
    reset_rattrapage,
    sauvegarder_erreur,
    get_erreurs_recentes,
    get_exercice_pool,
    sauvegarder_exercice_pool
)
from cours_data import COURS

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════
NIVEAUX          = ["Débutant", "Intermédiaire", "Avancé"]
SEUIL_NORMALE    = 10
SEUIL_RATTRAPAGE = 5

# Alternance automatique des types sur 10 exercices
ALTERNANCE_TYPES = [
    "QCM", "QRO", "Complétion", "Détection", "Logique",
    "QCM", "Complétion", "Détection", "QRO", "Logique"
]

TYPES_INFO = {
    "QCM":        {"icone": "🔘", "label": "Question à Choix Multiples"},
    "QRO":        {"icone": "✍️", "label": "Question à Réponse Ouverte"},
    "Complétion": {"icone": "🔧", "label": "Complétion de code"},
    "Détection":  {"icone": "🐛", "label": "Détection et correction d'erreurs"},
    "Logique":    {"icone": "🧩", "label": "Exercice de logique algorithmique"}
}

# ══════════════════════════════════════════════════════════════════
# CALCUL NIVEAU ADAPTATIF
# Priorité : score exercices récents > diagnostic onboarding
# ══════════════════════════════════════════════════════════════════
def calculer_niveau(eleve_id, matiere):
    """Retourne (niveau, taux, source)."""
    # Priorité 1 — exercices récents (≥3 faits)
    stats = get_stats_par_theme(eleve_id)
    for theme, total, reussis in stats:
        if theme == matiere and total >= 3:
            taux = round(reussis / total * 100)
            if taux >= 80:   return "Avancé",        taux, "exercices récents"
            elif taux >= 50: return "Intermédiaire",  taux, "exercices récents"
            else:            return "Débutant",       taux, "exercices récents"

    # Priorité 2 — diagnostic onboarding
    ob = get_onboarding(eleve_id)
    if ob and ob.get("scores"):
        sc_raw = ob["scores"]
        if isinstance(sc_raw, str):
            try: sc_raw = json.loads(sc_raw)
            except: sc_raw = {}
        corresp = {
            "Algorithmique avancée": "Algorithmique avancee",
            "Langage C": "Langage C",
            "HTML et CSS": "HTML et CSS",
            "JavaScript": "JavaScript"
        }
        sc = sc_raw.get(corresp.get(matiere, matiere), {})
        if sc.get("total", 0) > 0:
            taux = round(sc["reussis"] / sc["total"] * 100)
            if taux >= 80:   return "Avancé",        taux, "diagnostic initial"
            elif taux >= 50: return "Intermédiaire",  taux, "diagnostic initial"
            else:            return "Débutant",       taux, "diagnostic initial"

    return "Débutant", 0, "niveau par défaut"


# ══════════════════════════════════════════════════════════════════
# GÉNÉRATION D'UN EXERCICE
# ══════════════════════════════════════════════════════════════════
def generer_exercice(matiere, chapitre, niveau, type_ex,
                     num_ex=1, erreurs=None):
    """Génère un exercice ou le récupère depuis le pool BDD."""

    # Pool BDD en priorité
    ex_pool = get_exercice_pool(matiere, chapitre, niveau, type_ex)
    if ex_pool:
        return ex_pool

    # Sous-difficulté progressive
    sous = (
        "très simple — concept isolé"      if num_ex <= 2 else
        "simple — application directe"     if num_ex <= 4 else
        "standard"                         if num_ex <= 6 else
        "modéré — 2 notions combinées"     if num_ex <= 8 else
        "difficile — limite haute du niveau"
    )

    # Conventions matière
    conv = {
        "Algorithmique avancée": "LDA UNIQUEMENT (JAMAIS Python/C/JS). Structure : Algorithme/Variable/Début.../Fin. Affectation : <-. Lire()/Écrire(). Si/FinSi. Pour/FinPour. TantQue/FinTantQue.",
        "Langage C":             "C99. #include <stdio.h>. int main(){...return 0;}. Déclarer variables. Terminer par ;",
        "HTML et CSS":           "HTML5. <!DOCTYPE html>. Balises fermées. CSS valide. Exemples camerounais.",
        "JavaScript":            "ES6+. Intégré dans HTML. Terminer par ;. DOM si pertinent."
    }.get(matiere, "")

    if matiere == "Algorithmique avancée" and "algorigramme" in chapitre.lower():
        conv = "Symboles officiels camerounais : (DÉBUT/FIN)=ovale, [traitement]=rectangle, /E-S/=parallélogramme, <cond>=losange OUI/NON. Fournir algorigramme ASCII + LDA correspondant."

    # Gabarit par type
    gabarits = {
        "QCM": """QCM : question sur UN concept, 4 propositions A/B/C/D, UNE seule bonne réponse, 3 distracteurs plausibles.
JSON : {"titre":"...","enonce":"Question ?","propositions":{"A":"...","B":"...","C":"...","D":"..."},"reponse_correcte":"B","explication":"Pourquoi B est correct, pourquoi A/C/D sont faux.","code_depart":""}""",

        "QRO": """QRO : question ouverte nécessitant 2-5 phrases. Formulations : Définissez..., Expliquez..., Quelle différence entre...
JSON : {"titre":"...","enonce":"Question ouverte ?","propositions":{},"reponse_correcte":"Réponse modèle 3-5 phrases.","explication":"Éléments clés attendus.","code_depart":""}""",

        "Complétion": """COMPLÉTION : code avec 2-5 blancs marqués _____. Chaque blanc = 1 mot-clé/opérateur précis. Code fonctionnel une fois complété.
JSON : {"titre":"...","enonce":"Complète le code pour qu'il [objectif].","propositions":{},"reponse_correcte":"Code complet avec blancs remplis","explication":"Blanc 1=X car Y. Blanc 2=A car B.","code_depart":"Code avec les _____"}""",

        "Détection": """DÉTECTION : code avec EXACTEMENT UNE erreur réaliste. Élève doit : 1) Identifier 2) Expliquer 3) Corriger.
JSON : {"titre":"...","enonce":"Ce code contient une erreur. Identifie-la, explique et corrige.","propositions":{},"reponse_correcte":"1. Erreur: ... 2. Raison: ... 3. Correction: [code corrigé]","explication":"Impact pédagogique de cette erreur.","code_depart":"Code avec l'erreur"}""",

        "Logique": """LOGIQUE : problème concret camerounais. Énoncé précis : entrées + traitement + sorties + exemple.
JSON : {"titre":"...","enonce":"Contexte. Données:[...]. Écrire un algo/programme qui [...]. Exemple: entrée=[...] → sortie=[...].","propositions":{},"reponse_correcte":"Solution complète et commentée","explication":"Étape 1:... Étape 2:...","code_depart":"Structure de départ si nécessaire"}"""
    }

    ctx_rattrapage = ""
    if erreurs:
        ctx_rattrapage = f"\n⚠️ RATTRAPAGE — Cible ces erreurs :\n" + \
            "\n".join([f"  • {e['question'][:80]} → {e['reponse_eleve'][:60]}"
                       for e in erreurs[:3]])

    prompt = f"""Professeur informatique 1ère TI Cameroun (STI).
Matière:{matiere} | Chapitre:{chapitre} | Niveau:{niveau} | Type:{type_ex}
Exercice {num_ex}/10 — difficulté : {sous}

GABARIT OBLIGATOIRE :
{gabarits.get(type_ex,"")}

CONVENTIONS :
{conv}
{ctx_rattrapage}

Règles : porter sur "{chapitre}", contexte camerounais, solution unique et correcte.
JSON valide uniquement, sans texte avant ou après."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Professeur STI Cameroun. JSON valide UNIQUEMENT. LDA pour algo (jamais Python/C). Gabarit respecté strictement."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=900, temperature=0.5
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        d = raw.find("{"); f = raw.rfind("}") + 1
        if d != -1 and f > d: raw = raw[d:f]
        ex = json.loads(raw)
        if not ex.get("titre") or not ex.get("enonce"):
            raise ValueError("Exercice incomplet")
        sauvegarder_exercice_pool(matiere, chapitre, niveau, type_ex, {
            "titre": ex["titre"], "description": ex["enonce"],
            "code_depart": ex.get("code_depart",""),
            "solution": ex.get("reponse_correcte",""),
            "explication": ex.get("explication","")
        })
        return ex
    except Exception as e:
        st.error(f"Erreur génération : {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# CORRECTION
# ══════════════════════════════════════════════════════════════════
def corriger(exercice, reponse_eleve, type_ex, matiere, niveau):
    criteres = {
        "QCM":        "Vérifie la lettre. Explique pourquoi correcte ou fausse. Mentionne pourquoi les autres sont incorrectes.",
        "QRO":        "Évalue la compréhension, pas la formulation exacte. Correct si notions essentielles présentes.",
        "Complétion": "Vérifie chaque blanc. Correct si TOUS corrects. Indique lequel est faux sinon.",
        "Détection":  "Vérifie les 3 éléments : 1)erreur identifiée 2)explication juste 3)correction exacte. Correct seulement si les 3 sont présents.",
        "Logique":    "Évalue logique + syntaxe. Logique correcte + syntaxe imparfaite = partiellement correct."
    }.get(type_ex, "")

    prompt = f"""Tuteur STI 1ère TI Cameroun. Bienveillant et précis.
Type:{type_ex} | Matière:{matiere} | Niveau:{niveau}
Exercice : {exercice.get("titre","")}
Solution : {exercice.get("reponse_correcte","")[:300]}
Réponse élève : {reponse_eleve}
Critères : {criteres}
- Commence par "Correct !" ou "Pas tout à fait."
- 3-4 phrases max. Encourageant."""

    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250, temperature=0.3
        )
        fb     = r.choices[0].message.content
        reussi = 1 if fb.lower().startswith("correct") else 0
        return fb, reussi
    except Exception as e:
        return f"Erreur : {e}", 0


# ══════════════════════════════════════════════════════════════════
# INDICE
# ══════════════════════════════════════════════════════════════════
def get_indice(exercice, niveau_indice, indices_prec, type_ex, matiere):
    niv = {
        1: "Concept clé seulement. Très vague, pas de code.",
        2: "Piste méthodologique. Pas de solution.",
        3: f"Fragment 1-2 lignes avec blanc.{' LDA uniquement.' if 'Algorithmique' in matiere else ''}"
    }
    hist = f"Déjà donnés : {' | '.join(indices_prec)}" if indices_prec else ""
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f"STI {type_ex}. {exercice.get('titre','')} — {exercice.get('enonce','')[:100]}\n{hist}\nIndice {niveau_indice}/3 : {niv[niveau_indice]}\nJamais la solution. 2 phrases max."}],
            max_tokens=100, temperature=0.5
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Erreur : {e}"


# ══════════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════════
def get_niveau_suivant(niveau):
    idx = NIVEAUX.index(niveau) if niveau in NIVEAUX else 0
    return NIVEAUX[idx + 1] if idx < len(NIVEAUX) - 1 else None

def get_language(matiere):
    return {"Algorithmique avancée":"text","Langage C":"c",
            "HTML et CSS":"html","JavaScript":"javascript"}.get(matiere,"text")

def get_type(num):
    """Type selon position dans la série."""
    return ALTERNANCE_TYPES[(num - 1) % len(ALTERNANCE_TYPES)]


# ══════════════════════════════════════════════════════════════════
# ZONE DE RÉPONSE PAR TYPE
# ══════════════════════════════════════════════════════════════════
def zone_reponse(ex, type_ex, matiere):
    lang = get_language(matiere)

    if ex.get("code_depart","").strip():
        lbl = "Algorithme :" if matiere == "Algorithmique avancée" else "Code :"
        st.markdown(f"**{lbl}**")
        st.code(ex["code_depart"], language=lang)

    if type_ex == "QCM":
        props = ex.get("propositions", {})
        if props:
            return st.radio("**Ta réponse :**",
                            list(props.keys()),
                            format_func=lambda k: f"{k}. {props[k]}",
                            index=None)
        return st.radio("**Ta réponse :**", ["A","B","C","D"], index=None, horizontal=True)

    ph = {
        "QRO":        "Rédigez votre réponse (2 à 5 phrases)...",
        "Complétion": "Recopiez le code complet en remplaçant chaque _____ par la bonne valeur...",
        "Détection":  "1. L'erreur se trouve à : ...\n\n2. Pourquoi c'est une erreur : ...\n\n3. Code corrigé :\n   ...",
        "Logique": {
            "Algorithmique avancée": "Algorithme NomAlgo\nVariable ...\nDébut\n  ...\nFin",
            "Langage C":             "#include <stdio.h>\n\nint main() {\n    \n    return 0;\n}",
            "HTML et CSS":           "<!DOCTYPE html>\n<html>\n<head>...</head>\n<body>\n  ...\n</body>\n</html>",
            "JavaScript":            "// Votre solution\n"
        }
    }.get(type_ex, "Votre réponse...")

    if isinstance(ph, dict): ph = ph.get(matiere, "Votre solution...")
    h = 220 if type_ex in ["Logique","Détection"] else 160
    return st.text_area("**Ta réponse :**", height=h, placeholder=ph)


# ══════════════════════════════════════════════════════════════════
# PAGE PRINCIPALE — même pattern que onboarding.py
# ══════════════════════════════════════════════════════════════════
def page_exercices():
    st.title("🧠 Exercices")

    eleve    = st.session_state["eleve"]
    eleve_id = eleve["id"]

    # ── Étape courante (comme onboarding_etape) ───────────────────
    etape = st.session_state.get("ex_etape", "selection")

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 1 — Sélection matière + chapitre
    # ════════════════════════════════════════════════════════════
    if etape == "selection":
        matieres  = list(COURS.keys())
        col1, col2 = st.columns(2)
        matiere   = col1.selectbox(
            "Matière",
            matieres,
            format_func=lambda m: f"{COURS[m]['icone']} {m}"
        )
        chapitres = [c["titre"] for c in COURS[matiere]["chapitres"]]
        chapitre  = col2.selectbox("Chapitre", chapitres)

        st.divider()

        # Niveau calculé automatiquement
        niveau, taux, source = calculer_niveau(eleve_id, matiere)
        c_niv = {"Débutant":"#E53E3E","Intermédiaire":"#D69E2E","Avancé":"#38A169"}.get(niveau,"#1565C0")
        st.markdown(
            f"""<div style='background:var(--color-background-secondary);
            border-left:3px solid {c_niv};border-radius:8px;
            padding:10px 14px;margin-bottom:1rem;
            display:flex;justify-content:space-between;align-items:center'>
            <span style='font-size:13px;color:#1A237E'>
                🎯 Niveau détecté : <strong>{niveau}</strong>
            </span>
            <span style='font-size:12px;color:var(--color-text-secondary)'>
                {source} — {taux}%
            </span>
            </div>""",
            unsafe_allow_html=True
        )

        if matiere == "Algorithmique avancée":
            st.markdown(
                """<div style='background:#E8F5E9;border-left:3px solid #2E7D32;
                border-radius:8px;padding:8px 12px;font-size:13px;color:#1B5E20;
                margin-bottom:1rem'>
                📌 Algorithmique : pseudo-code LDA uniquement.
                </div>""",
                unsafe_allow_html=True
            )

        if st.button(
            "🚀 Commencer les exercices",
            use_container_width=True,
            type="primary"
        ):
            # Initialiser la progression si nécessaire
            prog = get_progression_exercices(eleve_id, matiere, chapitre, niveau)
            if not prog:
                init_progression_exercices(eleve_id, matiere, chapitre, niveau)

            # Sauvegarder les paramètres de la session
            st.session_state.update({
                "ex_etape":   "exercice",
                "ex_matiere": matiere,
                "ex_chapitre": chapitre,
                "ex_niveau":  niveau,
                "ex_index":   0,        # index dans la série (0-9)
                "ex_serie":   "normale",
                "ex_scores":  {"reussis": 0, "tentes": 0}
            })
            # Nettoyer l'exercice précédent si existant
            for k in ["exercice", "ex_repondu", "indices"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 2 — Série d'exercices (même pattern que diagnostic)
    # ════════════════════════════════════════════════════════════
    elif etape == "exercice":

        matiere  = st.session_state["ex_matiere"]
        chapitre = st.session_state["ex_chapitre"]
        niveau   = st.session_state["ex_niveau"]
        serie    = st.session_state["ex_serie"]
        index    = st.session_state["ex_index"]
        scores   = st.session_state["ex_scores"]
        seuil    = SEUIL_NORMALE if serie == "normale" else SEUIL_RATTRAPAGE

        # ── En-tête ───────────────────────────────────────────
        st.markdown(
            f"""<div style='text-align:center;padding:1rem 0 0.5rem'>
            <h2 style='font-size:1.3rem;font-weight:500;
            color:var(--color-text-primary);margin-bottom:4px'>
                {'🎯 Série de rattrapage' if serie == 'rattrapage' else '📝 Série d\'exercices'}
            </h2>
            <p style='font-size:13px;color:var(--color-text-secondary)'>
                {matiere} · {chapitre} · Niveau {niveau}
            </p>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Barre de progression (identique au diagnostic) ────
        pct = round(index / seuil * 100)
        st.markdown(
            f"""<div style='margin-bottom:1.5rem'>
            <div style='display:flex;justify-content:space-between;
            margin-bottom:6px'>
                <span style='font-size:12px;color:var(--color-text-tertiary)'>
                    Exercice {index + 1} sur {seuil}
                </span>
                <span style='font-size:12px;font-weight:500;color:#1565C0'>
                    ✅ {scores['reussis']}/{scores['tentes']} réussi(s)
                </span>
            </div>
            <div style='background:var(--color-background-secondary);
            border-radius:4px;height:6px'>
                <div style='background:#1565C0;width:{pct}%;
                height:100%;border-radius:4px;transition:width .4s'></div>
            </div>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Exercice en cours ─────────────────────────────────
        if index < seuil:

            # Générer l'exercice si pas encore en session
            if "exercice" not in st.session_state:
                type_ex = get_type(index + 1)
                erreurs = (
                    get_erreurs_recentes(eleve_id, matiere, chapitre, niveau)
                    if serie == "rattrapage" else None
                )
                with st.spinner("L'IA prépare ton exercice..."):
                    ex = generer_exercice(
                        matiere, chapitre, niveau, type_ex,
                        index + 1, erreurs
                    )
                if not ex:
                    st.error("Erreur de génération. Réessaie.")
                    return
                st.session_state["exercice"]   = ex
                st.session_state["ex_type"]    = type_ex
                st.session_state["ex_repondu"] = False
                st.session_state["indices"]    = []
                st.session_state["ex_debut"]   = time.time()

            ex      = st.session_state["exercice"]
            type_ex = st.session_state["ex_type"]
            lang    = get_language(matiere)

            # Badge type + niveau
            ti = TYPES_INFO.get(type_ex, {})
            st.markdown(
                f"""<div style='margin-bottom:1rem'>
                <span style='font-size:11px;font-weight:500;padding:3px 10px;
                border-radius:20px;background:#E3F2FD;color:#1565C0;
                margin-right:6px'>{ti.get('icone','📝')} {ti.get('label',type_ex)}</span>
                <span style='font-size:11px;padding:3px 10px;
                border-radius:20px;background:#F3E5F5;color:#6A1B9A'>
                {niveau}</span>
                {'<span style="font-size:11px;padding:3px 10px;border-radius:20px;background:#FBE9E7;color:#BF360C;margin-left:6px">🔄 Rattrapage</span>' if serie == "rattrapage" else ""}
                </div>""",
                unsafe_allow_html=True
            )

            # Carte énoncé
            st.markdown(
                f"""<div style='background:var(--color-background-primary);
                border:0.5px solid var(--color-border-tertiary);
                border-left:4px solid #1565C0;
                border-radius:var(--border-radius-lg);
                padding:1.25rem 1.5rem;margin-bottom:1.25rem'>
                <p style='font-size:15px;font-weight:500;
                color:var(--color-text-primary);line-height:1.7;margin:0'>
                    {ex.get("titre","")}
                </p>
                <p style='font-size:14px;color:var(--color-text-secondary);
                line-height:1.7;margin:8px 0 0'>
                    {ex.get("enonce","").replace(chr(10),"<br>")}
                </p>
                </div>""",
                unsafe_allow_html=True
            )

                        # Zone réponse
            reponse = zone_reponse(ex, type_ex, matiere)

            # ── Avant vérification ───────────────────────────────────────
            if not st.session_state.get("ex_repondu", False):
                
                # Boutons de contrôle (Vérifier, Indices, Solution)
                col_v, col_i, col_s = st.columns(3)

                if col_v.button(
                    "✓ Vérifier",
                    use_container_width=True,
                    type="primary"
                ):
                    if not reponse:
                        st.warning("Écris d'abord ta réponse !")
                    else:
                        with st.spinner("Correction..."):
                            feedback, reussi = corriger(
                                ex, reponse, type_ex, matiere, niveau
                            )
                            temps = int(time.time() - st.session_state.get("ex_debut", time.time()))

                        # Affichage du feedback
                        if reussi:
                            msgs = ["💪 Continue !", "🌟 Parfait !", "🚀 Excellent !", "👏 Bravo !"]
                            st.success(feedback)
                            st.info(random.choice(msgs))
                        else:
                            st.error(feedback)
                            # Solution immédiate si erreur
                            with st.expander("📖 Solution correcte", expanded=True):
                                sol = ex.get("reponse_correcte", "")
                                if type_ex in ["Complétion","Détection","Logique"]:
                                    st.code(sol, language=lang)
                                else:
                                    st.markdown(f"**Réponse :** {sol}")
                                if ex.get("explication"):
                                    st.info(f"**Explication :** {ex['explication']}")
                            sauvegarder_erreur(
                                eleve_id, matiere, chapitre, niveau,
                                type_ex,
                                ex.get("enonce","")[:200],
                                str(reponse)[:200],
                                ex.get("reponse_correcte","")[:200]
                            )

                        # Mise à jour des scores
                        st.session_state["ex_scores"]["tentes"] += 1
                        if reussi:
                            st.session_state["ex_scores"]["reussis"] += 1
                        
                        st.session_state["ex_repondu"] = True
                        
                        # STOCKER LE FEEDBACK POUR L'AFFICHER À NOUVEAU
                        st.session_state["last_feedback"] = feedback
                        st.session_state["last_reussi"] = reussi
                        st.session_state["last_msgs"] = msgs if reussi else None
                        
                        # RERUN POUR AFFICHER LE BOUTON SUIVANT
                        st.rerun()

                # Indices (avant vérification)
                indices       = st.session_state.get("indices", [])
                niveau_indice = len(indices) + 1
                if niveau_indice <= 3:
                    if col_i.button(
                        f"💡 Indice {niveau_indice}/3",
                        use_container_width=True
                    ):
                        with st.spinner("Réflexion..."):
                            ind = get_indice(
                                ex, niveau_indice, indices, type_ex, matiere
                            )
                            st.session_state["indices"].append(ind)
                            st.rerun()
                else:
                    col_i.button(
                        "Plus d'indices", disabled=True,
                        use_container_width=True
                    )

                for i, ind in enumerate(indices, 1):
                    st.info(f"{'🟡🟠🔴'[i-1]} **Indice {i}/3 :** {ind}")

                if col_s.button("📖 Solution", use_container_width=True):
                    st.code(ex.get("reponse_correcte",""), language=lang)
                    if ex.get("explication"):
                        st.info(f"**Explication :** {ex['explication']}")

            # ── Après vérification ───────────────────────────────────────
            else:
                # RÉAFFICHER LE FEEDBACK (important !)
                if "last_feedback" in st.session_state:
                    if st.session_state.get("last_reussi", False):
                        st.success(st.session_state["last_feedback"])
                        if st.session_state.get("last_msgs"):
                            st.info(random.choice(st.session_state["last_msgs"]))
                    else:
                        st.error(st.session_state["last_feedback"])
                
                # Afficher également la solution si l'exercice était faux
                if not st.session_state.get("last_reussi", False) and "exercice" in st.session_state:
                    with st.expander("📖 Solution correcte", expanded=False):
                        sol = st.session_state["exercice"].get("reponse_correcte", "")
                        if type_ex in ["Complétion","Détection","Logique"]:
                            st.code(sol, language=lang)
                        else:
                            st.markdown(f"**Réponse :** {sol}")
                        if st.session_state["exercice"].get("explication"):
                            st.info(f"**Explication :** {st.session_state['exercice']['explication']}")
                
                st.divider()
                
                # Bouton suivant
                label_suiv = (
                    "📊 Voir mes résultats →"
                    if st.session_state["ex_index"] + 1 >= seuil
                    else f"➡️ Exercice suivant ({st.session_state['ex_index'] + 2}/{seuil})"
                )
                
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if st.button(
                        label_suiv,
                        key=f"next_{st.session_state['ex_index']}",
                        use_container_width=True,
                        type="primary"
                    ):
                        # Incrémenter l'index pour passer à l'exercice suivant
                        st.session_state["ex_index"] += 1
                        # Nettoyer les données de l'exercice courant
                        for k in ["exercice", "ex_repondu", "indices", "ex_type", "ex_debut", "last_feedback", "last_reussi", "last_msgs"]:
                            if k in st.session_state:
                                st.session_state.pop(k, None)
                        st.rerun()

        # ── Fin de série → résultats ──────────────────────────
        else:
            st.session_state["ex_etape"] = "resultats"
            st.rerun()

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 3 — Résultats (même pattern que onboarding)
    # ════════════════════════════════════════════════════════════
    elif etape == "resultats":

        matiere  = st.session_state["ex_matiere"]
        chapitre = st.session_state["ex_chapitre"]
        niveau   = st.session_state["ex_niveau"]
        serie    = st.session_state["ex_serie"]
        scores   = st.session_state["ex_scores"]
        seuil    = SEUIL_NORMALE if serie == "normale" else SEUIL_RATTRAPAGE

        reussis = scores["reussis"]
        tentes  = scores["tentes"]
        pct     = round(reussis / tentes * 100) if tentes > 0 else 0

        emoji, msg, couleur = (
            ("🏆", "Parfait !",            "#38A169") if pct == 100 else
            ("🎉", "Excellent !",           "#38A169") if pct >= 80  else
            ("👍", "Bon travail !",         "#D69E2E") if pct >= 60  else
            ("💪", "Continue tes efforts !", "#E53E3E")
        )

        # En-tête résultats
        st.markdown(
            f"""<div style='text-align:center;padding:1.5rem 0 1rem'>
            <h2 style='font-size:1.4rem;font-weight:500;
            color:var(--color-text-primary);margin-bottom:0.5rem'>
                Tes résultats
            </h2>
            <p style='font-size:13px;color:var(--color-text-secondary)'>
                {matiere} · {chapitre} · Niveau {niveau}
            </p>
            </div>""",
            unsafe_allow_html=True
        )

        # Score final
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            st.markdown(
                f"""<div style='background:white;border:2px solid {couleur};
                border-radius:16px;padding:2rem;text-align:center'>
                <div style='font-size:48px'>{emoji}</div>
                <div style='font-size:40px;font-weight:700;
                color:{couleur};margin:8px 0'>{pct}%</div>
                <div style='font-size:17px;font-weight:500;
                color:#1A237E'>{msg}</div>
                <div style='font-size:14px;
                color:var(--color-text-secondary);margin-top:6px'>
                    {reussis} réussi(s) sur {tentes} exercices
                    {'— Rattrapage' if serie == 'rattrapage' else ''}
                </div>
                </div>""",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Décision selon score ──────────────────────────────
        if serie == "normale":
            if pct == 100:
                # 10/10 → niveau supérieur
                valider_niveau(eleve_id, matiere, chapitre, niveau)
                nv = get_niveau_suivant(niveau)
                st.balloons()
                if nv:
                    st.success(
                        f"🎉 Niveau **{niveau}** maîtrisé ! "
                        f"Tu passes au niveau **{nv}** !"
                    )
                else:
                    st.success("🏆 Tous les niveaux maîtrisés !")

                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if nv:
                        if st.button(
                            f"🚀 Continuer en {nv}",
                            use_container_width=True,
                            type="primary"
                        ):
                            st.session_state.update({
                                "ex_etape":  "selection",
                                "ex_niveau": nv
                            })
                            for k in ["exercice","ex_repondu","indices",
                                      "ex_type","ex_debut","ex_index",
                                      "ex_scores","ex_serie"]:
                                st.session_state.pop(k, None)
                            st.rerun()
                    if st.button(
                        "🔁 Autre chapitre",
                        use_container_width=True
                    ):
                        for k in ["ex_etape","ex_matiere","ex_chapitre",
                                  "ex_niveau","ex_index","ex_scores",
                                  "ex_serie","exercice","ex_repondu",
                                  "indices","ex_type","ex_debut"]:
                            st.session_state.pop(k, None)
                        st.rerun()
            else:
                # Score insuffisant → rattrapage
                reset_rattrapage(eleve_id, matiere, chapitre, niveau)
                st.warning(
                    f"💪 {reussis}/{tentes} — "
                    f"{SEUIL_RATTRAPAGE} exercices ciblés sur tes erreurs t'attendent !"
                )
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if st.button(
                        "🎯 Commencer le rattrapage",
                        use_container_width=True,
                        type="primary"
                    ):
                        st.session_state.update({
                            "ex_etape":  "exercice",
                            "ex_serie":  "rattrapage",
                            "ex_index":  0,
                            "ex_scores": {"reussis": 0, "tentes": 0}
                        })
                        for k in ["exercice","ex_repondu","indices",
                                  "ex_type","ex_debut"]:
                            st.session_state.pop(k, None)
                        st.rerun()

        else:  # rattrapage
            if pct == 100:
                # Rattrapage réussi → niveau supérieur
                valider_niveau(eleve_id, matiere, chapitre, niveau)
                nv = get_niveau_suivant(niveau)
                st.balloons()
                st.success(
                    f"🎉 Excellent rattrapage ! "
                    f"Tu passes au niveau **{nv or 'suivant'}** !"
                )
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if nv and st.button(
                        f"🚀 Continuer en {nv}",
                        use_container_width=True,
                        type="primary"
                    ):
                        st.session_state.update({
                            "ex_etape":  "selection",
                            "ex_niveau": nv
                        })
                        for k in ["exercice","ex_repondu","indices",
                                  "ex_type","ex_debut","ex_index",
                                  "ex_scores","ex_serie"]:
                            st.session_state.pop(k, None)
                        st.rerun()
            else:
                # Rattrapage insuffisant → cours
                st.error(
                    f"📚 {reussis}/{tentes} — "
                    f"Je te recommande de revoir le cours avant de continuer."
                )
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    c1, c2 = st.columns(2)
                    if c1.button("📖 Revoir le cours", use_container_width=True):
                        st.session_state.update({
                            "cours_theme":    matiere,
                            "cours_chapitre": chapitre,
                            "page":           "📖 Cours"
                        })
                        st.rerun()
                    if c2.button("🔄 Réessayer", use_container_width=True):
                        reset_rattrapage(eleve_id, matiere, chapitre, niveau)
                        st.session_state.update({
                            "ex_etape":  "exercice",
                            "ex_serie":  "rattrapage",
                            "ex_index":  0,
                            "ex_scores": {"reussis": 0, "tentes": 0}
                        })
                        for k in ["exercice","ex_repondu","indices",
                                  "ex_type","ex_debut"]:
                            st.session_state.pop(k, None)
                        st.rerun()

    # ── Admin ─────────────────────────────────────────────────
    if st.session_state.get("admin_auth", False):
        with st.expander("⚙️ Options admin"):
            c1, c2 = st.columns(2)
            matiere_admin  = st.session_state.get("ex_matiere", "")
            chapitre_admin = st.session_state.get("ex_chapitre", "")
            niveau_admin   = st.session_state.get("ex_niveau", "")
            type_admin     = st.session_state.get("ex_type", "")
            if c1.button("🔄 Vider ce pool", use_container_width=True):
                import requests as req
                from database import supabase_url, headers
                try:
                    req.delete(
                        f"{supabase_url()}/rest/v1/exercices_contenu",
                        headers=headers(),
                        params={
                            "theme":    f"eq.{matiere_admin}",
                            "chapitre": f"eq.{chapitre_admin}",
                            "niveau":   f"eq.{niveau_admin}",
                            "type_ex":  f"eq.{type_admin}"
                        }
                    )
                    st.success("Pool vidé.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
            if c2.button("🗑️ Vider matière", use_container_width=True):
                import requests as req
                from database import supabase_url, headers
                try:
                    req.delete(
                        f"{supabase_url()}/rest/v1/exercices_contenu",
                        headers=headers(),
                        params={"theme": f"eq.{matiere_admin}"}
                    )
                    st.success("Pool matière vidé.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
