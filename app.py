import streamlit as st

# 1. Database condiviso tra tutti gli utenti del server
@st.cache_resource
def get_shared_state():
    return {
        "chiave": None,
        "cronologia": [],
        "turno": 0  # Per gestire l'alternanza (opzionale)
    }

shared = get_shared_state()

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

st.set_page_config(page_title="Mastermind Sincrono", page_icon="👥")
st.title("👥 Mastermind Sincrono")

# --- LOGICA DI RESET ---
if st.sidebar.button("🗑️ Reset Totale Partita"):
    shared["chiave"] = None
    shared["cronologia"] = []
    st.rerun()

# --- FASE 1: IMPOSTAZIONE CHIAVE ---
if shared["chiave"] is None:
    st.subheader("Configurazione Partita")
    st.write("Uno dei due giocatori inserisca la chiave segreta.")
    nuova_chiave = st.text_input("Inserisci chiave (5 cifre):", type="password")
    if st.button("Conferma Chiave"):
        if len(nuova_chiave) == 5 and nuova_chiave.isdigit():
            shared["chiave"] = nuova_chiave
            st.rerun()
        else:
            st.error("Deve essere di 5 cifre!")

# --- FASE 2: GIOCO SINCRONO ---
else:
    st.success("Partita in corso! Entrambi vedete gli stessi tentativi.")
    
    # Form per l'inserimento
    with st.form(key='sync_form', clear_on_submit=True):
        tentativo = st.text_input("Inserisci il tuo tentativo:")
        submit = st.form_submit_button("Invia Mossa")

    if submit:
        if len(tentativo) == 5 and tentativo.isdigit():
            risultato = calcola_feedback(shared["chiave"], tentativo)
            # Aggiungiamo alla lista condivisa
            shared["cronologia"].insert(0, f"Mossa: {tentativo} -> Feedback: {risultato}")
            if risultato == "VVVVV":
                st.balloons()
            st.rerun() # Forza l'aggiornamento per l'altro utente
        else:
            st.error("Inserisci 5 cifre.")

    # Visualizzazione Cronologia Condivisa
    st.subheader("Tabellone di gioco")
    if not shared["cronologia"]:
        st.write("In attesa della prima mossa...")
    for mossa in shared["cronologia"]:
        st.code(mossa)

    # Auto-refresh: siccome Streamlit non è "push", aggiungiamo un tasto per aggiornare
    if st.button("🔄 Aggiorna Tabellone"):
        st.rerun()
