# modules/cours_data.py
# Données partagées entre tous les modules (cours, progression, app, etc.)

NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"]

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
