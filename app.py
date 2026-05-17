import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Pro 1-9", layout="wide")
st_autorefresh(interval=1500, key="global_refresh") # Refresh leggermente più veloce

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
    """Callback: quando un widget cambia, scrive nel game globale"""
    game[key] = st.session_state[f"widget_{key}"]

def sync_local_session():
    """Allinea i widget locali allo stato globale del game"""
    if "ruolo" not in st.session_state:
        for key in ["modalita", "n_cifre", "range_cifre", "max_tentativi"]:
            st.session_state[f"widget_{key}"] = game[key]

# Chiamiamo la sincronizzazione prima di renderizzare i widget
sync_local_session()

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
    st.title("🕵️ Mastermind Online 1-9")
    impostazioni_bloccate = game["p1_preso"] or game["p2_preso"]
    col_cfg, col_players = st.columns([1, 1], gap="large")
    
    with col_cfg:
        st.subheader("⚙️ Regole della Sfida")
        
        # Widget con on_change per aggiornare il game globale istantaneamente
        st.radio("Modalità:", ["Colori", "Numeri"], 
                 key="widget_modalita", on_change=update_shared_config, args=("modalita",),
                 horizontal=True, disabled=impostazioni_bloccate)
        
        st.slider("Lunghezza sequenza:", 3, 8, 
                  key="widget_n_cifre", on_change=update_shared_config, args=("n_cifre",),
                  disabled=impostazioni_bloccate)
        
        st.select_slider("Intervallo cifre/colori:", options=list(range(1, 10)), 
                         key="widget_range_cifre", on_change=update_shared_config, args=("range_cifre",),
                         disabled=impostazioni_bloccate)
        
        st.number_input("Max tentativi (0=∞):", 0, 50, 
                        key="widget_max_tentativi", on_change=update_shared_config, args=("max_tentativi",),
                        disabled=impostazioni_bloccate)
        
        if impostazioni_bloccate:
            st.warning("🔒 Impostazioni bloccate da un giocatore.")

    with col_players:
        st.subheader("👥 Scegli il tuo Ruolo")
        low, high = game["range_cifre"]
        config_valida = low < high
        
        if not config_valida:
            st.error("Seleziona un intervallo valido (min < max)!")
        
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
low, high = game["range_cifre"]

with st.sidebar:
    st.title(f"🎮 {ruolo}")
    if st.button("⬅️ Esci (Resetta Stanza)"):
        reset_game()
        del st.session_state.ruolo
        st.rerun()
    st.divider()
    mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]
    if mia_chiave and st.checkbox("👁️ Mostra mia chiave"):
        st.info("".join([COLOR_MAP[c] for c in mia_chiave]) if game["modalita"] == "Colori" else f"Chiave: {mia_chiave}")

# --- FASE CHIAVE E GIOCO (Stesso codice precedente, coerente con le nuove variabili) ---
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

# --- LOOP DI GIOCO ---
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.success(f"🏆 VINCITORE: {game['vincitore']}!")
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
            # Implementazione numerica omessa per brevità (identica a prima)
            pass
