import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime
import json

st.set_page_config(
    page_title="En Preparación",
    page_icon="🔥",
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
require_role(['cocinero', 'gerente'])

render_sidebar()

st.title(f"🔥 Pedidos en Preparación - {get_user_name()}")

# Filtros
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    filtro = st.selectbox(
        "Mostrar",
        options=['Mis Pedidos', 'Todos los Pedidos'],
        index=0
    )

with col2:
    ordenar = st.selectbox(
        "Ordenar por",
        options=['Más antiguos primero', 'Más recientes primero', 'Por mesa'],
        index=0
    )

with col3:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ============================================
# OBTENER PEDIDOS EN PREPARACIÓN
# ============================================
@st.cache_data(ttl=5)
def get_pedidos_en_cocina(cocinero_id=None, filtro='Mis Pedidos'):
    """Obtener pedidos en preparación"""
    query = supabase.table('pedidos')\
        .select('*, usuarios!mesero_id(nombre)')
    
    query = query.eq('estado', 'en_cocina')
    
    if filtro == 'Mis Pedidos' and cocinero_id:
        query = query.eq('cocinero_id', cocinero_id)
    
    query = query.order('updated_at')
    
    response = query.execute()
    return response.data if response.data else []

pedidos = get_pedidos_en_cocina(get_user_id(), filtro)

# Ordenar según selección
if ordenar == 'Más recientes primero':
    pedidos = sorted(pedidos, key=lambda x: x['updated_at'], reverse=True)
elif ordenar == 'Por mesa':
    pedidos = sorted(pedidos, key=lambda x: x['mesa_id'])

# ============================================
# ESTADÍSTICAS
# ============================================
if pedidos:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔥 En Preparación", len(pedidos))
    
    with col2:
        mis_pedidos = [p for p in pedidos if p.get('cocinero_id') == get_user_id()]
        st.metric("👨‍🍳 Mis Pedidos", len(mis_pedidos))
    
    with col3:
        ahora = datetime.now()
        pedidos_lentos = []
        for p in pedidos:
            updated = datetime.fromisoformat(p['updated_at'].replace('Z', '+00:00'))
            mins = int((ahora - updated.replace(tzinfo=None)).total_seconds() / 60)
            if mins > 15:
                pedidos_lentos.append(p)
        st.metric("⚠️ Tiempo > 15 min", len(pedidos_lentos))
    
    with col4:
        total_items = sum(len(json.loads(p['items']) if isinstance(p['items'], str) else p['items']) for p in pedidos)
        st.metric("🍽️ Items Totales", total_items)
    
    st.divider()
    
    # Alertas
    if pedidos_lentos:
        st.warning(f"⚠️ {len(pedidos_lentos)} pedido(s) lleva(n) más de 15 minutos en preparación")
    
    # ============================================
    # MOSTRAR PEDIDOS
    # ============================================
    for pedido in pedidos:
        # Calcular tiempo en preparación
        updated = datetime.fromisoformat(pedido['updated_at'].replace('Z', '+00:00'))
        created = datetime.fromisoformat(pedido['created_at'].replace('Z', '+00:00'))
        ahora_local = datetime.now()
        
        tiempo_preparacion = int((ahora_local - updated.replace(tzinfo=None)).total_seconds() / 60)
        tiempo_total = int((ahora_local - created.replace(tzinfo=None)).total_seconds() / 60)
        
        # Determinar color según tiempo
        if tiempo_preparacion > 15:
            color = "#FF4B4B"
            emoji = "🔴"
        elif tiempo_preparacion > 10:
            color = "#FFA500"
            emoji = "🟡"
        else:
            color = "#51CF66"
            emoji = "🟢"
        
        with st.container():
            # Header
            col_info, col_tiempo, col_accion = st.columns([3, 1, 1])
            
            with col_info:
                # Indicador de pedido propio
                es_mio = pedido.get('cocinero_id') == get_user_id()
                indicador = "👨‍🍳 " if es_mio else ""
                
                st.markdown(f"### {indicador}Pedido #{pedido['numero_pedido']} - Mesa {pedido['mesa_id']}")
                
                # Mesero
                mesero_data = pedido.get('usuarios', {})
                if isinstance(mesero_data, dict):
                    mesero_nombre = mesero_data.get('nombre', 'Desconocido')
                else:
                    mesero_nombre = 'Desconocido'
                
                st.caption(f"👤 Mesero: {mesero_nombre}")
                st.caption(f"🕐 Pedido: {created.strftime('%I:%M %p')} | Cocina: {updated.strftime('%I:%M %p')}")
            
            with col_tiempo:
                st.markdown(
                    f"""
                    <div style='text-align: center;'>
                        <h2 style='color: {color};'>{emoji}</h2>
                        <h3 style='color: {color};'>{tiempo_preparacion} min</h3>
                        <small>Total: {tiempo_total} min</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col_accion:
                st.write("")  # Espaciado
                
                # Solo puede marcar como listo si es su pedido
                if es_mio:
                    if st.button(
                        "✅ MARCAR LISTO",
                        key=f"listo_{pedido['id']}",
                        use_container_width=True,
                        type="primary"
                    ):
                        try:
                            # Calcular tiempo total de preparación
                            tiempo_prep = ahora_local - updated.replace(tzinfo=None)
                            
                            # Actualizar estado
                            supabase.table('pedidos').update({
                                'estado': 'listo',
                                'tiempo_preparacion': str(tiempo_prep),
                                'updated_at': datetime.now().isoformat()
                            }).eq('id', pedido['id']).execute()
                            
                            st.success(f"✅ Pedido #{pedido['numero_pedido']} listo!")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.caption("🔒 Pedido de otro cocinero")
            
            # Items del pedido
            st.markdown("**🍽️ Items:**")
            
            items = pedido['items']
            if isinstance(items, str):
                items = json.loads(items)
            
            # Mostrar items con checkboxes para ir marcando
            cols = st.columns(4)
            for idx, item in enumerate(items):
                col_idx = idx % 4
                with cols[col_idx]:
                    # Guardar progreso de items en session_state
                    check_key = f"item_{pedido['id']}_{idx}"
                    
                    if check_key not in st.session_state:
                        st.session_state[check_key] = False
                    
                    completado = st.checkbox(
                        f"{item['cantidad']}x {item['nombre']}",
                        value=st.session_state[check_key],
                        key=check_key,
                        disabled=not es_mio
                    )
                    
                    if item.get('notas'):
                        st.caption(f"📝 {item['notas']}")
            
            # Barra de progreso
            if es_mio:
                items_completados = sum(1 for i in range(len(items)) if st.session_state.get(f"item_{pedido['id']}_{i}", False))
                progreso = items_completados / len(items) if items else 0
                
                st.progress(progreso)
                st.caption(f"Progreso: {items_completados}/{len(items)} items")
            
            # Notas del pedido
            if pedido.get('notas'):
                st.info(f"💬 **Nota:** {pedido['notas']}")
            
            st.divider()

else:
    # No hay pedidos en preparación
    st.success("✨ ¡Sin pedidos en preparación!")
    
    if filtro == 'Mis Pedidos':
        st.info("👉 No tienes pedidos asignados actualmente. Ve a **Pedidos Pendientes** para tomar nuevos pedidos.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📋 Ir a Pedidos Pendientes", use_container_width=True, type="primary"):
                st.switch_page("pages/Pedidos_Pendientes.py")
    else:
        st.info("No hay pedidos en cocina en este momento")

# ============================================
# RESUMEN
# ============================================
if pedidos:
    st.divider()
    
    with st.expander("📊 Estadísticas Detalladas"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("⏱️ Tiempos")
            tiempos = []
            for p in pedidos:
                updated = datetime.fromisoformat(p['updated_at'].replace('Z', '+00:00'))
                ahora_local = datetime.now()
                mins = int((ahora_local - updated.replace(tzinfo=None)).total_seconds() / 60)
                tiempos.append(mins)
            
            if tiempos:
                st.metric("Promedio", f"{sum(tiempos)/len(tiempos):.1f} min")
                st.metric("Más rápido", f"{min(tiempos)} min")
                st.metric("Más lento", f"{max(tiempos)} min")
        
        with col2:
            st.subheader("👨‍🍳 Por Cocinero")
            
            # Obtener nombres de cocineros
            cocineros = {}
            for p in pedidos:
                cocinero_id = p.get('cocinero_id')
                if cocinero_id:
                    if cocinero_id not in cocineros:
                        cocinero = supabase.table('usuarios').select('nombre').eq('id', cocinero_id).execute()
                        if cocinero.data:
                            cocineros[cocinero_id] = cocinero.data[0]['nombre']
                        else:
                            cocineros[cocinero_id] = 'Desconocido'
            
            # Contar por cocinero
            conteo = {}
            for p in pedidos:
                cocinero_id = p.get('cocinero_id')
                nombre = cocineros.get(cocinero_id, 'Sin asignar')
                conteo[nombre] = conteo.get(nombre, 0) + 1
            
            for nombre, count in sorted(conteo.items()):
                st.write(f"{nombre}: {count} pedido(s)")
        
        with col3:
            st.subheader("🍽️ Por Mesa")
            mesas = {}
            for p in pedidos:
                mesa = p['mesa_id']
                mesas[mesa] = mesas.get(mesa, 0) + 1
            
            for mesa, count in sorted(mesas.items()):
                st.write(f"Mesa {mesa}: {count} pedido(s)")

# Auto-refresh cada 5 segundos
if pedidos:
    import time
    time.sleep(5)
    st.rerun()