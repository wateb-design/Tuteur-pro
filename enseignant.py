import streamlit as st
import hashlib
import json
import pandas as pd
from database import (
    inserer_enseignant,
    get_enseignant_par_email,
    get_tous_eleves,
    get_stats_globales,
    get_stats_eleve,
    get_stats_par_theme,
    get_progression_cours,
    get_progression_complete_eleve,
    get_resultats_eleve
)
from cours import COURS

# ── Hashage mot de passe ──────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── Authentification enseignant ───────────────────────────────────
def connecter_enseignant(email, password):
    if not email or not password:
        return False, None
    row = get_enseignant_par_email(email, hash_password(password))
    if row:
        return True, {"id": row[0], "nom": row[1], "email": email}
    return False, None

def deconnecter_enseignant():
    for key in ["enseignant", "eleve_selectionne"]:
        st.session_state.pop(key, None)
    st.rerun()

# ── Page de connexion enseignant ──────────────────────────────────
def page_connexion_enseignant():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            """<div style='text-align:center;padding:2rem 0 1.5rem'>
            <div style='font-size:48px'>👨‍🏫</div>
            <h2 style='font-size:1.4rem;font-weight:500;margin-bottom:4px'>
                Espace Enseignant
            </h2>
            <p style='font-size:13px;color:var(--color-text-secondary)'>
                Tuteur Pro · 1ère TI
            </p>
            </div>""",
            unsafe_allow_html=True
        )

        onglet = st.radio("", ["Connexion", "Créer un compte"], horizontal=True)

        if onglet == "Connexion":
            email    = st.text_input("Email", placeholder="votre@email.com")
            password = st.text_input("Mot de passe", type="password")

            if st.button("Se connecter", use_container_width=True, type="primary"):
                if not email or not password:
                    st.warning("Remplis tous les champs.")
                else:
                    ok, enseignant = connecter_enseignant(email, password)
                    if ok:
                        st.session_state["enseignant"] = enseignant
                        st.success(f"Bienvenue {enseignant['nom']} !")
                        st.rerun()
                    else:
                        st.error("Email ou mot de passe incorrect.")

        else:
            nom      = st.text_input("Nom complet")
            email    = st.text_input("Email", placeholder="votre@email.com")
            password  = st.text_input("Mot de passe", type="password")
            password2 = st.text_input("Confirmer", type="password")

            if st.button("Créer mon compte", use_container_width=True, type="primary"):
                if not nom or not email or not password:
                    st.warning("Remplis tous les champs.")
                elif password != password2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 6:
                    st.warning("Mot de passe trop court (6 caractères min).")
                else:
                    ok = inserer_enseignant(nom, email, hash_password(password))
                    if ok:
                        st.success("Compte créé ! Connectez-vous.")
                    else:
                        st.error("Cet email est déjà utilisé.")


# ── Barre de progression visuelle ────────────────────────────────
def barre_progression(valeur, total, couleur="#1565C0"):
    pct = round(valeur / total * 100) if total > 0 else 0
    return f"""
    <div style='background:var(--color-background-secondary);
    border-radius:4px;height:8px;margin-top:4px'>
        <div style='background:{couleur};width:{pct}%;
        height:100%;border-radius:4px'></div>
    </div>
    <div style='font-size:11px;color:var(--color-text-tertiary);
    margin-top:2px'>{valeur}/{total} — {pct}%</div>"""


