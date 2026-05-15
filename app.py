import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione
st.set_page_config(page_title="Mastermind Pro", layout="wide")
st_autorefresh(interval=1500, key="global_refresh")

COLOR_MAP = {
    "1": "🔴", "2": "🔵", "3": "🟢", "4": "🟡", 
    "5": "🟣", "6": "🟠", "7": "🟤", "8": "⚫", "9": "⚪"
}

@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None,
        "n_cifre": 4, 
        "range_cifre": (1, 9), 
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
    if "ruolo" in st.session_state: 
        del st.session_state.ruolo
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
    return ("✅" * v) + ("⭕" * o)

# --- FUNZIONI CALLBACK PER INGRESSO IMMEDIATO ---
def entra_giocatore_1():
    game["p1_preso"] = True
    st.session_state.ruolo = "Giocatore 1"

def entra_giocatore_2():
    game["p2_preso"] = True
    st.session_state.ruolo = "Giocatore 2"

# --- CONTROLLO DISCONNESSIONE ---
if "ruolo" in st.session_state:
    if not game["p1_preso"] or not game["p2_preso"]:
        del st.session_state.ruolo
        st.rerun()

# --- LOBBY ---
if "ruolo" not in st.session_state:
    st.title("🕵️ Mastermind Multiplayer")
    
    col_cfg, col_p = st.columns(2)
    
    with col_cfg:
        st.subheader("⚙️ Impostazioni Partita")
        n_c = st.select_slider("Numero di cifre (difficoltà)", options=[3, 4, 5, 6, 7, 8], value=game["n_cifre"])
        mod = st.radio("Modalità", ["Colori", "Numeri"], index=0 if game["modalita"]=="Colori" else 1, horizontal=True)
        
        st.write("Range Valori (Cardinalità)")
        c1, c2 = st.columns(2)
        v_min = c1.selectbox("Min", range(1, 9), index=game["range_cifre"][0]-1)
        v_max = c2.selectbox("Max", range(2, 10), index=game["range_cifre"][1]-2)
        
        if st.button("Applica Regole 🛠️"):
            if v_min < v_max:
                game["n_cifre"] = n_c
                game["modalita"] = mod
                game["range_cifre"] = (v_min, v_max)
                st.success("Regole aggiornate!")
            else:
                st.error("Il Min deve essere minore del Max")

    with col_p:
        st.subheader("👥 Partecipa alla Stanza")
        
        # Gestione Tasto Unico con on_click nativo di Streamlit
        if not game["p1_preso"]:
            st.button(
                "🎮 ENTRA IN PARTITA (Sarai Giocatore 1)", 
                on_click=entra_giocatore_1, 
                use_container_width=True, 
                type="primary"
            )
        elif not game["p2_preso"]:
            st.button(
                "🎮 ENTRA IN PARTITA (Sarai Giocatore 2)", 
                on_click=entra_giocatore_2, 
                use_container_width=True, 
                type="primary"
            )
        else:
            st.button("🚫 STANZA PIENA", disabled=True, use_container_width=True)
            
        st.write("")
        st.write(f"Stato Slot 1: {'🟢 Libero' if not game['p1_preso'] else '🔴 Occupato'}")
        st.write(f"Stato Slot 2: {'🟢 Libero' if not game['p2_preso'] else '🔴 Occupato'}")
        
    st.stop()

# --- GIOCO ATTIVO ---
ruolo = st.session_state.ruolo
n_cifre = game["n_cifre"]
low, high = game["range_cifre"]
mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]

# SIDEBAR
st.sidebar.title(f"🕹️ {ruolo}")
if st.sidebar.button("Esci / Abbandona ⬅️"):
    reset_game()

if mia_chiave:
    if st.sidebar.checkbox("👁️ Mostra la mia chiave"):
        chiave_visiva = "".join([COLOR_MAP[c] if game["modalita"] == "Colori" else c for c in mia_chiave])
        st.sidebar.info(f"Codice segreto: {chiave_visiva}")

# 1. Impostazione Chiave
if mia_chiave is None:
    st.header(f"🔐 Crea il tuo codice ({n_cifre} cifre)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    
    cols = st.columns(high - low + 1)
    for i, val in enumerate(range(low, high + 1)):
        label = COLOR_MAP[str(val)] if game["modalita"] == "Colori" else str(val)
        if cols[i].button(label, key=f"set_{val}"):
            if len(st.session_state.temp_key) < n_cifre:
                st.session_state.temp_key += str(val)
    
    visual_key = "".join([COLOR_MAP[c] if game["modalita"]=="Colori" else c for c in st.session_state.temp_key])
    st.subheader(f"Selezione: {visual_key}")
    
    c1, c2 = st.columns(2)
    if c1.button("CONFERMA CHIAVE ✅", disabled=len(st.session_state.temp_key) != n_cifre):
        if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
        else: game["p2_chiave"] = st.session_state.temp_key
        st.session_state.temp_key = ""
        st.rerun()
    if c2.button("Cancella ❌"): st.session_state.temp_key = ""
    st.stop()

# 2. Match
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.success(f"🏆 VINCITORE: {game['vincitore']}!")
        if st.button("Torna alla lobby"): reset_game()
        st.stop()

    st.subheader(f"Turno: {game['turno']}")
    col_input, col_hist = st.columns(2)
    
    with col_input:
        mio_turno = (game["turno"] == ruolo)
        if "temp_guess" not in st.session_state: st.session_state.temp_guess = ""
        
        st.write("Componi il tuo tentativo:")
        g_cols = st.columns(high - low + 1)
        for i, val in enumerate(range(low, high + 1)):
            label = COLOR_MAP[str(val)] if game["modalita"] == "Colori" else str(val)
            if g_cols[i].button(label, key=f"g_{val}", disabled=not mio_turno):
                if len(st.session_state.temp_guess) < n_cifre:
                    st.session_state.temp_guess += str(val)
        
        visual_guess = "".join([COLOR_MAP[c] if game["modalita"]=="Colori" else c for c in st.session_state.temp_guess])
        st.write(f"Tentativo attuale: **{visual_guess}**")
        
        b1, b2 = st.columns(2)
        if b1.button("INVIA MOSSA 🚀", disabled=not (mio_turno and len(st.session_state.temp_guess) == n_cifre)):
            target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
            res = calcola_feedback(target, st.session_state.temp_guess, n_cifre)
            
            if ruolo == "Giocatore 1":
                game["p1_mosse"].insert(0, (st.session_state.temp_guess, res))
                game["turno"] = "Giocatore 2"
            else:
                game["p2_mosse"].insert(0, (st.session_state.temp_guess, res))
                game["turno"] = "Giocatore 1"
            
            if res == "✅" * n_cifre: game["vincitore"] = ruolo
            st.session_state.temp_guess = ""
            st.rerun()
        if b2.button("Svuota 🗑️", disabled=not mio_turno): st.session_state.temp_guess = ""

    with col_hist:
        t1, t2 = st.tabs(["I miei tentativi", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        with t1:
            for m, r in mie:
                m_txt = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.write(f"{m_txt} ➡️ Esito: {r if r else '❌ (Nessun riscontro)'}")
        with t2:
            for m, r in avv:
                st.write(f"L'avversario ha tentato una mossa ➡️ Esito: {r if r else '❌'}")
else:
    st.info("In attesa che l'avversario imposti la sua chiave segreta...")
