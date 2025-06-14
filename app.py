import streamlit as st
import yaml
import os
import glob

st.set_page_config(page_title="Daytrading Signalgenerator", layout="centered")

STRATEGIE_PFAD = "strategien"

@st.cache_data
def lade_strategien(pfad):
    strategien = {}
    for file in glob.glob(os.path.join(pfad, "*.yaml")):
        with open(file, "r", encoding="utf-8") as f:
            try:
                inhalt = yaml.safe_load(f)
                name = inhalt.get("Strategie_Name", os.path.basename(file))
                strategien[name] = inhalt
            except yaml.YAMLError as e:
                st.error(f"Fehler in {file}: {e}")
    return strategien

strategien = lade_strategien(STRATEGIE_PFAD)

st.title("📊 Daytrading Signalgenerator")

if not strategien:
    st.warning("Keine Strategien gefunden.")
else:
    auswahl = st.selectbox("Wähle eine Strategie:", list(strategien.keys()))
    strat = strategien[auswahl]

    st.subheader(f"Strategie: {strat['Strategie_Name']}")
    st.markdown(f"**Beschreibung:** {strat.get('Beschreibung', 'Keine Beschreibung vorhanden.')}")

    indikatorwerte = {}
    st.markdown("### Eingabe aktueller Indikatorwerte")
    with st.form("indikator_eingabe"):
        for indikator, details in strat.get("Indikatoren", {}).items():
            if "Einstiegsschwelle" in details or "Ausstiegsschwelle" in details:
                indikatorwerte[indikator] = st.number_input(f"{indikator} (aktueller Wert):", step=1.0)
            elif indikator == "Momentum":
                indikatorwerte[indikator] = st.selectbox("Momentum-Zustand:", ["positiv", "neutral", "negativ"])
            elif indikator == "Volumen":
                indikatorwerte[indikator] = st.selectbox("Volumen-Zustand:", ["unterdurchschnittlich", "normal", "überdurchschnittlich"])
            elif indikator == "Widerstand":
                indikatorwerte[indikator] = st.radio("Widerstand durchbrochen?", ["ja", "nein"])
            elif indikator == "Bollinger_Bänder":
                indikatorwerte["Kurs"] = st.number_input("Aktueller Kurswert:", step=0.1)

        risiko_dropdown = st.selectbox("💰 Kapitalrisiko pro Trade", ["1%", "2%", "3%", "5%", "10%", "individuell"])
        submitted = st.form_submit_button("🔍 Signal generieren")

    if submitted:
        signal = "⏸️ Beobachten"
        begruendung = []
        farbe = "gray"

        ein_bed = strat.get("Einstieg", {}).get("Bedingung", "")
        if "RSI" in indikatorwerte and "<" in ein_bed and float(indikatorwerte["RSI"]) < 30:
            signal = "📈 Einstiegssignal"
            begruendung.append("RSI unter 30")
            farbe = "green"
        if "Momentum" in indikatorwerte and "Momentum positiv" in ein_bed and indikatorwerte["Momentum"] == "positiv":
            signal = "📈 Einstiegssignal"
            begruendung.append("Momentum positiv")
            farbe = "green"
        if "CCI" in indikatorwerte and float(indikatorwerte["CCI"]) < -100:
            signal = "📈 CCI unter -100"
            begruendung.append("CCI < -100")
            farbe = "green"
        if "Kurs" in indikatorwerte and "unteres Band" in ein_bed and float(indikatorwerte["Kurs"]) < 95:
            signal = "📈 Kurs unter unterem Bollinger-Band"
            begruendung.append("Kurs < unteres Band")
            farbe = "green"
        if "Volumen" in indikatorwerte and indikatorwerte["Volumen"] == "überdurchschnittlich" and indikatorwerte.get("Widerstand") == "ja":
            signal = "📈 Breakout-Einstieg"
            begruendung.append("Volumen hoch + Widerstand durchbrochen")
            farbe = "green"

        aus_bed = strat.get("Ausstieg", {}).get("Bedingung", "")
        if "RSI" in indikatorwerte and ">" in aus_bed and float(indikatorwerte["RSI"]) > 70:
            signal = "📉 Ausstiegssignal"
            begruendung.append("RSI über 70")
            farbe = "red"
        if "Momentum" in indikatorwerte and "negativ" in aus_bed and indikatorwerte["Momentum"] == "negativ":
            signal = "📉 Momentum negativ"
            begruendung.append("Momentum negativ")
            farbe = "red"
        if "CCI" in indikatorwerte and float(indikatorwerte["CCI"]) > 100:
            signal = "📉 CCI über 100"
            begruendung.append("CCI > 100")
            farbe = "red"

        st.subheader("📋 Ergebnis")
        st.markdown(f"<div style='background-color:{farbe};padding:1rem;border-radius:0.5rem;color:white;text-align:center;font-size:1.5rem;'>{signal}</div>", unsafe_allow_html=True)

        if begruendung:
            st.markdown("**Begründung:**")
            for b in begruendung:
                st.markdown(f"- {b}")

        rm = strat.get("Risikomanagement", {})
        st.markdown("### 📌 Risikomanagement")
        st.markdown(f"- Risiko-Einstellung: **{risiko_dropdown}**")
        for k, v in rm.items():
            st.markdown(f"- {k}: **{v}**")
