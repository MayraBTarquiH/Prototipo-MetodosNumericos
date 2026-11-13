import streamlit as st
from core.ui import pagina_pendiente

st.set_page_config(page_title="SIMTELE-RISK", page_icon="🚡", layout="wide")
pagina_pendiente("sensores")
