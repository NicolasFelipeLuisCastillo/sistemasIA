import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime
import json

st.set_page_config(
    page_title="Pedidos Pendientes",
    page_icon="📋",
    layout="wide"
)

# Ocultar menú automático de Streamlit
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Estilos para pedidos urgentes */
    .urgent-order {
        animation: pulse 2s infinite;
        border: 2px solid #FF4B4B;
        border-radius: 10px;
        padding: 1rem;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)

check_auth()
require_role(['cocinero', 'gerente'])

render_sidebar()

st.title(f"📋 Pedidos Pendientes - {get_user_name()}")

# Auto-refresh controls
col1, col2, col3 = st.columns([2, 3, 1])

with col1:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.rerun()

with col2:
    auto_refresh = st.checkbox("🔁 Auto-refresh (cada 10 seg)", value=True)

with col3:
    # Contador de actualización
    if 'refresh_count' not in st.session_state:
        st.session_state.refresh_count = 0
    st.caption(f"🔄 {st.session_state.refresh_count}")

st.divider()

# ============================================
# OBTENER PEDIDOS PENDIENTES
# ============================================
@st.cache_data(ttl=5)
def get_pedidos_pendientes():
    """Obtener todos los pedidos pendientes ordenados por antigüedad"""
    response = supabase.table('pedidos')\
        .select('*, usuarios!mesero_id(nombre)')\
        .eq('estado', 'pendiente')\
        .order('created_at')\
        .execute()
    return response.data if response.data else []

pedidos = get_pedidos_pendientes()

