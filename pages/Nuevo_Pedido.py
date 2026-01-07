import streamlit as st
from utils.auth import check_auth, require_role, get_user_id, get_user_name
from utils.database import supabase
from components.sidebar import render_sidebar
from datetime import datetime
import json

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

st.set_page_config(
    page_title="Nuevo Pedido",
    page_icon="➕",
    layout="wide"
)

# Verificar autenticación y rol
check_auth()
require_role(['mesero', 'gerente'])

# Renderizar sidebar
render_sidebar()

st.title("➕ Crear Nuevo Pedido")

# Inicializar carrito en session state
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Obtener menú disponible
@st.cache_data(ttl=300)
def get_menu():
    response = supabase.table('menu')\
        .select('*')\
        .eq('activo', True)\
        .order('categoria')\
        .execute()
    return response.data

menu = get_menu()

if not menu:
    st.error("❌ No hay platos disponibles en el menú")
    st.stop()

# Layout principal
col_menu, col_carrito = st.columns([2, 1])

with col_menu:
    st.subheader("🍔 Menú Disponible")
    
    # Agrupar por categorías
    categorias = {}
    for plato in menu:
        cat = plato['categoria']
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(plato)
    
    # Mostrar por categorías
    for categoria, platos in categorias.items():
        st.markdown(f"### {categoria}")
        
        for plato in platos:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{plato['nombre']}**")
                    if plato.get('descripcion'):
                        st.caption(plato['descripcion'])
                
                with col2:
                    st.write(f"${plato['precio_venta']:,.0f}")
                
                with col3:
                    if st.button("➕ Agregar", key=f"add_{plato['plato_id']}", use_container_width=True):
                        # Verificar si ya está en el carrito
                        existe = False
                        for item in st.session_state.carrito:
                            if item['plato_id'] == plato['plato_id']:
                                item['cantidad'] += 1
                                existe = True
                                break
                        
                        if not existe:
                            st.session_state.carrito.append({
                                'plato_id': plato['plato_id'],
                                'nombre': plato['nombre'],
                                'categoria': plato['categoria'],
                                'precio': plato['precio_venta'],
                                'cantidad': 1,
                                'notas': ''
                            })
                        
                        st.rerun()
        
        st.divider()

with col_carrito:
    st.subheader("🛒 Pedido Actual")
    
    # Número de mesa
    mesa = st.number_input(
        "Número de Mesa",
        min_value=1,
        max_value=100,
        value=1,
        help="Selecciona el número de mesa"
    )
    
    st.divider()
    
    # Mostrar carrito
    if st.session_state.carrito:
        total = 0
        items_to_remove = []
        
        for idx, item in enumerate(st.session_state.carrito):
            with st.container():
                st.markdown(f"**{item['nombre']}**")
                
                col_cant, col_subtotal = st.columns([2, 1])
                
                with col_cant:
                    cantidad = st.number_input(
                        "Cantidad",
                        min_value=1,
                        max_value=50,
                        value=item['cantidad'],
                        key=f"cant_{idx}",
                        label_visibility="collapsed"
                    )
                    st.session_state.carrito[idx]['cantidad'] = cantidad
                
                with col_subtotal:
                    subtotal = item['precio'] * cantidad
                    st.write(f"${subtotal:,.0f}")
                    total += subtotal
                
                # Notas especiales
                notas = st.text_input(
                    "Notas especiales",
                    value=item.get('notas', ''),
                    key=f"notas_{idx}",
                    placeholder="Ej: Sin cebolla",
                    label_visibility="collapsed"
                )
                st.session_state.carrito[idx]['notas'] = notas
                
                # Botón eliminar
                if st.button("🗑️ Eliminar", key=f"del_{idx}", use_container_width=True):
                    items_to_remove.append(idx)
                
                st.divider()
        
        # Eliminar items marcados
        for idx in reversed(items_to_remove):
            st.session_state.carrito.pop(idx)
        
        if items_to_remove:
            st.rerun()
        
        # Total
        st.markdown(f"### Total: ${total:,.0f}")
        
        # Notas generales del pedido
        notas_pedido = st.text_area(
            "Notas del pedido",
            placeholder="Comentarios generales del pedido...",
            help="Información adicional para cocina"
        )
        
        st.divider()
        
        # Botones de acción
        col_cancelar, col_enviar = st.columns(2)
        
        with col_cancelar:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        
        with col_enviar:
            if st.button("✅ Enviar a Cocina", use_container_width=True, type="primary"):
                try:
                    # Crear pedido en la base de datos
                    pedido_data = {
                        'mesa_id': mesa,
                        'mesero_id': get_user_id(),
                        'estado': 'pendiente',
                        'items': json.dumps(st.session_state.carrito),
                        'total': total,
                        'notas': notas_pedido if notas_pedido else None
                    }
                    
                    response = supabase.table('pedidos').insert(pedido_data).execute()
                    
                    if response.data:
                        # Obtener el ID del pedido insertado
                        pedido_id = response.data[0].get('id')
                        
                        # Obtener el pedido completo con numero_pedido
                        pedido_completo = supabase.table('pedidos')\
                            .select('numero_pedido')\
                            .eq('id', pedido_id)\
                            .execute()
                        
                        if pedido_completo.data:
                            numero_pedido = pedido_completo.data[0].get('numero_pedido', 'N/A')
                            st.success(f"✅ Pedido #{numero_pedido} enviado a cocina!")
                        else:
                            st.success("✅ Pedido enviado a cocina!")
                        
                        st.balloons()
                        
                        # Limpiar carrito
                        st.session_state.carrito = []
                        
                        # Esperar un momento y recargar
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Error al crear el pedido")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    else:
        st.info("🛒 El carrito está vacío")
        st.caption("Agrega platos del menú para crear un pedido")

# Botón de recargar menú
if st.button("🔄 Actualizar Menú"):
    st.cache_data.clear()
    st.rerun()