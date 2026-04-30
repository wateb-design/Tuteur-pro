import streamlit as st
import json
import re
import time
from groq import Groq
from database import inserer_resultat, get_stats_eleve

# ── Import des thèmes depuis cours.py ────────────────────────────
# On importe directement le dictionnaire COURS pour avoir
# exactement les mêmes matières et chapitres que dans cours.py.
# Si on ajoute une matière dans cours.py, elle apparaît ici automatiquement.
from cours import COURS

# ── Client Groq ───────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Niveaux disponibles ───────────────────────────────────────────
NIVEAUX = ["Facile", "Moyen", "Difficile"]

# ── Types d'exercices ─────────────────────────────────────────────
# 4 types définis dans le cahier des charges (section 4.3)
TYPES = ["Compléter le code", "QCM", "Exercice de logique", "Détecter l'erreur"]


# ── Génération d'un exercice via Groq ─────────────────────────────
# On précise la matière, le chapitre, le niveau ET le type
# pour que Groq génère un exercice vraiment ciblé.
def generer_exercice(matiere, chapitre, niveau, type_ex):
    prompt = f"""Tu es un professeur expert en informatique pour élèves de 1ère TI au Cameroun.
Génère un exercice de type "{type_ex}" sur le chapitre "{chapitre}" (matière : {matiere}, niveau : {niveau}).

Réponds UNIQUEMENT en JSON sans texte avant ou après :
{{
  "titre": "titre court de l'exercice",
  "description": "énoncé clair en 2-3 phrases",
  "code_depart": "code de départ si nécessaire, sinon chaîne vide",
  "solution": "solution complète et commentée",
  "verification": "ce que le code/réponse doit produire"
}}

Instructions selon le type :
- "Compléter le code" : fournir un code avec des blancs à remplir (marquer les blancs avec _____)
- "QCM" : poser une question avec 4 choix A/B/C/D dans la description, indiquer la bonne réponse dans solution
- "Exercice de logique" : problème algorithmique à résoudre étape par étape
- "Détecter l'erreur" : fournir un code avec une erreur intentionnelle dans code_depart"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.7
    )

    raw = response.choices[0].message.content
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


# ── Correction de la réponse de l'élève ──────────────────────────
# Groq analyse la réponse selon le type d'exercice.
# Pour un QCM → vérifie la lettre. Pour du code → analyse la logique.
def corriger_reponse(exercice, reponse_eleve, type_ex):
    prompt = f"""Tu es un tuteur pédagogique bienveillant pour élèves de 1ère TI.
Type d'exercice : {type_ex}
Exercice : {exercice['titre']}
Description : {exercice['description']}
Solution attendue : {exercice['solution']}
Réponse de l'élève : {reponse_eleve}

Évalue la réponse en 2-3 phrases.
- Si correct : commence OBLIGATOIREMENT par "Correct !"
- Si incorrect : commence OBLIGATOIREMENT par "Pas tout à fait."
Explique pourquoi et donne une piste d'amélioration."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.3
    )

    feedback = response.choices[0].message.content
    reussi = 1 if feedback.lower().startswith("correct") else 0
    return feedback, reussi


