import streamlit as st
from utils.auth import get_user_name, get_user_role, logout

def render_sidebar():
    """Renderizar sidebar con información del usuario y navegación"""

    with st.sidebar:
        st.title("🍽️ Restaurante App")
        
        # Información del usuario
        if 'user' in st.session_state and st.session_state.user:
            st.divider()
            st.write(f"👤 **{get_user_name()}**")
            
            role_emoji = {
                'gerente': '👔',
                'mesero': '🍽️',
                'cocinero': '👨‍🍳'
            }
            
            role_name = {
                'gerente': 'Gerente',
                'mesero': 'Mesero',
                'cocinero': 'Cocinero'
            }
            
            user_role = get_user_role()
            st.caption(f"{role_emoji.get(user_role, '👤')} {role_name.get(user_role, user_role)}")
            
            st.divider()
            
            # Navegación según el rol
            render_navigation(user_role)
            
            st.divider()
            
            # Botón de cerrar sesión
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                logout()

def render_navigation(role: str):
    """Renderizar menú de navegación según el rol"""
    
    st.subheader("📍 Navegación")
    
    if role == 'gerente':
        st.page_link("pages/Dashboard.py", label="📊 Dashboard", icon="📊")
        
    elif role == 'mesero':
        st.page_link("pages/Mi_Turno.py", label="Mi Turno", icon="🕐")
        st.page_link("pages/Nuevo_Pedido.py", label="Nuevo Pedido", icon="➕")
        st.page_link("pages/Mis_Pedidos.py", label="Mis Pedidos", icon="📋")
        
    elif role == 'cocinero':
        st.page_link("pages/Pedidos_Pendientes.py", label="📋 Pendientes", icon="📋")
        st.page_link("pages/En_Preparacion.py", label="🔥 En Preparación", icon="🔥")