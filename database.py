import sqlite3

DB_PATH = "tuteur.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# ── Initialisation ────────────────────────────────────────────────
# CREATE TABLE IF NOT EXISTS est sans danger — ne recrée pas
# si la table existe déjà. Appelé au démarrage ET dans chaque
# fonction pour garantir que les tables existent toujours.
def init_db():
    conn = get_connection()
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
            eleve_id  INTEGER NOT NULL,
            theme     TEXT,
            niveau    TEXT,
            reussi    INTEGER,
            temps     INTEGER,
            date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id)
        )
    """)

    conn.commit()
    conn.close()

# ── Élèves ────────────────────────────────────────────────────────

def inserer_eleve(prenom, email, password_hash):
    init_db()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO eleves (prenom, email, password) VALUES (?, ?, ?)",
            (prenom, email, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_eleve_par_email(email, password_hash):
    init_db()
    conn = get_connection()
    row = conn.execute(
        "SELECT id, prenom FROM eleves WHERE email=? AND password=?",
        (email, password_hash)
    ).fetchone()
    conn.close()
    return row

# ── Résultats ─────────────────────────────────────────────────────

def inserer_resultat(eleve_id, theme, niveau, reussi, temps=0):
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO resultats (eleve_id, theme, niveau, reussi, temps) VALUES (?,?,?,?,?)",
        (eleve_id, theme, niveau, reussi, temps)
    )
    conn.commit()
    conn.close()

def get_resultats_eleve(eleve_id):
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT theme, niveau, reussi, temps, date FROM resultats WHERE eleve_id=? ORDER BY date DESC",
        (eleve_id,)
    ).fetchall()
    conn.close()
    return rows

def get_stats_eleve(eleve_id):
    init_db()
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*), SUM(reussi) FROM resultats WHERE eleve_id=?",
        (eleve_id,)
    ).fetchone()
    conn.close()
    total   = row[0] or 0
    reussis = row[1] or 0
    taux    = round(reussis / total * 100) if total > 0 else 0
    return {"total": total, "reussis": reussis, "taux": taux}

def get_stats_par_theme(eleve_id):
    init_db()
    conn = get_connection()
    rows = conn.execute(
        """SELECT theme,
                  COUNT(*) as total,
                  SUM(reussi) as reussis
           FROM resultats
           WHERE eleve_id=?
           GROUP BY theme""",
        (eleve_id,)
    ).fetchall()
    conn.close()
    return rows
