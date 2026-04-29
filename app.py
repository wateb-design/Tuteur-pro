import streamlit as st

st.title("Mon premier projet en ligne ! 🚀")
st.write("Bienvenue sur ma première application Streamlit.")

nom = st.text_input("Comment vous appelez-vous ?")
if nom:
    st.write(f"Bonjour {nom} !")
