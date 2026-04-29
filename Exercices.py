import streamlit as st
import json
import re
import time
from groq import Groq
from database import inserer_resultat, get_stats_eleve

# ── Initialisation du client Groq ─────────────────────────────────
# On récupère la clé API depuis les secrets Streamlit (jamais en dur).
# Ce client est utilisé pour générer les exercices ET les corrections.
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Thèmes et niveaux disponibles ─────────────────────────────────
# Centralisés ici pour ne pas les réécrire dans chaque fonction.
THEMES = ["Python — bases", "Streamlit", "Groq Cloud", "SQLite"]
NIVEAUX = ["Facile", "Moyen", "Difficile"]


# ── Génération d'un exercice via Groq ─────────────────────────────
# On envoie un prompt structuré à Groq et on lui demande
# de répondre UNIQUEMENT en JSON pour pouvoir parser la réponse.
# Le modèle llama3-8b-8192 est rapide et suffisant pour ce cas.
def generer_exercice(theme, niveau):
    prompt = f"""Tu es un professeur de programmation pour élèves de 1ère TI au Cameroun.
Génère un exercice de niveau {niveau} sur le thème : {theme}.

Réponds UNIQUEMENT en JSON, sans texte avant ou après, avec ce format exact :
{{
  "titre": "titre court de l'exercice",
  "description": "énoncé clair en 2-3 phrases",
  "code_depart": "code Python de départ (laisser vide si pas nécessaire)",
  "solution": "code Python complet de la solution",
  "verification": "ce que le code doit produire ou retourner"
}}"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.7  # Un peu de variété dans les exercices générés
    )

    # Nettoyage de la réponse : Groq peut ajouter des ```json ... ```
    # re.sub supprime ces balises markdown si elles sont présentes
    raw = response.choices[0].message.content
    raw = re.sub(r"```json|```", "", raw).strip()

    # json.loads convertit la chaîne JSON en dictionnaire Python
    return json.loads(raw)


# ── Correction de la réponse de l'élève via Groq ──────────────────
# On envoie l'exercice + la solution attendue + la réponse de l'élève.
# Groq analyse et retourne un feedback pédagogique personnalisé.
# On détecte si c'est correct en vérifiant le début de la réponse.
def corriger_reponse(exercice, reponse_eleve):
    prompt = f"""Tu es un tuteur pédagogique bienveillant pour élèves de 1ère TI.
Exercice : {exercice['titre']}
Description : {exercice['description']}
Solution attendue : {exercice['solution']}
Réponse de l'élève : {reponse_eleve}

Évalue la réponse en 2-3 phrases maximum.
- Si correct : commence OBLIGATOIREMENT par "Correct !"
- Si incorrect : commence OBLIGATOIREMENT par "Pas tout à fait."
Explique pourquoi et donne une piste d'amélioration si nécessaire."""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.3  # Moins de variété pour la correction → plus fiable
    )

    feedback = response.choices[0].message.content
    # On détecte le résultat en vérifiant le premier mot de la réponse
    reussi = 1 if feedback.lower().startswith("correct") else 0
    return feedback, reussi


# ── Génération d'un indice progressif ────────────────────────────
# niveau_indice va de 1 à 3 :
#   1 → concept général, très vague
#   2 → piste concrète sans code
#   3 → fragment de code partiel
# On passe les indices déjà donnés pour éviter les répétitions.
def get_indice(exercice, niveau_indice, indices_precedents):
    instructions = {
        1: "Oriente vers le concept clé à utiliser. Sois très vague, pas de code.",
        2: "Donne une piste concrète sur la méthode. Toujours pas de code complet.",
        3: "Montre un tout petit fragment de code (1-2 lignes max) avec un blanc à remplir."
    }

    historique = ""
    if indices_precedents:
        historique = f"Indices déjà donnés : {' | '.join(indices_precedents)}"

    prompt = f"""Tu es un tuteur pédagogique pour élèves de 1ère TI.
Exercice : {exercice['titre']} — {exercice['description']}
{historique}

Donne un indice de niveau {niveau_indice}/3.
Instruction : {instructions[niveau_indice]}
Ne donne JAMAIS la solution complète. Sois encourageant. Max 3 phrases."""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.5
    )
    return response.choices[0].message.content


