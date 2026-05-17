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
        "p1_preso": False, "p2_preso": False,
        "p1_chiave": None, "p2_chiave": None,
        "p1_mosse": [], "p2_mosse": [],
        "turno": "Giocatore 1", "vincitore": None,
        "n_cifre": 4, "max_tentativi": 0,
        "range_cifre": (1, 9), 
        "modalita": "Colori",
        "ripetizione_ammessa": True
    }

game = get_shared_game()

# --- CALCOLO FEEDBACK CON EMOJI ---
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
    return ('✅' * v) + ('⚪' * o)

def reset_game():
    for k in ["p1_chiave", "p2_chiave", "vincitore"]: game[k] = None
    game.update({
        "p1_mosse": [], "p2_mosse": [], 
        "turno": "Giocatore 1", 
        "p1_preso": False, 
        "p2_preso": False
    })

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
        
        def on_modalita_change():
            game["modalita"] = st.session_state[f"radio_mod_{game['modalita']}"]
        def on_cifre_change():
            game["n_cifre"] = st.session_state[f"slider_cifre_{game['n_cifre']}"]
        def on_range_change():
            game["range_cifre"] = st.session_state[f"slider_rng_{game['range_cifre'][0]}_{game['range_cifre'][1]}"]
        def on_tentativi_change():
            game["max_tentativi"] = st.session_state[f"num_tent_{game['max_tentativi']}"]
        def on_ripetizione_change():
            game["ripetizione_ammessa"] = st.session_state[f"chk_rip_{game['ripetizione_ammessa']}"]

        st.radio("Modalità:", ["Colori", "Numeri"], index=0 if game["modalita"] == "Colori" else 1, key=f"radio_mod_{game['modalita']}", on_change=on_modalita_change, disabled=impostazioni_bloccate)
        st.slider("Lunghezza sequenza:", 3, 8, value=game["n_cifre"], key=f"slider_cifre_{game['n_cifre']}", on_change=on_cifre_change, disabled=impostazioni_bloccate)
        st.write("Intervallo cifre/colori consentiti:")
        r_min, r_max = st.select_slider("Seleziona Min e Max:", options=list(range(1, 10)), value=game["range_cifre"], key=f"slider_rng_{game['range_cifre'][0]}_{game['range_cifre'][1]}", on_change=on_range_change, disabled=impostazioni_bloccate)
        st.number_input("Max tentativi (0=∞):", 0, 50, value=game["max_tentativi"], key=f"num_tent_{game['max_tentativi']}", on_change=on_tentativi_change, disabled=impostazioni_bloccate)
        st.checkbox("Permetti ripetizione di simboli/numeri uguali nella chiave", value=game["ripetizione_ammessa"], key=f"chk_rip_{game['ripetizione_ammessa']}", on_change=on_ripetizione_change, disabled=impostazioni_bloccate)

    with col_players:
        st.subheader("👥 Stato Stanza")
        config_valida = game["range_cifre"][0] < game["range_cifre"][1]
        elementi_disponibili = game["range_cifre"][1] - game["range_cifre"][0] + 1
        
        if not game["ripetizione_ammessa"] and game["n_cifre"] > elementi_disponibili:
            config_valida = False
            st.error(f"Errore: Senza ripetizioni, la lunghezza della sequenza ({game['n_cifre']}) non può superare il numero di elementi disponibili ({elementi_disponibili})!")
        elif not config_valida:
            st.error("Errore: Seleziona almeno due valori diversi nel range!")

        st.write(f"Giocatore 1: {'🟢 Pronto' if game['p1_preso'] else '⚪ Libero'}")
        st.write(f"Giocatore 2: {'🟢 Pronto' if game['p2_preso'] else '⚪ Libero'}")
        st.write("")
        
        if not game["p1_preso"]:
            testo_bottone, ruolo_assegnato, disabilitato = "🚪 ENTRA COME GIOCATORE 1", "Giocatore 1", False
        elif not game["p2_preso"]:
            testo_bottone, ruolo_assegnato, disabilitato = "🚪 ENTRA COME GIOCATORE 2", "Giocatore 2", False
        else:
            testo_bottone, ruolo_assegnato, disabilitato = "❌ STANZA PIENA", None, True
            
        if st.button(testo_bottone, use_container_width=True, disabled=disabilitato or not config_valida):
            if ruolo_assegnato == "Giocatore 1":
                game["p1_preso"] = True
                st.session_state.ruolo = "Giocatore 1"
            elif ruolo_assegnato == "Giocatore 2":
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
    if mia_chiave and st.checkbox("👁️ Mostra mia chiave"):
        if game["modalita"] == "Colori":
            st.info("".join([COLOR_MAP[c] for c in mia_chiave]))
        else:
            st.info(f"Chiave: {mia_chiave}")

