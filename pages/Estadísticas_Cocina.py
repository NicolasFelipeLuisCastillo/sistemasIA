import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(
    page_title="Estadísticas Cocina",
    page_icon="📊",
    layout="wide"
)

# Ocultar menú automático
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

st.title(f"📊 Estadísticas de Cocina - {get_user_name()}")

# ============================================
# FILTROS
# ============================================
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    fecha_desde = st.date_input(
        "Desde",
        value=date.today() - timedelta(days=7),
        max_value=date.today()
    )

with col2:
    fecha_hasta = st.date_input(
        "Hasta",
        value=date.today(),
        max_value=date.today()
    )

with col3:
    st.write("")
    st.write("")
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ============================================
# OBTENER DATOS
# ============================================
@st.cache_data(ttl=60)
def get_pedidos_completados(fecha_inicio, fecha_fin, cocinero_id):
    """Obtener pedidos completados en el rango de fechas"""
    
    fecha_inicio_str = datetime.combine(fecha_inicio, datetime.min.time()).isoformat()
    fecha_fin_str = datetime.combine(fecha_fin, datetime.max.time()).isoformat()
    
    # Pedidos del cocinero
    response = supabase.table('pedidos')\
        .select('*')\
        .eq('cocinero_id', cocinero_id)\
        .in_('estado', ['listo', 'entregado'])\
        .gte('created_at', fecha_inicio_str)\
        .lte('created_at', fecha_fin_str)\
        .execute()
    
    return response.data if response.data else []

pedidos = get_pedidos_completados(fecha_desde, fecha_hasta, get_user_id())

