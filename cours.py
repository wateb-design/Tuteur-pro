import streamlit as st
from groq import Groq
import json
import re
from database import (
    sauvegarder_diagnostic,
    get_niveau_detecte,
    marquer_cours_vu,
    marquer_quiz_reussi,
    get_progression_cours,
    # ── Nouvelles fonctions cache BDD ─────────────────────────────
    get_cours_contenu,
    sauvegarder_cours_contenu,
    get_quiz_contenu,
    sauvegarder_quiz_contenu,
    get_diagnostic_questions,
    sauvegarder_diagnostic_questions
)

from cours_data import COURS, NIVEAUX

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Instructions spécifiques par matière (niveau global) ─────────
INSTRUCTIONS_SPECIFIQUES = {

    "Algorithmique avancée": """
REGLES STRICTES — Algorithmique :
- Utilise UNIQUEMENT le pseudo-code LDA (Langage de Description d Algorithme)
- INTERDIT : Python, C, JavaScript ou tout autre langage de programmation
- Syntaxe obligatoire :
  * Debut / Fin
  * Variable nom : Type  (Types : Entier, Reel, Caractere, Booleen, Chaine)
  * Constante NOM = valeur
  * nom <- valeur  (affectation)
  * Lire(nom)  /  Ecrire(valeur)
  * Si condition Alors ... Sinon ... FinSi
  * Selon nom Faire cas1: ... cas2: ... FinSelon
  * Pour i <- debut A fin Faire ... FinPour
  * TantQue condition Faire ... FinTantQue
  * Repeter ... Jusqu A condition
  * Tableau T[n] : Type
  * Enregistrement nom ... FinEnregistrement
  * Fonction nom(params) : TypeRetour ... FinFonction
  * Procedure nom(params) ... FinProcedure
- Trace d execution obligatoire pour les exemples
- Exemple complet avec Debut...Fin""",

    "Algorithmique avancée_algorigramme": """
REGLES STRICTES — Algorigrammes (symboles officiels programme camerounais) :

SYMBOLES A UTILISER :
+----------------------+------------------------------------------+
| REPRESENTATION ASCII | DESIGNATION OFFICIELLE                   |
+----------------------+------------------------------------------+
|  (  DEBUT / FIN  )   | Ovale : debut, fin ou interruption       |
+----------------------+------------------------------------------+
|  [  traitement   ]   | Rectangle : operation sur donnees        |
+----------------------+------------------------------------------+
| [| sous-programme|]  | Rectangle double barre : sous-programme  |
+----------------------+------------------------------------------+
|  /  Lire/Ecrire  /   | Parallelogramme : entree ou sortie       |
+----------------------+------------------------------------------+
|      /  oui \        | Losange : branchement / decision         |
|     / condit \       | Sorties : OUI (gauche/bas) NON (droite)  |
|     \        /       |                                          |
|      \  non /        |                                          |
+----------------------+------------------------------------------+
|        O             | Cercle : renvoi / connecteur             |
+----------------------+------------------------------------------+
|        |             | Ligne de liaison (haut vers bas)         |
|        v             | Fleche pour cheminement different        |
+----------------------+------------------------------------------+

REGLES DE CONSTRUCTION :
1. Cheminement de HAUT en BAS, de GAUCHE a DROITE
2. Toujours commencer par ovale DEBUT et finir par ovale FIN
3. Entrees/sorties dans le parallelogramme uniquement
4. Decisions dans le losange uniquement
5. Sous-programmes dans le rectangle double barre
- Algorigramme ASCII complet + pseudo-code LDA correspondant
- Legende des symboles utilises
- 2 exemples de complexite croissante""",

    "Langage C": """
REGLES — Langage C :
- C standard C99 uniquement
- Toujours inclure les headers (#include <stdio.h> etc.)
- Fonction main() complete obligatoire
- Afficher la sortie attendue du programme""",

    "HTML et CSS": """
REGLES — HTML/CSS :
- HTML5 (DOCTYPE html)
- Structure complete de la page toujours presente
- Exemples concrets camerounais
- Decrire le rendu visuel attendu""",

    "JavaScript": """
REGLES — JavaScript :
- JS moderne integre dans une page HTML complete
- Montrer l interaction DOM
- Afficher le resultat attendu dans le navigateur
- Exemples concrets camerounais"""
}

