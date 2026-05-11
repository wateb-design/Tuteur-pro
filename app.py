import streamlit as st
from database import init_db, get_onboarding, get_stats_eleve, get_progression_cours
from auth import page_auth, deconnecter
from Exercices import page_exercices
from cours import page_cours
from progression import page_progression
from chat import page_chat
from style import inject_css
from onboarding import page_onboarding
from enseignant import page_connexion_enseignant, page_enseignant
from cours_data import COURS

# ── Configuration ─────────────────────────────────────────────────
# UNE SEULE FOIS — c'était le bug : deux st.set_page_config
st.set_page_config(
    page_title="Tuteur Pro — Programmation",
    page_icon="🤖",
    layout="wide"
)

inject_css()
init_db()

# ── Espace enseignant ─────────────────────────────────────────────
if "enseignant" in st.session_state:
    page_enseignant()
    st.stop()

with st.sidebar:
    if st.button("👨‍🏫 Espace enseignant", use_container_width=False):
        st.session_state["mode_enseignant"] = True
        st.rerun()

if st.session_state.get("mode_enseignant") and \
   "enseignant" not in st.session_state:
    page_connexion_enseignant()
    if st.button("← Retour élève"):
        st.session_state.pop("mode_enseignant", None)
        st.rerun()
    st.stop()

# ── Garde 1 : authentification ────────────────────────────────────
if "eleve" not in st.session_state:
    page_auth()
    st.stop()

eleve    = st.session_state["eleve"]
eleve_id = eleve["id"]

# ── Garde 2 : onboarding ──────────────────────────────────────────
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
    ["🏠 Accueil", "📖 Cours", "🧠 Exercices",
     "💬 Assistant", "📊 Ma progression"],
    index=["🏠 Accueil", "📖 Cours", "🧠 Exercices",
           "💬 Assistant", "📊 Ma progression"]
          .index(st.session_state["page"])
)
st.session_state["page"] = page

st.sidebar.divider()
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnecter()

# ── Admin sidebar ─────────────────────────────────────────────────
if not st.session_state.get("admin_auth", False):
    with st.sidebar.expander("🔐 Admin"):
        mdp = st.text_input(
            "Mot de passe :",
            type="password",
            key="mdp_sidebar_admin"
        )
        if st.button("Valider", key="btn_sidebar_admin"):
            if mdp == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state["admin_auth"] = True
                st.success("Mode admin activé ✅")
                st.rerun()
            else:
                st.error("Incorrect.")
else:
    st.sidebar.markdown(
        "<span style='font-size:12px;color:#38A169'>✅ Mode admin actif</span>",
        unsafe_allow_html=True
    )
    if st.sidebar.button("🚪 Quitter admin", use_container_width=True):
        st.session_state["admin_auth"] = False
        st.rerun()

# ── Routeur ───────────────────────────────────────────────────────
if page == "🏠 Accueil":
    st.title(f"Bienvenue {eleve['prenom']} 🤖")
    st.markdown("Améliore tes performances en informatique · 1ère TI")
    st.divider()

    # Stats des cours
    total_chapitres      = 0
    chapitres_vus        = 0
    quiz_reussis         = 0
    progression_par_mat  = {}

    for theme, data in COURS.items():
        total_mat = len(data["chapitres"])
        total_chapitres += total_mat
        prog = get_progression_cours(eleve_id, theme)
        vus  = sum(1 for p in prog
                   if p.get("cours_vu") and p["chapitre"] != "__diagnostic__")
        quiz = sum(1 for p in prog if p.get("quiz_reussi"))
        chapitres_vus += vus
        quiz_reussis  += quiz
        pct = round(vus / total_mat * 100) if total_mat > 0 else 0
        progression_par_mat[theme] = {
            "vus": vus, "total": total_mat,
            "pct": pct, "quiz": quiz,
            "icone": data["icone"]
        }

    prog_globale    = round(chapitres_vus / total_chapitres * 100) \
                      if total_chapitres > 0 else 0
    stats_exercices = get_stats_eleve(eleve_id)

    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📚 Chapitres vus",    f"{chapitres_vus}/{total_chapitres}")
    col2.metric("✅ Quiz réussis",      f"{quiz_reussis}")
    col3.metric("📖 Progression cours", f"{prog_globale}%")
    col4.metric(
        "🎯 Exercices réussis",
        f"{stats_exercices['taux']}%",
        help=f"{stats_exercices['reussis']}/{stats_exercices['total']}"
    )

    st.divider()
    st.markdown("#### 📊 Progression par matière")

    for theme, stats in progression_par_mat.items():
        st.markdown(
            f"""<div style='margin-bottom:16px'>
            <div style='display:flex;justify-content:space-between;
            margin-bottom:4px'>
                <span style='font-weight:600'>{stats['icone']} {theme}</span>
                <span style='color:#1565C0'>{stats['vus']}/{stats['total']} chapitres</span>
            </div>
            <div style='background:#E3F2FD;border-radius:8px;height:20px;overflow:hidden'>
                <div style='background:#1565C0;width:{stats['pct']}%;height:100%;
                display:flex;align-items:center;justify-content:flex-end;
                padding-right:8px;color:white;font-size:11px'>
                {stats['pct']}%</div>
            </div></div>""",
            unsafe_allow_html=True
        )
        with st.expander(f"📖 Détails — {theme}"):
            prog_detail = get_progression_cours(eleve_id, theme)
            rows = []
            for chap in COURS[theme]["chapitres"]:
                pc = next(
                    (p for p in prog_detail if p["chapitre"] == chap["titre"]),
                    None
                )
                rows.append({
                    "Chapitre": chap["titre"][:50],
                    "Cours":    "✅ Vu"    if pc and pc.get("cours_vu")    else "⭕ Non vu",
                    "Quiz":     "✅ Réussi" if pc and pc.get("quiz_reussi") else "⭕ Non fait"
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### 💡 Recommandations")

    # Matière avec le plus de retard
    matiere_retard = min(
        progression_par_mat.items(),
        key=lambda x: x[1]["pct"]
    )[0] if progression_par_mat else None

    if matiere_retard and progression_par_mat[matiere_retard]["pct"] < 100:
        st.warning(
            f"⚠️ Progression en **{matiere_retard}** : "
            f"{progression_par_mat[matiere_retard]['pct']}% — "
            f"Concentre-toi sur cette matière !"
        )

    # Prochain chapitre
    prochain_chap  = None
    prochain_theme = None
    for theme, data in COURS.items():
        prog = get_progression_cours(eleve_id, theme)
        vus_set = {p["chapitre"] for p in prog if p.get("cours_vu")}
        for chap in data["chapitres"]:
            if chap["titre"] not in vus_set:
                prochain_chap  = chap["titre"]
                prochain_theme = theme
                break
        if prochain_chap:
            break

    if prochain_chap:
        st.info(
            f"💡 **Prochain objectif :** "
            f"{progression_par_mat[prochain_theme]['icone']} "
            f"{prochain_theme} — \"{prochain_chap}\""
        )

    if chapitres_vus == total_chapitres and total_chapitres > 0:
        st.success("🎉 Félicitations ! Tu as terminé tous les chapitres !")

    st.divider()
    st.markdown("#### 🚀 Par où commencer ?")
    c1, c2, c3 = st.columns(3)
    if c1.button("📖 Voir les cours",      use_container_width=True):
        st.session_state["page"] = "📖 Cours"
        st.rerun()
    if c2.button("🧠 Faire des exercices", use_container_width=True):
        st.session_state["page"] = "🧠 Exercices"
        st.rerun()
    if c3.button("💬 Poser une question",  use_container_width=True):
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
