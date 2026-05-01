import streamlit as st
import json
import re
import time
from groq import Groq
from database import sauvegarder_onboarding

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Génération des 10 questions de diagnostic global ──────────────
# Couvre les 4 matières du programme de manière équilibrée :
# 2-3 questions par matière, difficulté variée.
@st.cache_data(show_spinner=False)
def generer_questions_diagnostic():
    prompt = """Tu es un professeur d'informatique au Cameroun.
Génère exactement 10 questions QCM pour évaluer le niveau global
d'un élève de 1ère TI sur l'ensemble du programme.

Répartition OBLIGATOIRE :
- 3 questions Algorithmique avancée (Variables/boucles/tableaux/tri)
- 2 questions Langage C (structure, types, boucles)
- 3 questions HTML et CSS (balises, formulaires, styles)
- 2 questions JavaScript (variables, DOM, événements)

Difficulté variée : mélange facile, moyen, difficile.

Réponds UNIQUEMENT en JSON :
{
  "questions": [
    {
      "id": 1,
      "matiere": "Algorithmique avancée",
      "difficulte": "Facile",
      "question": "...",
      "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "reponse": "A",
      "explication": "..."
    }
  ]
}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.6
    )
    raw = re.sub(r"```json|```", "", response.choices[0].message.content).strip()
    return json.loads(raw)["questions"]


# ── Calcul des scores par matière ─────────────────────────────────
def calculer_scores(questions, reponses):
    scores = {
        "Algorithmique avancée": {"total": 0, "reussis": 0},
        "Langage C":             {"total": 0, "reussis": 0},
        "HTML et CSS":           {"total": 0, "reussis": 0},
        "JavaScript":            {"total": 0, "reussis": 0},
    }
    for i, q in enumerate(questions):
        matiere = q["matiere"]
        if matiere in scores:
            scores[matiere]["total"] += 1
            if reponses.get(i) == q["reponse"]:
                scores[matiere]["reussis"] += 1
    return scores


# ── Génération de la recommandation personnalisée ─────────────────
# Groq analyse les scores et recommande par où commencer,
# avec un plan d'apprentissage personnalisé.
def generer_recommandation(prenom, scores):
    scores_str = "\n".join([
        f"- {m} : {v['reussis']}/{v['total']}"
        for m, v in scores.items()
    ])

    prompt = f"""Tu es un tuteur pédagogique bienveillant pour élèves de 1ère TI au Cameroun.
L'élève {prenom} vient de passer un diagnostic. Voici ses scores :
{scores_str}

