import streamlit as st

def calcola_feedback(chiave, tentativo):
    usato_chiave = [False] * 5
    usato_tentativo = [False] * 5
    v_count = 0
    o_count = 0
    for i in range(5):
        if tentativo[i] == chiave[i]:
            v_count += 1
            usato_chiave[i] = True
            usato_tentativo[i] = True
    for i in range(5):
        if not usato_tentativo[i]:
            for j in range(5):
                if not usato_chiave[j] and tentativo[i] == chiave[j]:
                    o_count += 1
                    usato_chiave[j] = True
                    break
    return ('V' * v_count) + ('O' * o_count)

st.title("🕵️ Mastermind Online")

# Inizializzazione variabili di sessione
if 'chiave' not in st.session_state:
    st.session_state.chiave = None
if 'cronologia' not in st.session_state:
    st.session_state.cronologia = []

# FASE 1: Impostazione Chiave
if st.session_state.chiave is None:
    st.subheader("Configurazione Partita")
    nuova_chiave = st.text_input("Inserisci la chiave segreta (5 cifre):", type="password")
    if st.button("Imposta Chiave"):
        if len(nuova_chiave) == 5 and nuova_chiave.isdigit():
            st.session_state.chiave = nuova_chiave
            st.rerun()
        else:
            st.error("La chiave deve essere di 5 cifre!")

# FASE 2: Gioco
else:
    st.info("Chiave impostata! L'avversario può iniziare a indovinare.")
    
    with st.form(key='gioco_form', clear_on_submit=True):
        tentativo = st.text_input("Inserisci il tuo tentativo (5 cifre):")
        submit = st.form_submit_button("Invia")

    if submit:
        if len(tentativo) == 5 and tentativo.isdigit():
            risultato = calcola_feedback(st.session_state.chiave, tentativo)
            st.session_state.cronologia.insert(0, f"Tentativo: {tentativo} | Risultato: {risultato}")
            if risultato == "VVVVV":
                st.balloons()
                st.success("VITTORIA! Hai indovinato la sequenza.")
        else:
            st.error("Inserisci 5 cifre.")

    # Tasto ESC (Reset)
    if st.button("🔄 Reset (Nuova Chiave)"):
        st.session_state.chiave = None
        st.session_state.cronologia = []
        st.rerun()

    # Visualizzazione cronologia
    for r in st.session_state.cronologia:
        st.write(r)