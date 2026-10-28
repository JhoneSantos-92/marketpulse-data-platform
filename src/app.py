import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

st.set_page_config(
    page_title="MarketPulse Data Platform - AI Assistant",
    page_icon="📈",
    layout="wide",
)

st.title("MarketPulse Data Platform & AI Intelligence")

# Check if GEMINI_API_KEY is configured
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    st.error(
        "🚨 **Alerta de Configuração:** `GEMINI_API_KEY` não está configurada. "
        "Por favor, defina a chave no arquivo `.env` ou nas variáveis de ambiente para utilizar os recursos de IA do Gemini."
    )
else:
    st.success("✅ `GEMINI_API_KEY` configurada com sucesso.")

st.sidebar.header("Configurações")
env = os.getenv("ENVIRONMENT", "production")
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
st.sidebar.text(f"Ambiente: {env}")
st.sidebar.text(f"Modelo LLM: {model}")

st.markdown(
    """
    ### Bem-vindo ao MarketPulse
    Plataforma de engenharia de dados em tempo real com streaming de criptoativos (Binance), conversão cambial (Banco Central do Brasil), armazenamento Delta Lake (SeaweedFS) e inteligência analítica.
    """
)
