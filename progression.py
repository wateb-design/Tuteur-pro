import streamlit as st
import pandas as pd
from database import get_resultats_eleve, get_stats_eleve, get_stats_par_theme

# ── Page principale de la progression ────────────────────────────
# Appelée depuis app.py avec : from progression import page_progression
# Elle affiche toutes les statistiques de l'élève connecté,
# récupérées depuis la base SQLite via les fonctions de database.py.
def page_progression():
    st.title("📊 Ma progression")

    # On récupère l'élève connecté depuis la session Streamlit
    eleve = st.session_state["eleve"]
    eleve_id = eleve["id"]

    # ── Statistiques globales ─────────────────────────────────────
    # get_stats_eleve() retourne un dict :
    # {"total": 10, "reussis": 7, "taux": 70}
    stats = get_stats_eleve(eleve_id)

    if stats["total"] == 0:
        st.info("Tu n'as pas encore fait d'exercices. Lance-toi ! 🚀")
        if st.button("Aller aux exercices →"):
            st.session_state["page"] = "🧠 Exercices"
            st.rerun()
        return

    # ── Niveau adaptatif calculé depuis le taux de réussite ───────
    # Logique du cahier des charges (section 4.6) :
    # Score < 50%  → Débutant  (révision nécessaire)
    # Score 50-80% → Moyen     (en progression)
    # Score > 80%  → Avancé    (très bon niveau)
    def get_niveau_adaptatif(taux):
        if taux < 50:
            return "Débutant", "🔴", "Révise les bases — des exercices faciles t'attendent !"
        elif taux <= 80:
            return "Moyen", "🟡", "Tu progresses bien — continue avec les exercices moyens !"
        else:
            return "Avancé", "🟢", "Excellent niveau — essaie les exercices difficiles !"

    niveau, couleur, conseil = get_niveau_adaptatif(stats["taux"])

    # ── Bandeau de niveau adaptatif ───────────────────────────────
    st.markdown(
        f"""<div style='padding:1rem;border-radius:10px;
        background:var(--background-color);border:1px solid #e0e0e0;
        margin-bottom:1rem'>
        <span style='font-size:20px'>{couleur}</span>
        <strong> Niveau actuel : {niveau}</strong><br>
        <span style='color:gray;font-size:14px'>{conseil}</span>
        </div>""",
        unsafe_allow_html=True
    )

    # ── 3 métriques principales ───────────────────────────────────
    # st.metric affiche une valeur avec un label — idéal pour les stats.
    col1, col2, col3 = st.columns(3)
    col1.metric("Exercices tentés",  stats["total"])
    col2.metric("Exercices réussis", stats["reussis"])
    col3.metric("Taux de réussite",  f"{stats['taux']}%")

    st.divider()

    # ── Statistiques par thème ────────────────────────────────────
    # get_stats_par_theme() retourne une liste de tuples :
    # [("Python — bases", 5, 4), ("SQLite", 3, 1), ...]
    #  (theme, total, reussis)
    st.markdown("#### 📚 Résultats par thème")

    stats_themes = get_stats_par_theme(eleve_id)

    if stats_themes:
        # On construit un DataFrame pour afficher un tableau propre
        lignes = []
        for theme, total, reussis in stats_themes:
            taux_theme = round(reussis / total * 100) if total > 0 else 0

            # Barre de progression visuelle avec des blocs Unicode
            # 10 blocs au total, remplis proportionnellement au taux
            blocs_pleins = round(taux_theme / 10)
            barre = "█" * blocs_pleins + "░" * (10 - blocs_pleins)

            lignes.append({
                "Thème":      theme,
                "Tentés":     total,
                "Réussis":    reussis,
                "Taux":       f"{taux_theme}%",
                "Progression": barre
            })

        df_themes = pd.DataFrame(lignes)
        st.dataframe(df_themes, use_container_width=True, hide_index=True)

        # ── Graphique en barres par thème ─────────────────────────
        # st.bar_chart attend un DataFrame avec l'index = labels.
        # On le construit à partir des données déjà récupérées.
        st.markdown("#### 📈 Taux de réussite par thème")
        df_chart = pd.DataFrame({
            "Taux de réussite (%)": [
                round((r / t * 100) if t > 0 else 0)
                for _, t, r in stats_themes
            ]
        }, index=[s[0] for s in stats_themes])

        st.bar_chart(df_chart)

    st.divider()

    # ── Historique détaillé ───────────────────────────────────────
    # get_resultats_eleve() retourne la liste de tous les exercices
    # tentés, triés du plus récent au plus ancien.
    st.markdown("#### 🕒 Historique des exercices")

    resultats = get_resultats_eleve(eleve_id)

    if resultats:
        # Construction du DataFrame d'historique
        # resultats = [(theme, niveau, reussi, temps, date), ...]
        df_hist = pd.DataFrame(
            resultats,
            columns=["Thème", "Niveau", "Réussi", "Temps (s)", "Date"]
        )

        # Formatage des colonnes pour un affichage lisible
        df_hist["Réussi"]    = df_hist["Réussi"].map({1: "✅ Réussi", 0: "❌ À revoir"})
        df_hist["Temps (s)"] = df_hist["Temps (s)"].apply(
            lambda t: f"{t}s" if t else "—"
        )
        # On garde uniquement la date sans les microsecondes
        df_hist["Date"] = pd.to_datetime(df_hist["Date"]).dt.strftime("%d/%m/%Y %H:%M")

        st.dataframe(df_hist, use_container_width=True, hide_index=True)

        # ── Temps moyen de réponse ────────────────────────────────
        # On filtre les lignes où le temps est renseigné (> 0)
        temps_valides = [r[3] for r in resultats if r[3] and r[3] > 0]
        if temps_valides:
            temps_moyen = round(sum(temps_valides) / len(temps_valides))
            st.caption(f"⏱️ Temps moyen par exercice : {temps_moyen} secondes")

    st.divider()

    # ── Recommandation personnalisée ──────────────────────────────
    # On identifie le thème avec le taux de réussite le plus bas
    # et on recommande à l'élève de s'y concentrer.
    if stats_themes:
        theme_faible = min(
            stats_themes,
            key=lambda x: (x[2] / x[1]) if x[1] > 0 else 1
        )
        taux_faible = round(theme_faible[2] / theme_faible[1] * 100) if theme_faible[1] > 0 else 0

        st.markdown("#### 💡 Recommandation")
        st.warning(
            f"Tu as un taux de réussite de **{taux_faible}%** en **{theme_faible[0]}**. "
            f"Je te recommande de revoir les cours sur ce thème avant de refaire des exercices."
        )

        col1, col2 = st.columns(2)
        if col1.button("📖 Revoir les cours", use_container_width=True):
            st.session_state["cours_theme"] = theme_faible[0]
            st.rerun()
        if col2.button("🧠 Faire des exercices", use_container_width=True):
            st.session_state["page"] = "🧠 Exercices"
            st.rerun()