# ── Page principale enseignant ────────────────────────────────────
def page_enseignant():
    enseignant = st.session_state["enseignant"]

    # ── Sidebar enseignant ────────────────────────────────────────
    st.sidebar.title("👨‍🏫 Espace Enseignant")
    st.sidebar.markdown(f"**{enseignant['nom']}**")
    st.sidebar.divider()

    vue = st.sidebar.radio("Vue", [
        "📊 Tableau de bord",
        "👥 Liste des élèves",
        "🔍 Élève en détail",
        "📈 Statistiques matières"
    ])

    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
        deconnecter_enseignant()

    # ════════════════════════════════════════════════════════════
    # VUE 1 — TABLEAU DE BORD
    # ════════════════════════════════════════════════════════════
    if vue == "📊 Tableau de bord":
        st.title("📊 Tableau de bord")

        eleves, resultats = get_stats_globales()

        if not eleves:
            st.info("Aucun élève inscrit pour le moment.")
            return

        # ── Métriques globales ────────────────────────────────
        total_eleves  = len(eleves)
        total_exercices = len(resultats)
        total_reussis = sum(r["reussi"] for r in resultats) if resultats else 0
        taux_global   = round(total_reussis / total_exercices * 100) \
                        if total_exercices > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Élèves inscrits",    total_eleves)
        col2.metric("Exercices tentés",   total_exercices)
        col3.metric("Exercices réussis",  total_reussis)
        col4.metric("Taux de réussite",   f"{taux_global}%")

        st.divider()

        # ── Taux de réussite par matière ──────────────────────
        st.markdown("#### Taux de réussite par matière")

        themes = {}
        for r in resultats:
            t = r["theme"]
            if t not in themes:
                themes[t] = {"total": 0, "reussis": 0}
            themes[t]["total"]   += 1
            themes[t]["reussis"] += r["reussi"]

        if themes:
            cols = st.columns(len(themes))
            icones = {
                "Algorithmique avancée": "🧠",
                "Langage C":             "⚙️",
                "HTML et CSS":           "🌐",
                "JavaScript":            "✨"
            }
            for i, (theme, data) in enumerate(themes.items()):
                taux = round(data["reussis"] / data["total"] * 100) \
                       if data["total"] > 0 else 0
                couleur = (
                    "#E53E3E" if taux < 50
                    else "#D69E2E" if taux < 80
                    else "#38A169"
                )
                cols[i].markdown(
                    f"""<div style='background:var(--color-background-primary);
                    border:0.5px solid var(--color-border-tertiary);
                    border-radius:var(--border-radius-lg);
                    padding:1rem;text-align:center'>
                    <div style='font-size:20px'>{icones.get(theme, '📖')}</div>
                    <div style='font-size:12px;color:var(--color-text-secondary);
                    margin:4px 0'>{theme.split()[0]}</div>
                    <div style='font-size:22px;font-weight:500;color:{couleur}'>
                        {taux}%
                    </div>
                    <div style='font-size:11px;color:var(--color-text-tertiary)'>
                        {data["reussis"]}/{data["total"]}
                    </div>
                    </div>""",
                    unsafe_allow_html=True
                )

        st.divider()

        # ── Top élèves ────────────────────────────────────────
        st.markdown("#### Top 5 élèves")

        eleve_stats = []
        for eleve in eleves:
            stats = get_stats_eleve(eleve["id"])
            eleve_stats.append({
                "Prénom":          eleve["prenom"],
                "Exercices":       stats["total"],
                "Réussis":         stats["reussis"],
                "Taux de réussite": f"{stats['taux']}%"
            })

        eleve_stats.sort(
            key=lambda x: int(x["Taux de réussite"].replace("%", "")),
            reverse=True
        )

        df = pd.DataFrame(eleve_stats[:5])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════
    # VUE 2 — LISTE DES ÉLÈVES
    # ════════════════════════════════════════════════════════════
    elif vue == "👥 Liste des élèves":
        st.title("👥 Liste des élèves")

        eleves = get_tous_eleves()

        if not eleves:
            st.info("Aucun élève inscrit.")
            return

        st.caption(f"{len(eleves)} élève(s) inscrit(s)")

        # Recherche
        recherche = st.text_input("Rechercher un élève", placeholder="Nom...")

        for eleve in eleves:
            if recherche and recherche.lower() not in eleve["prenom"].lower():
                continue

            stats = get_stats_eleve(eleve["id"])
            taux  = stats["taux"]
            couleur = (
                "#E53E3E" if taux < 50
                else "#D69E2E" if taux < 80
                else "#38A169"
            )

            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.markdown(
                f"**{eleve['prenom']}**  \n"
                f"<span style='font-size:12px;color:var(--color-text-tertiary)'>"
                f"{eleve['email']}</span>",
                unsafe_allow_html=True
            )
            col2.markdown(
                f"<div style='text-align:center'>"
                f"<div style='font-size:18px;font-weight:500;color:{couleur}'>"
                f"{taux}%</div>"
                f"<div style='font-size:11px;color:var(--color-text-tertiary)'>"
                f"Réussite</div></div>",
                unsafe_allow_html=True
            )
            col3.markdown(
                f"<div style='text-align:center'>"
                f"<div style='font-size:18px;font-weight:500'>"
                f"{stats['total']}</div>"
                f"<div style='font-size:11px;color:var(--color-text-tertiary)'>"
                f"Exercices</div></div>",
                unsafe_allow_html=True
            )
            if col4.button("Détail →", key=f"detail_{eleve['id']}"):
                st.session_state["eleve_selectionne"] = eleve
                st.session_state["vue_enseignant"]    = "🔍 Élève en détail"
                st.rerun()

            st.divider()

    # ════════════════════════════════════════════════════════════
    # VUE 3 — ÉLÈVE EN DÉTAIL
    # ════════════════════════════════════════════════════════════
    elif vue == "🔍 Élève en détail":
        st.title("🔍 Élève en détail")

        # Sélection de l'élève
        eleves = get_tous_eleves()
        if not eleves:
            st.info("Aucun élève inscrit.")
            return

        eleve_selectionne = st.session_state.get("eleve_selectionne")
        noms    = [e["prenom"] for e in eleves]
        idx_def = 0
        if eleve_selectionne:
            try:
                idx_def = noms.index(eleve_selectionne["prenom"])
            except ValueError:
                idx_def = 0

        choix = st.selectbox("Choisir un élève", noms, index=idx_def)
        eleve = next(e for e in eleves if e["prenom"] == choix)

        st.divider()

        # ── Stats globales élève ──────────────────────────────
        stats = get_stats_eleve(eleve["id"])
        prog  = get_progression_complete_eleve(eleve["id"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Exercices tentés",  stats["total"])
        col2.metric("Réussis",           stats["reussis"])
        col3.metric("Taux de réussite",  f"{stats['taux']}%")

        # ── Niveau adaptatif ──────────────────────────────────
        taux = stats["taux"]
        niveau_global = (
            "Débutant" if taux < 50
            else "Intermédiaire" if taux < 80
            else "Avancé"
        )
        couleur_niv = (
            "#E53E3E" if taux < 50
            else "#D69E2E" if taux < 80
            else "#38A169"
        )
        st.markdown(
            f"""<div style='background:var(--color-background-secondary);
            border-left:3px solid {couleur_niv};
            border-radius:var(--border-radius-lg);
            padding:10px 14px;margin:1rem 0'>
            <strong>Niveau global détecté : {niveau_global}</strong>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Résultats diagnostic onboarding ───────────────────
        if prog["onboarding"]:
            st.markdown("#### Diagnostic initial")
            scores_raw = prog["onboarding"].get("scores", {})
            if isinstance(scores_raw, str):
                try:
                    scores_raw = json.loads(scores_raw)
                except Exception:
                    scores_raw = {}

            if scores_raw:
                cols = st.columns(len(scores_raw))
                icones = {
                    "Algorithmique avancee": "🧠",
                    "Langage C":             "⚙️",
                    "HTML et CSS":           "🌐",
                    "JavaScript":            "✨"
                }
                for i, (mat, sc) in enumerate(scores_raw.items()):
                    t = round(sc["reussis"] / sc["total"] * 100) \
                        if sc.get("total", 0) > 0 else 0
                    cols[i].metric(
                        f"{icones.get(mat, '📖')} {mat.split()[0]}",
                        f"{t}%",
                        f"{sc.get('reussis', 0)}/{sc.get('total', 0)}"
                    )

        st.divider()

        # ── Progression par matière ───────────────────────────
        st.markdown("#### Progression des cours")

        for theme, data in COURS.items():
            cours_eleve = get_progression_cours(eleve["id"], theme)
            total_chap  = len(data["chapitres"])
            vus         = sum(
                1 for c in cours_eleve
                if c.get("cours_vu") and c["chapitre"] != "__diagnostic__"
            )
            quiz_ok = sum(1 for c in cours_eleve if c.get("quiz_reussi"))
            pct     = round(vus / total_chap * 100) if total_chap > 0 else 0

            st.markdown(
                f"""<div style='background:var(--color-background-primary);
                border:0.5px solid var(--color-border-tertiary);
                border-radius:var(--border-radius-lg);
                padding:10px 14px;margin-bottom:8px'>
                <div style='display:flex;justify-content:space-between;
                margin-bottom:6px'>
                    <span style='font-size:13px;font-weight:500'>
                        {data['icone']} {theme}
                    </span>
                    <span style='font-size:12px;
                    color:var(--color-text-secondary)'>
                        {vus}/{total_chap} chapitres · {quiz_ok} quiz ✅
                    </span>
                </div>
                <div style='background:var(--color-background-secondary);
                border-radius:4px;height:6px'>
                    <div style='background:#1565C0;width:{pct}%;
                    height:100%;border-radius:4px'></div>
                </div>
                </div>""",
                unsafe_allow_html=True
            )

        st.divider()

        # ── Progression exercices adaptatifs ──────────────────
        st.markdown("#### Progression exercices adaptatifs")

        ex_prog = prog["exercices"]
        if ex_prog:
            lignes = []
            for ep in ex_prog:
                taux_ex = round(
                    ep["exercices_reussis"] / ep["exercices_tentes"] * 100
                ) if ep["exercices_tentes"] > 0 else 0
                lignes.append({
                    "Matière":     ep["theme"],
                    "Chapitre":    ep["chapitre"][:30] + "..." \
                                   if len(ep["chapitre"]) > 30 \
                                   else ep["chapitre"],
                    "Niveau":      ep["niveau_actuel"],
                    "Série":       ep["serie_actuelle"],
                    "Tentés":      ep["exercices_tentes"],
                    "Réussis":     ep["exercices_reussis"],
                    "Taux":        f"{taux_ex}%",
                    "Validé":      "✅" if ep["niveau_valide"] else "⏳"
                })
            df = pd.DataFrame(lignes)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Cet élève n'a pas encore fait d'exercices.")

        st.divider()

        # ── Historique des 10 derniers exercices ──────────────
        st.markdown("#### Derniers exercices")

        resultats = get_resultats_eleve(eleve["id"])
        if resultats:
            df_hist = pd.DataFrame(
                resultats[:10],
                columns=["Thème", "Niveau", "Réussi", "Temps (s)", "Date"]
            )
            df_hist["Réussi"]    = df_hist["Réussi"].map({1: "✅", 0: "❌"})
            df_hist["Temps (s)"] = df_hist["Temps (s)"].apply(
                lambda t: f"{t}s" if t else "—"
            )
            df_hist["Date"] = pd.to_datetime(
                df_hist["Date"]
            ).dt.strftime("%d/%m %H:%M")
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun exercice enregistré.")

    # ════════════════════════════════════════════════════════════
    # VUE 4 — STATISTIQUES MATIÈRES
    # ════════════════════════════════════════════════════════════
    elif vue == "📈 Statistiques matières":
        st.title("📈 Statistiques par matière")

        eleves, resultats = get_stats_globales()

        if not resultats:
            st.info("Pas encore de données.")
            return

        # Regroupement par matière
        themes = {}
        for r in resultats:
            t = r["theme"]
            if t not in themes:
                themes[t] = {
                    "total": 0, "reussis": 0,
                    "niveaux": {"Facile": 0, "Moyen": 0, "Difficile": 0}
                }
            themes[t]["total"]   += 1
            themes[t]["reussis"] += r["reussi"]
            niv = r.get("niveau", "Facile")
            if niv in themes[t]["niveaux"]:
                themes[t]["niveaux"][niv] += 1

        for theme, data in themes.items():
            taux = round(data["reussis"] / data["total"] * 100) \
                   if data["total"] > 0 else 0
            couleur = (
                "#E53E3E" if taux < 50
                else "#D69E2E" if taux < 80
                else "#38A169"
            )

            with st.expander(
                f"{COURS.get(theme, {}).get('icone', '📖')} "
                f"{theme} — {taux}% de réussite"
            ):
                col1, col2, col3 = st.columns(3)
                col1.metric("Total exercices", data["total"])
                col2.metric("Réussis",         data["reussis"])
                col3.metric("Taux",            f"{taux}%")

                # Répartition par niveau
                st.markdown("**Répartition par niveau :**")
                for niv, count in data["niveaux"].items():
                    pct_niv = round(count / data["total"] * 100) \
                              if data["total"] > 0 else 0
                    st.markdown(
                        f"""<div style='margin-bottom:6px'>
                        <div style='display:flex;justify-content:space-between;
                        font-size:13px'>
                            <span>{niv}</span>
                            <span>{count} exercices ({pct_niv}%)</span>
                        </div>
                        <div style='background:var(--color-background-secondary);
                        border-radius:4px;height:6px;margin-top:3px'>
                            <div style='background:{couleur};width:{pct_niv}%;
                            height:100%;border-radius:4px'></div>
                        </div>
                        </div>""",
                        unsafe_allow_html=True
                    )

                # Élèves les plus actifs sur cette matière
                st.markdown("**Élèves les plus actifs :**")
                eleve_theme = {}
                for r in resultats:
                    if r["theme"] == theme:
                        eid = r["eleve_id"]
                        if eid not in eleve_theme:
                            eleve_theme[eid] = {"total": 0, "reussis": 0}
                        eleve_theme[eid]["total"]   += 1
                        eleve_theme[eid]["reussis"] += r["reussi"]

                eleve_map = {e["id"]: e["prenom"] for e in eleves}
                top = sorted(
                    eleve_theme.items(),
                    key=lambda x: x[1]["total"],
                    reverse=True
                )[:5]

                if top:
                    lignes = []
                    for eid, s in top:
                        t_e = round(s["reussis"] / s["total"] * 100) \
                              if s["total"] > 0 else 0
                        lignes.append({
                            "Élève":    eleve_map.get(eid, f"#{eid}"),
                            "Exercices": s["total"],
                            "Réussis":  s["reussis"],
                            "Taux":     f"{t_e}%"
                        })
                    st.dataframe(
                        pd.DataFrame(lignes),
                        use_container_width=True,
                        hide_index=True
                    )
