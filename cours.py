import streamlit as st
from groq import Groq

# ── Client Groq ───────────────────────────────────────────────────
# Même pattern que dans exercices.py : clé API depuis les secrets.
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Contenu des cours ─────────────────────────────────────────────
# Dictionnaire qui structure tout le programme.
# Chaque thème contient ses chapitres avec un titre et une description.
# Groq génère le contenu détaillé à la demande — on ne stocke pas
# tout en dur pour garder le fichier léger et le contenu dynamique.
COURS = {
    "Python — bases": {
        "icone": "🐍",
        "chapitres": [
            {
                "titre": "Variables et types",
                "description": "int, float, str, bool — déclarer et utiliser des variables"
            },
            {
                "titre": "Conditions",
                "description": "if, elif, else — prendre des décisions dans le code"
            },
            {
                "titre": "Boucles",
                "description": "for, while — répéter des instructions"
            },
            {
                "titre": "Fonctions",
                "description": "def, return — organiser et réutiliser le code"
            },
            {
                "titre": "Listes et tableaux",
                "description": "Créer, parcourir et manipuler des collections de données"
            },
        ]
    },
    "Streamlit": {
        "icone": "📊",
        "chapitres": [
            {
                "titre": "Introduction à Streamlit",
                "description": "Créer une application web en Python en quelques lignes"
            },
            {
                "titre": "Widgets interactifs",
                "description": "st.button, st.selectbox, st.text_input, st.slider…"
            },
            {
                "titre": "Mise en page",
                "description": "st.columns, st.sidebar, st.tabs — organiser l'interface"
            },
            {
                "titre": "Affichage de données",
                "description": "st.dataframe, st.metric, st.chart — visualiser des données"
            },
            {
                "titre": "Session state",
                "description": "Conserver des données entre les interactions utilisateur"
            },
        ]
    },
    "Groq Cloud": {
        "icone": "⚡",
        "chapitres": [
            {
                "titre": "Introduction aux LLM",
                "description": "Qu'est-ce qu'un modèle de langage et comment l'utiliser"
            },
            {
                "titre": "API Groq",
                "description": "Connexion, authentification et premier appel à l'API"
            },
            {
                "titre": "Prompts efficaces",
                "description": "Comment bien formuler une instruction pour obtenir le bon résultat"
            },
            {
                "titre": "Réponses structurées",
                "description": "Demander du JSON à Groq et parser la réponse en Python"
            },
            {
                "titre": "Intégration Streamlit + Groq",
                "description": "Construire une app IA complète avec les deux outils"
            },
        ]
    },
    "SQLite": {
        "icone": "🗄️",
        "chapitres": [
            {
                "titre": "Introduction aux bases de données",
                "description": "Concept de base de données relationnelle et SQL"
            },
            {
                "titre": "Créer des tables",
                "description": "CREATE TABLE, types de colonnes, clés primaires"
            },
            {
                "titre": "Insérer des données",
                "description": "INSERT INTO — ajouter des enregistrements"
            },
            {
                "titre": "Lire des données",
                "description": "SELECT, WHERE, ORDER BY — interroger la base"
            },
            {
                "titre": "Modifier et supprimer",
                "description": "UPDATE et DELETE — mettre à jour la base de données"
            },
        ]
    },
}

NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"]


# ── Génération du contenu d'un chapitre via Groq ──────────────────
# Groq génère une explication claire + un exemple de code concret.
# On utilise st.cache_data pour ne pas rappeler l'API si l'élève
# revient sur le même chapitre — économise du temps et des tokens.
@st.cache_data(show_spinner=False)
def generer_contenu(theme, chapitre, niveau):
    prompt = f"""Tu es un professeur de programmation expert pour élèves de 1ère TI au Cameroun.
Rédige un cours clair sur : "{chapitre}" (thème : {theme}, niveau : {niveau}).

Structure ta réponse EXACTEMENT ainsi :
## Explication
(2-3 paragraphes clairs, langage simple, adapté au niveau {niveau})

## Exemple de code
(un bloc de code Python commenté, adapté au niveau {niveau})

## À retenir
(3 points essentiels sous forme de liste)

## Erreurs fréquentes
(2 erreurs courantes que font les débutants sur ce sujet)"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        temperature=0.4  # Peu de variété → contenu fiable et cohérent
    )
    return response.choices[0].message.content


# ── Génération d'un quiz rapide sur le chapitre ───────────────────
# Après avoir lu le cours, l'élève peut tester sa compréhension
# avec une question QCM générée par Groq sur le chapitre en cours.
@st.cache_data(show_spinner=False)
def generer_quiz(theme, chapitre, niveau):
    prompt = f"""Génère une question QCM sur "{chapitre}" (thème : {theme}, niveau : {niveau}).
Réponds UNIQUEMENT en JSON :
{{
  "question": "...",
  "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "reponse": "A",
  "explication": "..."
}}"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.5
    )
    import json, re
    raw = response.choices[0].message.content
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


