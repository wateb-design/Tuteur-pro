import streamlit as st
from database import init_db, get_onboarding, get_stats_eleve
from auth import page_auth, deconnecter
from Exercices import page_exercices
from cours import page_cours
from progression import page_progression
from chat import page_chat
from style import inject_css
from onboarding import page_onboarding

# ── Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Tuteur Pro — Programmation",
    page_icon="🤖",
    layout="wide"
)
inject_css()
init_db()

# ── Garde 1 : authentification ────────────────────────────────────
# eleve n'existe pas encore ici — on vérifie d'abord la session
if "eleve" not in st.session_state:
    page_auth()
    st.stop()


eleve = st.session_state["eleve"]
#st.write("Email session :", eleve.get("email", "NON TROUVÉ"))
#st.write("Email admin secrets :", st.secrets.get("ADMIN_EMAIL", "NON DÉFINI"))
# eleve est maintenant défini — toutes les lignes suivantes peuvent l'utiliser
eleve    = st.session_state["eleve"]
eleve_id = eleve["id"]


# ── Garde 2 : onboarding ──────────────────────────────────────────
# On utilise eleve_id défini juste au-dessus
onboarding_data = get_onboarding(eleve_id)
onboarding_fait = (
    onboarding_data and onboarding_data.get("onboarding_fait")
) or st.session_state.get("onboarding_fait", False)

if not onboarding_fait:
    page_onboarding()
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────
st.sidebar.title("📚 Tuteur Pro")
st.sidebar.markdown(f"Bonjour **{eleve['prenom']}** 👋")
st.sidebar.divider()

if "page" not in st.session_state:
    st.session_state["page"] = "🏠 Accueil"

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Accueil", "📖 Cours", "🧠 Exercices", "💬 Assistant", "📊 Ma progression"],
    index=["🏠 Accueil", "📖 Cours", "🧠 Exercices", "💬 Assistant", "📊 Ma progression"]
          .index(st.session_state["page"])
)
st.session_state["page"] = page

st.sidebar.divider()
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnecter()

# ── Routeur ───────────────────────────────────────────────────────
if page == "🏠 Accueil":
    st.title(f"Bienvenue {eleve['prenom']} 🤖")
    st.markdown("Améliore tes performances en informatique · 1ère TI")
    st.divider()

    stats = get_stats_eleve(eleve_id)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Exercices tentés",  stats["total"])
    col2.metric("Réussis",           stats["reussis"])
    col3.metric("Taux de réussite",  f"{stats['taux']}%")
    col4.metric("Matières",          "4")

    st.divider()
    st.markdown("#### Par où commencer ?")
    c1, c2, c3 = st.columns(3)

    if c1.button("📖 Voir les cours", use_container_width=True):
        st.session_state["page"] = "📖 Cours"
        st.rerun()
    if c2.button("🧠 Faire des exercices", use_container_width=True):
        st.session_state["page"] = "🧠 Exercices"
        st.rerun()
    if c3.button("💬 Poser une question", use_container_width=True):
        st.session_state["page"] = "💬 Assistant"
        st.rerun()

elif page == "📖 Cours":
    page_cours()
elif page == "🧠 Exercices":
    page_exercices()
elif page == "💬 Assistant":
    page_chat()
elif page == "📊 Ma progression":
    page_progression()
