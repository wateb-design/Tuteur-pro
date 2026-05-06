import streamlit as st
import json
import re
import time
from groq import Groq
from database import inserer_resultat, get_stats_eleve
from cours import COURS

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

NIVEAUX = ["Facile", "Moyen", "Difficile"]
TYPES   = ["Compléter le code", "QCM", "Exercice de logique", "Détecter l'erreur"]

# ── Instructions spécifiques par matière ──────────────────────────
# Même logique que dans cours.py — chaque matière a ses conventions.
# L'algorithmique utilise uniquement le pseudo-code LDA.
# Les algorigrammes utilisent les symboles officiels camerounais.
INSTRUCTIONS_MATIERE = {

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
2. Toujours commencer par l ovale (DEBUT) et finir par l ovale (FIN)
3. Entrees/sorties dans le parallelogramme uniquement
4. Decisions (Si, TantQue, Pour) dans le losange uniquement
5. Sous-programmes dans le rectangle double barre

FORMAT DE RENDU OBLIGATOIRE :
- Algorigramme ASCII complet avec les bons symboles
- Algorithme pseudo-code LDA correspondant
- Legende des symboles utilises
- Au moins 2 exemples de complexite croissante""",

    "Langage C": """
REGLES — Langage C :
- C standard C99 uniquement
- Toujours inclure les headers (#include <stdio.h> etc.)
- Fonction main() complete obligatoire
- Afficher la sortie attendue du programme
- Correspondance algo pseudo-code -> C si pertinent""",

    "HTML et CSS": """
REGLES — HTML/CSS :
- HTML5 (DOCTYPE html)
- Structure complete de la page toujours presente
- Exemples concrets camerounais (noms, villes, contextes locaux)
- Decrire le rendu visuel attendu dans le navigateur""",

    "JavaScript": """
REGLES — JavaScript :
- JS moderne integre dans une page HTML complete
- Montrer l interaction DOM (getElementById, innerHTML)
- Afficher le resultat attendu dans le navigateur
- Exemples concrets camerounais"""
}


# ── Génération d'un exercice via Groq ─────────────────────────────
def generer_exercice(matiere, chapitre, niveau, type_ex):
    # Sélection de l'instruction selon matière et chapitre
    if matiere == "Algorithmique avancée" and "algorigramme" in chapitre.lower():
        instruction = INSTRUCTIONS_MATIERE["Algorithmique avancée_algorigramme"]
    else:
        instruction = INSTRUCTIONS_MATIERE.get(matiere, "")

    # Instructions spécifiques par type d'exercice
    instructions_type = {
        "Compléter le code": """
Type : COMPLETER LE CODE
- Fournis un code/algorithme avec des blancs a remplir marques par _____
- Les blancs doivent porter sur les notions cles du chapitre
- La solution complete tous les blancs""",

        "QCM": """
Type : QCM
- Question claire avec 4 choix A/B/C/D
- Une seule bonne reponse
- Les distracteurs doivent etre plausibles (erreurs courantes)
- La solution indique la lettre correcte et explique pourquoi""",

        "Exercice de logique": """
Type : EXERCICE DE LOGIQUE
- Probleme algorithmique a resoudre de A a Z
- L eleve doit ecrire un algorithme/code complet
- La solution est l algorithme/code complet et correct""",

        "Détecter l'erreur": """
Type : DETECTER L ERREUR
- Fournis un code/algorithme avec UNE erreur intentionnelle dans code_depart
- L erreur peut etre : syntaxe, logique, semantique
- L eleve doit identifier ET corriger l erreur
- La solution montre le code corrige et explique l erreur"""
    }

    instruction_type = instructions_type.get(type_ex, "")

    prompt = f"""Tu es un professeur expert en informatique pour eleves de 1ere TI au Cameroun.
Genere un exercice pour le chapitre "{chapitre}" (matiere : {matiere}, niveau : {niveau}).

{instruction}

{instruction_type}

Reponds UNIQUEMENT en JSON valide, sans texte avant ou apres :
{{
  "titre": "titre court et clair",
  "description": "enonce precis en 2-3 phrases",
  "code_depart": "code ou algorithme de depart (vide si non necessaire)",
  "solution": "solution complete et correcte",
  "explication": "explication pedagogique de la solution en 2 phrases"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"""Tu es un professeur expert en informatique au Cameroun.
Tu respectes STRICTEMENT les conventions de chaque matiere :
- Algorithmique : pseudo-code LDA UNIQUEMENT (jamais Python ou autre langage)
- Algorigrammes : schemas ASCII avec symboles officiels camerounais
- Langage C : code C standard avec main() complete
- HTML/CSS : HTML5 avec structure complete
- JavaScript : JS moderne integre dans HTML
Tu reponds UNIQUEMENT en JSON valide."""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=900,
            temperature=0.5
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        debut = raw.find("{")
        fin   = raw.rfind("}") + 1
        if debut != -1 and fin > debut:
            raw = raw[debut:fin]
        return json.loads(raw)

    except Exception as e:
        st.error(f"Erreur génération exercice : {e}")
        return None


# ── Correction de la réponse ──────────────────────────────────────
def corriger_reponse(exercice, reponse_eleve, type_ex, matiere):
    # Instruction de correction selon la matière
    if "Algorithmique" in matiere:
        critere = "Verifie que l eleve a utilise le pseudo-code LDA correct (pas de Python ou C). Verifie la syntaxe : <-, Lire(), Ecrire(), Si/FinSi, Pour/FinPour, TantQue/FinTantQue."
    elif matiere == "Langage C":
        critere = "Verifie la syntaxe C, les includes necessaires, la fonction main(), les types de variables."
    elif matiere == "HTML et CSS":
        critere = "Verifie la structure HTML5, les balises correctes, la syntaxe CSS."
    elif matiere == "JavaScript":
        critere = "Verifie la syntaxe JS, l integration HTML, les fonctions et evenements."
    else:
        critere = "Verifie la correction generale de la reponse."

    prompt = f"""Tu es un tuteur pedagogique bienveillant pour eleves de 1ere TI au Cameroun.
Type d exercice : {type_ex} | Matiere : {matiere}
Exercice : {exercice['titre']}
Description : {exercice['description']}
Solution attendue : {exercice['solution']}
Reponse de l eleve : {reponse_eleve}

Criteres de correction : {critere}

Evalue en 2-3 phrases.
- Si correct : commence OBLIGATOIREMENT par "Correct !"
- Si incorrect : commence OBLIGATOIREMENT par "Pas tout a fait."
Explique l erreur et donne une piste d amelioration.
Sois encourageant meme en cas d erreur."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un tuteur pedagogique bienveillant. Tu corriges avec precision et encouragement."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        feedback = response.choices[0].message.content
        reussi   = 1 if feedback.lower().startswith("correct") else 0
        return feedback, reussi

    except Exception as e:
        return f"Erreur de correction : {e}", 0


# ── Génération d'un indice progressif ────────────────────────────
def get_indice(exercice, niveau_indice, indices_precedents, type_ex, matiere):
    instructions_niv = {
        1: "Oriente vers le concept cle. Tres vague, pas de code ni pseudo-code.",
        2: "Donne une piste concrete sur la methode. Toujours pas de solution complete.",
        3: "Montre un tout petit fragment (1-2 lignes max) avec un blanc a remplir."
    }

    # Pour l'algo : préciser que les indices doivent être en pseudo-code
    if "Algorithmique" in matiere and niveau_indice == 3:
        instructions_niv[3] = "Montre un fragment de pseudo-code LDA (1-2 lignes max) avec un blanc. Jamais de Python ou C."

    historique = ""
    if indices_precedents:
        historique = f"Indices deja donnes : {' | '.join(indices_precedents)}"

    prompt = f"""Tu es un tuteur pedagogique pour eleves de 1ere TI au Cameroun.
Matiere : {matiere} | Type : {type_ex}
Exercice : {exercice['titre']} — {exercice['description']}
{historique}

Donne un indice de niveau {niveau_indice}/3.
Instruction : {instructions_niv[niveau_indice]}
Ne donne JAMAIS la solution complete. Sois encourageant. Max 3 phrases."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur indice : {e}"


# ── Coloration syntaxique selon la matière ────────────────────────
def get_language(matiere):
    """Retourne le langage pour st.code() selon la matière."""
    mapping = {
        "Algorithmique avancée": "text",   # pseudo-code = texte brut
        "Langage C":             "c",
        "HTML et CSS":           "html",
        "JavaScript":            "javascript"
    }
    return mapping.get(matiere, "text")


# ── Page principale des exercices ─────────────────────────────────
def page_exercices():
    st.title("🧠 Exercices")

    eleve    = st.session_state["eleve"]
    matieres = list(COURS.keys())

    # ── Sélecteurs ───────────────────────────────────────────────
    col1, col2 = st.columns(2)
    matiere = col1.selectbox(
        "Matière",
        matieres,
        format_func=lambda m: f"{COURS[m]['icone']} {m}"
    )

    chapitres = [c["titre"] for c in COURS[matiere]["chapitres"]]
    chapitre  = col2.selectbox("Chapitre", chapitres)

    col3, col4 = st.columns(2)
    niveau  = col3.selectbox("Niveau",           NIVEAUX)
    type_ex = col4.selectbox("Type d'exercice",  TYPES)

    # Indication spéciale pour l'algorithmique
    if matiere == "Algorithmique avancée":
        st.markdown(
            """<div style='background:#E3F2FD;border-left:3px solid #1565C0;
            border-radius:8px;padding:8px 12px;font-size:13px;
            color:#1A237E;margin-bottom:0.5rem'>
            📌 Les exercices d'algorithmique utilisent
            <strong>uniquement le pseudo-code LDA</strong>
            — aucun langage de programmation.
            </div>""",
            unsafe_allow_html=True
        )

    if matiere == "Algorithmique avancée" and "algorigramme" in chapitre.lower():
        st.markdown(
            """<div style='background:#E8F5E9;border-left:3px solid #2E7D32;
            border-radius:8px;padding:8px 12px;font-size:13px;
            color:#1B5E20;margin-bottom:0.5rem'>
            📐 Les algorigrammes utilisent les
            <strong>symboles officiels du programme camerounais</strong>
            (ovale, rectangle, parallélogramme, losange, cercle).
            </div>""",
            unsafe_allow_html=True
        )

    # ── Bouton de génération ──────────────────────────────────────
    if st.button("✨ Générer un exercice", use_container_width=True, type="primary"):
        with st.spinner("L'IA prépare ton exercice..."):
            ex = generer_exercice(matiere, chapitre, niveau, type_ex)
            if ex:
                st.session_state["exercice"] = ex
                st.session_state["matiere"]  = matiere
                st.session_state["chapitre"] = chapitre
                st.session_state["niveau"]   = niveau
                st.session_state["type_ex"]  = type_ex
                st.session_state["indices"]  = []
                st.session_state["debut"]    = time.time()

    # ── Affichage de l'exercice ───────────────────────────────────
    if "exercice" not in st.session_state:
        return

    ex       = st.session_state["exercice"]
    matiere  = st.session_state.get("matiere",  matiere)
    type_ex  = st.session_state.get("type_ex",  type_ex)
    lang     = get_language(matiere)

    st.divider()

    # En-tête exercice
    st.caption(
        f"{COURS[matiere]['icone']} {matiere} · "
        f"{st.session_state['chapitre']} · "
        f"{st.session_state['niveau']} · {type_ex}"
    )

    # Titre dans une carte
    st.markdown(
        f"""<div style='background:white;border:0.5px solid #BBDEFB;
        border-left:3px solid #1565C0;border-radius:10px;
        padding:1rem 1.25rem;margin-bottom:1rem'>
        <div style='font-size:16px;font-weight:500;
        color:#1A237E;margin-bottom:6px'>{ex["titre"]}</div>
        <div style='font-size:14px;color:#5C6BC0;line-height:1.6'>
        {ex["description"]}</div>
        </div>""",
        unsafe_allow_html=True
    )

    # Code de départ
    if ex.get("code_depart", "").strip():
        label = (
            "Algorithme de départ :"
            if matiere == "Algorithmique avancée"
            else "Code de départ :"
        )
        st.markdown(f"**{label}**")
        st.code(ex["code_depart"], language=lang)

    # ── Zone de réponse ───────────────────────────────────────────
    placeholder = (
        "Écris ton algorithme en pseudo-code LDA ici...\n\n"
        "Exemple :\nAlgorithme MonAlgo\nVariable x : Entier\nDebut\n  ...\nFin"
        if matiere == "Algorithmique avancée" and type_ex != "QCM"
        else "Écris ta réponse ici..."
    )

    if type_ex == "QCM":
        reponse = st.radio(
            "Ta réponse :",
            ["A", "B", "C", "D"],
            index=None,
            horizontal=True
        )
    else:
        reponse = st.text_area(
            "Ta réponse :",
            height=180,
            placeholder=placeholder
        )

    # ── Boutons d'action ──────────────────────────────────────────
    col_verif, col_indice, col_solution = st.columns(3)

    # Vérifier
    if col_verif.button("✓ Vérifier", use_container_width=True, type="primary"):
        if not reponse:
            st.warning("Écris d'abord ta réponse !")
        else:
            with st.spinner("Correction en cours..."):
                feedback, reussi = corriger_reponse(
                    ex, reponse, type_ex, matiere
                )
                temps = int(
                    time.time() - st.session_state.get("debut", time.time())
                )

                if reussi:
                    st.success(feedback)
                    st.balloons()
                else:
                    st.error(feedback)
                    # Affiche la solution correcte si raté
                    email_connecte  = st.session_state["eleve"].get("email", "")
                    email_admin     = st.secrets.get("ADMIN_EMAIL", "")
                    est_admin       = email_connecte == email_admin                    
                    if est_admin:
                        with st.expander("⚙️ Options admin"):                    
                        st.markdown("**Solution :**")
                        st.code(ex["solution"], language=lang)
                        if ex.get("explication"):
                            st.info(f"**Explication :** {ex['explication']}")

                inserer_resultat(
                    eleve_id=eleve["id"],
                    theme=matiere,
                    niveau=st.session_state["niveau"],
                    reussi=reussi,
                    temps=temps
                )

                stats = get_stats_eleve(eleve["id"])
                st.caption(
                    f"Taux de réussite global : **{stats['taux']}%** "
                    f"({stats['reussis']}/{stats['total']} exercices)"
                )

    # Indice
    indices       = st.session_state.get("indices", [])
    niveau_indice = len(indices) + 1

    if niveau_indice <= 3:
        if col_indice.button(
            f"💡 Indice {niveau_indice}/3",
            use_container_width=True
        ):
            with st.spinner("Réflexion..."):
                indice = get_indice(
                    ex, niveau_indice, indices, type_ex, matiere
                )
                st.session_state["indices"].append(indice)
                st.rerun()
    else:
        col_indice.button(
            "Plus d'indices", disabled=True, use_container_width=True
        )

    # Affichage des indices
    if indices:
        couleurs = {1: "🟡", 2: "🟠", 3: "🔴"}
        for i, ind in enumerate(indices, 1):
            st.info(f"{couleurs[i]} **Indice {i}/3 :** {ind}")

    # Solution directe
    if col_solution.button("📖 Solution", use_container_width=True):
        st.markdown("**Solution complète :**")
        st.code(ex["solution"], language=lang)
        if ex.get("explication"):
            st.info(f"**Explication :** {ex['explication']}")
        st.caption(
            "Prends le temps de bien comprendre "
            "avant de passer à l'exercice suivant."
        )
