import streamlit as st
from groq import Groq
import json
import re

# ── Client Groq ───────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Contenu des cours mis à jour pour 1ère TI ─────────────────────
# 4 matières du programme : Algorithmique avancé, Langage C,
# HTML/CSS, Introduction au JavaScript
COURS = {
    "Algorithmique avancé": {
        "icone": "🧠",
        "chapitres": [
            {
                "titre": "Rappels sur les algorithmes",
                "description": "Structure d'un algorithme, variables, entrées/sorties"
            },
            {
                "titre": "Structures conditionnelles",
                "description": "Si/Sinon, selon/cas — prise de décision dans un algorithme"
            },
            {
                "titre": "Structures répétitives",
                "description": "Pour, TantQue, Répéter — les boucles en algorithmique"
            },
            {
                "titre": "Tableaux et listes",
                "description": "Déclaration, parcours et manipulation de tableaux"
            },
            {
                "titre": "Sous-programmes",
                "description": "Procédures et fonctions — modulariser un algorithme"
            },
            {
                "titre": "Tri et recherche",
                "description": "Algorithmes de tri (bulles, sélection) et de recherche"
            },
        ]
    },
    "Langage C": {
        "icone": "⚙️",
        "chapitres": [
            {
                "titre": "Introduction au C",
                "description": "Structure d'un programme C, compilation, premier Hello World"
            },
            {
                "titre": "Variables et types",
                "description": "int, float, char, double — déclarer et utiliser des variables"
            },
            {
                "titre": "Opérateurs et expressions",
                "description": "Opérateurs arithmétiques, relationnels et logiques"
            },
            {
                "titre": "Structures de contrôle",
                "description": "if/else, switch, for, while, do/while en langage C"
            },
            {
                "titre": "Fonctions",
                "description": "Déclaration, définition, appel et retour de fonctions"
            },
            {
                "titre": "Tableaux et pointeurs",
                "description": "Tableaux à une dimension, pointeurs et adresses mémoire"
            },
        ]
    },
    "HTML et CSS": {
        "icone": "🌐",
        "chapitres": [
            {
                "titre": "Introduction au HTML",
                "description": "Structure d'une page web, balises de base, doctype"
            },
            {
                "titre": "Balises essentielles",
                "description": "Titres, paragraphes, liens, images, listes"
            },
            {
                "titre": "Formulaires HTML",
                "description": "input, select, textarea, button — collecter des données"
            },
            {
                "titre": "Introduction au CSS",
                "description": "Sélecteurs, propriétés, liaison CSS/HTML"
            },
            {
                "titre": "Mise en page CSS",
                "description": "Box model, display, flexbox — organiser les éléments"
            },
            {
                "titre": "Styles avancés",
                "description": "Couleurs, polices, bordures, ombres et animations simples"
            },
        ]
    },
    "Introduction au JavaScript": {
        "icone": "✨",
        "chapitres": [
            {
                "titre": "Introduction au JavaScript",
                "description": "Rôle du JS, liaison avec HTML, console.log, premiers scripts"
            },
            {
                "titre": "Variables et types",
                "description": "var, let, const — types string, number, boolean"
            },
            {
                "titre": "Conditions et boucles",
                "description": "if/else, for, while — contrôler le flux en JavaScript"
            },
            {
                "titre": "Fonctions",
                "description": "Déclaration, appel, paramètres et valeur de retour"
            },
            {
                "titre": "Manipulation du DOM",
                "description": "getElementById, innerHTML, addEventListener — interagir avec la page"
            },
            {
                "titre": "Événements",
                "description": "onclick, onmouseover, onsubmit — réagir aux actions utilisateur"
            },
        ]
    },
}

NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"]


# ── Génération du contenu d'un chapitre via Groq ──────────────────
# @st.cache_data évite de rappeler Groq si l'élève revient
# sur le même chapitre — économise du temps et des tokens.
@st.cache_data(show_spinner=False)
def generer_contenu(theme, chapitre, niveau):
    prompt = f"""Tu es un professeur expert en informatique pour élèves de 1ère TI au Cameroun.
Rédige un cours clair sur : "{chapitre}" (matière : {theme}, niveau : {niveau}).

Structure ta réponse EXACTEMENT ainsi :
## Explication
(2-3 paragraphes clairs, langage simple, adapté au niveau {niveau})

## Exemple de code
(un bloc de code commenté, adapté au niveau {niveau})

## À retenir
(3 points essentiels sous forme de liste)

## Erreurs fréquentes
(2 erreurs courantes que font les élèves sur ce sujet)"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",   # ← modèle mis à jour
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        temperature=0.4
    )
    return response.choices[0].message.content


# ── Génération d'un quiz QCM ──────────────────────────────────────
# Une question générée par Groq après chaque chapitre
# pour tester la compréhension de l'élève.
@st.cache_data(show_spinner=False)
def generer_quiz(theme, chapitre, niveau):
    prompt = f"""Génère une question QCM sur "{chapitre}" (matière : {theme}, niveau : {niveau}).
