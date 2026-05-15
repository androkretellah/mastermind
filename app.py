import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale e Rimozione Anchor Links
st.set_page_config(page_title="Mastermind Pro 1-9", layout="wide")
st_autorefresh(interval=1500, key="global_refresh")

# CSS per nascondere i link accanto ai titoli
st.markdown("""
    <style>
    .element-container:has(#stHeader) + div > div > div > h1 > a,
    .element-container:has(#stHeader) + div > div > div > h2 > a,
    .element-container:has(#stHeader) + div > div > div > h3 > a,
    a.header-anchor {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

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
        "n_cifre": 4, "max_tentativi": 0,
        "range_cifre": (1, 9), 
        "modalita": "Colori",
        "p1_preso": False, "p2_preso": False
    }

game = get_shared_game()

# --- FUNZIONI DI SINCRONIZZAZIONE ---
def update_shared_config(key):
    if key == "range_cifre":
        # Ricostruiamo la tupla prendendo i due widget separati
        game["range_cifre"] = (st.session_state["widget_min"], st.session_state["widget_max"])
    else:
        game[key] = st.session_state[f"widget_{key}"]

def sync_local_session():
    if "ruolo" not in st.session_state:
        for key in ["modalita", "n_cifre", "max_tentativi"]:
            st.session_state[f"widget_{key}"] = game[key]
        
        # Gestione sicura del range per i widget locali
        current_range = game.get("range_cifre", (1, 9))
        if not isinstance(current_range, (tuple, list)) or len(current_range) != 2:
            current_range = (1, 9)
        st.session_state["widget_min"] = current_range[0]
        st.session_state["widget_max"] = current_range[1]

sync_local_session()

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

def reset_game():
    for k in ["p1_chiave", "p2_chiave", "vincitore"]: game[k] = None
    game.update({"p1_mosse": [], "p2_mosse": [], "turno": "Giocatore 1", "p1_preso": False, "p2_preso": False})
    st.rerun()

# --- LOGICA DISCONNESSIONE ---
if "ruolo" in st.session_state:
    if (st.session_state.ruolo == "Giocatore 1" and not game["p1_preso"]) or \
       (st.session_state.ruolo == "Giocatore 2" and not game["p2_preso"]):
        del st.session_state.ruolo
        st.rerun()

# --- LOBBY ---
if "ruolo" not in st.session_state:
    st.title("🕵️ Mastermind Lobby")
    impostazioni_bloccate = game["p1_preso"] or game["p2_preso"]
    col_cfg, col_players = st.columns([1, 1], gap="large")
    
    with col_cfg:
        st.subheader("⚙️ Impostazioni")
        st.radio("Modalità:", ["Colori", "Numeri"], key="widget_modalita", on_change=update_shared_config, args=("modalita",), horizontal=True, disabled=impostazioni_bloccate)
        st.slider("Lunghezza sequenza:", 3, 8, key="widget_n_cifre", on_change=update_shared_config, args=("n_cifre",), disabled=impostazioni_bloccate)
        
        st.write("Range Valori:")
        c_min, c_max = st.columns(2)
        with c_min:
            st.selectbox("Minimo", options=list(range(1, 9)), key="widget_min", on_change=update_shared_config, args=("range_cifre",), disabled=impostazioni_bloccate)
        with c_max:
            st.selectbox("Massimo", options=list(range(2, 10)), key="widget_max", on_change=update_shared_config, args=("range_cifre",), disabled=impostazioni_bloccate)
            
        st.number_input("Max tentativi (0=∞):", 0, 50, key="widget_max_tentativi", on_change=update_shared_config, args=("max_tentativi",), disabled=impostazioni_bloccate)

    with col_players:
        st.subheader("👥 Ruoli")
        
        # Lettura sicura prima di estrarre low e high
        current_range = game.get("range_cifre", (1, 9))
        low = current_range[0] if isinstance(current_range, (tuple, list)) else 1
        high = current_range[1] if isinstance(current_range, (tuple, list)) else 9
        
        config_valida = low < high
        if not config_valida:
            st.error("Errore: Il valore Minimo deve essere inferiore al Massimo!")
            
        c1, c2 = st.columns(2)
        if c1.button("🟦 GIOCATORE 1", use_container_width=True, disabled=game["p1_preso"] or not config_valida):
            game["p1_preso"] = True
            st.session_state.ruolo = "Giocatore 1"
            st.rerun()
        if c2.button("🟥 GIOCATORE 2", use_container_width=True, disabled=game["p2_preso"] or not config_valida):
            game["p2_preso"] = True
            st.session_state.ruolo = "Giocatore 2"
            st.rerun()
    st.stop()

# --- GIOCO ATTIVO ---
ruolo = st.session_state.ruolo
n_cifre = game["n_cifre"]

# Lettura sicura del range per la fase di gioco attiva
current_range = game.get("range_cifre", (1, 9))
low = current_range[0] if isinstance(current_range, (tuple, list)) else 1
high = current_range[1] if isinstance(current_range, (tuple, list)) else 9

mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]

with st.sidebar:
    st.title(f"🎮 {ruolo}")
    if st.button("⬅️ Abbandona"):
        reset_game()
        del st.session_state.ruolo
        st.rerun()
    st.divider()
    if mia_chiave and st.checkbox("👁️ Mostra mia chiave"):
        st.info("".join([COLOR_MAP[c] for c in mia_chiave]) if game["modalita"] == "Colori" else f"Chiave: {mia_chiave}")

# FASE IMPOSTAZIONE CHIAVE
if mia_chiave is None:
    st.subheader(f"Imposta la tua chiave ({n_cifre} posizioni)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    
    if game["modalita"] == "Colori":
        cols = st.columns(high - low + 1)
        for i, val in enumerate(range(low, high + 1)):
            if cols[i].button(COLOR_MAP[str(val)], key=f"kset_{val}"):
                if len(st.session_state.temp_key) < n_cifre: st.session_state.temp_key += str(val)
        st.write(f"Selezione: {' '.join([COLOR_MAP[c] for c in st.session_state.temp_key])}")
        c1, c2 = st.columns(2)
        if c1.button("❌"): st.session_state.temp_key = ""
        if c2.button("✅") and len(st.session_state.temp_key) == n_cifre:
            if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
            else: game["p2_chiave"] = st.session_state.temp_key
            st.session_state.temp_key = ""
            st.rerun()
    else:
        with st.form("set_num"):
            k = st.text_input(f"Codice ({n_cifre} cifre tra {low} e {high}):", type="password")
            if st.form_submit_button("Conferma") and len(k) == n_cifre:
                if all(c.isdigit() and low <= int(c) <= high for c in k):
                    if ruolo == "Giocatore 1": game["p1_chiave"] = k
                    else: game["p2_chiave"] = k
                    st.rerun()
                else: st.error(f"Usa solo cifre comprese tra {low} e {high}!")
    st.stop()

# LOOP DI GIOCO
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.success(f"🏆 Vincitore: {game['vincitore']}!")
        if st.button("Nuova Partita"): reset_game()
        st.stop()

    col_gioco, col_stats = st.columns([1, 1])
    mio_turno = (game["turno"] == ruolo)

    with col_gioco:
        st.subheader(f"Turno: {game['turno']}")
        if "current_guess" not in st.session_state: st.session_state.current_guess = ""
        
        if game["modalita"] == "Colori":
            btn_cols = st.columns(high - low + 1)
            for i, val in enumerate(range(low, high + 1)):
                if btn_cols[i].button(COLOR_MAP[str(val)], key=f"gbtn_{val}", disabled=not mio_turno):
                    if len(st.session_state.current_guess) < n_cifre: st.session_state.current_guess += str(val)
            st.write(f"Tentativo: {' '.join([COLOR_MAP[c] for c in st.session_state.current_guess])}")
            c1, c2 = st.columns(2)
            if c1.button("🗑️", disabled=not mio_turno): st.session_state.current_guess = ""
            if c2.button("🚀 Invia", disabled=not (mio_turno and len(st.session_state.current_guess) == n_cifre)):
                target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                res = calcola_feedback(target, st.session_state.current_guess, n_cifre)
                if ruolo == "Giocatore 1":
                    game["p1_mosse"].insert(0, (st.session_state.current_guess, res)); game["turno"] = "Giocatore 2"
                else:
                    game["p2_mosse"].insert(0, (st.session_state.current_guess, res)); game["turno"] = "Giocatore 1"
                if res == "V" * n_cifre: game["vincitore"] = ruolo
                st.session_state.current_guess = ""
                st.rerun()
        else:
            with st.form("num_g"):
                g = st.text_input(f"Inserisci {n_cifre} cifre:", disabled=not mio_turno)
                if st.form_submit_button("Invia") and len(g) == n_cifre:
                    if all(c.isdigit() and low <= int(c) <= high for c in g):
                        target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                        res = calcola_feedback(target, g, n_cifre)
                        if ruolo == "Giocatore 1":
                            game["p1_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 2"
                        else:
                            game["p2_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 1"
                        if res == "V" * n_cifre: game["vincitore"] = ruolo
                        st.rerun()
                    else: st.error(f"Usa cifre nel range {low}-{high}!")

    with col_stats:
        t1, t2 = st.tabs(["Io", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        with t1:
            for m, r in mie:
                m_str = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.markdown(f"**{m_str}** → `{r}`")
        with t2:
            for m, r in avv: st.write(f"Esito avversario: `{r}`")
else:
    st.info("In attesa delle chiavi...")
