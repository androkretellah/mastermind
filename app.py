# --- FASE IMPOSTAZIONE CHIAVE ---
if mia_chiave is None:
    st.subheader(f"Imposta la tua chiave segreta ({n_cifre} posizioni)")
    if "temp_key" not in st.session_state: st.session_state.temp_key = ""
    
    if not game["ripetizione_ammessa"]:
        st.warning("⚠️ Nota: La ripetizione degli stessi elementi NON è consentita!")

    if game["modalita"] == "Colori":
        cols = st.columns(high - low + 1)
        for i, val in enumerate(range(low, high + 1)):
            val_str = str(val)
            
            # 1. Blocco visivo (Streamlit standard)
            bottone_disabilitato = (not game["ripetizione_ammessa"] and val_str in st.session_state.temp_key)
            
            if cols[i].button(COLOR_MAP[val_str], key=f"key_set_{val}", disabled=bottone_disabilitato):
                # 2. BLOCCO DI SICUREZZA ISTANTANEO (Anti-Click Veloce)
                # Se l'utente ha cliccato due volte velocemente prima del refresh, questo IF blocca il secondo inserimento
                if not game["ripetizione_ammessa"] and val_str in st.session_state.temp_key:
                    st.toast("⚠️ Non puoi ripetere questo colore!", icon="🚫")
                elif len(st.session_state.temp_key) < n_cifre:
                    st.session_state.temp_key += val_str
                    st.rerun() # Forza il refresh immediato per ridisegnare i bottoni come disabilitati
        
        st.markdown(f"### Selezione: {' '.join([COLOR_MAP[c] for c in st.session_state.temp_key])}")
        
        c1, c2 = st.columns(2)
        if c1.button("❌ Cancella"): 
            st.session_state.temp_key = ""
            st.rerun()
        if c2.button("✅ Conferma Chiave") and len(st.session_state.temp_key) == n_cifre:
            if ruolo == "Giocatore 1": game["p1_chiave"] = st.session_state.temp_key
            else: game["p2_chiave"] = st.session_state.temp_key
            st.session_state.temp_key = ""
            st.rerun()