Réponds UNIQUEMENT en JSON sans texte avant ou après :
{{
  "question": "...",
  "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "reponse": "A",
  "explication": "..."
}}"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",   # ← modèle mis à jour
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.5
    )
    raw = response.choices[0].message.content
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


# ── Page principale des cours ─────────────────────────────────────
def page_cours():
    st.title("📖 Cours")

    # ── Sélection du thème ────────────────────────────────────────
    st.markdown("#### Choisis une matière")

    cols = st.columns(4)
    for i, (theme, data) in enumerate(COURS.items()):
        if cols[i].button(
            f"{data['icone']} {theme}",
            use_container_width=True,
            key=f"theme_{i}"
        ):
            st.session_state["cours_theme"]    = theme
            st.session_state["cours_chapitre"] = None
            st.rerun()

    if "cours_theme" not in st.session_state:
        st.info("👆 Choisis une matière pour commencer.")
        return

    theme = st.session_state["cours_theme"]
    data  = COURS[theme]

    st.divider()
    st.markdown(f"#### {data['icone']} {theme} — Chapitres")

    # Niveau d'explication adaptatif
    niveau = st.select_slider(
        "Niveau d'explication",
        options=NIVEAUX,
        value="Débutant"
    )

    # Liste des chapitres
    for j, chap in enumerate(data["chapitres"], 1):
        col_btn, col_desc = st.columns([1, 3])
        if col_btn.button(f"Chapitre {j}", key=f"chap_{j}", use_container_width=True):
            st.session_state["cours_chapitre"] = chap["titre"]
            st.session_state["cours_niveau"]   = niveau
            st.session_state["quiz_repondu"]   = False
            st.rerun()
        col_desc.markdown(
            f"**{chap['titre']}**  \n"
            f"<span style='font-size:13px;color:gray'>{chap['description']}</span>",
            unsafe_allow_html=True
        )

    if not st.session_state.get("cours_chapitre"):
        return

    chapitre = st.session_state["cours_chapitre"]
    niveau   = st.session_state.get("cours_niveau", "Débutant")

    st.divider()
    st.markdown(f"### 📘 {chapitre}")
    st.caption(f"Matière : {theme} · Niveau : {niveau}")

    # Génération et affichage du contenu
    with st.spinner("Groq génère ton cours..."):
        contenu = generer_contenu(theme, chapitre, niveau)
    st.markdown(contenu)

    # ── Quiz de compréhension ─────────────────────────────────────
    st.divider()
    st.markdown("#### 🧪 Teste ta compréhension")

    if "quiz_actuel" not in st.session_state or \
       st.session_state.get("quiz_chapitre") != chapitre:
        with st.spinner("Préparation du quiz..."):
            try:
                st.session_state["quiz_actuel"]   = generer_quiz(theme, chapitre, niveau)
                st.session_state["quiz_chapitre"] = chapitre
                st.session_state["quiz_repondu"]  = False
            except Exception as e:
                st.warning(f"Quiz indisponible : {e}")
                return

    quiz = st.session_state["quiz_actuel"]
    st.write(quiz["question"])
    choix = st.radio("Ta réponse :", quiz["choix"], index=None)

    if choix and not st.session_state.get("quiz_repondu"):
        lettre_choisie  = choix[0]
        lettre_correcte = quiz["reponse"]
        if lettre_choisie == lettre_correcte:
            st.success("Bonne réponse ! 🎉")
        else:
            st.error(f"Pas tout à fait. La bonne réponse était : {lettre_correcte}")
        st.info(f"**Explication :** {quiz['explication']}")
        st.session_state["quiz_repondu"] = True

    # Bouton chapitre suivant
    st.divider()
    chapitres_liste = [c["titre"] for c in data["chapitres"]]
    idx_actuel = chapitres_liste.index(chapitre)

    if idx_actuel < len(chapitres_liste) - 1:
        if st.button("Chapitre suivant →", use_container_width=True):
            st.session_state["cours_chapitre"] = chapitres_liste[idx_actuel + 1]
            st.session_state["quiz_repondu"]   = False
            st.rerun()
    else:
        st.success("Tu as terminé tous les chapitres de cette matière ! 🎉")
        if st.button("Aller aux exercices →", use_container_width=True):
            st.session_state["page"] = "🧠 Exercices"
            st.rerun()
