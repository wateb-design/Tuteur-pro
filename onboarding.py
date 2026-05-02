import streamlit as st
import json
import re
import time
from groq import Groq
from database import sauvegarder_onboarding

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@st.cache_data(show_spinner=False)
def generer_questions_diagnostic():
    prompt = """Tu es un professeur d informatique au Cameroun.
Genere exactement 10 questions QCM pour evaluer le niveau global
d un eleve de 1ere TI sur l ensemble du programme.

Repartition OBLIGATOIRE :
- 3 questions Algorithmique avancee (Variables/boucles/tableaux/tri)
- 2 questions Langage C (structure, types, boucles)
- 3 questions HTML et CSS (balises, formulaires, styles)
- 2 questions JavaScript (variables, DOM, evenements)

Difficulte variee : melange facile, moyen, difficile.
Reponds UNIQUEMENT en JSON valide, sans texte avant ou apres :
{
  "questions": [
    {
      "id": 1,
      "matiere": "Algorithmique avancee",
      "difficulte": "Facile",
      "question": "...",
      "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "reponse": "A",
      "explication": "..."
    }
  ]
}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Tu reponds UNIQUEMENT en JSON valide. Pas de texte avant ou apres. Pas de markdown. Pas d apostrophes dans les valeurs JSON."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        debut = raw.find("{")
        fin   = raw.rfind("}") + 1
        if debut != -1 and fin > debut:
            raw = raw[debut:fin]
        return json.loads(raw)["questions"]
    except Exception as e:
        st.error(f"Erreur generation questions : {e}")
        return []


def calculer_scores(questions, reponses):
    scores = {
        "Algorithmique avancee": {"total": 0, "reussis": 0},
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


def generer_recommandation(prenom, scores):
    scores_str = "\n".join([
        f"- {m} : {v['reussis']}/{v['total']}"
        for m, v in scores.items()
    ])
    prompt = f"""Tu es un tuteur pedagogique bienveillant pour eleves de 1ere TI au Cameroun.
L eleve {prenom} vient de passer un diagnostic. Voici ses scores :
{scores_str}

