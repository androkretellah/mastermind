import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione - Pulita al massimo
st.set_page_config(page_title="Mastermind Pro", layout="wide")
st_autorefresh(interval=2000, key="global_refresh")

COLOR_MAP = {
    "1": "🔴", "2": "🔵", "3": "🟢", "4": "🟡", 
    "5": "🟣", "6": "🟠", "7": "🟤", "8": "⚫", "9": "⚪"
}

# Oggetto condiviso tra i browser
@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None,
        "n_cifre": 4, "range_cifre": (1, 9), 
        "modalita": "Colori",
        "p1_preso": False, "p2_preso": False
    }

game = get_shared_game()

def reset_game():
    game.update({
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None,
        "p1_preso": False, "p2_preso": False
    })
    if "ruolo" in st.session_state: del st.session_state.ruolo
    st.rerun()

def calcola_feedback(chiave, tentativo, n_cifre):
    usato_chiave, usato_tentativo = [False]*n_cifre, [False]*n_cifre
    v, o = 0, 0
    for i in range(n_cifre):
        if tentativo[i] == chiave[i]:
            v += 1
            usato_chiave[i] = usato_tentativo[i] = True
    for i in range(n_cifre):
        if not usato_tentativo[i]:
            for j in range(n_cifre):
                if not usato_chiave[j] and tentativo[i] == chiave[j]:
                    o += 1
                    usato_chiave[j] = True
                    break
    return ('V' * v) + ('O' * o)

# --- LOGICA LOBBY ---
if "ruolo" not in st.session_state:
    st.title("🕵️ Mastermind Multiplayer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Configurazione")
        # Widget locali (non collegati direttamente al game per evitare blocchi)
        n_cifre = st.slider("Cifre", 3, 6, game["n_cifre"])
        mod = st.radio("Modalità", ["Colori", "Numeri"], index=0 if game["modalita"]=="Colori" else 1)
        
        if st.button("Salva Impostazioni"):
            game["n_cifre"] = n_cifre
            game["modalita"] = mod
            st.success("Impostazioni salvate!")

    with col2:
        st.subheader("👥 Scegli Ruolo")
        c_a, c_b = st.columns(2)
        if c_a.button("GIOCATORE 1", disabled=game["p1_preso"], use_container_width=True):
            game["p1_preso"] = True
            st.session_state.ruolo = "Giocatore 1"
            st.rerun()
        if c_b.button("GIOCATORE 2", disabled=game["p2_preso"], use_container_width=True):
            game["p2_preso"] = True
            st.session_state.ruolo = "Giocatore 2"
            st.rerun()
    st.stop()

# --- LOGICA GIOCO ---
ruolo = st.session_state.ruolo
n_cifre = game["n_cifre"]
mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]

st.sidebar.title(f"Sei: {ruolo}")
if st.sidebar.button("Esci / Reset"):
    reset_game()

# 1. Impostazione Chiave
if mia_chiave is None:
    st.header("🔑 Crea il tuo codice segreto")
    chiave_input = st.text_input(f"Inserisci {n_cifre} cifre (es. 1234)", key="key_input")
    if st.button("Conferma Codice"):
        if len(chiave_input) == n_cifre and chiave_input.isdigit():
            if ruolo == "Giocatore 1": game["p1_chiave"] = chiave_input
            else: game["p2_chiave"] = chiave_input
            st.rerun()
        else:
            st.error(f"Inserisci esattamente {n_cifre} numeri!")
    st.stop()

# 2. Partita in corso
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.balloons()
        st.success(f"PARTITA FINITA! Vincitore: {game['vincitore']}")
        if st.button("Nuova Partita"): reset_game()
        st.stop()

    st.subheader(f"Turno di: {game['turno']}")
    
    col_input, col_hist = st.columns(2)
    
    with col_input:
        mio_turno = (game["turno"] == ruolo)
        tentativo = st.text_input("Tuo tentativo:", key="mossa_input", disabled=not mio_turno)
        if st.button("Invia Mossa", disabled=not mio_turno):
            if len(tentativo) == n_cifre:
                bersaglio = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                risultato = calcola_feedback(bersaglio, tentativo, n_cifre)
                
                # Registra mossa
                mossa_data = (tentativo, risultato)
                if ruolo == "Giocatore 1":
                    game["p1_mosse"].insert(0, mossa_data)
                    game["turno"] = "Giocatore 2"
                else:
                    game["p2_mosse"].insert(0, mossa_data)
                    game["turno"] = "Giocatore 1"
                
                if risultato == "V" * n_cifre:
                    game["vincitore"] = ruolo
                st.rerun()

    with col_hist:
        t1, t2 = st.tabs(["Mie Mosse", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        
        with t1:
            for m, r in mie:
                # Converti in colori se modalità colori
                visual = "".join([COLOR_MAP.get(c, c) for c in m]) if game["modalita"] == "Colori" else m
                st.write(f"{visual} ➡️ `{r}`")
        with t2:
            for m, r in avv:
                st.write(f"Tentativo fatto ➡️ Risultato: `{r}`")
else:
    st.warning("In attesa che l'altro giocatore scelga il suo codice...")
