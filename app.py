import streamlit as st
from database import init_db
from auth import page_auth, deconnecter
from Exercices import page_exercices
from cours import page_cours
from progression import page_progression
from chat import page_chat
# Ajoutez cet import avec les autres :
from style import inject_css
from onboarding import page_onboarding
from database import get_onboarding

# ── Configuration de la page ──────────────────────────────────────
# Doit être le PREMIER appel Streamlit — avant tout autre st.*
# layout="wide" utilise toute la largeur de l'écran.
st.set_page_config(
    page_title="Tuteur IA — Programmation",
    page_icon="🤖",
    layout="wide"
)
inject_css()

# ── Initialisation de la base de données ─────────────────────────
# Crée les tables SQLite si elles n'existent pas encore.
# Appelé à chaque démarrage — sans danger car CREATE TABLE IF NOT EXISTS.
init_db()

# ── Garde d'authentification ──────────────────────────────────────
# Si l'élève n'est pas connecté → on affiche la page de connexion
# et st.stop() bloque l'exécution du reste du fichier.
# Aucune page ne sera accessible sans être connecté.
if "eleve" not in st.session_state:
    page_auth()
    st.stop()

# Ajoutez l'import en haut :
from onboarding import page_onboarding
from database import get_onboarding

# Juste après init_db() et la garde auth, avant la sidebar :
# ── Onboarding : première connexion ──────────────────────────────
onboarding_data = get_onboarding(eleve["id"])
onboarding_fait = (
    onboarding_data and onboarding_data.get("onboarding_fait")
) or st.session_state.get("onboarding_fait", False)

if not onboarding_fait:
    page_onboarding()
    st.stop()
    
# ── Sidebar : navigation et déconnexion ──────────────────────────
# Visible uniquement si l'élève est connecté (code au-dessus du stop).
eleve = st.session_state["eleve"]

st.sidebar.title("📚 Tuteur IA")
st.sidebar.markdown(f"Bonjour **{eleve['prenom']}** 👋")
st.sidebar.divider()

# On utilise session_state["page"] pour permettre aux autres modules
# de rediriger vers une page (ex: bouton "Aller aux exercices →")
if "page" not in st.session_state:
    st.session_state["page"] = "🏠 Accueil"

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Accueil", "📖 Cours", "🧠 Exercices",  "💬 Assistant", "📊 Ma progression"],
    index=["🏠 Accueil", "📖 Cours", "🧠 Exercices", "💬 Assistant", "📊 Ma progression"]
          .index(st.session_state["page"])
)

# Synchronise la session avec la sélection manuelle dans le menu
st.session_state["page"] = page

st.sidebar.divider()

# Bouton de déconnexion en bas de la sidebar
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnecter()



# ── Routeur de pages ──────────────────────────────────────────────
# Chaque condition appelle la fonction correspondante dans son module.
# app.py ne contient AUCUNE logique métier — uniquement la navigation.
if page == "🏠 Accueil":

    st.title(f"Bienvenue {eleve['prenom']} 🤖")
    st.markdown("Améliore tes performances en programmation Python, Streamlit, Groq et SQLite.")
    st.divider()

    # Aperçu rapide des stats sur la page d'accueil
    from database import get_stats_eleve
    stats = get_stats_eleve(eleve["id"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Exercices tentés",  stats["total"])
    col2.metric("Réussis",           stats["reussis"])
    col3.metric("Taux de réussite",  f"{stats['taux']}%")
    col4.metric("Thèmes disponibles", "4")

    st.divider()

    # Cartes de navigation rapide
    st.markdown("#### Par où commencer ?")
    c1, c2, c3 = st.columns(3)

    if c1.button("📖 Voir les cours", use_container_width=True):
        st.session_state["page"] = "📖 Cours"
        st.rerun()

    if c2.button("🧠 Faire des exercices", use_container_width=True):
        st.session_state["page"] = "🧠 Exercices"
        st.rerun()

    if c3.button("📊 Ma progression", use_container_width=True):
        st.session_state["page"] = "📊 Ma progression"
        st.rerun()

elif page == "📖 Cours":
    page_cours()

elif page == "🧠 Exercices":
    page_exercices()

elif page == "📊 Ma progression":
    page_progression()

elif page == "💬 Assistant":
    page_chat()