Reponds UNIQUEMENT avec du JSON valide, sans texte avant ou apres :
{{
  "niveau_global": "Debutant",
  "message": "Message encourageant pour {prenom} en 2 phrases.",
  "matiere_prioritaire": "Algorithmique avancee",
  "plan": [
    {{"ordre": 1, "matiere": "Algorithmique avancee", "raison": "...", "conseil": "..."}},
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
                    "content": "Tu reponds UNIQUEMENT en JSON valide sans texte avant ou apres."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        debut = raw.find("{")
        fin   = raw.rfind("}") + 1
        if debut != -1 and fin > debut:
            raw = raw[debut:fin]
        return json.loads(raw)
    except Exception as e:
        st.warning(f"Recommandation par defaut ({e})")
        matiere_faible = min(
            scores.items(),
            key=lambda x: x[1]["reussis"] / x[1]["total"] if x[1]["total"] > 0 else 1
        )[0]
        total_reussis = sum(v["reussis"] for v in scores.values())
        total_q       = sum(v["total"]   for v in scores.values())
        taux          = round(total_reussis / total_q * 100) if total_q > 0 else 0
        niveau        = "Debutant" if taux < 50 else "Intermediaire" if taux < 80 else "Avance"
        return {
            "niveau_global":       niveau,
            "message":             f"Bravo {prenom} ! Voici ton plan personnalise.",
            "matiere_prioritaire": matiere_faible,
            "plan": [
                {
                    "ordre":   i + 1,
                    "matiere": m,
                    "raison":  f"Score : {v['reussis']}/{v['total']}",
                    "conseil": "Commence par les chapitres de base."
                }
                for i, (m, v) in enumerate(
                    sorted(scores.items(),
                           key=lambda x: x[1]["reussis"] / x[1]["total"]
                           if x[1]["total"] > 0 else 0)
                )
            ]
        }


# ── Composants visuels ────────────────────────────────────────────

def carte_feature(icone, titre, items):
    """Carte feature avec liste de points."""
    items_html = "".join([
        f"<div style='display:flex;align-items:center;gap:8px;padding:5px 0;"
        f"border-bottom:0.5px solid var(--color-border-tertiary)'>"
        f"<span style='width:6px;height:6px;border-radius:50%;"
        f"background:#0D9AFC;flex-shrink:0'></span>"
        f"<span style='font-size:13px;color:var(--color-text-secondary)'>{item}</span>"
        f"</div>"
        for item in items
    ])
    return f"""
    <div style='background:var(--color-background-primary);
    border:0.5px solid var(--color-border-tertiary);
    border-radius:var(--border-radius-lg);
    padding:1.25rem;height:100%'>
    <div style='font-size:20px;margin-bottom:10px'>{icone}</div>
    <div style='font-size:14px;font-weight:500;
    color:var(--color-text-primary);margin-bottom:12px'>{titre}</div>
    {items_html}
    </div>"""


def badge_matiere(matiere, icone, taux, sc):
    """Badge de score par matière."""
    couleur = (
        "#E53E3E" if taux < 50
        else "#D69E2E" if taux < 80
        else "#38A169"
    )
    bg = (
        "#FEE2E2" if taux < 50
        else "#FEF3C7" if taux < 80
        else "#F0FFF4"
    )
    return f"""
    <div style='background:var(--color-background-primary);
    border:0.5px solid var(--color-border-tertiary);
    border-radius:var(--border-radius-lg);
    padding:1rem;text-align:center'>
    <div style='font-size:22px;margin-bottom:6px'>{icone}</div>
    <div style='font-size:12px;color:var(--color-text-secondary);
    margin-bottom:8px;line-height:1.3'>{matiere.split()[0]}</div>
    <div style='font-size:24px;font-weight:500;color:{couleur}'>{taux}%</div>
    <div style='font-size:11px;margin-top:4px;padding:2px 8px;
    border-radius:20px;background:{bg};color:{couleur};
    display:inline-block'>{sc["reussis"]}/{sc["total"]}</div>
    </div>"""


def carte_plan(item, icone, taux_m):
    """Carte du plan d'apprentissage."""
    priorite_txt = (
        "Prioritaire" if taux_m < 50
        else "A consolider" if taux_m < 80
        else "Approfondir"
    )
    priorite_bg = (
        "#FEE2E2" if taux_m < 50
        else "#FEF3C7" if taux_m < 80
        else "#F0FFF4"
    )
    priorite_col = (
        "#991B1B" if taux_m < 50
        else "#92400E" if taux_m < 80
        else "#276749"
    )
    return f"""
    <div style='background:var(--color-background-primary);
    border:0.5px solid var(--color-border-tertiary);
    border-left:3px solid #0D9AFC;
    border-radius:var(--border-radius-lg);
    padding:1rem 1.25rem;margin-bottom:10px'>
    <div style='display:flex;align-items:center;
    justify-content:space-between;margin-bottom:8px'>
        <div style='display:flex;align-items:center;gap:8px'>
            <span style='font-size:18px'>{icone}</span>
            <span style='font-size:14px;font-weight:500;
            color:var(--color-text-primary)'>
                {item["ordre"]}. {item["matiere"]}
            </span>
        </div>
        <span style='font-size:11px;padding:2px 10px;
        border-radius:20px;font-weight:500;
        background:{priorite_bg};color:{priorite_col}'>
            {priorite_txt}
        </span>
    </div>
    <div style='font-size:13px;color:var(--color-text-secondary);
    margin-bottom:4px;padding-left:26px'>
        {item["raison"]}
    </div>
    <div style='font-size:13px;color:#0D9AFC;padding-left:26px'>
        {item["conseil"]}
    </div>
    </div>"""


# ── Page onboarding ───────────────────────────────────────────────
def page_onboarding():
    eleve    = st.session_state["eleve"]
    prenom   = eleve["prenom"]
    eleve_id = eleve["id"]
    etape    = st.session_state.get("onboarding_etape", "presentation")

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 1 — Présentation
    # ════════════════════════════════════════════════════════════
    if etape == "presentation":

        # ── Hero ─────────────────────────────────────────────
        st.markdown(
            f"""<div style='text-align:center;padding:2.5rem 0 2rem'>
            <div style='width:72px;height:72px;border-radius:50%;
            background:linear-gradient(135deg,#0D9AFC,#0A7FD4);
            display:flex;align-items:center;justify-content:center;
            margin:0 auto 1.25rem;font-size:32px'>🤖</div>
            <h1 style='font-size:2rem;font-weight:500;
            color:var(--color-text-primary);margin-bottom:0.5rem;
            border:none;padding:0'>Bonjour {prenom} !</h1>
            <p style='font-size:1.1rem;color:var(--color-text-secondary);
            margin-bottom:0.25rem'>
                Bienvenue sur <strong style='color:#0D9AFC'>Tuteur Pro</strong>
            </p>
            <p style='font-size:14px;color:var(--color-text-tertiary)'>
                Ton assistant intelligent · Programmation 1ère TI · Cameroun
            </p>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Séparateur ────────────────────────────────────────
        st.markdown(
            "<hr style='border:none;border-top:0.5px solid "
            "var(--color-border-tertiary);margin:0 0 2rem'>",
            unsafe_allow_html=True
        )

        # ── Présentation ──────────────────────────────────────
        st.markdown(
            "<p style='font-size:15px;line-height:1.8;"
            "color:var(--color-text-secondary);text-align:center;"
            "max-width:520px;margin:0 auto 2rem'>Je connais ton programme officiel"
            " sur le bout des doigts et je vais adapter chaque cours, chaque"
            " exercice et chaque feedback à <strong style='color:"
            "var(--color-text-primary)'>ton niveau réel</strong>.</p>",
            unsafe_allow_html=True
        )

        # ── 4 cartes features ─────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(
            carte_feature("📚", "Cours APC", [
                "Algorithmique avancée",
                "Langage C",
                "HTML et CSS",
                "JavaScript"
            ]),
            unsafe_allow_html=True
        )
        col2.markdown(
            carte_feature("🧠", "Exercices adaptatifs", [
                "10 exercices/niveau",
                "4 types d'exercices",
                "Correction IA",
                "Indices progressifs"
            ]),
            unsafe_allow_html=True
        )
        col3.markdown(
            carte_feature("⚡", "IA personnalisée", [
                "Diagnostic de niveau",
                "Contenu adapté",
                "Feedback intelligent",
                "Progression auto"
            ]),
            unsafe_allow_html=True
        )
        col4.markdown(
            carte_feature("🏆", "Gamification", [
                "Points XP",
                "Badges et niveaux",
                "Classement",
                "Défis hebdo"
            ]),
            unsafe_allow_html=True
        )

        # ── Encart diagnostic ─────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """<div style='background:var(--color-background-secondary);
            border:0.5px solid var(--color-border-tertiary);
            border-left:3px solid #0D9AFC;
            border-radius:var(--border-radius-lg);
            padding:1.25rem 1.5rem;
            display:flex;align-items:flex-start;gap:14px;
            margin-bottom:1.5rem'>
            <div style='font-size:22px;flex-shrink:0;margin-top:2px'>📋</div>
            <div>
                <div style='font-size:14px;font-weight:500;
                color:var(--color-text-primary);margin-bottom:4px'>
                    Avant de commencer — Diagnostic de niveau
                </div>
                <div style='font-size:13px;color:var(--color-text-secondary);
                line-height:1.6'>
                    Je vais te poser <strong>10 questions</strong> couvrant
                    l'ensemble du programme (~5 minutes). Tes réponses me
                    permettront de <strong>personnaliser ton parcours</strong>
                    et de te recommander par où commencer.
                </div>
            </div>
            </div>""",
            unsafe_allow_html=True
        )

        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if st.button(
                "Commencer le diagnostic",
                use_container_width=True,
                type="primary"
            ):
                st.session_state["onboarding_etape"] = "diagnostic"
                st.rerun()

    # ════════════════════════════════════════════════════════════
    # ÉTAPE 2 — Diagnostic 10 questions
    # ════════════════════════════════════════════════════════════
    elif etape == "diagnostic":

        # ── En-tête ───────────────────────────────────────────
        st.markdown(
            """<div style='text-align:center;padding:1.5rem 0 1rem'>
            <h2 style='font-size:1.4rem;font-weight:500;
            color:var(--color-text-primary);margin-bottom:6px'>
                Diagnostic de niveau
            </h2>
            <p style='font-size:13px;color:var(--color-text-secondary)'>
                10 questions · Tout le programme · ~5 minutes
            </p>
            </div>""",
            unsafe_allow_html=True
        )

        # Chargement des questions
        if "diag_questions" not in st.session_state:
            with st.spinner("Préparation des questions..."):
                questions = generer_questions_diagnostic()
                if not questions:
                    st.error("Erreur de génération. Rechargez la page.")
                    return
                st.session_state["diag_questions"] = questions
                st.session_state["diag_reponses"]  = {}
                st.session_state["diag_index"]     = 0
                st.session_state["diag_debut"]     = time.time()

        questions = st.session_state["diag_questions"]
        index     = st.session_state["diag_index"]

        # ── Barre de progression ──────────────────────────────
        pct = round(index / len(questions) * 100)
        st.markdown(
            f"""<div style='margin-bottom:1.5rem'>
            <div style='display:flex;justify-content:space-between;
            margin-bottom:6px'>
                <span style='font-size:12px;
                color:var(--color-text-tertiary)'>
                    Question {min(index+1, len(questions))} sur {len(questions)}
                </span>
                <span style='font-size:12px;font-weight:500;color:#0D9AFC'>
                    {pct}%
                </span>
            </div>
            <div style='background:var(--color-background-secondary);
            border-radius:4px;height:6px'>
                <div style='background:#0D9AFC;width:{pct}%;
                height:100%;border-radius:4px;transition:width .4s'></div>
            </div>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Question en cours ─────────────────────────────────
        if index < len(questions):
            q = questions[index]

            # Badges matière + difficulté
            couleurs_diff = {
                "Facile":    ("#EAF3DE", "#3B6D11"),
                "Moyen":     ("#FEF3C7", "#92400E"),
                "Difficile": ("#FEE2E2", "#991B1B")
            }
            couleurs_mat = {
                "Algorithmique avancee": ("#EEEDFE", "#3C3489"),
                "Langage C":             ("#E1F5EE", "#085041"),
                "HTML et CSS":           ("#FFF7ED", "#9A3412"),
                "JavaScript":            ("#FEFCE8", "#713F12")
            }
            bg_d, fg_d = couleurs_diff.get(q["difficulte"], ("#F1EFE8", "#5F5E5A"))
            bg_m, fg_m = couleurs_mat.get(q["matiere"],     ("#F1EFE8", "#5F5E5A"))

            st.markdown(
                f"""<div style='margin-bottom:1.25rem'>
                <span style='font-size:11px;font-weight:500;padding:3px 10px;
                border-radius:20px;margin-right:6px;
                background:{bg_m};color:{fg_m}'>{q["matiere"]}</span>
                <span style='font-size:11px;font-weight:500;padding:3px 10px;
                border-radius:20px;
                background:{bg_d};color:{fg_d}'>{q["difficulte"]}</span>
                </div>""",
                unsafe_allow_html=True
            )

            # Question dans une carte
            st.markdown(
                f"""<div style='background:var(--color-background-primary);
                border:0.5px solid var(--color-border-tertiary);
                border-radius:var(--border-radius-lg);
                padding:1.25rem 1.5rem;margin-bottom:1.25rem'>
                <p style='font-size:15px;font-weight:500;
                color:var(--color-text-primary);line-height:1.6;margin:0'>
                    {q["question"]}
                </p>
                </div>""",
                unsafe_allow_html=True
            )

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
                    st.success("Bonne réponse !")
                else:
                    st.error(
                        f"Pas tout à fait. "
                        f"La bonne réponse était : **{q['reponse']}**"
                    )
                st.info(f"**Explication :** {q['explication']}")
                st.session_state["diag_reponses"][index] = repondu

                label_btn = (
                    "Question suivante"
                    if index < len(questions) - 1
                    else "Voir mes résultats"
                )
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if st.button(
                        label_btn,
                        key=f"onb_next_{index}",
                        use_container_width=True
                    ):
                        st.session_state["diag_index"] += 1
                        st.rerun()
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
        temps     = int(
            time.time() - st.session_state.get("diag_debut", time.time())
        )

        if "onb_recommandation" not in st.session_state:
            with st.spinner("Analyse de tes résultats..."):
                reco = generer_recommandation(prenom, scores)
                st.session_state["onb_recommandation"] = reco

        reco = st.session_state["onb_recommandation"]

        # ── En-tête résultats ─────────────────────────────────
        total_reussis = sum(v["reussis"] for v in scores.values())
        total_q       = sum(v["total"]   for v in scores.values())
        taux_global   = round(total_reussis / total_q * 100) if total_q > 0 else 0

        niveaux_config = {
            "Debutant":      ("#FEE2E2", "#991B1B", "Débutant"),
            "Intermediaire": ("#FEF3C7", "#92400E", "Intermédiaire"),
            "Avance":        ("#F0FFF4", "#276749", "Avancé")
        }
        bg_n, fg_n, label_n = niveaux_config.get(
            reco["niveau_global"], ("#EFF6FF", "#1D4ED8", reco["niveau_global"])
        )

        st.markdown(
            f"""<div style='text-align:center;padding:1.5rem 0 1rem'>
            <h2 style='font-size:1.4rem;font-weight:500;
            color:var(--color-text-primary);margin-bottom:0.5rem'>
                Tes résultats, {prenom}
            </h2>
            <p style='font-size:13px;color:var(--color-text-tertiary)'>
                Complété en {temps//60}min {temps%60}s
                · {total_reussis}/{total_q} bonnes réponses
            </p>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Niveau global ─────────────────────────────────────
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            st.markdown(
                f"""<div style='background:{bg_n};
                border-radius:var(--border-radius-lg);
                padding:1.25rem;text-align:center;margin-bottom:1.5rem'>
                <div style='font-size:13px;color:{fg_n};
                font-weight:500;margin-bottom:6px'>
                    Niveau détecté
                </div>
                <div style='font-size:2rem;font-weight:500;color:{fg_n}'>
                    {label_n}
                </div>
                <div style='font-size:13px;color:{fg_n};
                opacity:0.8;margin-top:4px'>
                    {taux_global}% de réussite
                </div>
                </div>""",
                unsafe_allow_html=True
            )

        # ── Message IA ────────────────────────────────────────
        st.markdown(
            f"""<div style='background:var(--color-background-secondary);
            border:0.5px solid var(--color-border-tertiary);
            border-left:3px solid #0D9AFC;
            border-radius:var(--border-radius-lg);
            padding:1rem 1.25rem;margin-bottom:1.5rem;
            font-size:14px;line-height:1.7;
            color:var(--color-text-secondary)'>
            {reco["message"]}
            </div>""",
            unsafe_allow_html=True
        )

        # ── Scores par matière ────────────────────────────────
        st.markdown(
            "<p style='font-size:14px;font-weight:500;"
            "color:var(--color-text-primary);margin-bottom:10px'>"
            "Scores par matière</p>",
            unsafe_allow_html=True
        )

        icones_mat = {
            "Algorithmique avancee": "🧠",
            "Langage C":             "⚙️",
            "HTML et CSS":           "🌐",
            "JavaScript":            "✨"
        }
        cols = st.columns(4)
        for i, (mat, sc) in enumerate(scores.items()):
            taux = round(sc["reussis"] / sc["total"] * 100) if sc["total"] > 0 else 0
            icone = icones_mat.get(mat, "📖")
            cols[i].markdown(
                badge_matiere(mat, icone, taux, sc),
                unsafe_allow_html=True
            )

        # ── Plan d'apprentissage ──────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:14px;font-weight:500;"
            "color:var(--color-text-primary);margin-bottom:4px'>"
            "Ton plan d'apprentissage personnalisé</p>"
            "<p style='font-size:13px;color:var(--color-text-secondary);"
            "margin-bottom:12px'>Dans cet ordre, selon tes résultats</p>",
            unsafe_allow_html=True
        )

        for item in reco["plan"]:
            mat    = item["matiere"]
            icone  = icones_mat.get(mat, "📖")
            sc     = scores.get(mat, {"reussis": 0, "total": 1})
            taux_m = round(sc["reussis"] / sc["total"] * 100) if sc["total"] > 0 else 0
            st.markdown(
                carte_plan(item, icone, taux_m),
                unsafe_allow_html=True
            )

        # ── CTA final ─────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        matiere_start = reco.get(
            "matiere_prioritaire", "Algorithmique avancee"
        )

        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if st.button(
                f"Commencer par {matiere_start}",
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
                st.session_state["onboarding_fait"] = True
                st.session_state["cours_theme"]     = matiere_start
                st.session_state["page"]            = "📖 Cours"

                for key in [
                    "diag_questions", "diag_reponses", "diag_index",
                    "diag_debut", "onb_recommandation", "onboarding_etape"
                ]:
                    st.session_state.pop(key, None)
                st.rerun()
