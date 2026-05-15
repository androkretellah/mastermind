import streamlit as st

# 1. Database condiviso sul server (comune a tutti i dispositivi)
@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None,
        "p2_chiave": None,
        "p1_mosse": [],
        "p2_mosse": [],
        "turno": "Giocatore 1",
        "vincitore": None
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

st.set_page_config(page_title="Mastermind Online 1vs1", layout="wide")

# --- SELEZIONE RUOLO (Locale per dispositivo) ---
if "ruolo" not in st.session_state:
    st.title("Benvenuto su Mastermind Online")
    ruolo = st.radio("Chi sei?", ["Seleziona...", "Giocatore 1", "Giocatore 2"])
    if ruolo != "Seleziona...":
        st.session_state.ruolo = ruolo
        st.rerun()
    st.stop()

ruolo_utente = st.session_state.ruolo
st.title(f"🕹️ {ruolo_utente} - Mastermind")

# --- SIDEBAR E RESET ---
with st.sidebar:
    st.write(f"Connesso come: **{ruolo_utente}**")
    if st.button("🗑️ Reset Totale (Per tutti)"):
        for k in game: game[k] = None
        game["p1_mosse"], game["p2_mosse"] = [], []
        game["turno"] = "Giocatore 1"
        st.rerun()
    st.info("Nota: Clicca 'Aggiorna' per vedere le mosse dell'avversario.")

# --- FASE 1: IMPOSTAZIONE CHIAVI ---
if game["p1_chiave"] is None or game["p2_chiave"] is None:
    st.subheader("Configurazione Partita")
    
    if ruolo_utente == "Giocatore 1":
        if game["p1_chiave"] is None:
            k1 = st.text_input("Imposta la chiave che G2 dovrà indovinare:", type="password")
            if st.button("Salva Chiave"):
                if len(k1) == 5:
                    game["p1_chiave"] = k1
                    st.rerun()
        else:
            st.warning("Hai già impostato la tua chiave. In attesa del Giocatore 2...")
            
    elif ruolo_utente == "Giocatore 2":
        if game["p2_chiave"] is None:
            k2 = st.text_input("Imposta la chiave che G1 dovrà indovinare:", type="password")
            if st.button("Salva Chiave"):
                if len(k2) == 5:
                    game["p2_chiave"] = k2
                    st.rerun()
        else:
            st.warning("Hai già impostato la tua chiave. In attesa del Giocatore 1...")
    
    if st.button("🔄 Controlla se l'altro ha finito"):
        st.rerun()
    st.stop()

# --- FASE 2: GIOCO ---
if game["vincitore"]:
    st.success(f"🏆 LA PARTITA È FINITA! VINCITORE: {game['vincitore']}")
    if st.button("Nuova Partita"):
        # Reset locale e globale
        del st.session_state.ruolo
        st.rerun()

col_gioco, col_info = st.columns([2, 1])

with col_gioco:
    st.subheader(f"Turno attuale: **{game['turno']}**")
    
    # Logica di input basata sul turno e sul ruolo
    es_mio_turno = (ruolo_utente == game["turno"])
    
    with st.form("mossa_form"):
        tentativo = st.text_input("Tuo tentativo (5 cifre):", disabled=not es_mio_turno)
        invia = st.form_submit_button("Invia Mossa", disabled=not es_mio_turno)
        
        if invia and es_mio_turno:
            if len(tentativo) == 5:
                # Se sono G1, provo a indovinare la chiave di G2
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

with col_info:
    if st.button("🔄 AGGIORNA TABELLONE"):
        st.rerun()
    
    st.markdown("### Cronologia")
    tab1, tab2 = st.tabs(["Mie Mosse", "Mosse Avversario"])
    
    mie_mosse = game["p1_mosse"] if ruolo_utente == "Giocatore 1" else game["p2_mosse"]
    avv_mosse = game["p2_mosse"] if ruolo_utente == "Giocatore 1" else game["p1_mosse"]
    
    with tab1:
        for m, r in mie_mosse:
            st.code(f"{m} -> {r}")
    with tab2:
        for m, r in avv_mosse:
            st.code(f"{m} -> {r}")
