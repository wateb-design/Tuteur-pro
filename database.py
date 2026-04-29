import psycopg2
import streamlit as st

# ── Connexion à Supabase via PostgreSQL ───────────────────────────
# On récupère l'URL depuis les secrets Streamlit.
# psycopg2 est le driver Python standard pour PostgreSQL.
def get_connection():
    return psycopg2.connect(
        st.secrets["SUPABASE_URL"],
        sslmode="require"
    )

# ── Initialisation des tables ─────────────────────────────────────
# Appelé au démarrage de l'app dans app.py.
# IF NOT EXISTS → sans danger si les tables existent déjà.
def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS eleves (
            id        SERIAL PRIMARY KEY,
            prenom    TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            date      TIMESTAMP DEFAULT NOW()
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS resultats (
            id        SERIAL PRIMARY KEY,
            eleve_id  INTEGER REFERENCES eleves(id),
            theme     TEXT,
            niveau    TEXT,
            reussi    INTEGER,
            temps     INTEGER,
            date      TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    conn.close()

# ── Élèves ────────────────────────────────────────────────────────

def inserer_eleve(prenom, email, password_hash):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO eleves (prenom, email, password) VALUES (%s, %s, %s)",
            (prenom, email, password_hash)
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        # Email déjà utilisé → UNIQUE constraint
        return False
    finally:
        conn.close()

def get_eleve_par_email(email, password_hash):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, prenom FROM eleves WHERE email=%s AND password=%s",
        (email, password_hash)
    )
    row = c.fetchone()
    conn.close()
    return row

# ── Résultats ─────────────────────────────────────────────────────

def inserer_resultat(eleve_id, theme, niveau, reussi, temps=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO resultats (eleve_id, theme, niveau, reussi, temps) VALUES (%s,%s,%s,%s,%s)",
        (eleve_id, theme, niveau, reussi, temps)
    )
    conn.commit()
    conn.close()

def get_resultats_eleve(eleve_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT theme, niveau, reussi, temps, date FROM resultats WHERE eleve_id=%s ORDER BY date DESC",
        (eleve_id,)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def get_stats_eleve(eleve_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*), SUM(reussi) FROM resultats WHERE eleve_id=%s",
        (eleve_id,)
    )
    row = c.fetchone()
    conn.close()
    total   = row[0] or 0
    reussis = row[1] or 0
    taux    = round(reussis / total * 100) if total > 0 else 0
    return {"total": total, "reussis": reussis, "taux": taux}

def get_stats_par_theme(eleve_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """SELECT theme,
                  COUNT(*) as total,
                  SUM(reussi) as reussis
           FROM resultats
           WHERE eleve_id=%s
           GROUP BY theme""",
        (eleve_id,)
    )
    rows = c.fetchall()
    conn.close()
    return rows
