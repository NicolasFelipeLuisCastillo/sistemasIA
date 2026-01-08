import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime, date, timedelta
import json


# IMPORTANTE: Ocultar el menú de navegación automático
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Mis Pedidos",
    page_icon="📋",
    layout="wide"
)

# Ocultar menú automático de Streamlit
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

check_auth()
require_role(['mesero', 'gerente'])

render_sidebar()

st.title(f"📋 Mis Pedidos - {get_user_name()}")

# ============================================
# VALIDAR QUE HAYA TURNO ACTIVO
# ============================================
def tiene_turno_activo():
    """Verificar si el mesero tiene un turno activo hoy"""
    try:
        response = supabase.table('turnos')\
            .select('*')\
            .eq('mesero_id', get_user_id())\
            .eq('fecha', date.today().isoformat())\
            .eq('estado', 'activo')\
            .execute()
        
        return response.data and len(response.data) > 0
    except Exception as e:
        st.error(f"Error al verificar turno: {str(e)}")
        return False

if not tiene_turno_activo():
    st.warning("⚠️ Debes iniciar tu turno primero")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🕐 Ir a Mi Turno", use_container_width=True, type="primary"):
            st.switch_page("pages/_Mi_Turno.py")
    st.stop()

# ============================================
# FILTROS
# ============================================
col_filtro1, col_filtro2, col_actualizar = st.columns([2, 2, 1])

with col_filtro1:
    fecha_filtro = st.date_input(
        "📅 Fecha",
        value=date.today(),
        max_value=date.today()
    )

with col_filtro2:
    estado_filtro = st.selectbox(
        "🔍 Estado",
        options=['Todos', 'Activos', 'pendiente', 'en_cocina', 'listo', 'entregado', 'cancelado']
    )

with col_actualizar:
    st.write("")  # Espaciado
    st.write("")
    if st.button("🔄 Actualizar", use_container_width=True):
        st.rerun()

st.divider()

# ============================================
# OBTENER PEDIDOS
# ============================================
@st.cache_data(ttl=30)
def get_pedidos_mesero(mesero_id, fecha, estado):
    """Obtener pedidos del mesero según filtros"""
    query = supabase.table('pedidos')\
        .select('*')\
        .eq('mesero_id', mesero_id)
    
    # Filtro por fecha
    fecha_inicio = datetime.combine(fecha, datetime.min.time()).isoformat()
    fecha_fin = datetime.combine(fecha, datetime.max.time()).isoformat()
    query = query.gte('created_at', fecha_inicio).lte('created_at', fecha_fin)
    
    # Filtro por estado
    if estado == 'Activos':
        query = query.in_('estado', ['pendiente', 'en_cocina', 'listo'])
    elif estado != 'Todos':
        query = query.eq('estado', estado)
    
    query = query.order('created_at', desc=True)
    
    response = query.execute()
    return response.data if response.data else []

pedidos = get_pedidos_mesero(get_user_id(), fecha_filtro, estado_filtro)

# ============================================
# ESTADÍSTICAS RÁPIDAS
# ============================================
col1, col2, col3, col4 = st.columns(4)

pedidos_activos = [p for p in pedidos if p['estado'] in ['pendiente', 'en_cocina', 'listo']]
pedidos_entregados = [p for p in pedidos if p['estado'] == 'entregado']
total_ventas = sum(p['total'] for p in pedidos_entregados)

with col1:
    st.metric("📋 Total Pedidos", len(pedidos))

with col2:
    st.metric("🔥 Activos", len(pedidos_activos))

with col3:
    st.metric("✅ Entregados", len(pedidos_entregados))

with col4:
    st.metric("💰 Ventas", f"${total_ventas:,.0f}")

st.divider()

# ============================================
# TABS POR ESTADO
# ============================================
tab_activos, tab_listos, tab_entregados, tab_todos = st.tabs([
    f"🔥 Activos ({len(pedidos_activos)})",
    f"✅ Listos ({len([p for p in pedidos if p['estado'] == 'listo'])})",
    f"📦 Entregados ({len(pedidos_entregados)})",
    f"📋 Todos ({len(pedidos)})"
])

