import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Mi Turno",
    page_icon="🕐",
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

st.title(f"🕐 Mi Turno - {get_user_name()}")

# Obtener turno activo del día
def get_turno_activo():
    """Obtener turno activo del usuario para hoy"""
    try:
        response = supabase.table('turnos')\
            .select('*')\
            .eq('mesero_id', get_user_id())\
            .eq('fecha', date.today().isoformat())\
            .eq('estado', 'activo')\
            .execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error al obtener turno: {str(e)}")
        return None

turno = get_turno_activo()

# Si no hay turno activo
if not turno:
    st.info("👋 No has iniciado tu turno hoy")
    
    # Mostrar historial de turnos anteriores
    with st.expander("📊 Ver turnos anteriores"):
        try:
            turnos_anteriores = supabase.table('turnos')\
                .select('*')\
                .eq('mesero_id', get_user_id())\
                .eq('estado', 'finalizado')\
                .order('fecha', desc=True)\
                .limit(10)\
                .execute()
            
            if turnos_anteriores.data:
                for t in turnos_anteriores.data:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        fecha_turno = datetime.fromisoformat(t['fecha']).strftime("%d/%m/%Y")
                        st.write(f"📅 **{fecha_turno}**")
                    
                    with col2:
                        entrada = datetime.fromisoformat(t['hora_entrada'].replace('Z', '+00:00'))
                        salida = datetime.fromisoformat(t['hora_salida'].replace('Z', '+00:00')) if t.get('hora_salida') else None
                        
                        st.write(f"⏰ {entrada.strftime('%I:%M %p')}")
                        if salida:
                            st.caption(f"hasta {salida.strftime('%I:%M %p')}")
                    
                    with col3:
                        if salida:
                            duracion = salida - entrada
                            horas = int(duracion.total_seconds() // 3600)
                            minutos = int((duracion.total_seconds() % 3600) // 60)
                            st.write(f"⏱️ {horas}h {minutos}m")
                    
                    st.divider()
            else:
                st.caption("No hay turnos anteriores registrados")
        except Exception as e:
            st.error(f"Error al cargar historial: {str(e)}")
    
    st.divider()
    
    # Botón para iniciar turno
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🟢 Iniciar Turno")
        st.caption(f"📅 {date.today().strftime('%A, %d de %B de %Y')}")
        st.caption(f"⏰ {datetime.now().strftime('%I:%M %p')}")
        
        if st.button("🟢 Registrar Entrada", use_container_width=True, type="primary"):
            try:
                nuevo_turno = {
                    'mesero_id': get_user_id(),
                    'fecha': date.today().isoformat(),
                    'hora_entrada': datetime.now().isoformat(),
                    'estado': 'activo'
                }
                
                response = supabase.table('turnos').insert(nuevo_turno).execute()
                
                if response.data:
                    st.success("✅ ¡Turno iniciado correctamente!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Error al iniciar turno")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Si hay turno activo
else:
    # Calcular tiempo trabajado
    entrada = datetime.fromisoformat(turno['hora_entrada'].replace('Z', '+00:00'))
    ahora = datetime.now(entrada.tzinfo)
    tiempo_trabajado = ahora - entrada
    horas = int(tiempo_trabajado.total_seconds() // 3600)
    minutos = int((tiempo_trabajado.total_seconds() % 3600) // 60)
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "⏰ Hora de Entrada",
            entrada.strftime("%I:%M %p")
        )
    
    with col2:
        st.metric(
            "⏱️ Tiempo Trabajado",
            f"{horas}h {minutos}m"
        )
    
    with col3:
        st.metric(
            "📅 Fecha",
            date.today().strftime("%d/%m/%Y")
        )
    
    st.divider()
    
    # Estadísticas del turno
    st.subheader("📊 Resumen del Turno")
    
    # Obtener pedidos del turno
    try:
        response = supabase.table('pedidos')\
            .select('*')\
            .eq('mesero_id', get_user_id())\
            .gte('created_at', turno['hora_entrada'])\
            .execute()
        
        pedidos = response.data if response.data else []
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Pedidos Totales", len(pedidos))
        
        with col2:
            pedidos_entregados = [p for p in pedidos if p['estado'] == 'entregado']
            st.metric("✅ Entregados", len(pedidos_entregados))
        
        with col3:
            total_ventas = sum(p['total'] for p in pedidos_entregados)
            st.metric("💰 Ventas", f"${total_ventas:,.0f}")
        
        with col4:
            ticket_promedio = total_ventas / len(pedidos_entregados) if pedidos_entregados else 0
            st.metric("🎫 Ticket Promedio", f"${ticket_promedio:,.0f}")
        
        st.divider()
        
        # Detalle de pedidos del turno
        if pedidos:
            st.subheader("📋 Detalle de Pedidos")
            
            # Tabs por estado
            tab_activos, tab_completados, tab_todos = st.tabs([
                "🔥 Activos",
                "✅ Completados",
                "📋 Todos"
            ])
            
            with tab_activos:
                pedidos_activos = [p for p in pedidos if p['estado'] in ['pendiente', 'en_cocina', 'listo']]
                
                if pedidos_activos:
                    for pedido in pedidos_activos:
                        with st.container():
                            col_num, col_mesa, col_estado, col_total, col_tiempo = st.columns([1, 1, 2, 1, 1])
                            
                            with col_num:
                                st.write(f"**#{pedido['numero_pedido']}**")
                            
                            with col_mesa:
                                st.write(f"🍽️ Mesa {pedido['mesa_id']}")
                            
                            with col_estado:
                                estado_emoji = {
                                    'pendiente': '⏳ Pendiente',
                                    'en_cocina': '🔥 En Cocina',
                                    'listo': '✅ Listo'
                                }
                                estado_color = {
                                    'pendiente': '#FFA500',
                                    'en_cocina': '#FF6B6B',
                                    'listo': '#51CF66'
                                }
                                estado_text = estado_emoji.get(pedido['estado'], pedido['estado'])
                                color = estado_color.get(pedido['estado'], '#888')
                                st.markdown(f"<span style='color: {color};'>**{estado_text}**</span>", unsafe_allow_html=True)
                            
                            with col_total:
                                st.write(f"${pedido['total']:,.0f}")
                            
                            with col_tiempo:
                                created = datetime.fromisoformat(pedido['created_at'].replace('Z', '+00:00'))
                                mins = int((ahora - created).total_seconds() / 60)
                                st.caption(f"{mins} min")
                            
                            st.divider()
                else:
                    st.info("No hay pedidos activos")
            
            with tab_completados:
                if pedidos_entregados:
                    for pedido in pedidos_entregados:
                        with st.container():
                            col_num, col_mesa, col_total, col_tiempo = st.columns([1, 1, 1, 1])
                            
                            with col_num:
                                st.write(f"**#{pedido['numero_pedido']}**")
                            
                            with col_mesa:
                                st.write(f"🍽️ Mesa {pedido['mesa_id']}")
                            
                            with col_total:
                                st.write(f"💰 ${pedido['total']:,.0f}")
                            
                            with col_tiempo:
                                created = datetime.fromisoformat(pedido['created_at'].replace('Z', '+00:00'))
                                st.caption(created.strftime("%I:%M %p"))
                            
                            st.divider()
                else:
                    st.info("No hay pedidos completados aún")
            
            with tab_todos:
                for pedido in pedidos:
                    with st.container():
                        col_num, col_mesa, col_estado, col_total = st.columns([1, 1, 2, 1])
                        
                        with col_num:
                            st.write(f"**#{pedido['numero_pedido']}**")
                        
                        with col_mesa:
                            st.write(f"🍽️ Mesa {pedido['mesa_id']}")
                        
                        with col_estado:
                            st.write(pedido['estado'])
                        
                        with col_total:
                            st.write(f"${pedido['total']:,.0f}")
                        
                        st.divider()
        
    except Exception as e:
        st.error(f"Error al cargar pedidos: {str(e)}")
    
    st.divider()
    
    # Botón finalizar turno
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔴 Finalizar Turno")
        
        # Verificar si hay pedidos activos
        pedidos_activos = [p for p in pedidos if p['estado'] in ['pendiente', 'en_cocina', 'listo']]
        
        if pedidos_activos:
            st.warning(f"⚠️ Tienes {len(pedidos_activos)} pedido(s) activo(s)")
            st.caption("Asegúrate de completar todos los pedidos antes de finalizar tu turno")
        
        if st.button("🔴 Finalizar Turno", use_container_width=True, type="primary"):
            if pedidos_activos:
                st.error("❌ No puedes finalizar el turno con pedidos activos")
            else:
                try:
                    supabase.table('turnos').update({
                        'hora_salida': datetime.now().isoformat(),
                        'estado': 'finalizado'
                    }).eq('id', turno['id']).execute()
                    
                    st.success("✅ ¡Turno finalizado correctamente!")
                    st.info(f"⏱️ Trabajaste {horas}h {minutos}m hoy")
                    st.balloons()
                    
                    # Esperar y recargar
                    import time
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Botón de actualizar
st.divider()
if st.button("🔄 Actualizar Datos", use_container_width=True):
    st.rerun()