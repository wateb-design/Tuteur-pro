import streamlit as st
import hashlib
from database import inserer_eleve, get_eleve_par_email

# ── Sécurité : chiffrement du mot de passe ────────────────────────
# On ne stocke JAMAIS un mot de passe en clair dans la base.
# hashlib.sha256 transforme "monpass" en une chaîne illisible
# de 64 caractères. Ce processus est irréversible.
# Exemple : "bonjour" → "b3cb47f..."
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ── Création d'un nouveau compte ──────────────────────────────────
# On hash le mot de passe AVANT de l'envoyer à la base de données.
# La fonction inserer_eleve() vient de database.py.
# Elle retourne False si l'email est déjà utilisé (UNIQUE en SQL).
def creer_compte(prenom, email, password):
    ok = inserer_eleve(prenom, email, hash_password(password))
    if ok:
        return True, "Compte créé avec succès !"
    return False, "Cet email est déjà utilisé."


# ── Connexion ─────────────────────────────────────────────────────
# On hash le mot de passe saisi, puis on cherche dans la base
# un élève avec cet email ET ce hash. Si on trouve → connecté.
# On retourne un dict avec id et prenom pour la session.

def connecter(email, password):
    if not email or not password:
        return False, None
    
    pwd_hash = hash_password(password)
    
    # Debug temporaire — à supprimer après
    #st.write("Email saisi :", email)
    #st.write("Hash généré :", pwd_hash[:20], "...")
    
    row = get_eleve_par_email(email, pwd_hash)
    
    # Debug temporaire
    #st.write("Résultat BDD :", row)
    
    if row:
        return True, {"id": row[0], "prenom": row[1], "email": email}
    return False, None

# ── Déconnexion ───────────────────────────────────────────────────
# st.session_state conserve les données entre les pages Streamlit.
# On supprime toutes les clés liées à l'élève pour "vider" la session.
# st.rerun() recharge la page → affiche le formulaire de connexion.
def deconnecter():
    cles_a_supprimer = ["eleve", "exercice", "theme", "niveau"]
    for cle in cles_a_supprimer:
        st.session_state.pop(cle, None)
    st.rerun()


# ── Validation des champs ─────────────────────────────────────────
# Centraliser les validations évite de les réécrire dans chaque page.
# Retourne (True, "") si tout est bon, sinon (False, "message erreur").
def valider_inscription(prenom, email, password, password2):
    if not prenom or not email or not password:
        return False, "Remplis tous les champs."
    if "@" not in email or "." not in email:
        return False, "Adresse email invalide."
    if len(password) < 6:
        return False, "Le mot de passe doit faire au moins 6 caractères."
    if password != password2:
        return False, "Les mots de passe ne correspondent pas."
    return True, ""


# ── Page affichée si l'élève n'est pas connecté ───────────────────
# Cette fonction est appelée dans app.py avant tout le reste.
# Si l'élève n'est pas dans st.session_state, on affiche ce formulaire
# et on bloque l'accès aux autres pages avec st.stop().
def page_auth():
    # Centrage du formulaire sur la page
    col_vide, col_form, col_vide2 = st.columns([1, 2, 1])

    with col_form:
        st.title("🤖 Tuteur-pro")
        st.markdown("##### Programmation · 1ère TI")
        st.divider()

        # Radio horizontal pour switcher entre Connexion et Inscription
        onglet = st.radio("", ["Connexion", "Créer un compte"], horizontal=True)

        # ── Formulaire de connexion ───────────────────────────────
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
                        # On sauvegarde l'élève dans la session Streamlit
                        st.session_state["eleve"] = eleve
                        st.success(f"Bienvenue {eleve['prenom']} !")
                        st.rerun()  # Recharge → accède aux pages
                    else:
                        st.error("Email ou mot de passe incorrect.")

        # ── Formulaire d'inscription ──────────────────────────────
        else:
            st.subheader("Créer un compte")

            prenom   = st.text_input("Prénom")
            email    = st.text_input("Email", placeholder="ton@email.com")
            password  = st.text_input("Mot de passe", type="password")
            password2 = st.text_input("Confirmer le mot de passe", type="password")

            if st.button("Créer mon compte", use_container_width=True):
                ok, msg = valider_inscription(prenom, email, password, password2)
                if not ok:
                    st.warning(msg)
                else:
                    ok2, msg2 = creer_compte(prenom, email, password)
                    if ok2:
                        st.success(msg2 + " Tu peux maintenant te connecter.")
                    else:
                        st.error(msg2)
