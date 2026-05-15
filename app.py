import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Ultimate 1vs1", layout="wide")
st_autorefresh(interval=3000, key="datarefresh")

# Mappa colori per la modalità grafica
COLOR_MAP = {
    "0": "🔴", "1": "🔵", "2": "🟢", "3": "🟡", 
    "4": "🟣", "5": "🟠", "6": "🟤", "7": "⚫", 
    "8": "⚪", "9": "🎨"
}

@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None,
        "configurato": False,
        "n_cifre": 5,
        "max_tentativi": 0, # Default Infinito
        "range_cifre": (0, 9),
        "modalita": "Numeri" # "Numeri" o "Colori"
    }

game = get_shared_game()

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

def reset_totale():
    for k in ["p1_chiave", "p2_chiave", "vincitore"]: game[k] = None
    game["p1_mosse"], game["p2_mosse"] = [], []
    game["turno"] = "Giocatore 1"
    game["configurato"] = False
    st.rerun()

# --- 1. CONFIGURAZIONE AVANZATA ---
if not game["configurato"]:
    st.markdown("<h1 style='text-align: center;'>⚙️ Impostazioni Sfida</h1>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        with st.container(border=True):
            mod = st.radio("Modalità di gioco:", ["Numeri", "Colori"], horizontal=True)
            n_cifre = st.slider("Lunghezza sequenza:", 3, 8, 5)
            
            c1, c2 = st.columns(2)
            with c1:
                start_digit = st.number_input("Cifra minima:", 0, 9, 0)
            with c2:
                end_digit = st.number_input("Cifra massima:", start_digit + 1, 9, 9)
            
            max_t = st.number_input("Tentativi massimi (0 = infiniti):", min_value=0, value=0)
            
            if st.button("🚀 INIZIA SFIDA", use_container_width=True):
                game.update({
                    "n_cifre": n_cifre, "max_tentativi": max_t,
                    "range_cifre": (start_digit, end_digit),
                    "modalita": mod, "configurato": True
                })
                st.rerun()
    st.stop()

# --- 2. SELEZIONE GIOCATORE ---
if "ruolo" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🕵️ Mastermind Online</h1>", unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns([1, 2, 1])
    with c_b:
        c1, c2 = st.columns(2)
        if c1.button("🟦 GIOCATORE 1", use_container_width=True):
            st.session_state.ruolo = "Giocatore 1"
            st.rerun()
        if c2.button("🟥 GIOCATORE 2", use_container_width=True):
            st.session_state.ruolo = "Giocatore 2"
            st.rerun()
    st.stop()

ruolo_utente = st.session_state.ruolo
low, high = game["range_cifre"]

# --- SIDEBAR ---
with st.sidebar:
    st.title(ruolo_utente)
    if st.button("⬅️ Esci"):
        del st.session_state.ruolo
        st.rerun()
    st.divider()
    st.write(f"Modo: **{game['modalita']}**")
    st.write(f"Cifre: **{game['n_cifre']}** (da {low} a {high})")
    if st.button("🗑️ Reset Totale"): reset_totale()
    
    mia_k = game["p1_chiave"] if ruolo_utente == "Giocatore 1" else game["p2_chiave"]
    if mia_k and st.checkbox("👁️ Mostra mia chiave"):
        if game["modalita"] == "Colori":
            st.write("".join([COLOR_MAP[c] for c in mia_k]))
        else:
            st.info(f"Chiave: {mia_k}")

# --- 3. IMPOSTAZIONE CHIAVI ---
if game["p1_chiave"] is None or game["p2_chiave"] is None:
    deve_impostare = (ruolo_utente == "Giocatore 1" and game["p1_chiave"] is None) or \
                     (ruolo_utente == "Giocatore 2" and game["p2_chiave"] is None)
    if deve_impostare:
        with st.form("set_k"):
            st.subheader("Imposta la tua chiave")
            st.caption(f"Usa cifre da {low} a {high}")
            if game["modalita"] == "Colori":
                st.info("💡 Associa i numeri ai colori: " + " ".join([f"{i}:{COLOR_MAP[str(i)]}" for i in range(low, high+1)]))
            k_in = st.text_input("Chiave:", type="password", max_chars=game["n_cifre"])
            if st.form_submit_button("Conferma"):
                if len(k_in) == game["n_cifre"] and all(low <= int(c) <= high for c in k_in if c.isdigit()):
                    if ruolo_utente == "Giocatore 1": game["p1_chiave"] = k_in
                    else: game["p2_chiave"] = k_in
                    st.rerun()
                else: st.error(f"Inserisci {game['n_cifre']} cifre nell'intervallo {low}-{high}!")
    else: st.warning("In attesa dell'avversario...")
    st.stop()

# --- 4. GIOCO ---
if game["vincitore"]:
    st.header(f"🏆 Vincitore: {game['vincitore']}!")
    if st.button("Nuova Partita"): reset_totale()
    st.stop()

mie_mosse = game["p1_mosse"] if ruolo_utente == "Giocatore 1" else game["p2_mosse"]
avv_mosse = game["p2_mosse"] if ruolo_utente == "Giocatore 1" else game["p1_mosse"]

col_in, col_viz = st.columns([1, 2])

with col_in:
    st.subheader(f"Turno: {game['turno']}")
    mio_turno = (ruolo_utente == game["turno"])
    
    with st.form("mossa", clear_on_submit=True):
        st.write(f"Inserisci {game['n_cifre']} cifre ({low}-{high})")
        if game["modalita"] == "Colori":
            cols = st.columns(len(range(low, high+1)))
            for idx, val in enumerate(range(low, high+1)):
                cols[idx % len(cols)].write(f"{val}:{COLOR_MAP[str(val)]}")
        
        guess = st.text_input("Tuo tentativo:", max_chars=game["n_cifre"], disabled=not mio_turno)
        if st.form_submit_button("INVIA", disabled=not mio_turno):
            if len(guess) == game["n_cifre"] and all(low <= int(c) <= high for c in guess if c.isdigit()):
                target = game["p2_chiave"] if ruolo_utente == "Giocatore 1" else game["p1_chiave"]
                res = calcola_feedback(target, guess, game["n_cifre"])
                if ruolo_utente == "Giocatore 1":
                    game["p1_mosse"].insert(0, (guess, res)); game["turno"] = "Giocatore 2"
                else:
                    game["p2_mosse"].insert(0, (guess, res)); game["turno"] = "Giocatore 1"
                if res == "V" * game["n_cifre"]: game["vincitore"] = ruolo_utente
                st.rerun()

with col_viz:
    t1, t2 = st.tabs(["I MIEI TENTATIVI", "AVVERSARIO"])
    def display_mossa(m):
        if game["modalita"] == "Colori":
            return "".join([COLOR_MAP[c] for c in m])
        return m

    with t1:
        for m, r in mie_mosse: st.markdown(f"### {display_mossa(m)}  →  `{r}`")
    with t2:
        for m, r in avv_mosse: st.write(f"Feedback avversario: `{r}`")
