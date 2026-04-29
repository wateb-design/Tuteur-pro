import streamlit as st
from groq import Groq
import sqlite3
import hashlib

# ── Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Tuteur IA — Programmation",
    page_icon="🤖",
    layout="wide"
)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Base de données ───────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("tuteur.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS eleves (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom    TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS resultats (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id  INTEGER,
            theme     TEXT,
            niveau    TEXT,
            reussi    INTEGER,
            date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Authentification ──────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def creer_compte(prenom, email, password):
    try:
        conn = sqlite3.connect("tuteur.db")
        conn.execute(
            "INSERT INTO eleves (prenom, email, password) VALUES (?, ?, ?)",
            (prenom, email, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True, "Compte créé avec succès !"
    except sqlite3.IntegrityError:
        return False, "Cet email est déjà utilisé."

def connecter(email, password):
    conn = sqlite3.connect("tuteur.db")
    row = conn.execute(
        "SELECT id, prenom FROM eleves WHERE email=? AND password=?",
        (email, hash_password(password))
    ).fetchone()
    conn.close()
    if row:
        return True, {"id": row[0], "prenom": row[1]}
    return False, None

def deconnecter():
    for key in ["eleve", "exercice", "theme", "niveau"]:
        st.session_state.pop(key, None)
    st.rerun()

# ── Page de connexion ─────────────────────────────────────────────
def page_auth():
    st.title("🤖 Tuteur IA — Programmation")
    st.markdown("##### Élèves de 1ère TI")
    st.divider()

    onglet = st.radio("", ["Connexion", "Créer un compte"], horizontal=True)

    if onglet == "Connexion":
        st.subheader("Connexion")
        email = st.text_input("Email", placeholder="ton@email.com")
        password = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter", use_container_width=True):
            if not email or not password:
                st.warning("Remplis tous les champs.")
            else:
                ok, eleve = connecter(email, password)
                if ok:
                    st.session_state["eleve"] = eleve
                    st.success(f"Bienvenue {eleve['prenom']} !")
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect.")

    else:
        st.subheader("Créer un compte")
        prenom = st.text_input("Prénom")
        email = st.text_input("Email", placeholder="ton@email.com")
        password = st.text_input("Mot de passe", type="password")
        password2 = st.text_input("Confirmer le mot de passe", type="password")

        if st.button("Créer mon compte", use_container_width=True):
            if not prenom or not email or not password:
                st.warning("Remplis tous les champs.")
            elif password != password2:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(password) < 6:
                st.warning("Le mot de passe doit faire au moins 6 caractères.")
            else:
                ok, msg = creer_compte(prenom, email, password)
                if ok:
                    st.success(msg + " Tu peux maintenant te connecter.")
                else:
                    st.error(msg)

# ── Garde : si non connecté → page auth ──────────────────────────
if "eleve" not in st.session_state:
    page_auth()
    st.stop()

# ── Sidebar (visible seulement si connecté) ───────────────────────
eleve = st.session_state["eleve"]

st.sidebar.title("📚 Tuteur IA")
st.sidebar.markdown(f"Bonjour **{eleve['prenom']}** 👋")
st.sidebar.divider()

page = st.sidebar.radio("Navigation", [
    "🏠 Accueil",
    "📖 Cours",
    "🧠 Exercices",
    "📊 Ma progression"
])

st.sidebar.divider()
if st.sidebar.button("🚪 Se déconnecter"):
    deconnecter()

# ── Pages ─────────────────────────────────────────────────────────
if page == "🏠 Accueil":
    st.title(f"Bienvenue {eleve['prenom']} 🤖")
    st.markdown("Améliore tes performances en programmation Python, Streamlit, Groq et SQLite.")

    conn = sqlite3.connect("tuteur.db")
    rows = conn.execute(
        "SELECT COUNT(*), SUM(reussi) FROM resultats WHERE eleve_id=?",
        (eleve["id"],)
    ).fetchone()
    conn.close()

    total = rows[0] or 0
    reussis = rows[1] or 0
    taux = round(reussis / total * 100) if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Exercices tentés", total)
    col2.metric("Réussis", reussis)
    col3.metric("Taux de réussite", f"{taux}%")

    st.info("👈 Utilise le menu à gauche pour naviguer.")

elif page == "📖 Cours":
    st.title("📖 Cours")
    st.info("Module en construction — disponible prochainement.")

elif page == "🧠 Exercices":
    st.title("🧠 Exercices")

    theme = st.selectbox("Thème", ["Python — bases", "Streamlit", "Groq Cloud", "SQLite"])
    niveau = st.selectbox("Niveau", ["Facile", "Moyen", "Difficile"])

    if st.button("Générer un exercice"):
        with st.spinner("L'IA prépare ton exercice..."):
            prompt = f"""Génère un exercice de programmation de niveau {niveau} sur : {theme}.
Réponds UNIQUEMENT en JSON :
{{
  "titre": "...",
  "description": "...",
  "code_depart": "...",
  "solution": "..."
}}"""
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            import json, re
            raw = response.choices[0].message.content
            raw = re.sub(r"```json|```", "", raw).strip()
            ex = json.loads(raw)
            st.session_state["exercice"] = ex
            st.session_state["theme"] = theme
            st.session_state["niveau"] = niveau

    if "exercice" in st.session_state:
        ex = st.session_state["exercice"]
        st.subheader(ex["titre"])
        st.write(ex["description"])
        if ex.get("code_depart"):
            st.code(ex["code_depart"], language="python")

        reponse = st.text_area("Ta réponse (code Python) :", height=150)
        col1, col2 = st.columns(2)

        if col1.button("Vérifier ma réponse"):
            with st.spinner("Correction en cours..."):
                fb = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content":
                        f"Exercice : {ex['titre']}\nSolution : {ex['solution']}\nRéponse élève : {reponse}\nÉvalue en 2 phrases. Commence par 'Correct !' ou 'Pas tout à fait.'"}],
                    max_tokens=200
                )
                feedback = fb.choices[0].message.content
                reussi = 1 if feedback.lower().startswith("correct") else 0
                if reussi:
                    st.success(feedback)
                else:
                    st.error(feedback)

                conn = sqlite3.connect("tuteur.db")
                conn.execute(
                    "INSERT INTO resultats (eleve_id, theme, niveau, reussi) VALUES (?,?,?,?)",
                    (eleve["id"], st.session_state["theme"],
                     st.session_state["niveau"], reussi)
                )
                conn.commit()
                conn.close()

        if col2.button("Indice"):
            with st.spinner("Réflexion..."):
                hint = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content":
                        f"Donne un seul indice sans donner la solution : {ex['titre']} — {ex['description']}"}],
                    max_tokens=100
                )
                st.info(hint.choices[0].message.content)

elif page == "📊 Ma progression":
    st.title("📊 Ma progression")

    conn = sqlite3.connect("tuteur.db")
    rows = conn.execute(
        "SELECT theme, niveau, reussi, date FROM resultats WHERE eleve_id=? ORDER BY date DESC",
        (eleve["id"],)
    ).fetchall()
    conn.close()

    if rows:
        import pandas as pd
        total = len(rows)
        reussis = sum(r[2] for r in rows)
        taux = round(reussis / total * 100)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total exercices", total)
        col2.metric("Réussis", reussis)
        col3.metric("Taux de réussite", f"{taux}%")

        st.divider()
        df = pd.DataFrame(rows, columns=["Thème", "Niveau", "Réussi", "Date"])
        df["Réussi"] = df["Réussi"].map({1: "✅", 0: "❌"})
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun résultat encore. Lance-toi sur les exercices !")
