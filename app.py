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

# --- SINCRONIZZAZIONE STATO INTERFACCIA (LOBBY) ---
# Questo blocco garantisce che le modifiche di un giocatore sovrascrivano lo stato locale dell'altro
if "ruolo" not in st.session_state:
    for opzione in ["modalita", "n_cifre", "range_cifre", "max_tentativi"]:
        if f"lobby_{opzione}" in st.session_state:
            # Se l'utente locale ha modificato il widget, aggiorna il server condiviso
            game[opzione] = st.session_state[f"lobby_{opzione}"]
        else:
            # Altrimenti (primo accesso o aggiornamento passivo), scarica il valore dal server condiviso
            st.session_state[f"lobby_{opzione}"] = game[opzione]

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
    # Resetta anche le chiavi di sessione temporanee della lobby
    for opzione in ["modalita", "n_cifre", "range_cifre", "max_tentativi"]:
        if f"lobby_{opzione}" in st.session_state:
            del st.session_state[f"lobby_{opzione}"]

# --- CONTROLLO SINCRONIZZAZIONE DISCONNESSI ---
if "ruolo" in st.session_state:
    if st.session_state.ruolo == "Giocatore 1" and not game["p1_preso"]:
        del st.session_state.ruolo
        st.rerun()
    elif st.session_state.ruolo == "Giocatore 2" and not game["p2_preso"]:
        del st.session_state.ruolo
        st.rerun()

# --- LOBBY UNIFICATA ---
if "ruolo" not in st.session_state:
    st.title("🕵️ Mastermind Online 1-9")
    
    impostazioni_bloccate = game["p1_preso"] or game["p2_preso"]
    
    col_cfg, col_players = st.columns([1, 1], gap="large")
    
    with col_cfg:
        st.subheader("⚙️ Regole della Sfida")
        
        # Sincronizzazione dinamica tramite la chiave 'on_change' implicitamente legata a st.session_state
        st.radio("Modalità:", ["Colori", "Numeri"], key="lobby_modalita", horizontal=True, disabled=impostazioni_bloccate)
        st.slider("Lunghezza sequenza:", 3, 8, key="lobby_n_cifre", disabled=impostazioni_bloccate)
        
        st.write("Intervallo cifre/colori consentiti:")
        st.select_slider(
            "Seleziona Min e Max:",
            options=list(range(1, 10)),
            key="lobby_range_cifre",
            disabled=impostazioni_bloccate
        )
        st.number_input("Max tentativi (0=∞):", 0, 50, key="lobby_max_tentativi", disabled=impostazioni_bloccate)

        if impostazioni_bloccate:
            st.warning("🔒 Impostazioni bloccate da un giocatore pronto.")

    with col_players:
        st.subheader("👥 Scegli il tuo Ruolo")
        c1, c2 = st.columns(2)
        
        r_min, r_max = game["range_cifre"]
        config_valida = r_min < r_max
        if not config_valida:
            st.error("Errore: Seleziona almeno due valori diversi nello slider!")
        
        if c1.button("🟦 GIOCATORE 1", use_container_width=True, disabled=game["p1_preso"] or not config_valida):
            game["p1_preso"] = True
            st.session_state.ruolo = "Giocatore 1"
            st.rerun()
        if c2.button("🟥 GIOCATORE 2", use_container_width=True, disabled=game["p2_preso"] or not config_valida):
            game["p2_preso"] = True
            st.session_state.ruolo = "Giocatore 2"
            st.rerun()
    st.stop()

# --- VARIABILI DI GIOCO ATTIVE ---
ruolo = st.session_state.ruolo
n_cifre = game["n_cifre"]
low, high = game["range_cifre"]

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
    st.divider()
    
    mia_chiave = game["p1_chiave"] if ruolo == "Giocatore 1" else game["p2_chiave"]
    if mia_chiave:
        if st.checkbox("👁️ Mostra mia chiave"):
            if game["modalita"] == "Colori":
                st.info("".join([COLOR_MAP[c] for c in mia_chiave]))
            else:
                st.info(f"Chiave: {mia_chiave}")

# --- FASE IMPOSTAZIONE CHIAVE ---
if mia_chiave is None:
    st.subheader(f"Imposta la tua chiave segreta ({n_cifre} posizioni)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    
    if game["modalita"] == "Colori":
        cols = st.columns(high - low + 1)
        for i, val in enumerate(range(low, high + 1)):
            if cols[i].button(COLOR_MAP[str(val)], key=f"key_set_{val}"):
                if len(st.session_state.temp_key) < n_cifre:
                    st.session_state.temp_key += str(val)
        
        st.markdown(f"### Selezione: {' '.join([COLOR_MAP[c] for c in st.session_state.temp_key])}")
        
        c1, c2 = st.columns(2)
        if c1.button("❌ Cancella"): st.session_state.temp_key = ""
        if c2.button("✅ Conferma Chiave") and len(st.session_state.temp_key) == n_cifre:
            if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
            else: game["p2_chiave"] = st.session_state.temp_key
            st.session_state.temp_key = ""
            st.rerun()
    else:
        with st.form("set_numeric_key"):
            k = st.text_input(f"Digita {n_cifre} cifre (range {low}-{high}):", type="password", max_chars=n_cifre)
            if st.form_submit_button("Conferma") and len(k) == n_cifre:
                if all(c.isdigit() and low <= int(c) <= high for c in k):
                    if ruolo == "Giocatore 1": game["p1_chiave"] = k
                    else: game["p2_chiave"] = k
                    st.rerun()
                else: st.error(f"Usa cifre tra {low} e {high}!")
    st.stop()

# --- FASE DI GIOCO ---
if game["p1_chiave"] and game["p2_chiave"]:
    if game["vincitore"]:
        st.success(f"🏆 IL VINCITORE È {game['vincitore']}!")
        if st.button("Ricomincia (Nuova Partita)"): 
            reset_game()
            st.rerun()
        st.stop()

    col_gioco, col_stats = st.columns([1, 1])
    mio_turno = (game["turno"] == ruolo)

    with col_gioco:
        st.subheader(f"Turno: {game['turno']}")
        if "current_guess" not in st.session_state: st.session_state.current_guess = ""
        
        if game["modalita"] == "Colori":
            st.write("Tastierino colori:")
            btn_cols = st.columns(high - low + 1)
            for i, val in enumerate(range(low, high + 1)):
                if btn_cols[i].button(COLOR_MAP[str(val)], key=f"btn_g_{val}", disabled=not mio_turno):
                    if len(st.session_state.current_guess) < n_cifre:
                        st.session_state.current_guess += str(val)
            
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
                g = st.text_input(f"Inserisci {n_cifre} cifre:", max_chars=n_cifre, disabled=not mio_turno)
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
                    else: st.error("Input non valido!")

    with col_stats:
        t1, t2 = st.tabs(["Mie Mosse", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        
        with t1:
            for m, r in mie:
                m_str = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.markdown(f"#### {m_str} ➔ `{r}`")
        with t2:
            for m, r in avv:
                st.write(f"Mossa avversario: `{r}`")
else:
    st.info("In attesa che entrambi i giocatori impostino la propria chiave...")
