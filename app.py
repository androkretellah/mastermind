import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Pro 1vs1", layout="wide")

# Auto-refresh ogni 3 secondi per sincronizzare i due giocatori
st_autorefresh(interval=3000, key="datarefresh")

@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None
    }

game = get_shared_game()

def calcola_feedback(chiave, tentativo):
    usato_chiave, usato_tentativo = [False]*5, [False]*5
    v, o = 0, 0
    for i in range(5):
        if tentativo[i] == chiave[i]:
            v += 1
            usato_chiave[i] = usato_tentativo[i] = True
    for i in range(5):
        if not usato_tentativo[i]:
            for j in range(5):
                if not usato_chiave[j] and tentativo[i] == chiave[j]:
                    o += 1
                    usato_chiave[j] = True
                    break
    return ('V' * v) + ('O' * o)

# --- SCHERMATA DI SELEZIONE ---
if "ruolo" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🕵️ Mastermind Online 1vs1</h1>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        c1, c2 = st.columns(2)
        if c1.button("🟦 GIOCATORE 1", use_container_width=True):
            st.session_state.ruolo = "Giocatore 1"
            st.rerun()
        if c2.button("🟥 GIOCATORE 2", use_container_width=True):
            st.session_state.ruolo = "Giocatore 2"
            st.rerun()
    st.stop()

ruolo_utente = st.session_state.ruolo

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"Stai giocando come:<br><h2>{ruolo_utente}</h2>", unsafe_allow_html=True)
    if st.button("🗑️ Reset Partita"):
        for k in game: game[k] = None
        game["p1_mosse"], game["p2_mosse"] = [], []
        game["turno"] = "Giocatore 1"
        st.rerun()
    
    st.divider()
    
    # PULSANTE PER MOSTRARE LA PROPRIA CHIAVE
    mia_chiave_impostata = game["p1_chiave"] if ruolo_utente == "Giocatore 1" else game["p2_chiave"]
    if mia_chiave_impostata:
        if st.checkbox("👁️ Mostra la mia chiave"):
            st.info(f"La tua chiave segreta è: **{mia_chiave_impostata}**")

# --- FASE 1: SETTING CHIAVI (Con supporto INVIO) ---
if game["p1_chiave"] is None or game["p2_chiave"] is None:
    st.info("Configurazione chiavi in corso...")
    
    # Verifichiamo se l'utente attuale deve ancora impostare la chiave
    deve_impostare = (ruolo_utente == "Giocatore 1" and game["p1_chiave"] is None) or \
                     (ruolo_utente == "Giocatore 2" and game["p2_chiave"] is None)

    if deve_impostare:
        with st.form("form_chiave", clear_on_submit=True):
            st.subheader("Imposta la tua chiave")
            st.write("L'avversario dovrà indovinare questa sequenza.")
            k_input = st.text_input("Inserisci 5 cifre e premi INVIO:", type="password", max_chars=5)
            submit_k = st.form_submit_button("Conferma Chiave")
            
            if submit_k:
                if len(k_input) == 5 and k_input.isdigit():
                    if ruolo_utente == "Giocatore 1": game["p1_chiave"] = k_input
                    else: game["p2_chiave"] = k_input
                    st.rerun()
                else:
                    st.error("Inserisci esattamente 5 cifre numeriche.")
    else:
        st.warning("Hai già impostato la tua chiave. In attesa dell'avversario...")
        if st.button("🔄 Controlla se è pronto"): st.rerun()
    st.stop()

# --- FASE 2: GIOCO ---
if game["vincitore"]:
    if game["vincitore"] == ruolo_utente:
        st.balloons()
        st.success("🎉 HAI VINTO!")
    else:
        st.error(f"💀 HAI PERSO! Il {game['vincitore']} ha vinto.")
    if st.button("Torna alla Selezione"):
        del st.session_state.ruolo
        st.rerun()
    st.stop()

col_input, col_log = st.columns([1, 2])

with col_input:
    st.markdown(f"#### Turno di: **{game['turno']}**")
    mio_turno = (ruolo_utente == game["turno"])
    
    with st.form("guess_form", clear_on_submit=True):
        st.write("Fai il tuo tentativo")
        tentativo = st.text_input("Cifre (Invio per confermare):", max_chars=5, disabled=not mio_turno)
        submit = st.form_submit_button("INVIA", use_container_width=True, disabled=not mio_turno)
        
        if submit and mio_turno:
            if len(tentativo) == 5 and tentativo.isdigit():
                # Bersaglio incrociato
                target = game["p2_chiave"] if ruolo_utente == "Giocatore 1" else game["p1_chiave"]
                res = calcola_feedback(target, tentativo)
                
                if ruolo_utente == "Giocatore 1":
                    game["p1_mosse"].insert(0, (tentativo, res))
                    game["turno"] = "Giocatore 2"
                else:
                    game["p2_mosse"].insert(0, (tentativo, res))
                    game["turno"] = "Giocatore 1"
                
                if res == "VVVVV":
                    game["vincitore"] = ruolo_utente
                st.rerun()

with col_log:
    tab1, tab2 = st.tabs(["📊 I MIEI TENTATIVI", "🔭 MOSSE AVVERSARIO"])
    mie = game["p1_mosse"] if ruolo_utente == "Giocatore 1" else game["p2_mosse"]
    avv = game["p2_mosse"] if ruolo_utente == "Giocatore 1" else game["p1_mosse"]
    
    with tab1:
        for m, r in mie: st.markdown(f"**{m}** → `{r}`")
    with tab2:
        for m, r in avv: st.markdown(f"Mossa avversario → `{r}`")