# --- FASE IMPOSTAZIONE CHIAVE ---
if mia_chiave is None:
    st.subheader(f"Imposta la tua chiave segreta ({n_cifre} posizioni)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    if "errore_chiave" not in st.session_state: st.session_state.errore_chiave = ""
    
    if not game["ripetizione_ammessa"]:
        st.warning("⚠️ Nota: La ripetizione degli stessi elementi NON è consentita!")

    if st.session_state.errore_chiave:
        st.error(st.session_state.errore_chiave)

    if game["modalita"] == "Colori":
        cols = st.columns(high - low + 1)
        for i, val in enumerate(range(low, high + 1)):
            val_str = str(val)
            bottone_disabilitato = (not game["ripetizione_ammessa"] and val_str in st.session_state.temp_key)
            
            if cols[i].button(COLOR_MAP[val_str], key=f"key_set_{val}", disabled=bottone_disabilitato):
                st.session_state.errore_chiave = ""
                if not game["ripetizione_ammessa"] and val_str in st.session_state.temp_key:
                    pass 
                elif len(st.session_state.temp_key) < n_cifre:
                    st.session_state.temp_key += val_str
                    st.rerun()
        
        st.markdown(f"### Selezione: {' '.join([COLOR_MAP[c] for c in st.session_state.temp_key])}")
        
        c1, c2 = st.columns(2)
        if c1.button("❌ Cancella"): 
            st.session_state.temp_key = ""
            st.session_state.errore_chiave = ""
            st.rerun()
        if c2.button("✅ Conferma Chiave") and len(st.session_state.temp_key) == n_cifre:
            if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
            else: game["p2_chiave"] = st.session_state.temp_key
            st.session_state.temp_key = ""
            st.session_state.errore_chiave = ""
            st.rerun()
    else:
        with st.form("set_numeric_key"):
            k = st.text_input(f"Digita {n_cifre} cifre (range {low}-{high}):", type="password", max_chars=n_cifre)
            if st.form_submit_button("Conferma") and len(k) == n_cifre:
                if all(c.isdigit() and low <= int(c) <= high for c in k):
                    if not game["ripetizione_ammessa"] and len(set(k)) != len(k):
                        st.session_state.errore_chiave = "Errore: Ci sono cifre ripetute, ma le ripetizioni sono disattivate!"
                        st.rerun()
                    else:
                        if ruolo == "Giocatore 1": game["p1_chiave"] = k
                        else: game["p2_chiave"] = k
                        st.session_state.errore_chiave = ""
                        st.rerun()
                else:
                    st.session_state.errore_chiave = f"Usa cifre tra {low} e {high}!"
                    st.rerun()
    st.stop()

# --- FASE DI GIOCO ATTIVA ---
if game["p1_chiave"] and game["p2_chiave"]:
    col_gioco, col_stats = st.columns([1, 1])
    mio_turno = (game["turno"] == ruolo)
    
    if "errore_gioco" not in st.session_state: st.session_state.errore_gioco = ""

    with col_gioco:
        if game["vincitore"]:
            st.success(f"🏆 IL VINCITORE È {game['vincitore']}!")
            if st.button("Ricomincia (Nuova Partita)", use_container_width=True): 
                reset_game()
                st.rerun()
        else:
            st.subheader(f"Turno attuale: {game['turno']}")
            if mio_turno:
                st.info("🟢 È il tuo turno! Componi e invia la sequenza.")
            else:
                st.warning("⏳ Turno dell'avversario. Puoi portarti avanti preparando la sequenza.")

            if st.session_state.errore_gioco:
                st.error(st.session_state.errore_gioco)

            if "current_guess" not in st.session_state: st.session_state.current_guess = ""
            
            if game["modalita"] == "Colori":
                st.write("Tastierino colori:")
                btn_cols = st.columns(high - low + 1)
                for i, val in enumerate(range(low, high + 1)):
                    val_str = str(val)
                    bottone_disabilitato = (not game["ripetizione_ammessa"] and val_str in st.session_state.current_guess)
                    
                    if btn_cols[i].button(COLOR_MAP[val_str], key=f"btn_g_{val}", disabled=bottone_disabilitato):
                        st.session_state.errore_gioco = ""
                        if not game["ripetizione_ammessa"] and val_str in st.session_state.current_guess:
                            pass
                        elif len(st.session_state.current_guess) < n_cifre:
                            st.session_state.current_guess += val_str
                            st.rerun()
                
                st.markdown(f"### Tentativo in preparazione: {' '.join([COLOR_MAP[c] for c in st.session_state.current_guess])}")
                
                c1, c2 = st.columns(2)
                if c1.button("🗑️ Reset"): 
                    st.session_state.current_guess = ""
                    st.session_state.errore_gioco = ""
                    st.rerun()
                
                if c2.button("🚀 INVIA MOSSA", use_container_width=True, disabled=not (mio_turno and len(st.session_state.current_guess) == n_cifre)):
                    target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                    res = calcola_feedback(target, st.session_state.current_guess, n_cifre)
                    if ruolo == "Giocatore 1":
                        game["p1_mosse"].insert(0, (st.session_state.current_guess, res)); game["turno"] = "Giocatore 2"
                    else:
                        game["p2_mosse"].insert(0, (st.session_state.current_guess, res)); game["turno"] = "Giocatore 1"
                    if res == "✅" * n_cifre: game["vincitore"] = ruolo
                    st.session_state.current_guess = ""
                    st.session_state.errore_gioco = ""
                    st.rerun()
            else:
                g = st.text_input(f"Inserisci {n_cifre} cifre:", value=st.session_state.current_guess, max_chars=n_cifre)
                st.session_state.current_guess = g
                
                c1, c2 = st.columns(2)
                if c1.button("🗑️ Cancella tutto"):
                    st.session_state.current_guess = ""
                    st.session_state.errore_gioco = ""
                    st.rerun()
                    
                if c2.button("Invia", disabled=not (mio_turno and len(g) == n_cifre)):
                    if all(c.isdigit() and low <= int(c) <= high for c in g):
                        if not game["ripetizione_ammessa"] and len(set(g)) != len(g):
                            st.session_state.errore_gioco = "L'avversario ha impostato 'No Ripetizioni'. Inserisci cifre uniche!"
                            st.rerun()
                        else:
                            target = game["p2_chiave"] if ruolo == "Giocatore 1" else game["p1_chiave"]
                            res = calcola_feedback(target, g, n_cifre)
                            if ruolo == "Giocatore 1":
                                game["p1_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 2"
                            else:
                                game["p2_mosse"].insert(0, (g, res)); game["turno"] = "Giocatore 1"
                            if res == "✅" * n_cifre: game["vincitore"] = ruolo
                            st.session_state.current_guess = ""
                            st.session_state.errore_gioco = ""
                            st.rerun()
                    else:
                        st.session_state.errore_gioco = "Input non valido! Controlla i limiti impostati."
                        st.rerun()

    # --- FIX CRONOLOGIA AVVERSARIO ---
    with col_stats:
        st.subheader("📊 Cronologia Partita")
        t1, t2 = st.tabs(["Mie Mosse", "Avversario"])
        mie = game["p1_mosse"] if ruolo == "Giocatore 1" else game["p2_mosse"]
        avv = game["p2_mosse"] if ruolo == "Giocatore 1" else game["p1_mosse"]
        
        with t1:
            for m, r in mie:
                m_str = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.markdown(f"#### {m_str} ➔ {r}")
        with t2:
            for m, r in avv:
                # MODIFICA: Adesso anche per l'avversario formattiamo correttamente la mossa prima del feedback 'r'
                m_str = "".join([COLOR_MAP[c] for c in m]) if game["modalita"] == "Colori" else m
                st.markdown(f"#### {m_str} ➔ {r}")
else:
    st.info("In attesa che entrambi i giocatori impostino la propria chiave...")