Génère une recommandation personnalisée.
Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après, sans markdown :
{{
  "niveau_global": "Débutant",
  "message": "Message encourageant pour {prenom} en 2 phrases.",
  "matiere_prioritaire": "Algorithmique avancée",
  "plan": [
    {{"ordre": 1, "matiere": "Algorithmique avancée", "raison": "score faible", "conseil": "commence par les bases"}},
    {{"ordre": 2, "matiere": "Langage C", "raison": "...", "conseil": "..."}},
    {{"ordre": 3, "matiere": "HTML et CSS", "raison": "...", "conseil": "..."}},
    {{"ordre": 4, "matiere": "JavaScript", "raison": "...", "conseil": "..."}}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant qui répond UNIQUEMENT en JSON valide, sans aucun texte avant ou après."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3  # Température basse → réponse plus fiable
        )

        raw = response.choices[0].message.content.strip()

        # Nettoyage robuste : supprime tout ce qui n'est pas du JSON
        raw = re.sub(r"```json|```", "", raw).strip()

        # Si la réponse contient du texte avant le {, on l'ignore
        debut = raw.find("{")
        fin   = raw.rfind("}") + 1
        if debut != -1 and fin > debut:
            raw = raw[debut:fin]

        return json.loads(raw)

    except Exception as e:
        # Fallback : recommandation par défaut si Groq échoue
        st.warning(f"Recommandation auto générée (erreur IA : {e})")

        # Calcul de la matière la plus faible sans Groq
        matiere_faible = min(
            scores.items(),
            key=lambda x: x[1]["reussis"] / x[1]["total"] if x[1]["total"] > 0 else 1
        )[0]

        total_reussis = sum(v["reussis"] for v in scores.values())
        total_q       = sum(v["total"] for v in scores.values())
        taux          = round(total_reussis / total_q * 100) if total_q > 0 else 0

        niveau = "Débutant" if taux < 50 else "Intermédiaire" if taux < 80 else "Avancé"

        return {
            "niveau_global":       niveau,
            "message":             f"Bravo {prenom} pour avoir complété le diagnostic ! Voici ton plan personnalisé.",
            "matiere_prioritaire": matiere_faible,
            "plan": [
                {
                    "ordre":   i + 1,
                    "matiere": m,
                    "raison":  f"Score : {v['reussis']}/{v['total']}",
                    "conseil": "Commence par les chapitres de base."
                }
                for i, (m, v) in enumerate(
                    sorted(scores.items(), key=lambda x: x[1]["reussis"] / x[1]["total"] if x[1]["total"] > 0 else 0)
                )
            ]
        }


# ── Page d'onboarding ─────────────────────────────────────────────
def page_onboarding():
    eleve    = st.session_state["eleve"]
    prenom   = eleve["prenom"]
    eleve_id = eleve["id"]

    etape = st.session_state.get("onboarding_etape", "presentation")

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 1 — Présentation de Tuteur Pro
    # ════════════════════════════════════════════════════════════
    if etape == "presentation":
        # Centrage du contenu
        _, col, _ = st.columns([1, 3, 1])
        with col:
            st.markdown(
                f"""<div style='text-align:center;padding:2rem 0'>
                <div style='font-size:64px'>🤖</div>
                <h1 style='border:none;font-size:1.8rem;margin-top:0.5rem'>
                    Bonjour {prenom} !
                </h1>
                <p style='font-size:16px;color:#4A5568;margin-bottom:2rem'>
                    Bienvenue sur <strong>Tuteur Pro</strong>
                </p>
                </div>""",
                unsafe_allow_html=True
            )

            # Présentation en cards
            st.markdown(
                """<div style='background:#EFF6FF;border-radius:14px;
                padding:1.5rem;margin-bottom:1rem'>
                <h3 style='color:#0D9AFC;margin-bottom:1rem'>
                    🎓 Qui suis-je ?
                </h3>
                <p style='font-size:15px;line-height:1.8;color:#1A202C'>
                Je suis ton <strong>tuteur intelligent</strong> conçu spécialement
                pour les élèves de <strong>1ère TI au Cameroun</strong>.<br><br>
                Je connais ton programme officiel sur le bout des doigts :
                l'<strong>Algorithmique</strong>, le <strong>Langage C</strong>,
                <strong>HTML/CSS</strong> et <strong>JavaScript</strong>.
                </p>
                </div>""",
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)

            col1.markdown(
                """<div style='background:#F0FFF4;border-radius:12px;
                padding:1.2rem;height:100%'>
                <h4 style='color:#38A169'>📚 Ce que je fais</h4>
                <ul style='font-size:14px;line-height:2;color:#1A202C'>
                <li>Cours adaptés à ton niveau</li>
                <li>Exercices personnalisés</li>
                <li>Correction intelligente</li>
                <li>Suivi de ta progression</li>
                <li>Chat pour tes questions</li>
                </ul>
                </div>""",
                unsafe_allow_html=True
            )

            col2.markdown(
                """<div style='background:#FFFBEB;border-radius:12px;
                padding:1.2rem;height:100%'>
                <h4 style='color:#D69E2E'>⚡ Comment ça marche</h4>
                <ul style='font-size:14px;line-height:2;color:#1A202C'>
                <li>Je détecte ton niveau réel</li>
                <li>J'adapte le contenu</li>
                <li>Je génère des exercices ciblés</li>
                <li>Je t'encourage à progresser</li>
                <li>Je mesure tes acquis</li>
                </ul>
                </div>""",
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.info(
                "📋 Avant de commencer, je vais te poser **10 questions rapides** "
                "pour évaluer ton niveau sur l'ensemble du programme. "
                "Cela me permettra de te recommander par où commencer !"
            )

            if st.button(
                "🚀 Commencer le diagnostic →",
                use_container_width=True,
                type="primary"
            ):
                st.session_state["onboarding_etape"] = "diagnostic"
                st.rerun()

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 2 — Diagnostic 10 questions
    # ════════════════════════════════════════════════════════════
    elif etape == "diagnostic":
        st.title("🎯 Diagnostic de niveau")
        st.caption("10 questions · Tout le programme · ~5 minutes")

        # Chargement des questions (une seule fois)
        if "diag_questions" not in st.session_state:
            with st.spinner("Préparation des questions..."):
                try:
                    st.session_state["diag_questions"] = generer_questions_diagnostic()
                    st.session_state["diag_reponses"]  = {}
                    st.session_state["diag_index"]     = 0
                    st.session_state["diag_debut"]     = time.time()
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    return

        questions = st.session_state["diag_questions"]
        index     = st.session_state["diag_index"]
        reponses  = st.session_state["diag_reponses"]

        # Barre de progression
        pct = round(index / len(questions) * 100)
        st.markdown(
            f"""<div style='margin-bottom:1.5rem'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                <span style='font-size:13px;color:#718096'>
                    Question {min(index+1, len(questions))}/{len(questions)}
                </span>
                <span style='font-size:13px;color:#0D9AFC;font-weight:600'>
                    {pct}%
                </span>
            </div>
            <div style='background:#E2E8F0;border-radius:4px;height:8px'>
                <div style='background:#0D9AFC;width:{pct}%;
                height:100%;border-radius:4px;transition:width .3s'></div>
            </div>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Question en cours ─────────────────────────────────
        if index < len(questions):
            q = questions[index]

            # Badge matière + difficulté
            couleurs_diff = {
                "Facile":   ("#EAF3DE", "#3B6D11"),
                "Moyen":    ("#FEF3C7", "#92400E"),
                "Difficile": ("#FEE2E2", "#991B1B")
            }
            bg, fg = couleurs_diff.get(q["difficulte"], ("#EFF6FF", "#1D4ED8"))
            couleurs_mat = {
                "Algorithmique avancée": "#0D9AFC",
                "Langage C":             "#38A169",
                "HTML et CSS":           "#E07B39",
                "JavaScript":            "#D69E2E"
            }
            cmat = couleurs_mat.get(q["matiere"], "#0D9AFC")

            st.markdown(
                f"""<div style='margin-bottom:1rem'>
                <span style='background:{bg};color:{fg};font-size:11px;
                font-weight:600;padding:2px 10px;border-radius:20px;
                margin-right:8px'>{q['difficulte']}</span>
                <span style='background:#EFF6FF;color:{cmat};font-size:11px;
                font-weight:600;padding:2px 10px;border-radius:20px'>
                {q['matiere']}</span>
                </div>""",
                unsafe_allow_html=True
            )

            st.markdown(f"**{q['question']}**")
            choix = st.radio(
                "Ta réponse :",
                q["choix"],
                index=None,
                key=f"onb_q_{index}"
            )

            if choix:
                repondu = choix[0]
                correct = repondu == q["reponse"]

                if correct:
                    st.success("✅ Bonne réponse !")
                else:
                    st.error(f"❌ La bonne réponse était : **{q['reponse']}**")

                st.info(f"**Explication :** {q['explication']}")

                # Sauvegarde la réponse
                st.session_state["diag_reponses"][index] = repondu

                label_btn = (
                    "Question suivante →"
                    if index < len(questions) - 1
                    else "Voir mes résultats →"
                )
                if st.button(label_btn, key=f"onb_next_{index}"):
                    st.session_state["diag_index"] += 1
                    st.rerun()

        # ── Fin du diagnostic → Résultats ─────────────────────
        else:
            st.session_state["onboarding_etape"] = "resultats"
            st.rerun()

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 3 — Résultats et recommandations
    # ════════════════════════════════════════════════════════════
    elif etape == "resultats":
        questions = st.session_state.get("diag_questions", [])
        reponses  = st.session_state.get("diag_reponses", {})
        scores    = calculer_scores(questions, reponses)
        temps     = int(time.time() - st.session_state.get("diag_debut", time.time()))

        # Génération de la recommandation IA
        if "onb_recommandation" not in st.session_state:
            with st.spinner("Analyse de tes résultats..."):
                try:
                    reco = generer_recommandation(prenom, scores)
                    st.session_state["onb_recommandation"] = reco
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    return

        reco = st.session_state["onb_recommandation"]

        _, col, _ = st.columns([0.5, 4, 0.5])
        with col:
            st.markdown(
                f"""<div style='text-align:center;padding:1rem 0 1.5rem'>
                <div style='font-size:48px'>📊</div>
                <h2>Tes résultats, {prenom} !</h2>
                <p style='color:#718096'>Complété en {temps//60}min {temps%60}s</p>
                </div>""",
                unsafe_allow_html=True
            )

            # Score global
            total_reussis = sum(v["reussis"] for v in scores.values())
            total_q       = sum(v["total"] for v in scores.values())
            taux_global   = round(total_reussis / total_q * 100) if total_q > 0 else 0

            niveaux_color = {
                "Débutant":      ("#FEE2E2", "#991B1B", "🔴"),
                "Intermédiaire": ("#FEF3C7", "#92400E", "🟡"),
                "Avancé":        ("#F0FFF4", "#276749", "🟢")
            }
            bg, fg, em = niveaux_color.get(
                reco["niveau_global"], ("#EFF6FF", "#1D4ED8", "🔵")
            )

            st.markdown(
                f"""<div style='background:{bg};border-radius:14px;
                padding:1.2rem 1.5rem;text-align:center;margin-bottom:1.5rem'>
                <div style='font-size:32px'>{em}</div>
                <div style='font-size:20px;font-weight:700;color:{fg}'>
                    Niveau global : {reco['niveau_global']}
                </div>
                <div style='font-size:15px;color:{fg};opacity:0.8'>
                    {total_reussis}/{total_q} bonnes réponses ({taux_global}%)
                </div>
                </div>""",
                unsafe_allow_html=True
            )

            # Message personnalisé de Groq
            st.markdown(
                f"""<div style='background:#EFF6FF;border-left:4px solid #0D9AFC;
                border-radius:8px;padding:1rem 1.2rem;margin-bottom:1.5rem;
                font-size:15px;line-height:1.7'>
                💬 {reco['message']}
                </div>""",
                unsafe_allow_html=True
            )

            # Scores par matière
            st.markdown("#### 📚 Scores par matière")
            icones_mat = {
                "Algorithmique avancée": "🧠",
                "Langage C":             "⚙️",
                "HTML et CSS":           "🌐",
                "JavaScript":            "✨"
            }
            cols = st.columns(4)
            for i, (mat, sc) in enumerate(scores.items()):
                taux = round(sc["reussis"] / sc["total"] * 100) if sc["total"] > 0 else 0
                couleur = (
                    "#E53E3E" if taux < 50
                    else "#D69E2E" if taux < 80
                    else "#38A169"
                )
                cols[i].markdown(
                    f"""<div style='background:white;border-radius:12px;
                    padding:1rem;text-align:center;border:1px solid #E2E8F0;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06)'>
                    <div style='font-size:24px'>{icones_mat.get(mat,'📖')}</div>
                    <div style='font-size:12px;color:#718096;margin:4px 0'>
                        {mat.split()[0]}
                    </div>
                    <div style='font-size:22px;font-weight:700;color:{couleur}'>
                        {taux}%
                    </div>
                    <div style='font-size:11px;color:#A0AEC0'>
                        {sc['reussis']}/{sc['total']}
                    </div>
                    </div>""",
                    unsafe_allow_html=True
                )

            # Plan d'apprentissage recommandé
            st.markdown(
                "<br>#### 🗺️ Ton plan d'apprentissage personnalisé",
                unsafe_allow_html=True
            )
            st.caption("Dans cet ordre, selon tes résultats :")

            for item in reco["plan"]:
                mat    = item["matiere"]
                icone  = icones_mat.get(mat, "📖")
                sc     = scores.get(mat, {"reussis": 0, "total": 1})
                taux_m = round(sc["reussis"] / sc["total"] * 100) if sc["total"] > 0 else 0
                priorite = (
                    "⚠️ Priorité" if taux_m < 50
                    else "📈 À consolider" if taux_m < 80
                    else "🌟 Approfondir"
                )

                st.markdown(
                    f"""<div style='background:white;border-radius:12px;
                    padding:1rem 1.2rem;margin-bottom:10px;
                    border:1px solid #E2E8F0;
                    border-left:4px solid #0D9AFC;
                    box-shadow:0 2px 6px rgba(0,0,0,0.05)'>
                    <div style='display:flex;align-items:center;
                    justify-content:space-between;margin-bottom:6px'>
                        <span style='font-weight:600;font-size:15px'>
                            {item['ordre']}. {icone} {mat}
                        </span>
                        <span style='font-size:12px;color:#718096'>
                            {priorite} · {taux_m}%
                        </span>
                    </div>
                    <div style='font-size:13px;color:#4A5568;margin-bottom:4px'>
                        📌 {item['raison']}
                    </div>
                    <div style='font-size:13px;color:#0D9AFC'>
                        💡 {item['conseil']}
                    </div>
                    </div>""",
                    unsafe_allow_html=True
                )

            # Sauvegarde en Supabase et accès à l'app
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(
                f"🚀 Commencer par {reco['matiere_prioritaire']} →",
                use_container_width=True,
                type="primary"
            ):
                # Sauvegarde dans Supabase
                sauvegarder_onboarding(
                    eleve_id,
                    {m: {"reussis": v["reussis"], "total": v["total"]}
                     for m, v in scores.items()},
                    json.dumps(reco, ensure_ascii=False)
                )

                # Redirige vers la page cours avec la matière recommandée
                st.session_state["onboarding_fait"]  = True
                st.session_state["cours_theme"]       = reco["matiere_prioritaire"]
                st.session_state["page"]              = "📖 Cours"

                # Nettoyage session diagnostic
                for key in ["diag_questions", "diag_reponses",
                            "diag_index", "diag_debut", "onb_recommandation",
                            "onboarding_etape"]:
                    st.session_state.pop(key, None)
                st.rerun()
