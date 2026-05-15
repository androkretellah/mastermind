import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Pro 1-9", layout="wide")
st_autorefresh(interval=1500, key="global_refresh")

# CSS CORRETTO: Nasconde le icone link senza bloccare i click
st.markdown("""
    <style>
    /* Nasconde l'icona del link (catena) accanto ai titoli */
    .header-anchor {
        display: none !important;
    }
    /* Impedisce che lo spazio dell'icona intercetti i click */
    [data-testid="stHeaderActionElements"] {
        display: none !important;
    }
    h1 a, h2 a, h3 a {
        display: none !important;
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
        game["range_cifre"] = (st.session_state["widget_min"], st.session_state["widget_max"])
    else:
        game[key] = st.session_state[f"widget_{key}"]

def sync_local_session():
    if "ruolo" not in st.session_state:
        for key in ["modalita", "n_cifre", "max_tentativi"]:
            st.session_state[f"widget_{key}"] = game.get(key)
        
        rng = game.get("range_cifre", (1, 9))
        st.session_state["widget_min"] = rng[0]
        st.session_state["widget_max"] = rng[1]

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
    pronto = game["p1_preso"] or game["p2_preso"]
    
    col_cfg, col_players = st.columns([1, 1])
    
    with col_cfg:
        st.subheader("⚙️ Regole")
        st.radio("Modalità", ["Colori", "Numeri"], key="widget_modalita", on_change=update_shared_config, args=("modalita",), horizontal=True, disabled=pronto)
        st.slider("Cifre", 3, 8, key="widget_n_cifre", on_change=update_shared_config, args=("n_cifre",), disabled=pronto)
        
        st.write("Range (1-9)")
        c_min, c_max = st.columns(2)
        with c_min:
            st.selectbox("Min", options=list(range(1, 9)), key="widget_min", on_change=update_shared_config, args=("range_cifre",), disabled=pronto)
        with c_max:
            st.selectbox("Max", options=list(range(2, 10)), key="widget_max", on_change=update_shared_config, args=("range_cifre",), disabled=pronto)

    with col_players:
        st.subheader("👥 Ruoli")
        low, high = game["range_cifre"]
        valido = low < high
        if not valido: st.error("Min deve essere < Max")
        
        c1, c2 = st.columns(2)
        if c1.button("🟦 GIOCATORE 1", use_container_width=True, disabled=game["p1_preso"] or not valido):
            game["p1_preso"] = True
            st.session_state.ruolo = "Giocatore 1"
            st.rerun()
        if c2.button("🟥 GIOCATORE 2", use_container_width=True, disabled=game["p2_preso"] or not valido):
            game["p2_preso"] = True
            st.session_state.ruolo = "Giocatore 2"
            st.rerun()
    st.stop()

# --- GIOCO ATTIVO ---
ruolo = st.session_state.ruolo
n_cifre = game["n_cifre"]
low, high = game["range_cifre"]
mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]

with st.sidebar:
    st.title(ruolo)
    if st.button("⬅️ Esci"):
        reset_game()
        del st.session_state.ruolo
        st.rerun()
    if mia_chiave and st.checkbox("Mostra chiave"):
        st.info("".join([COLOR_MAP[c] for c in mia_chiave]) if game["modalita"] == "Colori" else mia_chiave)

# IMPOSTAZIONE CHIAVE
if mia_chiave is None:
    st.subheader(f"Crea il tuo codice ({n_cifre} posizioni)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    
    if game["modalita"] == "Colori":
        btn_cols = st.columns(high - low + 1)
        for i, v in enumerate(range(low, high + 1)):
            if btn_cols[i].button(COLOR_MAP[str(v)], key=f"k_{v}"):
                if len(st.session_state.temp_key) < n_cifre: st.session_state.temp_key += str(v)
        st.write("Selezione:", "".join([COLOR_MAP[c] for c in st.session_state.temp_key]))
        if st.button("Conferma ✅") and len(st.session_state.temp_key) == n_cifre:
            if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
            else: game["p2_chiave"] = st.session_state.temp_key
            st.session_state.temp_key = ""
            st.rerun()
        if st.button("Cancella ❌"): st.session_state.temp_key = ""
    else:
        with st.form("num_key"):
            k = st.text_input("Codice:", type="password")
            if st.form_submit_button("Conferma") and len(k) == n_cifre:
                if ruolo == "Giocatore 1": game["p1_chiave"] = k
                else: game["p2_chiave"] = k
                st.rerun()
    st.stop()

# GIOCO
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.success(f"Vincitore: {game['vincitore']}")
        if st.button("Nuova Partita"): reset_game()
        st.stop()

    col_sx, col_dx = st.columns(2)
    turno_mio = (game["turno"] == ruolo)

    with col_sx:
        st.subheader(f"Turno: {game['turno']}")
        if "current_guess" not in st.session_state: st.session_state.current_guess = ""
        
        if game["modalita"] == "Colori":
            g_cols = st.columns(high - low + 1)
            for i, v in enumerate(range(low, high + 1)):
                if g_cols[i].button(COLOR_MAP[str(v)], key=f"g_{v}", disabled=not turno_mio):
                    if len(st.session_state.current_guess) < n_cifre: st.session_state.current_guess += str(v)
            st.write("Tentativo:", "".join([COLOR_MAP[c] for c in st.session_state.current_guess]))
            if st.button("Invia 🚀", disabled=not (turno_mio and len(st.session_state.current_guess) == n_cifre)):
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
            with st.form("guess_num"):
                g = st.text_input("Prova:", disabled=not turno_mio)
                if st.form_submit_button("Invia") and len(g) == n_cifre:
                    target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                    res = calcola_feedback(target, g, n_cifre)
                    if ruolo == "Giocatore 1":
                        game["p1_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 2"
                    else:
                        game["p2_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 1"
                    if res == "V" * n_cifre: game["vincitore"] = ruolo
                    st.rerun()

    with col_dx:
        t1, t2 = st.tabs(["Io", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        with t1:
            for m, r in mie:
                m_txt = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.write(f"{m_txt} -> `{r}`")
        with t2:
            for m, r in avv: st.write(f"Esito: `{r}`")
else:
    st.info("In attesa delle chiavi...")
