import streamlit as st
from database import init_db, get_onboarding, get_stats_eleve
from auth import page_auth, deconnecter
from Exercices import page_exercices
from cours import page_cours
from progression import page_progression
from chat import page_chat
from style import inject_css
from onboarding import page_onboarding
from enseignant import page_connexion_enseignant, page_enseignant
from cours_data import COURS

# ⚠️ AJOUTEZ CES 3 LIGNES ICI ⚠️
import sys
print(f"[DEBUG] app.py chargé - COURS disponible: {len(COURS)} matières", file=sys.stderr)
sys.stderr.flush()

# ── Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Tuteur Pro — Programmation",
    page_icon="🤖",
    layout="wide"
)

# ── Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Tuteur Pro — Programmation",
    page_icon="🤖",
    layout="wide"
)
inject_css()
init_db()

# ── Espace enseignant ─────────────────────────────────────────────
# Accessible via ?mode=enseignant dans l'URL ou bouton dédié
if "enseignant" in st.session_state:
    page_enseignant()
    st.stop()

# Bouton discret dans la sidebar pour accéder à l'espace enseignant
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

    # ===== Récupération des stats RÉELLES des cours =====
    from database import get_progression_cours, get_niveau_detecte
    
    # Initialiser les compteurs
    total_chapitres = 0
    chapitres_vus = 0
    quiz_reussis = 0
    progression_par_matiere = {}
    
    # Parcourir toutes les matières pour calculer les vraies stats
    for theme, data in COURS.items():
        total_chapitres_matiere = len(data["chapitres"])
        total_chapitres += total_chapitres_matiere
        
        # Récupérer la progression RÉELLE depuis la base de données
        progression = get_progression_cours(eleve_id, theme)
        
        # Compter les chapitres vus (cours_vu = True)
        vus = sum(1 for p in progression if p.get("cours_vu") and p["chapitre"] != "__diagnostic__")
        chapitres_vus += vus
        
        # Compter les quiz réussis
        quiz_ok = sum(1 for p in progression if p.get("quiz_reussi"))
        quiz_reussis += quiz_ok
        
        # Calculer le pourcentage pour cette matière
        if total_chapitres_matiere > 0:
            pct = round((vus / total_chapitres_matiere) * 100)
        else:
            pct = 0
            
        progression_par_matiere[theme] = {
            "vus": vus,
            "total": total_chapitres_matiere,
            "pct": pct,
            "quiz": quiz_ok,
            "icone": data["icone"]
        }
    
    # Calculer la progression globale
    if total_chapitres > 0:
        progression_globale = round((chapitres_vus / total_chapitres) * 100)
    else:
        progression_globale = 0
    
    # Récupérer les stats des exercices (existantes)
    from database import get_stats_eleve
    stats_exercices = get_stats_eleve(eleve_id)
    
    # AFFICHAGE DES STATS RÉELLES
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📚 Chapitres vus",
            f"{chapitres_vus}/{total_chapitres}",
            help=f"{progression_globale}% de progression dans les cours"
        )
    
    with col2:
        st.metric(
            "✅ Quiz réussis",
            f"{quiz_reussis}",
            help="Nombre de quiz validés avec succès"
        )
    
    with col3:
        st.metric(
            "📖 Progression cours",
            f"{progression_globale}%",
            help="Pourcentage des chapitres terminés"
        )
    
    with col4:
        if stats_exercices["total"] > 0:
            st.metric(
                "🎯 Exercices réussis",
                f"{stats_exercices['taux']}%",
                help=f"{stats_exercices['reussis']}/{stats_exercices['total']} exercices"
            )
        else:
            st.metric("🎯 Exercices", "0%", help="Commence des exercices !")
    
    st.divider()
    
    # AFFICHAGE DÉTAILLÉ PAR MATIÈRE
    st.markdown("#### 📊 Progression par matière")
    
    for theme, stats in progression_par_matiere.items():
        # Barre de progression
        st.markdown(
            f"""
            <div style='margin-bottom: 20px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                    <span style='font-weight: 600;'>{stats['icone']} {theme}</span>
                    <span style='color: #1565C0;'>
                        {stats['vus']}/{stats['total']} chapitres
                    </span>
                </div>
                <div style='background: #E3F2FD; border-radius: 8px; height: 24px; overflow: hidden;'>
                    <div style='background: #1565C0; width: {stats['pct']}%; height: 100%; 
                                display: flex; align-items: center; justify-content: flex-end;
                                padding-right: 8px; color: white; font-size: 12px; font-weight: 500;'>
                        {stats['pct']}%
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Afficher les détails des chapitres de cette matière
        with st.expander(f"📖 Détails des chapitres - {theme}"):
            progression_detail = get_progression_cours(eleve_id, theme)
            
            # Créer un tableau des chapitres
            chapitres_data = []
            for chapitre in COURS[theme]["chapitres"]:
                prog_chap = next(
                    (p for p in progression_detail if p["chapitre"] == chapitre["titre"]),
                    None
                )
                
                statut_cours = "✅ Vu" if prog_chap and prog_chap.get("cours_vu") else "⭕ Non vu"
                statut_quiz = "✅ Réussi" if prog_chap and prog_chap.get("quiz_reussi") else "⭕ Non fait"
                
                chapitres_data.append({
                    "Chapitre": chapitre["titre"][:50],
                    "Cours": statut_cours,
                    "Quiz": statut_quiz
                })
            
            st.dataframe(chapitres_data, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # RECOMMANDATIONS PERSONNALISÉES
    st.markdown("#### 💡 Recommandations")
    
    # Trouver la matière avec le plus de retard
    matiere_retard = None
    pct_min = 100
    for theme, stats in progression_par_matiere.items():
        if stats["pct"] < pct_min and stats["total"] > 0:
            pct_min = stats["pct"]
            matiere_retard = theme
    
    if matiere_retard and pct_min < 100:
        st.warning(
            f"⚠️ Ta progression en **{matiere_retard}** est de {pct_min}%. "
            f"Concentre-toi sur cette matière pour améliorer ton niveau !"
        )
    
    # Trouver le prochain chapitre à faire
    prochain_chapitre = None
    prochain_theme = None
    for theme, data in COURS.items():
        progression = get_progression_cours(eleve_id, theme)
        chapitres_vus_set = {p["chapitre"] for p in progression if p.get("cours_vu")}
        
        for chapitre in data["chapitres"]:
            if chapitre["titre"] not in chapitres_vus_set:
                prochain_chapitre = chapitre["titre"]
                prochain_theme = theme
                break
        if prochain_chapitre:
            break
    
    if prochain_chapitre:
        st.info(
            f"💡 **Prochain objectif :** {progression_par_matiere[prochain_theme]['icone']} "
            f"{prochain_theme} - Chapitre \"{prochain_chapitre}\""
        )
    
    # Si tout est terminé
    if chapitres_vus == total_chapitres and total_chapitres > 0:
        st.success("🎉 Félicitations ! Tu as terminé tous les chapitres de toutes les matières !")
    
    st.divider()
    
    # BOUTONS DE NAVIGATION
    st.markdown("#### 🚀 Par où commencer ?")
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

    # ⚠️ METTEZ LE BLOC DEBUG ICI (à l'intérieur du if, tout à la fin)
    #with st.expander("🔍 Debug - Voir les données brutes"):
       # st.write("Progression par matière:", progression_par_matiere)
        #st.write("Total chapitres:", total_chapitres)
        #st.write("Chapitres vus:", chapitres_vus)
        #st.write("Quiz réussis:", quiz_reussis)