# ── Génération contenu APC ────────────────────────────────────────
# ── Génération contenu APC avec cache BDD ────────────────────────
# Logique : BDD d'abord → Groq si absent → sauvegarde BDD
# Avantage : affichage instantané si déjà généré, tokens économisés
def generer_contenu(theme, chapitre, niveau, competence, savoir_faire):

    # ── Étape 1 : chercher en BDD ─────────────────────────────────
    contenu_bdd = get_cours_contenu(theme, chapitre, niveau)
    if contenu_bdd:
        return contenu_bdd  # Affichage instantané depuis Supabase

    # ── Étape 2 : générer avec Groq si absent ─────────────────────
    sf_str = "\n".join([f"- {sf}" for sf in savoir_faire])

    if theme == "Algorithmique avancée" and "algorigramme" in chapitre.lower():
        instruction = INSTRUCTIONS_SPECIFIQUES.get(
            "Algorithmique avancée_algorigramme", ""
        )
    else:
        instruction = INSTRUCTIONS_SPECIFIQUES.get(theme, "")

    prompt = f"""Tu es un professeur expert en informatique au Cameroun, specialiste APC.
Redige un cours complet et detaille selon le modele APC pour eleves de 1ere TI, niveau {niveau}.

Matiere : {theme} | Chapitre : {chapitre}
Competence officielle : {competence}
Savoir-faire a developper :
{sf_str}

{instruction}

Structure EXACTE — respecte ces titres mot pour mot, dans cet ordre :

## 🎯 Competence visee
Reprends la competence officielle telle quelle.

## 🧩 Situation-probleme
Construis une situation-probleme complete avec ces 4 composants :

**Contexte** :
Decris une situation reelle et concrete du quotidien camerounais liee a {theme}.
Reponds aux questions : qui ? ou ? quand ? pourquoi ? (2-3 phrases precises)

**Support** :
Fournis les ressources necessaires : extrait de code, algorithme incomplet,
tableau de donnees, schema textuel ou tout element d information utile.
Le support doit etre suffisamment riche pour permettre de resoudre le probleme.

**Tache** :
Formule le defi principal que l eleve doit relever.
Commence par un verbe d action (Ecris, Construis, Realise, Developpe, Analyse...).
La tache doit necessiter la combinaison de PLUSIEURS savoirs du chapitre.

**Consignes** :
1. Premiere instruction claire et precise
2. Deuxieme instruction
3. Troisieme instruction
4. Quatrieme instruction si necessaire
Les consignes indiquent ce qui est attendu SANS donner la solution.

## 📚 Savoirs essentiels
Cette section doit etre TRES DETAILLEE. Structure-la ainsi :

### Definitions et concepts cles
Pour chaque notion importante du chapitre :
- Donne une definition precise et claire
- Explique le concept avec des mots simples adaptes au niveau {niveau}
- Illustre avec un exemple concret du contexte camerounais

### Syntaxe et regles
- Presente la syntaxe officielle de chaque element du chapitre
- Explique chaque composant de la syntaxe
- Montre les variantes possibles si elles existent

### Proprietes et caracteristiques
- Liste les proprietes importantes
- Explique les contraintes et limitations
- Presente les cas particuliers a connaitre

### Tableau recapitulatif
Presente un tableau clair resumant les elements cles :
| Element | Description | Exemple |
|---------|-------------|---------|
| ...     | ...         | ...     |

## 💻 Exemples commentes
Fournis 2 exemples progressifs :

### Exemple 1 — Niveau de base
(Exemple simple illustrant le concept fondamental, bien commente)

### Exemple 2 — Niveau avance
#(Exemple plus complexe combinant plusieurs notions, )

## ⚠️ Erreurs frequentes
Pour chaque erreur :
- **Erreur** : description de l erreur
- **Mauvais exemple** : montrer le code/algo incorrect
- **Correction** : montrer la version correcte
- **Explication** : pourquoi c est une erreur

## 📝 Synthese
Presente une synthese structuree :

### Points cles a retenir
(3-5 points essentiels sous forme de liste claire)

### Schema de rappel
(Un schema textuel ou tableau resumant les elements importants)

### Conseil methode
(1-2 conseils pratiques pour bien maitriser ce chapitre)"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un professeur expert en informatique au Cameroun.
Tu enseignes en 1ere TI selon le programme officiel camerounais.
Tu respectes STRICTEMENT les conventions de chaque matiere :
- Algorithmique : pseudo-code LDA UNIQUEMENT (jamais Python ou autre langage)
- Algorigrammes : schemas ASCII avec symboles officiels camerounais
- Langage C : code C standard avec main() complete
- HTML/CSS : HTML5 avec structure complete
- JavaScript : JS moderne integre dans HTML
Tu structures tes cours selon le modele APC sans jamais inclure
de sections exercices guides ou savoir-faire a toi de jouer.
La section Savoirs essentiels doit etre tres detaillee."""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        contenu = response.choices[0].message.content

        # ── Étape 3 : sauvegarder en BDD pour les prochains appels ──
        sauvegarder_cours_contenu(theme, chapitre, niveau, contenu)

        return contenu

    except Exception as e:
        return f"Erreur de génération : {e}"

