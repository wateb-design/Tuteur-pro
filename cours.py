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

# ── Programme officiel 1ère TI ────────────────────────────────────
COURS = {
    "Algorithmique avancée": {
        "icone": "🧠",
        "chapitres": [
            {
                "titre": "Variables, constantes et instructions de base",
                "competence": "Déclarer et utiliser les variables et les constantes ; utiliser convenablement les instructions algorithmiques de base (lecture, écriture, affectation).",
                "savoirs": "Types de données, déclaration, affectation, lecture/écriture",
                "savoir_faire": ["Déclarer une variable/constante", "Écrire une instruction d'affectation", "Utiliser lecture et écriture dans un algorithme séquentiel"]
            },
            {
                "titre": "Structures alternatives (Si, Si…Sinon)",
                "competence": "Utiliser les structures alternatives (Si, Si…Sinon) ; lister des exemples de structures de contrôle.",
                "savoirs": "Structure Si, Si…Sinon, conditions, opérateurs de comparaison",
                "savoir_faire": ["Écrire un Si simple", "Écrire un Si…Sinon", "Identifier les instructions d'incrémentation et de décrémentation"]
            },
            {
                "titre": "Structures itératives (Pour, TantQue, Répéter)",
                "competence": "Utiliser les structures itératives (Pour…Faire, TantQue…Faire, Répéter…Jusqu'à) ; identifier la condition d'arrêt d'une boucle.",
                "savoirs": "Boucle Pour, TantQue, Répéter…Jusqu'à, compteur, condition d'arrêt",
                "savoir_faire": ["Écrire une boucle Pour", "Écrire une boucle TantQue", "Identifier et corriger une boucle infinie"]
            },
            {
                "titre": "Tableaux à une dimension",
                "competence": "Déclarer un tableau à une dimension ; initialiser, accéder, parcourir, afficher, modifier les éléments.",
                "savoirs": "Déclaration tableau, indice, parcours séquentiel",
                "savoir_faire": ["Déclarer un tableau", "Initialiser un tableau", "Parcourir et afficher les éléments"]
            },
            {
                "titre": "Enregistrements",
                "competence": "Déclarer un enregistrement ; initialiser, accéder, afficher, modifier les champs.",
                "savoirs": "Structure enregistrement, champs, accès aux champs",
                "savoir_faire": ["Déclarer un enregistrement", "Accéder et modifier les champs", "Utiliser un enregistrement dans un algorithme"]
            },
            {
                "titre": "Fonctions et procédures",
                "competence": "Déclarer et appeler une fonction/procédure ; distinguer variables locales et globales ; différencier paramètres formels et effectifs.",
                "savoirs": "Fonction, procédure, paramètres, variables locales/globales",
                "savoir_faire": ["Écrire une fonction simple", "Écrire une procédure", "Distinguer variables locales et globales"]
            },
            {
                "titre": "Algorigrammes",
                "competence": "Identifier les symboles d'un algorigramme ; transformer un algorigramme en algorithme ; dérouler un algorigramme.",
                "savoirs": "Symboles (début/fin, traitement, décision, E/S)",
                "savoir_faire": ["Identifier les symboles", "Transformer un algorigramme en algorithme", "Dérouler pas à pas"]
            },
            {
                "titre": "Tri par sélection et insertion",
                "competence": "Exécuter les algorithmes de tri par sélection et insertion ; écrire un algorithme de tri simple.",
                "savoirs": "Tri par sélection, tri par insertion, comparaison, échange",
                "savoir_faire": ["Exécuter un tri par sélection", "Exécuter un tri par insertion", "Écrire l'algorithme complet"]
            },
            {
                "titre": "Recherche séquentielle et dichotomique",
                "competence": "Décrire et écrire les algorithmes de recherche séquentielle et dichotomique.",
                "savoirs": "Recherche séquentielle, dichotomique, tableau trié",
                "savoir_faire": ["Écrire une recherche séquentielle", "Exécuter une recherche dichotomique", "Comparer les deux méthodes"]
            },
        ]
    },
    "Langage C": {
        "icone": "⚙️",
        "chapitres": [
            {
                "titre": "Structure minimale d'un programme C",
                "competence": "Établir la différence entre langage interprété et compilé ; écrire la structure minimale d'un programme C ; afficher un message simple.",
                "savoirs": "Compilation vs interprétation, #include, main(), printf()",
                "savoir_faire": ["Écrire un Hello World", "Identifier les parties d'un programme C", "Compiler avec CodeBlocks ou Dev-C++"]
            },
            {
                "titre": "Variables, constantes et types de base",
                "competence": "Énumérer les types de base en C ; déclarer une variable et une constante ; utiliser les opérateurs.",
                "savoirs": "int, float, char, double, const",
                "savoir_faire": ["Déclarer des variables de différents types", "Utiliser les opérateurs", "Utiliser printf et scanf"]
            },
            {
                "titre": "Entrées/Sorties — printf et scanf",
                "competence": "Utiliser les fonctions de stdio.h et math.h (printf, scanf, sqrt, abs, cos).",
                "savoirs": "printf, scanf, %d %f %c, stdio.h, math.h",
                "savoir_faire": ["Afficher des données formatées", "Saisir avec scanf", "Utiliser sqrt, abs, cos"]
            },
            {
                "titre": "Structures alternatives (if, if…else, switch)",
                "competence": "Utiliser les structures alternatives (if, if…else, switch) en C.",
                "savoirs": "if, if…else, else if, switch…case, break",
                "savoir_faire": ["Écrire un if…else", "Écrire un switch…case", "Traduire Si…Sinon en C"]
            },
            {
                "titre": "Boucles en C (for, while, do…while)",
                "competence": "Utiliser les boucles (for, while, do…while) ; exécuter pas à pas un programme C.",
                "savoirs": "for, while, do…while, variable de contrôle",
                "savoir_faire": ["Écrire une boucle for", "Écrire une boucle while", "Traduire une boucle algorithmique en C"]
            },
            {
                "titre": "Traduction algorithme → C",
                "competence": "Traduire un algorithme en C ; tester et déboguer des programmes C.",
                "savoirs": "Correspondances algo/C, test, débogage",
                "savoir_faire": ["Traduire un algorithme complet en C", "Tester et corriger", "Exécuter pas à pas dans un IDE"]
            },
        ]
    },
    "HTML et CSS": {
        "icone": "🌐",
        "chapitres": [
            {
                "titre": "Structure HTML et balises essentielles",
                "competence": "Utiliser les balises appropriées ; insérer liens, images, listes ; utiliser les balises de section.",
                "savoirs": "DOCTYPE, html, head, body, h1-h6, p, a, img, ul, ol, section",
                "savoir_faire": ["Créer une page HTML valide", "Insérer un lien relatif/absolu", "Insérer une image", "Imbriquer des listes"]
            },
            {
                "titre": "Tableaux HTML",
                "competence": "Insérer un tableau ; utiliser border, width, cellpadding ; fusionner avec colspan et rowspan.",
                "savoirs": "table, tr, td, th, colspan, rowspan, border",
                "savoir_faire": ["Créer un tableau simple", "Fusionner des cellules", "Styliser un tableau"]
            },
            {
                "titre": "Formulaires HTML",
                "competence": "Insérer un formulaire (champs, boutons radio, cases à cocher, liste déroulante, boutons).",
                "savoirs": "form, input, select, textarea, button, type, name",
                "savoir_faire": ["Créer un formulaire complet", "Utiliser les types d'input", "Organiser les dossiers"]
            },
            {
                "titre": "CSS — Introduction et sélecteurs",
                "competence": "Écrire la structure minimale d'une feuille de style ; utiliser background-color, color, font-size, font-family.",
                "savoirs": "Sélecteurs, propriétés CSS, liaison HTML/CSS",
                "savoir_faire": ["Lier une feuille CSS", "Utiliser les sélecteurs", "Appliquer les propriétés de base"]
            },
            {
                "titre": "CSS — Mise en page et styles avancés",
                "competence": "Utiliser width, height, text-align, border, margin, padding, font-weight, text-decoration.",
                "savoirs": "Box model, margin, padding, border, display",
                "savoir_faire": ["Comprendre le box model", "Centrer des éléments", "Utiliser margin et padding"]
            },
        ]
    },
    "JavaScript": {
        "icone": "✨",
        "chapitres": [
            {
                "titre": "Introduction au JavaScript",
                "competence": "Énoncer les caractéristiques du JS ; écrire la syntaxe d'insertion dans un document HTML.",
                "savoirs": "Caractéristiques JS, balise script, insertion",
                "savoir_faire": ["Insérer un script dans HTML", "Afficher avec alert et console.log", "Distinguer JS vs C"]
            },
            {
                "titre": "Variables, types et opérateurs",
                "competence": "Déclarer variables et constantes ; utiliser les opérateurs ; utiliser parseInt() et parseFloat().",
                "savoirs": "var, let, const, string, number, boolean, opérateurs",
                "savoir_faire": ["Déclarer avec let/const", "Utiliser les opérateurs", "Convertir avec parseInt/parseFloat"]
            },
            {
                "titre": "Structures alternatives et boucles",
                "competence": "Utiliser if, if…else ; utiliser for, while, do…while ; déclarer et utiliser un tableau.",
                "savoirs": "if…else, for, while, do…while, tableau",
                "savoir_faire": ["Écrire un if…else", "Parcourir un tableau", "Créer et initialiser un tableau"]
            },
            {
                "titre": "Fonctions JavaScript",
                "competence": "Écrire une fonction qui retourne une valeur ou non ; appeler une fonction.",
                "savoirs": "function, return, paramètres, portée",
                "savoir_faire": ["Écrire une fonction avec paramètres", "Appeler une fonction", "Distinguer avec/sans retour"]
            },
            {
                "titre": "DOM et événements",
                "competence": "Accéder aux éléments HTML (getElementById) ; utiliser les événements (onClick, onChange…) ; valider un formulaire.",
                "savoirs": "getElementById, innerHTML, addEventListener, événements",
                "savoir_faire": ["Accéder et modifier un élément", "Réagir à un clic", "Valider un formulaire"]
            },
        ]
    },
}

NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"]


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
(Exemple plus complexe combinant plusieurs notions, avec trace d execution si algorithmique)

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
    st.title("📖 Cours")
    eleve    = st.session_state["eleve"]
    eleve_id = eleve["id"]

    # Bouton pour vider le cache
    with st.expander("⚙️ Options"):
        if st.button("🔄 Régénérer tous les cours", use_container_width=True):
            generer_contenu.clear()
            generer_quiz.clear()
            st.success("Cache vidé — les cours seront régénérés.")
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
    with st.expander("⚠️ Ce cours contient une erreur ?"):
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
            generer_contenu.clear()
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