# ── Page principale des exercices ─────────────────────────────────
# Appelée depuis app.py avec : from exercices import page_exercices
# Elle utilise st.session_state pour conserver l'exercice en cours
# entre les interactions (clics sur boutons).
def page_exercices():
    st.title("🧠 Exercices")

    eleve = st.session_state["eleve"]  # Récupéré depuis la session auth

    # ── Sélection du thème et du niveau ──────────────────────────
    col1, col2 = st.columns(2)
    theme = col1.selectbox("Thème", THEMES)
    niveau = col2.selectbox("Niveau", NIVEAUX)

    # ── Bouton de génération ──────────────────────────────────────
    if st.button("Générer un exercice", use_container_width=True):
        with st.spinner("L'IA prépare ton exercice..."):
            try:
                ex = generer_exercice(theme, niveau)
                # On sauvegarde l'exercice dans la session pour y accéder
                # après que l'élève ait cliqué sur "Vérifier" ou "Indice"
                st.session_state["exercice"] = ex
                st.session_state["theme"]    = theme
                st.session_state["niveau"]   = niveau
                st.session_state["indices"]  = []      # Réinitialise les indices
                st.session_state["debut"]    = time.time()  # Chronomètre
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")

    # ── Affichage de l'exercice en cours ──────────────────────────
    # On vérifie si un exercice est stocké en session avant d'afficher
    if "exercice" in st.session_state:
        ex = st.session_state["exercice"]

        st.divider()
        st.subheader(ex["titre"])
        st.write(ex["description"])

        # Code de départ (affiché uniquement s'il n'est pas vide)
        if ex.get("code_depart", "").strip():
            st.markdown("**Code de départ :**")
            st.code(ex["code_depart"], language="python")

        # Zone de saisie de la réponse
        reponse = st.text_area(
            "Ta réponse (code Python) :",
            height=160,
            placeholder="Écris ton code ici..."
        )

        # ── Boutons d'action ──────────────────────────────────────
        col_verif, col_indice, col_solution = st.columns(3)

        # Bouton Vérifier
        if col_verif.button("Vérifier ✓", use_container_width=True):
            if not reponse.strip():
                st.warning("Écris d'abord ton code avant de vérifier !")
            else:
                with st.spinner("Correction en cours..."):
                    feedback, reussi = corriger_reponse(ex, reponse)

                    # Calcul du temps passé sur l'exercice (en secondes)
                    temps = int(time.time() - st.session_state.get("debut", time.time()))

                    # Affichage du feedback avec couleur selon résultat
                    if reussi:
                        st.success(feedback)
                        st.balloons()  # Petite célébration !
                    else:
                        st.error(feedback)

                    # Sauvegarde du résultat en base de données
                    inserer_resultat(
                        eleve_id=eleve["id"],
                        theme=st.session_state["theme"],
                        niveau=st.session_state["niveau"],
                        reussi=reussi,
                        temps=temps
                    )

                    # Affichage des stats mises à jour
                    stats = get_stats_eleve(eleve["id"])
                    st.caption(f"Ton taux de réussite global : {stats['taux']}%")

        # Bouton Indice (max 3 indices par exercice)
        indices = st.session_state.get("indices", [])
        niveau_indice = len(indices) + 1

        if niveau_indice <= 3:
            label = f"Indice {niveau_indice}/3"
            if col_indice.button(label, use_container_width=True):
                with st.spinner("Réflexion..."):
                    indice = get_indice(ex, niveau_indice, indices)
                    st.session_state["indices"].append(indice)
                    st.rerun()  # Recharge pour afficher le nouvel indice
        else:
            col_indice.button("Plus d'indices", disabled=True, use_container_width=True)

        # Affichage de tous les indices déjà demandés
        if indices:
            for i, ind in enumerate(indices, 1):
                couleurs = {1: "🟡", 2: "🟠", 3: "🔴"}
                st.info(f"{couleurs[i]} **Indice {i}/3 :** {ind}")

        # Bouton Solution (révèle la solution complète)
        if col_solution.button("Solution", use_container_width=True):
            st.markdown("**Solution complète :**")
            st.code(ex["solution"], language="python")
            st.caption("Essaie de bien comprendre avant de passer à l'exercice suivant.")