# ============================================
# ESTADÍSTICAS RÁPIDAS
# ============================================
if pedidos:
    # Calcular estadísticas
    ahora = datetime.now()
    pedidos_urgentes = []
    
    for p in pedidos:
        created = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
        mins = int((ahora - created.replace(tzinfo=None)).total_seconds() / 60)
        if mins > 10:
            pedidos_urgentes.append(p)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Pedidos Pendientes", len(pedidos))
    
    with col2:
        st.metric("⚠️ Urgentes (>10 min)", len(pedidos_urgentes))
    
    with col3:
        total_items = sum(len(json.loads(p['items']) if isinstance(p['items'], str) else p['items']) for p in pedidos)
        st.metric("🍽️ Items Totales", total_items)
    
    with col4:
        if pedidos:
            created_oldest = datetime.fromisoformat(pedidos[0]['created_at'].replace('Z', '+00:00'))
            mins_oldest = int((ahora - created_oldest.replace(tzinfo=None)).total_seconds() / 60)
            st.metric("⏱️ Más Antiguo", f"{mins_oldest} min")
    
    st.divider()
    
    # Alerta de pedidos urgentes
    if pedidos_urgentes:
        st.error(f"🚨 ¡HAY {len(pedidos_urgentes)} PEDIDO(S) URGENTE(S)!")
    
    # ============================================
    # MOSTRAR PEDIDOS
    # ============================================
    for idx, pedido in enumerate(pedidos):
        # Calcular tiempo transcurrido
        created = datetime.fromisoformat(pedido['created_at'].replace('Z', '+00:00'))
        ahora_local = datetime.now()
        tiempo_mins = int((ahora_local - created.replace(tzinfo=None)).total_seconds() / 60)
        
        # Determinar urgencia
        es_urgente = tiempo_mins > 10
        es_muy_urgente = tiempo_mins > 15
        
        # Container con estilo según urgencia
        with st.container():
            if es_muy_urgente:
                st.markdown('<div class="urgent-order">', unsafe_allow_html=True)
            
            # Header del pedido
            col_info, col_tiempo, col_accion = st.columns([3, 1, 1])
            
            with col_info:
                # Título con prioridad visual
                prioridad = ""
                if es_muy_urgente:
                    prioridad = "🚨 "
                elif es_urgente:
                    prioridad = "⚠️ "
                
                st.markdown(f"### {prioridad}Pedido #{pedido['numero_pedido']} - Mesa {pedido['mesa_id']}")
                
                # Información del mesero
                mesero_data = pedido.get('usuarios', {})
                if isinstance(mesero_data, dict):
                    mesero_nombre = mesero_data.get('nombre', 'Desconocido')
                else:
                    mesero_nombre = 'Desconocido'
                
                st.caption(f"👤 Mesero: {mesero_nombre}")
                st.caption(f"🕐 {created.strftime('%I:%M %p')}")
            
            with col_tiempo:
                # Tiempo con color según urgencia
                if es_muy_urgente:
                    color = "#FF4B4B"
                    emoji = "🔴"
                elif es_urgente:
                    color = "#FFA500"
                    emoji = "🟡"
                else:
                    color = "#51CF66"
                    emoji = "🟢"
                
                st.markdown(
                    f"<h2 style='color: {color}; text-align: center;'>{emoji}<br>{tiempo_mins} min</h2>",
                    unsafe_allow_html=True
                )
            
            with col_accion:
                st.write("")  # Espaciado
                if st.button(
                    "👨‍🍳 TOMAR PEDIDO",
                    key=f"tomar_{pedido['id']}",
                    use_container_width=True,
                    type="primary"
                ):
                    try:
                        # Actualizar estado y asignar cocinero
                        supabase.table('pedidos').update({
                            'estado': 'en_cocina',
                            'cocinero_id': get_user_id(),
                            'updated_at': datetime.now().isoformat()
                        }).eq('id', pedido['id']).execute()
                        
                        st.success(f"✅ Pedido #{pedido['numero_pedido']} tomado!")
                        st.cache_data.clear()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Items del pedido
            st.markdown("**🍽️ Items del pedido:**")
            
            items = pedido['items']
            if isinstance(items, str):
                items = json.loads(items)
            
            # Mostrar items en columnas
            cols = st.columns(3)
            for idx_item, item in enumerate(items):
                col_idx = idx_item % 3
                with cols[col_idx]:
                    st.markdown(
                        f"""
                        <div style='background-color: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: 5px; margin-bottom: 0.5rem;'>
                            <b>🍽️ {item['cantidad']}x {item['nombre']}</b><br>
                            <small>{item.get('categoria', '')}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if item.get('notas'):
                        st.info(f"📝 {item['notas']}")
            
            # Notas generales del pedido
            if pedido.get('notas'):
                st.warning(f"💬 **Nota importante:** {pedido['notas']}")
            
            if es_muy_urgente:
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.divider()

else:
    # No hay pedidos pendientes
    st.success("✨ ¡Excelente trabajo!")
    st.markdown("""
        <div style='text-align: center; padding: 3rem;'>
            <h2>🎉 No hay pedidos pendientes</h2>
            <p>Todos los pedidos han sido tomados por cocina</p>
        </div>
    """, unsafe_allow_html=True)

# ============================================
# RESUMEN AL FINAL
# ============================================
if pedidos:
    st.divider()
    
    with st.expander("📊 Resumen Detallado"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Por Mesa")
            mesas = {}
            for p in pedidos:
                mesa = p['mesa_id']
                mesas[mesa] = mesas.get(mesa, 0) + 1
            
            for mesa, count in sorted(mesas.items()):
                st.write(f"Mesa {mesa}: {count} pedido(s)")
        
        with col2:
            st.subheader("Por Mesero")
            meseros = {}
            for p in pedidos:
                mesero_data = p.get('usuarios', {})
                if isinstance(mesero_data, dict):
                    mesero = mesero_data.get('nombre', 'Desconocido')
                else:
                    mesero = 'Desconocido'
                meseros[mesero] = meseros.get(mesero, 0) + 1
            
            for mesero, count in sorted(meseros.items()):
                st.write(f"{mesero}: {count} pedido(s)")

# Auto-refresh si está activado
if auto_refresh and pedidos:
    st.session_state.refresh_count += 1
    import time
    time.sleep(10)
    st.rerun()