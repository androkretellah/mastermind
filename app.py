import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Pro 1vs1", layout="wide")

# Installazione necessaria: pip install streamlit-autorefresh
# Auto-refresh ogni 3 secondi per vedere le mosse dell'avversario
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

# --- SCHERMATA DI SELEZIONE CARINA ---
if "ruolo" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🕵️ Mastermind Online 1vs1</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Seleziona il tuo profilo per iniziare la sfida</p>", unsafe_allow_html=True)
    
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

# --- HEADER ---
st.markdown(f"### 🎮 Stai giocando come: `{ruolo_utente}`")
if st.sidebar.button("🗑️ Reset Partita"):
    for k in game: game[k] = None
    game["p1_mosse"], game["p2_mosse"] = [], []
    game["turno"] = "Giocatore 1"
    st.rerun()

# --- FASE 1: SETTING CHIAVI ---
if game["p1_chiave"] is None or game["p2_chiave"] is None:
    st.info("Attesa configurazione chiavi...")
    
    if ruolo_utente == "Giocatore 1" and game["p1_chiave"] is None:
        with st.container(border=True):
            k1 = st.text_input("Imposta chiave per il tuo avversario:", type="password", help="5 cifre")
            if st.button("Conferma Chiave"):
                if len(k1) == 5 and k1.isdigit():
                    game["p1_chiave"] = k1
                    st.rerun()
    elif ruolo_utente == "Giocatore 2" and game["p2_chiave"] is None:
        with st.container(border=True):
            k2 = st.text_input("Imposta chiave per il tuo avversario:", type="password", help="5 cifre")
            if st.button("Conferma Chiave"):
                if len(k2) == 5 and k2.isdigit():
                    game["p2_chiave"] = k2
                    st.rerun()
    else:
        st.warning("Hai fatto la tua parte! Aspetta che l'altro giocatore imposti la sua chiave.")
    st.stop()

# --- FASE 2: BATTLEFIELD ---
if game["vincitore"]:
    if game["vincitore"] == ruolo_utente:
        st.balloons()
        st.success("🎉 HAI VINTO!")
    else:
        st.error(f"💀 HAI PERSO! Il {game['vincitore']} ha indovinato per primo.")
    if st.button("Torna alla Home"):
        del st.session_state.ruolo
        st.rerun()
    st.stop()

# Layout Gioco
col_input, col_log = st.columns([1, 2])

with col_input:
    st.markdown(f"#### Turno di: **{game['turno']}**")
    mio_turno = (ruolo_utente == game["turno"])
    
    # Form con clear_on_submit=True resetta la casella automaticamente
    with st.form("guess_form", clear_on_submit=True):
        st.write("Inserisci il tuo tentativo")
        tentativo = st.text_input("Cifre:", max_chars=5, disabled=not mio_turno)
        submit = st.form_submit_button("INVIA TENTATIVO", use_container_width=True, disabled=not mio_turno)
        
        if submit and mio_turno:
            if len(tentativo) == 5 and tentativo.isdigit():
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
            else:
                st.error("Inserisci 5 cifre numeriche!")

with col_log:
    tab1, tab2 = st.tabs(["📊 I MIEI TENTATIVI", "🔭 AVVERSARIO"])
    
    mie = game["p1_mosse"] if ruolo_utente == "Giocatore 1" else game["p2_mosse"]
    avv = game["p2_mosse"] if ruolo_utente == "Giocatore 1" else game["p1_mosse"]
    
    with tab1:
        for m, r in mie:
            st.markdown(f"**{m}** → `{r}`")
            
    with tab2:
        for m, r in avv:
            # Mostriamo solo il feedback per non barare, o la mossa intera se preferisci
            st.markdown(f"Mossa avversario → `{r}`")
