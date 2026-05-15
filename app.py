import streamlit as st

# 1. Database condiviso (Stato del Server)
@st.cache_resource
def get_shared_game():
    return {
        "p1_chiave": None,
        "p2_chiave": None,
        "p1_mosse": [],
        "p2_mosse": [],
        "turno": "Giocatore 1",
        "vincitore": None
    }

game = get_shared_game()

def calcola_feedback(chiave, tentativo):
    usato_chiave, usato_tentativo = [False]*5, [False]*5
    v, o = 0, 0
    for i in range(5):
        if tentativo[i] == chiave[i]:
            v += 1
            usato_chiave[i] = usato_tentativo[i] = True
    for i in range(5):
        if not usato_tentativo[i]:
            for j in range(5):
                if not usato_chiave[j] and tentativo[i] == chiave[j]:
                    o += 1
                    usato_chiave[j] = True
                    break
    return ('V' * v) + ('O' * o)

st.set_page_config(page_title="Mastermind 1vs1 Sincrono", layout="wide")
st.title("⚔️ Mastermind: La Sfida")

# Sidebar per Reset e Info
with st.sidebar:
    if st.button("🗑️ Reset Totale Sfida"):
        for k in game: game[k] = None
        game["p1_mosse"], game["p2_mosse"] = [], []
        game["turno"] = "Giocatore 1"
        st.rerun()
    st.write("---")
    st.info("Regole: Impostate le chiavi, poi alternatevi i tentativi. Il primo che arriva a VVVVV vince!")

# FASE 1: Configurazione Chiavi
if game["p1_chiave"] is None or game["p2_chiave"] is None:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Giocatore 1")
        k1 = st.text_input("Imposta chiave per G2:", type="password", key="set_k1")
        if st.button("Conferma Chiave G1") and len(k1)==5:
            game["p1_chiave"] = k1
            st.success("Chiave G1 salvata!")
            st.rerun()
    with col2:
        st.subheader("Giocatore 2")
        k2 = st.text_input("Imposta chiave per G1:", type="password", key="set_k2")
        if st.button("Conferma Chiave G2") and len(k2)==5:
            game["p2_chiave"] = k2
            st.success("Chiave G2 salvata!")
            st.rerun()
    st.stop()

# FASE 2: Gioco Sincrono
if game["vincitore"]:
    st.balloons()
    st.success(f"🏆 IL VINCITORE È {game['vincitore']}!")
else:
    st.subheader(f"C'est le tour de: **{game['turno']}**")

col_g1, col_g2 = st.columns(2)

# --- GIOCATORE 1 ---
with col_g1:
    st.markdown("### 🟦 Giocatore 1")
    st.caption("Obiettivo: Indovinare la chiave di G2")
    if game["turno"] == "Giocatore 1" and not game["vincitore"]:
        with st.form("form_g1", clear_on_submit=True):
            t1 = st.text_input("Tuo tentativo:")
            if st.form_submit_button("Invia") and len(t1)==5:
                res = calcola_feedback(game["p2_chiave"], t1)
                game["p1_mosse"].insert(0, (t1, res))
                if res == "VVVVV": game["vincitore"] = "Giocatore 1"
                game["turno"] = "Giocatore 2"
                st.rerun()
    
    for m, r in game["p1_mosse"]:
        st.text(f"{m} -> {r}")

# --- GIOCATORE 2 ---
with col_g2:
    st.markdown("### 🟥 Giocatore 2")
    st.caption("Obiettivo: Indovinare la chiave di G1")
    if game["turno"] == "Giocatore 2" and not game["vincitore"]:
        with st.form("form_g2", clear_on_submit=True):
            t2 = st.text_input("Tuo tentativo:")
            if st.form_submit_button("Invia") and len(t2)==5:
                res = calcola_feedback(game["p1_chiave"], t2)
                game["p2_mosse"].insert(0, (t2, res))
                if res == "VVVVV": game["vincitore"] = "Giocatore 2"
                game["turno"] = "Giocatore 1"
                st.rerun()
    
    for m, r in game["p2_mosse"]:
        st.text(f"{m} -> {r}")

if st.button("🔄 Aggiorna Schermo"):
    st.rerun()
