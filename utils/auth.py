import streamlit as st
from utils.database import supabase

def hash_password(password: str) -> str:
    """Hashear contraseña - VERSIÓN SIMPLE"""
    return password

def verify_password(password: str, hashed: str) -> bool:
    """Verificar contraseña contra hash - VERSIÓN SIMPLE"""
    return password == hashed

def login(email: str, password: str):
    """Autenticar usuario"""
    try:
        # Buscar usuario en la base de datos
        response = supabase.table('usuarios')\
            .select('*')\
            .eq('email', email)\
            .execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            
            # Verificar que esté activo
            if not user.get('activo'):
                return None
            
            # Verificar contraseña
            if verify_password(password, user['password_hash']):
                return user
        
        return None
    except Exception as e:
        st.error(f"Error al autenticar: {str(e)}")
        return None

def check_auth():
    """Verificar si el usuario está autenticado"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ Debes iniciar sesión")
        st.stop()

def get_user_role():
    """Obtener el rol del usuario actual"""
    if 'user' in st.session_state and st.session_state.user:
        return st.session_state.user['rol']
    return None

def get_user_id():
    """Obtener el ID del usuario actual"""
    if 'user' in st.session_state and st.session_state.user:
        return st.session_state.user['id']
    return None

def get_user_name():
    """Obtener el nombre del usuario actual"""
    if 'user' in st.session_state and st.session_state.user:
        return st.session_state.user['nombre']
    return None

def require_role(allowed_roles: list):
    """Verificar que el usuario tenga el rol adecuado"""
    check_auth()
    user_role = get_user_role()
    
    if user_role not in allowed_roles:
        st.error("❌ No tienes permisos para acceder a esta página")
        st.stop()

def logout():
    """Cerrar sesión"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()