# ── Génération quiz avec cache BDD ────────────────────────────────
def generer_quiz(theme, chapitre, niveau, competence):

    # Étape 1 : chercher en BDD
    quiz_bdd = get_quiz_contenu(theme, chapitre, niveau)
    if quiz_bdd:
        return quiz_bdd

    # Étape 2 : générer avec Groq si absent
    prompt = f"""Genere un QCM APC pour :
Matiere : {theme} | Chapitre : {chapitre} | Niveau : {niveau}
Competence : {competence}

JSON uniquement, sans texte avant ou apres :
{{
  "question": "...",
  "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "reponse": "A",
  "explication": "...",
  "savoir_faire_evalue": "..."
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
            max_tokens=400,
            temperature=0.5
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        debut = raw.find("{")
        fin   = raw.rfind("}") + 1
        if debut != -1 and fin > debut:
            raw = raw[debut:fin]
        quiz = json.loads(raw)

        # Étape 3 : sauvegarder en BDD
        sauvegarder_quiz_contenu(theme, chapitre, niveau, quiz)
        return quiz

    except Exception as e:
        st.warning(f"Quiz indisponible : {e}")
        return None


# ── Diagnostic de niveau ──────────────────────────────────────────
@st.cache_data(show_spinner=False)
def generer_diagnostic(theme):
    prompt = f"""Tu es un professeur d informatique au Cameroun.
Genere exactement 3 questions QCM de difficulte croissante pour evaluer
un eleve de 1ere TI en {theme}.