# ============================================
# KPIs PRINCIPALES
# ============================================
if pedidos:
    col1, col2, col3, col4 = st.columns(4)
    
    # Total pedidos completados
    with col1:
        st.metric("✅ Pedidos Completados", len(pedidos))
    
    # Tiempo promedio de preparación
    with col2:
        tiempos = []
        for p in pedidos:
            if p.get('tiempo_preparacion'):
                try:
                    import re
                    tiempo_valor = str(p['tiempo_preparacion']).strip()
                    
                    # Patron para parsear intervalos de PostgreSQL
                    # Formato puede ser: "0:12:34", "1:23:45.678", "-1 day, 23:50:00", etc.
                    
                    # Si contiene "day", manejar por separado
                    if 'day' in tiempo_valor:
                        # Extraer días y tiempo
                        match = re.search(r'(-?\d+)\s+day[s]?,?\s+(\d+):(\d+):(\d+)', tiempo_valor)
                        if match:
                            dias = int(match.group(1))
                            horas = int(match.group(2))
                            mins = int(match.group(3))
                            
                            # Si hay días negativos, algo está mal, usar valor absoluto
                            total_mins = abs(dias * 24 * 60 + horas * 60 + mins)
                            
                            if total_mins > 0 and total_mins < 300:  # Entre 0 y 5 horas
                                tiempos.append(total_mins)
                    else:
                        # Formato simple HH:MM:SS
                        partes = tiempo_valor.replace('-', '').split(':')
                        if len(partes) >= 2:
                            horas = int(partes[0])
                            mins = int(partes[1])
                            
                            total_mins = abs(horas * 60 + mins)
                            
                            if total_mins > 0 and total_mins < 300:
                                tiempos.append(total_mins)
                
                except (ValueError, IndexError, AttributeError) as e:
                    # Si hay error, ignorar este tiempo
                    continue
        
        if tiempos:
            promedio = sum(tiempos) / len(tiempos)
            st.metric("⏱️ Tiempo Promedio", f"{promedio:.1f} min")
        else:
            st.metric("⏱️ Tiempo Promedio", "N/A")
    
    # Items preparados
    with col3:
        total_items = 0
        for p in pedidos:
            items = p['items']
            if isinstance(items, str):
                items = json.loads(items)
            total_items += sum(item['cantidad'] for item in items)
        
        st.metric("🍽️ Items Preparados", total_items)
    
    # Pedidos por día
    with col4:
        dias = (fecha_hasta - fecha_desde).days + 1
        promedio_dia = len(pedidos) / dias if dias > 0 else 0
        st.metric("📅 Promedio/Día", f"{promedio_dia:.1f}")
    
    st.divider()
    
    # ============================================
    # GRÁFICOS
    # ============================================
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Tendencias",
        "⏱️ Tiempos",
        "🍽️ Platos",
        "🏆 Rendimiento"
    ])
    
    with tab1:
        st.subheader("📈 Pedidos por Día")
        
        # Preparar datos
        df = pd.DataFrame(pedidos)
        df['fecha'] = pd.to_datetime(df['created_at']).dt.date
        pedidos_por_dia = df.groupby('fecha').size().reset_index(name='pedidos')
        
        # Gráfico de línea
        fig = px.line(
            pedidos_por_dia,
            x='fecha',
            y='pedidos',
            markers=True,
            title='Pedidos Completados por Día'
        )
        
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Pedidos",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Pedidos por hora del día
        st.subheader("📊 Pedidos por Hora del Día")
        
        df['hora'] = pd.to_datetime(df['created_at']).dt.hour
        pedidos_por_hora = df.groupby('hora').size().reset_index(name='pedidos')
        
        fig = px.bar(
            pedidos_por_hora,
            x='hora',
            y='pedidos',
            title='Distribución por Hora'
        )
        
        fig.update_layout(
            xaxis_title="Hora del día",
            yaxis_title="Pedidos",
            xaxis=dict(tickmode='linear', tick0=0, dtick=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("⏱️ Análisis de Tiempos")
        
        if tiempos:
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma de tiempos
                fig = px.histogram(
                    tiempos,
                    nbins=20,
                    title='Distribución de Tiempos de Preparación',
                    labels={'value': 'Tiempo (minutos)', 'count': 'Frecuencia'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Estadísticas
                st.markdown("**Estadísticas:**")
                st.write(f"• Más rápido: {min(tiempos)} min")
                st.write(f"• Más lento: {max(tiempos)} min")
                st.write(f"• Mediana: {sorted(tiempos)[len(tiempos)//2]} min")
            
            with col2:
                # Box plot
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=tiempos,
                    name='Tiempos',
                    boxmean='sd'
                ))
                
                fig.update_layout(
                    title='Distribución de Tiempos (Box Plot)',
                    yaxis_title='Tiempo (minutos)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Rangos
                st.markdown("**Por Rango:**")
                rapidos = len([t for t in tiempos if t <= 10])
                normales = len([t for t in tiempos if 10 < t <= 15])
                lentos = len([t for t in tiempos if t > 15])
                
                st.write(f"• 🟢 Rápido (≤10 min): {rapidos} ({rapidos/len(tiempos)*100:.1f}%)")
                st.write(f"• 🟡 Normal (10-15 min): {normales} ({normales/len(tiempos)*100:.1f}%)")
                st.write(f"• 🔴 Lento (>15 min): {lentos} ({lentos/len(tiempos)*100:.1f}%)")
        else:
            st.info("No hay datos de tiempo de preparación disponibles")
    
    with tab3:
        st.subheader("🍽️ Platos Más Preparados")
        
        # Contar platos
        conteo_platos = {}
        for p in pedidos:
            items = p['items']
            if isinstance(items, str):
                items = json.loads(items)
            
            for item in items:
                nombre = item['nombre']
                cantidad = item['cantidad']
                conteo_platos[nombre] = conteo_platos.get(nombre, 0) + cantidad
        
        # Top 10
        top_platos = sorted(conteo_platos.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_platos:
            df_platos = pd.DataFrame(top_platos, columns=['Plato', 'Cantidad'])
            
            fig = px.bar(
                df_platos,
                x='Cantidad',
                y='Plato',
                orientation='h',
                title='Top 10 Platos Más Preparados',
                color='Cantidad',
                color_continuous_scale='Greens'
            )
            
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla detallada
            st.markdown("**Detalle Completo:**")
            st.dataframe(
                df_platos,
                use_container_width=True,
                hide_index=True
            )
    
    with tab4:
        st.subheader("🏆 Rendimiento Personal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Resumen del Período")
            
            dias_trabajados = len(df['fecha'].unique())
            
            st.metric("📅 Días trabajados", dias_trabajados)
            st.metric("✅ Total pedidos", len(pedidos))
            st.metric("🍽️ Total items", total_items)
            
            if dias_trabajados > 0:
                st.metric("📈 Pedidos/día", f"{len(pedidos)/dias_trabajados:.1f}")
                st.metric("🍽️ Items/día", f"{total_items/dias_trabajados:.1f}")
        
        with col2:
            st.markdown("### 🎯 Objetivos")
            
            # Definir objetivos
            objetivo_pedidos_dia = 15
            objetivo_tiempo_promedio = 12
            
            # Calcular cumplimiento
            pedidos_dia_actual = len(pedidos) / dias if dias > 0 else 0
            cumplimiento_pedidos = (pedidos_dia_actual / objetivo_pedidos_dia * 100) if objetivo_pedidos_dia > 0 else 0
            
            st.progress(min(cumplimiento_pedidos / 100, 1.0))
            st.caption(f"Objetivo: {objetivo_pedidos_dia} pedidos/día")
            st.caption(f"Actual: {pedidos_dia_actual:.1f} pedidos/día")
            
            st.divider()
            
            if tiempos:
                tiempo_actual = sum(tiempos) / len(tiempos)
                # Invertido porque menor tiempo es mejor
                cumplimiento_tiempo = (objetivo_tiempo_promedio / tiempo_actual * 100) if tiempo_actual > 0 else 0
                
                st.progress(min(cumplimiento_tiempo / 100, 1.0))
                st.caption(f"Objetivo: ≤{objetivo_tiempo_promedio} min promedio")
                st.caption(f"Actual: {tiempo_actual:.1f} min promedio")
        
        st.divider()
        
        # Tabla de mejor día
        st.markdown("### 🌟 Mejor Día")
        
        mejor_dia = pedidos_por_dia.loc[pedidos_por_dia['pedidos'].idxmax()]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 Fecha", mejor_dia['fecha'].strftime('%d/%m/%Y'))
        with col2:
            st.metric("✅ Pedidos", int(mejor_dia['pedidos']))
        with col3:
            # Items de ese día
            pedidos_dia = [p for p in pedidos if pd.to_datetime(p['created_at']).date() == mejor_dia['fecha']]
            items_dia = 0
            for p in pedidos_dia:
                items = p['items']
                if isinstance(items, str):
                    items = json.loads(items)
                items_dia += sum(item['cantidad'] for item in items)
            st.metric("🍽️ Items", items_dia)

else:
    # Sin datos
    st.info(f"📊 No hay pedidos completados en el período {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}")
    st.caption("Completa algunos pedidos para ver estadísticas aquí")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋 Ir a Pedidos Pendientes", use_container_width=True, type="primary"):
            st.switch_page("pages/Pedidos_Pendientes.py")