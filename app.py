import requests
import streamlit as st

st.set_page_config(page_title="Motor Fault Classifier", layout="wide")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Configuracao")
    api_url = st.text_input("URL do endpoint", placeholder="http://<URL>")

# ── Session state ─────────────────────────────────────────────────────────────

if "falha_prevista" not in st.session_state:
    st.session_state.falha_prevista = None
    st.session_state.probabilidades = None

# ── Layout ────────────────────────────────────────────────────────────────────

col_sim, col_result = st.columns([1, 1])

# ── Coluna 1: Simulacao ───────────────────────────────────────────────────────

with col_sim:
    st.header("Simulacao")

    rotacao = st.slider("Rotacao (RPM)", 1300.0, 2100.0, 1776.0, 10.0)
    vibracao = st.slider("Vibracao (mm/s)", 0.5, 14.0, 2.7, 0.1)
    temperatura = st.slider("Temperatura (C)", 50.0, 110.0, 68.5, 0.5)
    corrente = st.slider("Corrente (A)", 8.0, 20.0, 12.3, 0.1)

    prever = st.button("Prever", type="primary", use_container_width=True, disabled=not api_url)

    if not api_url:
        st.caption("Informe a URL do endpoint na barra lateral.")

    if prever:
        payload = {
            "rotacao_rpm": rotacao,
            "vibracao_mm_s": vibracao,
            "temperatura_c": temperatura,
            "corrente_a": corrente,
        }
        try:
            response = requests.post(
                f"{api_url.rstrip('/')}/predict",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            resultado = response.json()
            st.session_state.falha_prevista = resultado["falha"]
            st.session_state.probabilidades = resultado["probabilidades"]
        except requests.exceptions.ConnectionError:
            st.error("Nao foi possivel conectar ao endpoint.")
        except requests.exceptions.HTTPError as e:
            st.error(f"Erro na requisicao: {e}")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")

# ── Coluna 2: Resultado ───────────────────────────────────────────────────────

with col_result:
    st.header("Resultado")

    if st.session_state.falha_prevista:
        falha = st.session_state.falha_prevista
        cor = "green" if falha == "Normal" else "red"
        st.markdown(f"# :{cor}[{falha}]")

        st.divider()

        probs = st.session_state.probabilidades
        c1, c2 = st.columns(2)
        for i, (classe, prob) in enumerate(probs.items()):
            (c1 if i % 2 == 0 else c2).metric(classe, f"{prob:.1%}")
    else:
        st.info("Ajuste os sliders e clique em **Prever**.")