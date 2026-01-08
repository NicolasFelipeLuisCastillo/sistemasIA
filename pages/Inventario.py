import streamlit as st

# Ocultar el menú de páginas automático de Streamlit
st.set_page_config(
    page_title="Nombre de la Página",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# IMPORTANTE: Ocultar el menú de navegación automático
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)