# ── Génération d'un indice progressif ────────────────────────────
# 3 niveaux d'indices de plus en plus précis.
# On passe les indices déjà donnés pour éviter les répétitions.
def get_indice(exercice, niveau_indice, indices_precedents, type_ex):
    instructions = {
        1: "Oriente vers le concept clé. Sois très vague, pas de code.",
        2: "Donne une piste concrète sur la méthode. Toujours pas de code complet.",
        3: "Montre un tout petit fragment (1-2 lignes max) avec un blanc à remplir."
    }

    historique = ""
    if indices_precedents:
        historique = f"Indices déjà donnés : {' | '.join(indices_precedents)}"

    prompt = f"""Tu es un tuteur pédagogique pour élèves de 1ère TI.
Type d'exercice : {type_ex}
Exercice : {exercice['titre']} — {exercice['description']}
{historique}

Donne un indice de niveau {niveau_indice}/3.
Instruction : {instructions[niveau_indice]}
Ne donne JAMAIS la solution complète. Sois encourageant. Max 3 phrases."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.5
    )
    return response.choices[0].message.content


# ── Page principale des exercices ─────────────────────────────────
def page_exercices():
    st.title("🧠 Exercices")

    eleve = st.session_state["eleve"]

    # ── Sélection de la matière ───────────────────────────────────
    # On construit la liste des matières depuis COURS importé de cours.py
    matieres = list(COURS.keys())
    matiere = st.selectbox(
        "Matière",
        matieres,
        format_func=lambda m: f"{COURS[m]['icone']} {m}"
    )

    # ── Sélection du chapitre selon la matière choisie ────────────
    # La liste des chapitres change dynamiquement selon la matière.
    chapitres = [c["titre"] for c in COURS[matiere]["chapitres"]]
    chapitre = st.selectbox("Chapitre", chapitres)

    # ── Sélection du niveau et du type ────────────────────────────
    col1, col2 = st.columns(2)
    niveau  = col1.selectbox("Niveau",          NIVEAUX)
    type_ex = col2.selectbox("Type d'exercice", TYPES)

    # ── Bouton de génération ──────────────────────────────────────
    if st.button("Générer un exercice ✨", use_container_width=True):
        with st.spinner("L'IA prépare ton exercice..."):
            try:
                ex = generer_exercice(matiere, chapitre, niveau, type_ex)
                st.session_state["exercice"] = ex
                st.session_state["matiere"]  = matiere
                st.session_state["chapitre"] = chapitre
                st.session_state["niveau"]   = niveau
                st.session_state["type_ex"]  = type_ex
                st.session_state["indices"]  = []
                st.session_state["debut"]    = time.time()
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")

    # ── Affichage de l'exercice ───────────────────────────────────
    if "exercice" not in st.session_state:
        return

    ex      = st.session_state["exercice"]
    type_ex = st.session_state.get("type_ex", "Compléter le code")

    st.divider()

    # Badge matière + chapitre
    st.caption(
        f"{COURS[st.session_state['matiere']]['icone']} "
        f"{st.session_state['matiere']} · "
        f"{st.session_state['chapitre']} · "
        f"{st.session_state['niveau']}"
    )
    st.subheader(ex["titre"])
    st.write(ex["description"])

    # Code de départ (affiché si présent)
    if ex.get("code_depart", "").strip():
        lang = "c" if st.session_state["matiere"] == "Langage C" else \
               "html" if st.session_state["matiere"] == "HTML et CSS" else \
               "javascript" if st.session_state["matiere"] == "Introduction au JavaScript" else \
               "text"
        st.markdown("**Code de départ :**")
        st.code(ex["code_depart"], language=lang)

    # Zone de réponse adaptée au type d'exercice
    if type_ex == "QCM":
        reponse = st.radio(
            "Ta réponse :",
            ["A", "B", "C", "D"],
            index=None,
            horizontal=True
        )
    else:
        reponse = st.text_area(
            "Ta réponse :",
            height=150,
            placeholder="Écris ta réponse ici..."
        )

    # ── Boutons d'action ──────────────────────────────────────────
    col_verif, col_indice, col_solution = st.columns(3)

    # Bouton Vérifier
    if col_verif.button("Vérifier ✓", use_container_width=True):
        if not reponse:
            st.warning("Écris d'abord ta réponse !")
        else:
            with st.spinner("Correction en cours..."):
                feedback, reussi = corriger_reponse(ex, reponse, type_ex)
                temps = int(time.time() - st.session_state.get("debut", time.time()))

                if reussi:
                    st.success(feedback)
                    st.balloons()
                else:
                    st.error(feedback)

                # Sauvegarde en base Supabase
                inserer_resultat(
                    eleve_id=eleve["id"],
                    theme=st.session_state["matiere"],
                    niveau=st.session_state["niveau"],
                    reussi=reussi,
                    temps=temps
                )

                stats = get_stats_eleve(eleve["id"])
                st.caption(f"Ton taux de réussite global : {stats['taux']}%")

    # Bouton Indice (max 3)
    indices       = st.session_state.get("indices", [])
    niveau_indice = len(indices) + 1

    if niveau_indice <= 3:
        if col_indice.button(f"Indice {niveau_indice}/3", use_container_width=True):
            with st.spinner("Réflexion..."):
                indice = get_indice(ex, niveau_indice, indices, type_ex)
                st.session_state["indices"].append(indice)
                st.rerun()
    else:
        col_indice.button("Plus d'indices", disabled=True, use_container_width=True)

    # Affichage des indices demandés
    if indices:
        couleurs = {1: "🟡", 2: "🟠", 3: "🔴"}
        for i, ind in enumerate(indices, 1):
            st.info(f"{couleurs[i]} **Indice {i}/3 :** {ind}")

    # Bouton Solution
    if col_solution.button("Solution", use_container_width=True):
        st.markdown("**Solution complète :**")
        st.code(ex["solution"], language="python")
        st.caption("Essaie de bien comprendre avant de passer à l'exercice suivant.")
