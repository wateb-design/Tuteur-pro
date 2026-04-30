import streamlit as st
from groq import Groq
from cours import COURS

# ── Client Groq ───────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Système de prompt strict ──────────────────────────────────────
# Le system prompt est le "contrat" donné à Groq.
# Il définit précisément ce que le tuteur peut et ne peut PAS faire.
# C'est la clé pour limiter les réponses au cadre scolaire.
SYSTEM_PROMPT = """Tu es un tuteur pédagogique spécialisé en informatique pour élèves de 1ère TI au Cameroun.

Tu enseignes UNIQUEMENT ces matières :
- Algorithmique avancé (structures conditionnelles, boucles, tableaux, sous-programmes, tri/recherche)
- Langage C (variables, fonctions, tableaux, pointeurs)
- HTML et CSS (balises, formulaires, mise en page, styles)
- Introduction au JavaScript (variables, conditions, boucles, DOM, événements)

RÈGLES STRICTES :
1. Tu réponds UNIQUEMENT aux questions liées à ces matières.
2. Si la question est hors sujet (politique, sport, actualité, autre langage, etc.), 
   réponds poliment : "Je suis ton tuteur en informatique 1ère TI. Je ne peux répondre 
   qu'aux questions sur l'algorithmique, le C, HTML/CSS et JavaScript. As-tu une question 
   sur ces matières ?"
3. Tu ne fais PAS les exercices à la place de l'élève — tu guides et expliques.
4. Tu utilises des exemples simples et concrets adaptés au niveau lycée.
5. Tu es encourageant, patient et bienveillant.
6. Tes réponses sont claires, structurées et en français.
7. Si l'élève demande la solution d'un exercice, donne un indice progressif au lieu de la solution directe."""


# ── Vérification hors-sujet ───────────────────────────────────────
# Avant d'envoyer le message à Groq, on vérifie rapidement
# si la question semble liée aux matières du programme.
# Liste de mots-clés des matières autorisées.
MOTS_CLES_AUTORISES = [
    # Algorithmique
    "algorithme", "algo", "boucle", "condition", "tableau", "tri", "recherche",
    "fonction", "procédure", "variable", "si", "sinon", "tantque", "pour",
    # Langage C
    "langage c", "pointeur", "printf", "scanf", "include", "main", "int",
    "float", "char", "struct", "malloc", "#include",
    # HTML/CSS
    "html", "css", "balise", "div", "span", "style", "classe", "id",
    "flexbox", "formulaire", "input", "body", "head", "href", "src",
    # JavaScript
    "javascript", "js", "dom", "event", "fonction", "var", "let", "const",
    "addeventlistener", "getelementbyid", "innerhtml", "console",
    # Général informatique
    "code", "programme", "erreur", "bug", "compiler", "syntaxe", "logique",
    "informatique", "programmation", "exercice", "cours", "expliquer", "comprendre"
]

def est_question_autorisee(message):
    """Retourne True si le message contient au moins un mot-clé autorisé."""
    message_lower = message.lower()
    return any(mot in message_lower for mot in MOTS_CLES_AUTORISES)


# ── Envoi d'un message à Groq ─────────────────────────────────────
# On envoie tout l'historique de la conversation à chaque appel
# pour que Groq ait le contexte des échanges précédents.
def envoyer_message(historique, message_eleve):
    # Construction des messages : system + historique + nouveau message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # On ajoute les 10 derniers messages pour limiter les tokens
    for msg in historique[-10:]:
        messages.append({
            "role":    msg["role"],
            "content": msg["content"]
        })

    # On ajoute le nouveau message de l'élève
    messages.append({"role": "user", "content": message_eleve})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500,
        temperature=0.5
    )
    return response.choices[0].message.content


# ── Page principale du chat ───────────────────────────────────────
def page_chat():
    st.title("💬 Assistant IA")
    st.caption("Pose tes questions sur l'algorithmique, le C, HTML/CSS et JavaScript.")

    eleve = st.session_state["eleve"]

    # ── Initialisation de l'historique ───────────────────────────
    # L'historique est stocké dans st.session_state pour persister
    # entre les interactions sans disparaître à chaque clic.
    if "chat_historique" not in st.session_state:
        st.session_state["chat_historique"] = []

        # Message de bienvenue personnalisé
        st.session_state["chat_historique"].append({
            "role":    "assistant",
            "content": f"Bonjour {eleve['prenom']} ! 👋 Je suis ton Tuteur-pro. "
                       f"Je peux t'aider sur l'**algorithmique**, le **langage C**, "
                       f"**HTML/CSS** et **JavaScript**. Quelle est ta question ?"
        })

    # ── Suggestions de questions rapides ─────────────────────────
    # Des boutons de raccourci pour aider l'élève à démarrer.
    if len(st.session_state["chat_historique"]) == 1:
        st.markdown("**Questions fréquentes :**")
        suggestions = [
            "C'est quoi un pointeur en C ?",
            "Comment fonctionne une boucle for en JavaScript ?",
            "Quelle est la différence entre margin et padding en CSS ?",
            "Comment trier un tableau avec l'algorithme des bulles ?"
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            if cols[i % 2].button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state["chat_historique"].append({
                    "role": "user", "content": suggestion
                })
                with st.spinner("Réflexion..."):
                    reponse = envoyer_message(
                        st.session_state["chat_historique"][:-1],
                        suggestion
                    )
                st.session_state["chat_historique"].append({
                    "role": "assistant", "content": reponse
                })
                st.rerun()

    # ── Affichage de l'historique ─────────────────────────────────
    # st.chat_message affiche les bulles de conversation
    # avec un style différent pour "user" et "assistant".
    for msg in st.session_state["chat_historique"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Saisie du message ─────────────────────────────────────────
    # st.chat_input est le champ de saisie en bas de page —
    # il retourne le message dès que l'élève appuie sur Entrée.
    if prompt := st.chat_input("Pose ta question ici..."):

        # Ajout du message de l'élève dans l'historique
        st.session_state["chat_historique"].append({
            "role": "user", "content": prompt
        })

        # Affichage immédiat du message de l'élève
        with st.chat_message("user"):
            st.markdown(prompt)

        # ── Vérification hors-sujet ───────────────────────────────
        # Si la question semble hors programme, on répond directement
        # sans appeler Groq — plus rapide et économise des tokens.
        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                if not est_question_autorisee(prompt):
                    reponse = (
                        "Je suis ton tuteur en informatique 1ère TI 🎓\n\n"
                        "Je ne peux répondre qu'aux questions sur :\n"
                        "- 🧠 Algorithmique avancé\n"
                        "- ⚙️ Langage C\n"
                        "- 🌐 HTML et CSS\n"
                        "- ✨ JavaScript\n\n"
                        "As-tu une question sur l'une de ces matières ?"
                    )
                else:
                    reponse = envoyer_message(
                        st.session_state["chat_historique"][:-1],
                        prompt
                    )

            st.markdown(reponse)

        # Ajout de la réponse dans l'historique
        st.session_state["chat_historique"].append({
            "role": "assistant", "content": reponse
        })

    # ── Bouton effacer l'historique ───────────────────────────────
    st.divider()
    if st.button("🗑️ Effacer la conversation", use_container_width=False):
        st.session_state.pop("chat_historique", None)
        st.rerun()
