import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Pro 1-9", layout="wide")
st_autorefresh(interval=2000, key="global_refresh")

COLOR_MAP = {
    "1": "🔴", "2": "🔵", "3": "🟢", "4": "🟡", 
    "5": "🟣", "6": "🟠", "7": "🟤", "8": "⚫", 
    "9": "⚪"
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

# --- LOGICA DI SINCRONIZZAZIONE ROBUSTA ---
def sync_lobby():
    # Definiamo i default nel caso qualcosa manchi
    defaults = {
        "modalita": "Colori",
        "n_cifre": 4,
        "range_cifre": (1, 9),
        "max_tentativi": 0
    }
    
    for key, def_val in defaults.items():
        sess_key = f"lobby_{key}"
        # Se il widget è stato toccato, aggiorna il server
        if sess_key in st.session_state:
            game[key] = st.session_state[sess_key]
        # Altrimenti, inizializza la sessione col valore del server o il default
        else:
            st.session_state[sess_key] = game.get(key, def_val)

if "ruolo" not in st.session_state:
    sync_lobby()

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
    for k in ["lobby_modalita", "lobby_n_cifre", "lobby_range_cifre", "lobby_max_tentativi"]:
        if k in st.session_state: del st.session_state[k]

# --- DISCONNESSIONE FORZATA ---
if "ruolo" in st.session_state:
    if (st.session_state.ruolo == "Giocatore 1" and not game["p1_preso"]) or \
       (st.session_state.ruolo == "Giocatore 2" and not game["p2_preso"]):
        del st.session_state.ruolo
        st.rerun()

# --- LOBBY ---
if "ruolo" not in st.session_state:
    st.title("🕵️ Mastermind Online 1-9")
    impostazioni_bloccate = game["p1_preso"] or game["p2_preso"]
    col_cfg, col_players = st.columns([1, 1], gap="large")
    
    with col_cfg:
        st.subheader("⚙️ Regole della Sfida")
        st.radio("Modalità:", ["Colori", "Numeri"], key="lobby_modalita", horizontal=True, disabled=impostazioni_bloccate)
        st.slider("Lunghezza sequenza:", 3, 8, key="lobby_n_cifre", disabled=impostazioni_bloccate)
        st.select_slider("Intervallo cifre/colori:", options=list(range(1, 10)), key="lobby_range_cifre", disabled=impostazioni_bloccate)
        st.number_input("Max tentativi (0=∞):", 0, 50, key="lobby_max_tentativi", disabled=impostazioni_bloccate)
        if impostazioni_bloccate: st.warning("🔒 Impostazioni bloccate.")

    with col_players:
        st.subheader("👥 Scegli il tuo Ruolo")
        # Estrazione sicura del range
        current_range = game.get("range_cifre", (1, 9))
        r_min, r_max = current_range if isinstance(current_range, (list, tuple)) else (1, 9)
        
        config_valida = r_min < r_max
        if not config_valida: st.error("Seleziona almeno due valori!")
        
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
n_cifre = game.get("n_cifre", 4)
# Estrazione sicura del range per la fase di gioco
current_range = game.get("range_cifre", (1, 9))
low, high = current_range if isinstance(current_range, (list, tuple)) else (1, 9)

with st.sidebar:
    st.title(f"🎮 {ruolo}")
    if st.button("⬅️ Cambia Ruolo / Esci"):
        reset_game()
        del st.session_state.ruolo
        st.rerun()
    st.divider()
    if st.button("🗑️ Reset Totale"): 
        reset_game()
        st.rerun()
    
    mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]
    if mia_chiave and st.checkbox("👁️ Mostra mia chiave"):
        st.info("".join([COLOR_MAP[c] for c in mia_chiave]) if game["modalita"] == "Colori" else f"Chiave: {mia_chiave}")

# --- FASE CHIAVE ---
if mia_chiave is None:
    st.subheader(f"Imposta la tua chiave ({n_cifre} posizioni)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    
    if game["modalita"] == "Colori":
        cols = st.columns(high - low + 1)
        for i, val in enumerate(range(low, high + 1)):
            if cols[i].button(COLOR_MAP[str(val)], key=f"kset_{val}"):
                if len(st.session_state.temp_key) < n_cifre: st.session_state.temp_key += str(val)
        st.markdown(f"### Selezione: {' '.join([COLOR_MAP[c] for c in st.session_state.temp_key])}")
        c1, c2 = st.columns(2)
        if c1.button("❌ Cancella"): st.session_state.temp_key = ""
        if c2.button("✅ Conferma") and len(st.session_state.temp_key) == n_cifre:
            if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
            else: game["p2_chiave"] = st.session_state.temp_key
            st.session_state.temp_key = ""
            st.rerun()
    else:
        with st.form("set_numeric_key"):
            k = st.text_input(f"Range {low}-{high}:", type="password", max_chars=n_cifre)
            if st.form_submit_button("Conferma") and len(k) == n_cifre:
                if all(c.isdigit() and low <= int(c) <= high for c in k):
                    if ruolo == "Giocatore 1": game["p1_chiave"] = k
                    else: game["p2_chiave"] = k
                    st.rerun()
    st.stop()

# --- GIOCO ---
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.success(f"🏆 VINCITORE: {game['vincitore']}!")
        if st.button("Ricomincia"): reset_game(); st.rerun()
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
            st.markdown(f"### Tentativo: {' '.join([COLOR_MAP[c] for c in st.session_state.current_guess])}")
            c1, c2 = st.columns(2)
            if c1.button("🗑️ Reset", disabled=not mio_turno): st.session_state.current_guess = ""
            if c2.button("🚀 INVIA", use_container_width=True, disabled=not (mio_turno and len(st.session_state.current_guess) == n_cifre)):
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
            with st.form("num_guess", clear_on_submit=True):
                g = st.text_input("Mossa:", max_chars=n_cifre, disabled=not mio_turno)
                if st.form_submit_button("Invia") and len(g) == n_cifre:
                    target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                    res = calcola_feedback(target, g, n_cifre)
                    if ruolo == "Giocatore 1":
                        game["p1_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 2"
                    else:
                        game["p2_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 1"
                    if res == "V" * n_cifre: game["vincitore"] = ruolo
                    st.rerun()

    with col_stats:
        t1, t2 = st.tabs(["Mie Mosse", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        with t1:
            for m, r in mie:
                m_str = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.markdown(f"#### {m_str} ➔ `{r}`")
        with t2:
            for m, r in avv: st.write(f"Mossa avversario: `{r}`")
else:
    st.info("In attesa delle chiavi...")
