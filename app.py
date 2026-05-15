import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione Iniziale
st.set_page_config(page_title="Mastermind Custom 1vs1", layout="wide")

# Auto-refresh ogni 3 secondi per la sincronizzazione
st_autorefresh(interval=3000, key="datarefresh")

@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None,
        "configurato": False,
        "n_cifre": 5,
        "max_tentativi": 10
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

# --- LOGICA DI RESET TOTALE ---
def reset_totale():
    for k in ["p1_chiave", "p2_chiave", "vincitore"]: game[k] = None
    game["p1_mosse"], game["p2_mosse"] = [], []
    game["turno"] = "Giocatore 1"
    game["configurato"] = False
    st.rerun()

# --- 1. SCHERMATA DI CONFIGURAZIONE REGOLE ---
if not game["configurato"]:
    st.markdown("<h1 style='text-align: center;'>⚙️ Configurazione Partita</h1>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        with st.container(border=True):
            st.write("Imposta le regole della sfida (valide per entrambi):")
            n_cifre = st.slider("Numero di cifre da indovinare", 3, 8, 5)
            max_t = st.number_input("Numero massimo di tentativi (0 = infiniti)", min_value=0, value=10)
            
            if st.button("🚀 SALVA E INIZIA", use_container_width=True):
                game["n_cifre"] = n_cifre
                game["max_tentativi"] = max_t
                game["configurato"] = True
                st.rerun()
    st.stop()

# --- 2. SELEZIONE GIOCATORE ---
if "ruolo" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🕵️ Mastermind Online 1vs1</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Sfida a {game['n_cifre']} cifre - Max {game['max_tentativi']} tentativi</p>", unsafe_allow_html=True)
    
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
    st.title(ruolo_utente)
    if st.button("⬅️ Cambia Ruolo"):
        del st.session_state.ruolo
        st.rerun()
    st.divider()
    st.write(f"🔢 Cifre: **{game['n_cifre']}**")
    st.write(f"🎯 Tentativi: **{game['max_tentativi'] if game['max_tentativi'] > 0 else '∞'}**")
    if st.button("🗑️ Reset Totale"):
        reset_totale()
    st.divider()
    mia_k = game["p1_chiave"] if ruolo_utente == "Giocatore 1" else game["p2_chiave"]
    if mia_k and st.checkbox("👁️ Mostra mia chiave"):
        st.info(f"Chiave: {mia_k}")

# --- 3. IMPOSTAZIONE CHIAVI ---
if game["p1_chiave"] is None or game["p2_chiave"] is None:
    deve_impostare = (ruolo_utente == "Giocatore 1" and game["p1_chiave"] is None) or \
                     (ruolo_utente == "Giocatore 2" and game["p2_chiave"] is None)
    if deve_impostare:
        with st.form("set_k"):
            st.subheader(f"Imposta chiave ({game['n_cifre']} cifre)")
            k_in = st.text_input("Chiave:", type="password", max_chars=game["n_cifre"])
            if st.form_submit_button("Conferma") and len(k_in) == game["n_cifre"] and k_in.isdigit():
                if ruolo_utente == "Giocatore 1": game["p1_chiave"] = k_in
                else: game["p2_chiave"] = k_in
                st.rerun()
            elif len(k_in) > 0: st.error(f"Inserisci {game['n_cifre']} cifre!")
    else:
        st.warning("In attesa dell'altro giocatore...")
    st.stop()

# --- 4. GIOCO ---
mie_mosse = game["p1_mosse"] if ruolo_utente == "Giocatore 1" else game["p2_mosse"]
avv_mosse = game["p2_mosse"] if ruolo_utente == "Giocatore 1" else game["p1_mosse"]

# Controllo Sconfitta per esaurimento tentativi
if game["max_tentativi"] > 0:
    if len(mie_mosse) >= game["max_tentativi"] and not game["vincitore"]:
        st.error("Hai esaurito i tentativi!")

if game["vincitore"]:
    st.header(f"🏆 Vincitore: {game['vincitore']}!")
    if st.button("Nuova Partita"): reset_totale()
    st.stop()

col_in, col_viz = st.columns([1, 2])

with col_in:
    st.subheader(f"Turno: {game['turno']}")
    mio_turno = (ruolo_utente == game["turno"])
    # Controllo se ho ancora tentativi
    tentativi_rimasti = True if game["max_tentativi"] == 0 else len(mie_mosse) < game["max_tentativi"]
    
    with st.form("mossa", clear_on_submit=True):
        guess = st.text_input("Tuo tentativo:", max_chars=game["n_cifre"], disabled=not (mio_turno and tentativi_rimasti))
        if st.form_submit_button("INVIA", disabled=not (mio_turno and tentativi_rimasti)):
            if len(guess) == game["n_cifre"] and guess.isdigit():
                target = game["p2_chiave"] if ruolo_utente == "Giocatore 1" else game["p1_chiave"]
                res = calcola_feedback(target, guess, game["n_cifre"])
                
                if ruolo_utente == "Giocatore 1":
                    game["p1_mosse"].insert(0, (guess, res))
                    game["turno"] = "Giocatore 2"
                else:
                    game["p2_mosse"].insert(0, (guess, res))
                    game["turno"] = "Giocatore 1"
                
                if res == "V" * game["n_cifre"]:
                    game["vincitore"] = ruolo_utente
                st.rerun()

with col_viz:
    t1, t2 = st.tabs(["I MIEI TENTATIVI", "AVVERSARIO"])
    with t1:
        if game["max_tentativi"] > 0:
            st.progress(len(mie_mosse)/game["max_tentativi"], f"Tentativi: {len(mie_mosse)}/{game['max_tentativi']}")
        for m, r in mie_mosse: st.code(f"{m} -> {r}")
    with t2:
        for m, r in avv_mosse: st.write(f"Mossa avversario: `{r}`")
