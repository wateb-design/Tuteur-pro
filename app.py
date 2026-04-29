Parfait, les secrets sont configurés ! Maintenant on attaque le vrai code. Commençons par un `app.py` solide qui servira de base à toute l application.

Voici le contenu complet à coller dans votre `app.py` sur GitHub :

```python
import streamlit as st
from groq import Groq
import sqlite3

# ── Configuration de la page ──────────────────────────────────────
st.set_page_config(
    page_title="Tuteur IA — Programmation",
    page_icon="🤖",
    layout="wide"
)

# ── Connexion Groq ────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Base de données SQLite ────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("tuteur.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS resultats (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve     TEXT,
            theme     TEXT,
            niveau    TEXT,
            reussi    INTEGER,
            date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Navigation ────────────────────────────────────────────────────
st.sidebar.title("📚 Tuteur IA")
st.sidebar.markdown("Programmation · 1ère TI")
st.sidebar.divider()

page = st.sidebar.radio("Navigation", [
    "🏠 Accueil",
    "📖 Cours",
    "🧠 Exercices",
    "📊 Ma progression"
])

# ── Pages ─────────────────────────────────────────────────────────
if page == "🏠 Accueil":
    st.title("Bienvenue sur ton Tuteur IA 🤖")
    st.markdown("Améliore tes performances en programmation Python, Streamlit, Groq et SQLite.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Thèmes disponibles", "4")
    col2.metric("Niveaux", "3")
    col3.metric("Exercices générés par IA", "∞")

    st.info("👈 Utilise le menu à gauche pour naviguer.")

elif page == "📖 Cours":
    st.title("📖 Cours")
    st.info("Module en construction — disponible prochainement.")

elif page == "🧠 Exercices":
    st.title("🧠 Exercices")

    theme = st.selectbox("Thème", ["Python — bases", "Streamlit", "Groq Cloud", "SQLite"])
    niveau = st.selectbox("Niveau", ["Facile", "Moyen", "Difficile"])
    eleve = st.text_input("Ton prénom", value="Élève")

    if st.button("Générer un exercice"):
        with st.spinner("L'IA prépare ton exercice..."):
            prompt = f"""Génère un exercice de programmation de niveau {niveau} sur le thème : {theme}.
Réponds UNIQUEMENT en JSON avec ce format exact :
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
            st.session_state["eleve"] = eleve
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
                feedback_prompt = f"""Exercice : {ex['titre']}
Solution attendue : {ex['solution']}
Réponse de l'élève : {reponse}
Évalue en 2 phrases. Commence par "Correct !" ou "Pas tout à fait."."""
                fb = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": feedback_prompt}],
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
                    "INSERT INTO resultats (eleve, theme, niveau, reussi) VALUES (?,?,?,?)",
                    (st.session_state["eleve"], st.session_state["theme"],
                     st.session_state["niveau"], reussi)
                )
                conn.commit()
                conn.close()

        if col2.button("Indice"):
            with st.spinner("Réflexion..."):
                hint = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content":
                        f"Donne un seul indice pour cet exercice sans donner la solution : {ex['titre']} — {ex['description']}"}],
                    max_tokens=100
                )
                st.info(hint.choices[0].message.content)

elif page == "📊 Ma progression":
    st.title("📊 Ma progression")
    eleve = st.text_input("Ton prénom :", value="Élève")

    if st.button("Voir mes résultats"):
        conn = sqlite3.connect("tuteur.db")
        rows = conn.execute(
            "SELECT theme, niveau, reussi, date FROM resultats WHERE eleve=? ORDER BY date DESC",
            (eleve,)
        ).fetchall()
        conn.close()

        if rows:
            total = len(rows)
            reussis = sum(r[2] for r in rows)
            st.metric("Taux de réussite", f"{round(reussis/total*100)}%")

            import pandas as pd
            df = pd.DataFrame(rows, columns=["Thème", "Niveau", "Réussi", "Date"])
            df["Réussi"] = df["Réussi"].map({1: "✅", 0: "❌"})
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun résultat encore. Lance-toi sur les exercices !")
```