# ── Page principale des cours ─────────────────────────────────────
# Appelée depuis app.py avec : from cours import page_cours
# Navigation en deux étapes : d'abord choisir le thème,
# puis choisir le chapitre dans ce thème.
def page_cours():
    st.title("📖 Cours")

    # ── Sélection du thème ────────────────────────────────────────
    # On affiche les thèmes sous forme de cartes cliquables
    # plutôt qu'un simple selectbox — plus visuel et engageant.
    st.markdown("#### Choisis un thème")

    cols = st.columns(4)
    for i, (theme, data) in enumerate(COURS.items()):
        if cols[i].button(
            f"{data['icone']} {theme}",
            use_container_width=True,
            key=f"theme_{i}"
        ):
            # Sauvegarde le thème choisi et réinitialise le chapitre
            st.session_state["cours_theme"]    = theme
            st.session_state["cours_chapitre"] = None
            st.rerun()

    # ── Affichage des chapitres du thème choisi ───────────────────
    if "cours_theme" not in st.session_state:
        st.info("👆 Choisis un thème pour commencer.")
        return

    theme = st.session_state["cours_theme"]
    data  = COURS[theme]

    st.divider()
    st.markdown(f"#### {data['icone']} {theme} — Chapitres")

    # Niveau adaptatif : par défaut Débutant, modifiable par l'élève
    niveau = st.select_slider(
        "Niveau d'explication",
        options=NIVEAUX,
        value="Débutant"
    )

    # Liste des chapitres sous forme de boutons numérotés
    for j, chap in enumerate(data["chapitres"], 1):
        col_btn, col_desc = st.columns([1, 3])
        if col_btn.button(
            f"Chapitre {j}",
            key=f"chap_{j}",
            use_container_width=True
        ):
            st.session_state["cours_chapitre"] = chap["titre"]
            st.session_state["cours_niveau"]   = niveau
            st.session_state["quiz_repondu"]   = False
            st.rerun()
        col_desc.markdown(
            f"**{chap['titre']}**  \n"
            f"<span style='font-size:13px;color:gray'>{chap['description']}</span>",
            unsafe_allow_html=True
        )

    # ── Affichage du contenu du chapitre sélectionné ─────────────
    if not st.session_state.get("cours_chapitre"):
        return

    chapitre = st.session_state["cours_chapitre"]
    niveau   = st.session_state.get("cours_niveau", "Débutant")

    st.divider()
    st.markdown(f"### 📘 {chapitre}")
    st.caption(f"Niveau : {niveau}")

    # Génération du contenu avec spinner pendant le chargement
    # @st.cache_data évite de rappeler Groq si déjà généré
    with st.spinner("Groq génère ton cours..."):
        contenu = generer_contenu(theme, chapitre, niveau)

    # st.markdown interprète le format ## Titre retourné par Groq
    st.markdown(contenu)

    # ── Quiz de compréhension ─────────────────────────────────────
    st.divider()
    st.markdown("#### 🧪 Teste ta compréhension")

    # On génère le quiz une seule fois et on le met en cache session
    if "quiz_actuel" not in st.session_state or \
       st.session_state.get("quiz_chapitre") != chapitre:
        with st.spinner("Préparation du quiz..."):
            st.session_state["quiz_actuel"]   = generer_quiz(theme, chapitre, niveau)
            st.session_state["quiz_chapitre"] = chapitre
            st.session_state["quiz_repondu"]  = False

    quiz = st.session_state["quiz_actuel"]

    st.write(quiz["question"])
    choix = st.radio("Ta réponse :", quiz["choix"], index=None)

    if choix and not st.session_state.get("quiz_repondu"):
        # La lettre de la réponse est le premier caractère (ex: "A")
        lettre_choisie  = choix[0]
        lettre_correcte = quiz["reponse"]

        if lettre_choisie == lettre_correcte:
            st.success("Bonne réponse !")
        else:
            st.error(f"Pas tout à fait. La bonne réponse était : {lettre_correcte}")

        # On affiche l'explication dans tous les cas
        st.info(f"**Explication :** {quiz['explication']}")
        st.session_state["quiz_repondu"] = True

    # Bouton pour passer au chapitre suivant
    st.divider()
    chapitres_liste = [c["titre"] for c in data["chapitres"]]
    idx_actuel = chapitres_liste.index(chapitre)

    if idx_actuel < len(chapitres_liste) - 1:
        if st.button("Chapitre suivant →", use_container_width=True):
            st.session_state["cours_chapitre"] = chapitres_liste[idx_actuel + 1]
            st.session_state["quiz_repondu"]   = False
            st.rerun()
    else:
        st.success("Tu as terminé tous les chapitres de ce thème ! 🎉")
        if st.button("Aller aux exercices →", use_container_width=True):
            # Redirige vers la page exercices en modifiant la session
            st.session_state["page"] = "🧠 Exercices"
            st.rerun()
