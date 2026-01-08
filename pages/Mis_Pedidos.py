import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime, date, timedelta
import json

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
            st.switch_page("pages/Mi_Turno.py")
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
        st.cache_data.clear()
        st.rerun()

# Botón de debug (puedes quitarlo después)
with st.expander("🔍 Debug - Ver estado real en BD"):
    if st.button("Verificar pedidos en base de datos"):
        try:
            todos_pedidos = supabase.table('pedidos')\
                .select('numero_pedido, mesa_id, estado, created_at')\
                .eq('mesero_id', get_user_id())\
                .order('created_at', desc=True)\
                .limit(20)\
                .execute()
            
            if todos_pedidos.data:
                import pandas as pd
                df = pd.DataFrame(todos_pedidos.data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay pedidos")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# ============================================
# OBTENER PEDIDOS
# ============================================
@st.cache_data(ttl=10)  # Cache por solo 10 segundos
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
pedidos_cancelados = [p for p in pedidos if p['estado'] == 'cancelado']

tab_activos, tab_listos, tab_entregados, tab_cancelados, tab_todos = st.tabs([
    f"🔥 Activos ({len(pedidos_activos)})",
    f"✅ Listos ({len([p for p in pedidos if p['estado'] == 'listo'])})",
    f"📦 Entregados ({len(pedidos_entregados)})",
    f"❌ Cancelados ({len(pedidos_cancelados)})",
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
                # Botones de modificar y eliminar
                col_info, col_mod, col_del = st.columns([2, 1, 1])
                
                with col_info:
                    if pedido['estado'] == 'pendiente':
                        st.info("⏳ Esperando que cocina tome el pedido...")
                    else:
                        st.warning("⚠️ El pedido está en cocina. Modificar con precaución.")
                
                with col_mod:
                    if st.button(
                        "✏️ Modificar",
                        key=f"mod_{pedido['id']}",
                        use_container_width=True
                    ):
                        st.session_state[f'modificando_{pedido["id"]}'] = True
                        st.rerun()
                
                with col_del:
                    if st.button(
                        "🗑️ Eliminar",
                        key=f"del_{pedido['id']}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        st.session_state[f'confirmando_eliminar_{pedido["id"]}'] = True
                        st.rerun()
                
                # Modal de modificación
                if st.session_state.get(f'modificando_{pedido["id"]}', False):
                    st.markdown("---")
                    st.markdown("### ✏️ Modificar Pedido")
                    
                    with st.form(key=f"form_mod_{pedido['id']}"):
                        # Cambiar mesa
                        nueva_mesa = st.number_input(
                            "Número de Mesa",
                            min_value=1,
                            max_value=100,
                            value=pedido['mesa_id'],
                            key=f"mesa_mod_{pedido['id']}"
                        )
                        
                        # Modificar items
                        st.write("**Items del pedido:**")
                        items_modificados = []
                        
                        for idx, item in enumerate(items):
                            col_nombre, col_cant, col_eliminar = st.columns([3, 1, 1])
                            
                            with col_nombre:
                                st.write(f"• {item['nombre']}")
                            
                            with col_cant:
                                nueva_cantidad = st.number_input(
                                    "Cant.",
                                    min_value=0,
                                    max_value=50,
                                    value=item['cantidad'],
                                    key=f"cant_mod_{pedido['id']}_{idx}",
                                    label_visibility="collapsed"
                                )
                            
                            with col_eliminar:
                                mantener = st.checkbox(
                                    "Mantener",
                                    value=True,
                                    key=f"mantener_{pedido['id']}_{idx}",
                                    label_visibility="collapsed"
                                )
                            
                            if mantener and nueva_cantidad > 0:
                                item_modificado = item.copy()
                                item_modificado['cantidad'] = nueva_cantidad
                                items_modificados.append(item_modificado)
                        
                        # Nuevas notas
                        nuevas_notas = st.text_area(
                            "Notas del pedido",
                            value=pedido.get('notas', ''),
                            key=f"notas_mod_{pedido['id']}"
                        )
                        
                        # Calcular nuevo total
                        nuevo_total = sum(item['precio'] * item['cantidad'] for item in items_modificados)
                        st.markdown(f"**Nuevo Total:** ${nuevo_total:,.0f}")
                        
                        col_cancelar, col_guardar = st.columns(2)
                        
                        with col_cancelar:
                            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                            if cancelar:
                                st.session_state[f'modificando_{pedido["id"]}'] = False
                                st.rerun()
                        
                        with col_guardar:
                            guardar = st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary")
                            
                            if guardar:
                                if not items_modificados:
                                    st.error("❌ Debes mantener al menos un item")
                                else:
                                    try:
                                        supabase.table('pedidos').update({
                                            'mesa_id': nueva_mesa,
                                            'items': json.dumps(items_modificados),
                                            'total': nuevo_total,
                                            'notas': nuevas_notas if nuevas_notas else None,
                                            'updated_at': datetime.now().isoformat()
                                        }).eq('id', pedido['id']).execute()
                                        
                                        st.success("✅ Pedido modificado correctamente!")
                                        st.session_state[f'modificando_{pedido["id"]}'] = False
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                
                # Modal de confirmación de eliminación
                if st.session_state.get(f'confirmando_eliminar_{pedido["id"]}', False):
                    st.markdown("---")
                    st.warning(f"⚠️ ¿Estás seguro de eliminar el Pedido #{pedido['numero_pedido']}?")
                    st.caption("Esta acción no se puede deshacer.")
                    
                    col_no, col_si = st.columns(2)
                    
                    with col_no:
                        if st.button("❌ No, cancelar", key=f"no_eliminar_{pedido['id']}", use_container_width=True):
                            st.session_state[f'confirmando_eliminar_{pedido["id"]}'] = False
                            st.rerun()
                    
                    with col_si:
                        if st.button("✅ Sí, eliminar", key=f"si_eliminar_{pedido['id']}", use_container_width=True, type="primary"):
                            try:
                                # Actualizar estado a cancelado
                                response = supabase.table('pedidos').update({
                                    'estado': 'cancelado',
                                    'updated_at': datetime.now().isoformat()
                                }).eq('id', pedido['id']).execute()
                                
                                # Verificar que se actualizó
                                if response.data:
                                    st.success("✅ Pedido cancelado correctamente!")
                                    
                                    # Limpiar estado
                                    st.session_state[f'confirmando_eliminar_{pedido["id"]}'] = False
                                    
                                    # Limpiar cache
                                    st.cache_data.clear()
                                    
                                    # Forzar actualización inmediata
                                    import time
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("❌ No se pudo actualizar el pedido")
                                    
                            except Exception as e:
                                st.error(f"❌ Error al eliminar: {str(e)}")
                                import traceback
                                with st.expander("Ver detalles"):
                                    st.code(traceback.format_exc())
            
            elif pedido['estado'] == 'entregado':
                st.success(f"✅ Entregado hace {tiempo_mins} minutos")
            
            elif pedido['estado'] == 'cancelado':
                col_msg, col_eliminar_perm = st.columns([2, 1])
                
                with col_msg:
                    st.error(f"❌ Pedido cancelado")
                
                with col_eliminar_perm:
                    if st.button(
                        "🗑️ Eliminar Permanentemente",
                        key=f"eliminar_perm_{pedido['id']}",
                        use_container_width=True,
                        help="Eliminar completamente de la base de datos"
                    ):
                        st.session_state[f'confirmando_eliminar_perm_{pedido["id"]}'] = True
                        st.rerun()
                
                # Confirmación de eliminación permanente
                if st.session_state.get(f'confirmando_eliminar_perm_{pedido["id"]}', False):
                    st.markdown("---")
                    st.error(f"⚠️ ¿ELIMINAR PERMANENTEMENTE el Pedido #{pedido['numero_pedido']}?")
                    st.warning("Esta acción NO se puede deshacer. El pedido se borrará completamente de la base de datos.")
                    
                    col_no, col_si = st.columns(2)
                    
                    with col_no:
                        if st.button("❌ Cancelar", key=f"no_eliminar_perm_{pedido['id']}", use_container_width=True):
                            st.session_state[f'confirmando_eliminar_perm_{pedido["id"]}'] = False
                            st.rerun()
                    
                    with col_si:
                        if st.button("⚠️ SÍ, ELIMINAR PERMANENTEMENTE", key=f"si_eliminar_perm_{pedido['id']}", use_container_width=True, type="primary"):
                            try:
                                # ELIMINAR de la base de datos (no solo cancelar)
                                response = supabase.table('pedidos').delete().eq('id', pedido['id']).execute()
                                
                                if response:
                                    st.success("✅ Pedido eliminado permanentemente de la base de datos")
                                    
                                    # Limpiar estado
                                    st.session_state[f'confirmando_eliminar_perm_{pedido["id"]}'] = False
                                    
                                    # Limpiar cache
                                    st.cache_data.clear()
                                    
                                    # Recargar
                                    import time
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("❌ No se pudo eliminar el pedido")
                                    
                            except Exception as e:
                                st.error(f"❌ Error al eliminar permanentemente: {str(e)}")
                                import traceback
                                with st.expander("Ver detalles"):
                                    st.code(traceback.format_exc())
        
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
# TAB CANCELADOS
# ============================================
with tab_cancelados:
    if pedidos_cancelados:
        st.error(f"❌ {len(pedidos_cancelados)} pedido(s) cancelado(s)")
        
        # Botón para eliminar todos los cancelados
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Eliminar TODOS los Cancelados", use_container_width=True, type="secondary"):
                st.session_state['confirmando_eliminar_todos'] = True
                st.rerun()
        
        # Confirmación para eliminar todos
        if st.session_state.get('confirmando_eliminar_todos', False):
            st.markdown("---")
            st.error(f"⚠️ ¿ELIMINAR PERMANENTEMENTE los {len(pedidos_cancelados)} pedidos cancelados?")
            st.warning("Esta acción NO se puede deshacer. Todos los pedidos cancelados se borrarán completamente.")
            
            col_no, col_si = st.columns(2)
            
            with col_no:
                if st.button("❌ No, cancelar", key="no_eliminar_todos", use_container_width=True):
                    st.session_state['confirmando_eliminar_todos'] = False
                    st.rerun()
            
            with col_si:
                if st.button("⚠️ SÍ, ELIMINAR TODOS", key="si_eliminar_todos", use_container_width=True, type="primary"):
                    try:
                        # Obtener IDs de todos los cancelados
                        ids_cancelados = [p['id'] for p in pedidos_cancelados]
                        
                        # Eliminar todos
                        for pedido_id in ids_cancelados:
                            supabase.table('pedidos').delete().eq('id', pedido_id).execute()
                        
                        st.success(f"✅ {len(ids_cancelados)} pedidos eliminados permanentemente")
                        
                        # Limpiar estado
                        st.session_state['confirmando_eliminar_todos'] = False
                        
                        # Limpiar cache y recargar
                        st.cache_data.clear()
                        import time
                        time.sleep(0.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        st.divider()
        
        # Mostrar pedidos cancelados
        for pedido in pedidos_cancelados:
            renderizar_pedido(pedido, mostrar_acciones=True)
    else:
        st.success("✨ No hay pedidos cancelados")

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