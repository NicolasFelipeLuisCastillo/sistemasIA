import streamlit as st
from utils.auth import login
from utils.database import supabase

st.set_page_config(
    page_title="Sistema Restaurante",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

def main():
    # Si está autenticado, redirigir según el rol
    if st.session_state.authenticated and st.session_state.user:
        user_role = st.session_state.user['rol']
        
        if user_role == 'gerente':
            st.switch_page("pages/Dashboard.py")
        elif user_role == 'mesero':
            st.switch_page("pages/Mi_Turno.py")
        elif user_role == 'cocinero':
            st.switch_page("pages/Pedidos_Pendientes.py")
    else:
        show_login()

def show_login():
    # CSS personalizado
    st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stButton > button {
            width: 100%;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.75rem;
            border: none;
        }
        .stButton > button:hover {
            background-color: #FF6B6B;
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>Sistema de Restaurante</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Gestión integral para tu restaurante</p>", unsafe_allow_html=True)
        
        st.divider()
        
        # Formulario de login
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            
            email = st.text_input(
                "Email",
                placeholder="usuario@restaurante.com",
                help="Ingresa tu correo electrónico"
            )
            
            password = st.text_input(
                "Contraseña",
                type="password",
                placeholder="••••••••",
                help="Ingresa tu contraseña"
            )
            
            submit = st.form_submit_button("🔐 Ingresar")
            
            if submit:
                if email and password:
                    with st.spinner("Verificando credenciales..."):
                        # DEBUG: Ver qué usuarios hay
                        try:
                            st.write("🔍 Verificando conexión a BD...")
                            
                            # Prueba 1: Todos los usuarios sin filtro
                            test_response = supabase.table('usuarios').select('*').execute()
                            st.success("✅ Conexión exitosa a Supabase")
                            st.write("👥 Total usuarios encontrados:", len(test_response.data) if test_response.data else 0)
                            st.write("📋 Usuarios completos:", test_response.data)
                            
                            # Prueba 2: Solo activos
                            activos_response = supabase.table('usuarios').select('*').eq('activo', True).execute()
                            st.write("👥 Usuarios activos:", activos_response.data)
                            
                        except Exception as e:
                            st.error(f"❌ Error conectando a BD: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                        
                        user = login(email, password)
                        
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user = user
                            st.success(f"✅ Bienvenido, {user['nombre']}!")
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                            st.write("Email ingresado:", email)
                            st.write("Password ingresado:", password)
                    
        st.divider()
        
        # Usuarios de prueba (solo para desarrollo)
        with st.expander("👥 Usuarios de Prueba"):
            st.markdown("""
            **Gerente:**
            - Email: `gerente@test.com`
            - Password: `admin123`
            
            **Mesero:**
            - Email: `mesero@test.com`
            - Password: `admin123`
            
            **Cocinero:**
            - Email: `cocinero@test.com`
            - Password: `admin123`
            """)


if __name__ == "__main__":
    main()