# ============================================
# FUNCIÓN PARA RENDERIZAR PEDIDO
# ============================================
def renderizar_pedido(pedido, mostrar_acciones=True):
    """Renderizar un pedido con su información y acciones"""
    
    # Calcular tiempo transcurrido
    created = datetime.fromisoformat(pedido['created_at'].replace('Z', '+00:00'))
    ahora = datetime.now(created.tzinfo)
    tiempo_mins = int((ahora - created).total_seconds() / 60)
    
    # Colores por estado
    estado_colors = {
        'pendiente': '#FFA500',
        'en_cocina': '#FF6B6B',
        'listo': '#51CF66',
        'entregado': '#339AF0',
        'cancelado': '#868E96'
    }
    
    estado_emoji = {
        'pendiente': '⏳',
        'en_cocina': '🔥',
        'listo': '✅',
        'entregado': '📦',
        'cancelado': '❌'
    }
    
    with st.container():
        # Header del pedido
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        
        with col_header1:
            st.markdown(f"### Pedido #{pedido['numero_pedido']} - Mesa {pedido['mesa_id']}")
            st.caption(f"📅 {created.strftime('%d/%m/%Y %I:%M %p')}")
        
        with col_header2:
            color = estado_colors.get(pedido['estado'], '#868E96')
            emoji = estado_emoji.get(pedido['estado'], '❓')
            st.markdown(
                f"<h3 style='color: {color};'>{emoji} {pedido['estado'].title()}</h3>",
                unsafe_allow_html=True
            )
        
        with col_header3:
            st.metric("⏱️ Tiempo", f"{tiempo_mins} min")
        
        # Items del pedido
        items = pedido['items']
        if isinstance(items, str):
            items = json.loads(items)
        
        st.markdown("**Items del pedido:**")
        
        for item in items:
            col_item, col_cantidad, col_precio = st.columns([3, 1, 1])
            
            with col_item:
                st.write(f"• {item['nombre']}")
                if item.get('notas'):
                    st.caption(f"  _{item['notas']}_")
            
            with col_cantidad:
                st.write(f"x{item['cantidad']}")
            
            with col_precio:
                subtotal = item['precio'] * item['cantidad']
                st.write(f"${subtotal:,.0f}")
        
        # Notas generales
        if pedido.get('notas'):
            st.info(f"💬 **Nota:** {pedido['notas']}")
        
        # Total
        col_total1, col_total2 = st.columns([3, 1])
        with col_total2:
            st.markdown(f"### Total: ${pedido['total']:,.0f}")
        
        # Acciones según estado
        if mostrar_acciones:
            st.divider()
            
            if pedido['estado'] == 'listo':
                col_accion1, col_accion2, col_accion3 = st.columns([2, 1, 1])
                
                with col_accion2:
                    if st.button(
                        "✅ Marcar como Entregado",
                        key=f"entregar_{pedido['id']}",
                        use_container_width=True,
                        type="primary"
                    ):
                        try:
                            supabase.table('pedidos').update({
                                'estado': 'entregado',
                                'updated_at': datetime.now().isoformat()
                            }).eq('id', pedido['id']).execute()
                            
                            st.success("✅ Pedido marcado como entregado!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            elif pedido['estado'] in ['pendiente', 'en_cocina']:
                col_info = st.columns([1])[0]
                with col_info:
                    if pedido['estado'] == 'pendiente':
                        st.info("⏳ Esperando que cocina tome el pedido...")
                    else:
                        st.info("🔥 El pedido está siendo preparado en cocina...")
            
            elif pedido['estado'] == 'entregado':
                st.success(f"✅ Entregado hace {tiempo_mins} minutos")
        
        st.divider()

# ============================================
# TAB ACTIVOS
# ============================================
with tab_activos:
    if pedidos_activos:
        st.info(f"🔥 Tienes {len(pedidos_activos)} pedido(s) activo(s)")
        
        for pedido in pedidos_activos:
            renderizar_pedido(pedido, mostrar_acciones=True)
    else:
        st.success("✨ No tienes pedidos activos")
        st.caption("Todos los pedidos han sido completados")

# ============================================
# TAB LISTOS
# ============================================
with tab_listos:
    pedidos_listos = [p for p in pedidos if p['estado'] == 'listo']
    
    if pedidos_listos:
        st.success(f"✅ {len(pedidos_listos)} pedido(s) listo(s) para entregar")
        
        for pedido in pedidos_listos:
            renderizar_pedido(pedido, mostrar_acciones=True)
    else:
        st.info("No hay pedidos listos en este momento")

# ============================================
# TAB ENTREGADOS
# ============================================
with tab_entregados:
    if pedidos_entregados:
        st.success(f"📦 {len(pedidos_entregados)} pedido(s) entregado(s)")
        
        for pedido in pedidos_entregados:
            renderizar_pedido(pedido, mostrar_acciones=False)
    else:
        st.info("No has entregado pedidos en esta fecha")

# ============================================
# TAB TODOS
# ============================================
with tab_todos:
    if pedidos:
        # Filtro adicional en este tab
        col_orden = st.columns([1])[0]
        with col_orden:
            orden = st.radio(
                "Ordenar por:",
                options=['Más recientes primero', 'Más antiguos primero', 'Por mesa'],
                horizontal=True
            )
        
        # Ordenar según selección
        if orden == 'Más antiguos primero':
            pedidos_mostrar = sorted(pedidos, key=lambda x: x['created_at'])
        elif orden == 'Por mesa':
            pedidos_mostrar = sorted(pedidos, key=lambda x: x['mesa_id'])
        else:  # Más recientes primero
            pedidos_mostrar = pedidos
        
        st.divider()
        
        for pedido in pedidos_mostrar:
            renderizar_pedido(pedido, mostrar_acciones=False)
    else:
        st.info(f"No hay pedidos para {fecha_filtro.strftime('%d/%m/%Y')}")
        st.caption("Cambia la fecha en el filtro superior para ver pedidos de otros días")

# ============================================
# BOTÓN CREAR NUEVO PEDIDO
# ============================================
st.divider()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("➕ Crear Nuevo Pedido", use_container_width=True, type="primary"):
        st.switch_page("pages/Nuevo_Pedido.py")

# Auto-refresh cada 30 segundos para pedidos activos
if pedidos_activos:
    st.caption("🔄 Esta página se actualiza automáticamente cada 30 segundos")
    import time
    time.sleep(30)
    st.rerun()