Reponds UNIQUEMENT avec du JSON valide, sans texte avant ou apres.
Utilise uniquement des guillemets doubles. Pas d apostrophes dans les textes.
Format exact :
{{
  "questions": [
    {{
      "niveau": "Facile",
      "question": "Question facile sur {theme} ?",
      "choix": ["A. choix1", "B. choix2", "C. choix3", "D. choix4"],
      "reponse": "A",
      "explication": "Explication simple."
    }},
    {{
      "niveau": "Moyen",
      "question": "Question moyenne sur {theme} ?",
      "choix": ["A. choix1", "B. choix2", "C. choix3", "D. choix4"],
      "reponse": "B",
      "explication": "Explication moyenne."
    }},
    {{
      "niveau": "Difficile",
      "question": "Question difficile sur {theme} ?",
      "choix": ["A. choix1", "B. choix2", "C. choix3", "D. choix4"],
      "reponse": "C",
      "explication": "Explication avancee."
    }}
  ]
}}"""

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
            max_tokens=1000,
            temperature=0.2
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        debut = raw.find("{")
        fin   = raw.rfind("}") + 1
        if debut != -1 and fin > debut:
            raw = raw[debut:fin]
        return json.loads(raw)

    except json.JSONDecodeError:
        st.warning("Génération automatique du diagnostic...")
        return {
            "questions": [
                {
                    "niveau": "Facile",
                    "question": f"Parmi les elements suivants, lequel appartient au cours de {theme} ?",
                    "choix": ["A. Variable", "B. Photoshop", "C. Excel", "D. PowerPoint"],
                    "reponse": "A",
                    "explication": "Une variable est un concept fondamental en programmation."
                },
                {
                    "niveau": "Moyen",
                    "question": f"Quelle structure permet de repeter des instructions en {theme} ?",
                    "choix": ["A. Un tableau", "B. Une boucle", "C. Une couleur", "D. Un fichier"],
                    "reponse": "B",
                    "explication": "Une boucle permet de repeter des instructions."
                },
                {
                    "niveau": "Difficile",
                    "question": "Qu est-ce qu une fonction en programmation ?",
                    "choix": ["A. Un calcul mathematique", "B. Un bloc de code reutilisable", "C. Un type de variable", "D. Une boucle infinie"],
                    "reponse": "B",
                    "explication": "Une fonction est un bloc de code reutilisable qui effectue une tache precise."
                }
            ]
        }
    except Exception as e:
        st.error(f"Erreur : {e}")
        return None


def niveau_depuis_score(score):
    if score <= 1:
        return "Débutant"
    elif score == 2:
        return "Intermédiaire"
    else:
        return "Avancé"


# ── Indicateur de progression ─────────────────────────────────────
def afficher_progression(progression, total_chapitres):
    vus     = sum(1 for p in progression if p.get("cours_vu") and p["chapitre"] != "__diagnostic__")
    quiz_ok = sum(1 for p in progression if p.get("quiz_reussi"))
    pct     = round(vus / total_chapitres * 100) if total_chapitres > 0 else 0

    st.markdown(
        f"""<div style='background:#E3F2FD;border-radius:10px;
        padding:10px 14px;margin-bottom:1rem'>
        <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
            <span style='font-size:13px;font-weight:500;color:#1A237E'>
                Progression
            </span>
            <span style='font-size:13px;color:#1565C0;font-weight:500'>
                {vus}/{total_chapitres} chapitres · {quiz_ok} quiz réussis
            </span>
        </div>
        <div style='background:#BBDEFB;border-radius:4px;height:8px'>
            <div style='background:#1565C0;width:{pct}%;
            height:100%;border-radius:4px;transition:width .3s'></div>
        </div>
        </div>""",
        unsafe_allow_html=True
    )


# ── Page principale ───────────────────────────────────────────────
def page_cours():
    # Au début de chaque fonction page_xxx()
    st.write("Debug: Début du chargement de la page")
    st.write("COURS importé:", 'COURS' in dir())

    st.title("📖 Cours")
    eleve    = st.session_state["eleve"]
    eleve_id = eleve["id"]

    # ── Options admin ─────────────────────────────────────────────
    email_connecte  = st.session_state["eleve"].get("email", "")
    email_admin     = st.secrets.get("ADMIN_EMAIL", "")
    est_admin       = email_connecte == email_admin
    if est_admin:
        with st.expander("⚙️ Options admin"):
            if "admin_auth" not in st.session_state:
                st.session_state["admin_auth"] = False
        if not st.session_state["admin_auth"]:
            st.caption("Accès réservé à l'administrateur.")
            mdp = st.text_input(
                "Mot de passe admin :",
                type="password",
                key="mdp_admin_input"
            )
            if st.button("🔐 Valider", use_container_width=True):
                if mdp == st.secrets.get("ADMIN_PASSWORD", ""):
                    st.session_state["admin_auth"] = True
                    st.success("Accès admin accordé ✅")
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")

        else:
            st.caption(
                "Connecté en tant qu'admin. "
                "Les cours supprimés seront régénérés à la prochaine ouverture."
            )

            col1, col2 = st.columns(2)

            chapitre_actuel = st.session_state.get("cours_chapitre")
            theme_actuel    = st.session_state.get("cours_theme")
            niveau_actuel   = st.session_state.get("cours_niveau", "Débutant")

            if col1.button(
                "🔄 Ce chapitre",
                use_container_width=True,
                disabled=not chapitre_actuel
            ):
                import requests as req
                from database import supabase_url, headers
                try:
                    for table in ["cours_contenu", "quiz_contenu"]:
                        req.delete(
                            f"{supabase_url()}/rest/v1/{table}",
                            headers=headers(),
                            params={
                                "theme":    f"eq.{theme_actuel}",
                                "chapitre": f"eq.{chapitre_actuel}",
                                "niveau":   f"eq.{niveau_actuel}"
                            }
                        )
                    st.success(
                        f"Chapitre '{chapitre_actuel}' supprimé "
                        f"— sera régénéré à l'ouverture."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

            if col2.button(
                "🗑️ Toute la matière",
                use_container_width=True,
                disabled=not theme_actuel
            ):
                import requests as req
                from database import supabase_url, headers
                try:
                    for table in ["cours_contenu", "quiz_contenu"]:
                        req.delete(
                            f"{supabase_url()}/rest/v1/{table}",
                            headers=headers(),
                            params={"theme": f"eq.{theme_actuel}"}
                        )
                    st.success(
                        f"Matière '{theme_actuel}' supprimée "
                        f"— sera régénérée à l'ouverture."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

            st.divider()
            st.warning(
                "⚠️ Action irréversible — supprime tous les cours générés."
            )
            confirmation = st.text_input(
                "Tapez CONFIRMER pour supprimer tous les cours :",
                key="confirm_delete_all"
            )
            if st.button(
                "💣 Tout supprimer",
                use_container_width=True,
                disabled=confirmation != "CONFIRMER"
            ):
                import requests as req
                from database import supabase_url, headers
                try:
                    for table in ["cours_contenu", "quiz_contenu"]:
                        req.delete(
                            f"{supabase_url()}/rest/v1/{table}",
                            headers=headers()
                        )
                    st.success("Tous les cours supprimés — seront régénérés.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

            st.divider()
            if st.button("🚪 Déconnexion admin", use_container_width=True):
                st.session_state["admin_auth"] = False
                st.rerun()

       # ── Sélection de la matière ───────────────────────────────────
    st.markdown("#### Choisis une matière")
    cols = st.columns(4)
    for i, (theme, data) in enumerate(COURS.items()):
        prog  = get_progression_cours(eleve_id, theme)
        total = len(data["chapitres"])
        vus   = sum(
            1 for p in prog
            if p.get("cours_vu") and p["chapitre"] != "__diagnostic__"
        )
        pct = round(vus / total * 100) if total > 0 else 0

        if cols[i].button(
            f"{data['icone']} {theme}\n{pct}% vu",
            use_container_width=True,
            key=f"theme_{i}"
        ):
            st.session_state["cours_theme"]    = theme
            st.session_state["cours_chapitre"] = None
            st.rerun()

    if "cours_theme" not in st.session_state:
        st.info("👆 Choisis une matière pour commencer.")
        return

    theme           = st.session_state["cours_theme"]
    data            = COURS[theme]
    total_chapitres = len(data["chapitres"])

    st.divider()

    # ── Progression ───────────────────────────────────────────────
    prog = get_progression_cours(eleve_id, theme)
    afficher_progression(prog, total_chapitres)

    chapitres_vus     = {p["chapitre"] for p in prog if p.get("cours_vu")}
    chapitres_quiz_ok = {p["chapitre"] for p in prog if p.get("quiz_reussi")}

    # ── Diagnostic ────────────────────────────────────────────────
    niveau_sauvegarde = get_niveau_detecte(eleve_id, theme)

    if not niveau_sauvegarde:
        st.markdown(f"#### {data['icone']} {theme} — Diagnostic de niveau")
        st.info("Réponds à 3 questions pour adapter le cours à ton niveau réel.")

        if st.button("🎯 Commencer le diagnostic", use_container_width=True):
            with st.spinner("Préparation..."):
                try:
                    diag = generer_diagnostic(theme)
                    st.session_state[f"diag_q_{theme}"] = diag["questions"]
                    st.session_state[f"diag_e_{theme}"] = 0
                    st.session_state[f"diag_s_{theme}"] = 0
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if f"diag_q_{theme}" in st.session_state:
            questions = st.session_state[f"diag_q_{theme}"]
            etape     = st.session_state.get(f"diag_e_{theme}", 0)

            if etape < len(questions):
                q = questions[etape]
                st.markdown(f"**Question {etape+1}/3 — {q['niveau']}**")
                st.write(q["question"])
                choix = st.radio(
                    "Ta réponse :", q["choix"],
                    index=None, key=f"dq_{etape}"
                )

                if choix:
                    if choix[0] == q["reponse"]:
                        st.success("✅ Bonne réponse !")
                        st.session_state[f"diag_s_{theme}"] += 1
                    else:
                        st.error(f"❌ La bonne réponse : {q['reponse']}")
                    st.info(f"**Explication :** {q['explication']}")

                    if st.button("Suivant →", key=f"dn_{etape}"):
                        st.session_state[f"diag_e_{theme}"] += 1
                        st.rerun()
            else:
                score  = st.session_state.get(f"diag_s_{theme}", 0)
                niveau = niveau_depuis_score(score)
                sauvegarder_diagnostic(eleve_id, theme, score, niveau)

                col1, col2 = st.columns(2)
                col1.metric("Score", f"{score}/3")
                col2.metric("Niveau détecté", niveau)

                msgs = {
                    "Débutant":      "Pas d'inquiétude ! On commence depuis les bases. 💪",
                    "Intermédiaire": "Bon niveau ! On va consolider et approfondir. 📈",
                    "Avancé":        "Excellent ! On va aux concepts avancés. 🚀"
                }
                st.success(msgs[niveau])

                if st.button("📖 Accéder aux chapitres →", use_container_width=True):
                    st.rerun()
        return

    # ── Chapitres ─────────────────────────────────────────────────
    st.markdown(f"#### {data['icone']} {theme} — Chapitres")

    couleurs = {"Débutant": "🔴", "Intermédiaire": "🟡", "Avancé": "🟢"}
    st.markdown(
        f"{couleurs.get(niveau_sauvegarde, '🔵')} Ton niveau : "
        f"**{niveau_sauvegarde}** — Contenu personnalisé activé"
    )

    niveau = st.select_slider(
        "Ajuster le niveau :",
        options=NIVEAUX,
        value=niveau_sauvegarde
    )

    st.divider()

    for j, chap in enumerate(data["chapitres"], 1):
        vu      = chap["titre"] in chapitres_vus
        quiz_ok = chap["titre"] in chapitres_quiz_ok
        statut  = "✅" if quiz_ok else ("👁️" if vu else "⭕")

        col_btn, col_desc = st.columns([1, 3])
        if col_btn.button(
            f"{statut} Ch.{j}",
            key=f"chap_{j}",
            use_container_width=True
        ):
            st.session_state["cours_chapitre"] = chap["titre"]
            st.session_state["cours_niveau"]   = niveau
            st.session_state["quiz_repondu"]   = False
            st.rerun()

        col_desc.markdown(
            f"**{chap['titre']}**  \n"
            f"<span style='font-size:12px;color:#1565C0'>"
            f"🎯 {chap['competence'][:90]}...</span>",
            unsafe_allow_html=True
        )

    if not st.session_state.get("cours_chapitre"):
        return

    # ── Contenu du chapitre ───────────────────────────────────────
    chapitre_titre = st.session_state["cours_chapitre"]
    niveau_cours   = st.session_state.get("cours_niveau", niveau_sauvegarde)

    chap_data = next(
        (c for c in data["chapitres"] if c["titre"] == chapitre_titre), None
    )
    if not chap_data:
        return

    st.divider()
    st.markdown(f"### 📘 {chapitre_titre}")
    st.caption(f"{theme} · Niveau : {niveau_cours}")

    # Carte compétence APC
    st.markdown(
        f"""<div style='background:#E3F2FD;border-left:4px solid #1565C0;
        border-radius:8px;padding:12px 16px;margin-bottom:1rem'>
        <strong>🎯 Compétence visée</strong><br>
        <span style='font-size:14px;color:#1A237E'>
            {chap_data['competence']}
        </span>
        </div>""",
        unsafe_allow_html=True
    )

    # Carte savoir-faire
    sf_list = "".join([f"<li>{sf}</li>" for sf in chap_data["savoir_faire"]])
    st.markdown(
        f"""<div style='background:#E8F5E9;border-left:4px solid #2E7D32;
        border-radius:8px;padding:12px 16px;margin-bottom:1rem'>
        <strong>✅ Savoir-faire à développer</strong>
        <ul style='margin:8px 0 0 0;font-size:14px;color:#1A237E'>
            {sf_list}
        </ul>
        </div>""",
        unsafe_allow_html=True
    )

    # Bouton signaler erreur
    email_connecte  = st.session_state["eleve"].get("email", "")
    email_admin     = st.secrets.get("ADMIN_EMAIL", "")
    est_admin       = email_connecte == email_admin

    if est_admin:
        with st.expander("⚙️ Options admin"):
            type_erreur = st.selectbox(
                "Type d'erreur :",
                [
                    "Pseudo-code incorrect",
                    "Algorigramme mal illustré",
                    "Structure APC non respectée",
                    "Contenu incomplet",
                    "Autre erreur"
                ]
            )
        if st.button("📤 Signaler et régénérer", use_container_width=True):
    #       # generer_contenu.clear()
            st.session_state.pop("quiz_actuel", None)
            st.success("Cache vidé — le cours va être régénéré.")
            st.rerun()

    # Génération du cours
    with st.spinner("Groq génère le cours selon le programme officiel..."):
        contenu = generer_contenu(
            theme, chapitre_titre, niveau_cours,
            chap_data["competence"], chap_data["savoir_faire"]
        )

    marquer_cours_vu(eleve_id, theme, chapitre_titre, niveau_cours)
    st.markdown(contenu)

    # ── Évaluation APC ────────────────────────────────────────────
    st.divider()
    st.markdown("#### 🧪 Évaluation des acquis")

    if "quiz_actuel" not in st.session_state or \
       st.session_state.get("quiz_chapitre") != chapitre_titre:
        with st.spinner("Préparation de l'évaluation..."):
            quiz = generer_quiz(
                theme, chapitre_titre, niveau_cours, chap_data["competence"]
            )
            if quiz:
                st.session_state["quiz_actuel"]   = quiz
                st.session_state["quiz_chapitre"] = chapitre_titre
                st.session_state["quiz_repondu"]  = False
            else:
                st.warning("Évaluation indisponible.")
                quiz = None

    quiz = st.session_state.get("quiz_actuel")
    if quiz:
        st.write(quiz["question"])
        st.caption(
            f"*Savoir-faire évalué : {quiz.get('savoir_faire_evalue', '')}*"
        )
        choix = st.radio("Ta réponse :", quiz["choix"], index=None)
       
        if choix and not st.session_state.get("quiz_repondu"):
            if choix[0] == quiz["reponse"]:
                st.success("Bonne réponse ! Compétence acquise ✅")
                marquer_quiz_reussi(eleve_id, theme, chapitre_titre)
            else:
                st.error(f"Pas tout à fait. Réponse correcte : {quiz['reponse']}")
            st.info(f"**Explication :** {quiz['explication']}")
            st.session_state["quiz_repondu"] = True

    # ── Navigation ────────────────────────────────────────────────
    st.divider()
    chapitres_liste = [c["titre"] for c in data["chapitres"]]
    idx = chapitres_liste.index(chapitre_titre)

    if idx < len(chapitres_liste) - 1:
        if st.button("Chapitre suivant →", use_container_width=True):
            st.session_state["cours_chapitre"] = chapitres_liste[idx + 1]
            st.session_state["quiz_repondu"]   = False
            st.rerun()
    else:
        st.success("🎉 Tu as terminé tous les chapitres de cette matière !")
        if st.button("Aller aux exercices →", use_container_width=True):
            st.session_state["page"] = "🧠 Exercices"
            st.rerun()
