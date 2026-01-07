# 🍽️ Sistema de Restaurante - Aplicación Completa

Sistema integral de gestión para restaurantes con roles para Gerente, Meseros y Cocineros.

## 📋 Características

### 👔 Gerente
- Dashboard completo con KPIs
- Gestión de pedidos en tiempo real
- Control de empleados
- Gestión de inventario
- Administración del menú

### 🍽️ Meseros
- Sistema de turnos (entrada/salida)
- Crear y gestionar pedidos
- Ver historial de ventas personales
- Seguimiento de mesas

### 👨‍🍳 Cocineros
- Ver pedidos pendientes
- Marcar pedidos en preparación
- Completar pedidos
- Estadísticas de tiempos de cocina

## 🚀 Instalación

### 1. Crear entorno virtual (recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
python -m streamlit run Home.py
```

La aplicación se abrirá en http://localhost:8501

## 👥 Usuarios de Prueba

La aplicación viene con 3 usuarios pre-configurados:

**Gerente:**
- Email: `gerente@test.com`
- Password: `admin123`

**Mesero:**
- Email: `mesero@test.com`
- Password: `admin123`

**Cocinero:**
- Email: `cocinero@test.com`
- Password: `admin123`

## 📁 Estructura del Proyecto

```
app-restaurante/
├── Home.py                          # Página principal (login)
├── requirements.txt                 # Dependencias
├── .env.example                     # Ejemplo de variables de entorno
├── .gitignore                       # Archivos a ignorar en Git
│
├── utils/                           # Utilidades
│   ├── __init__.py
│   ├── auth.py                      # Sistema de autenticación
│   └── database.py                  # Conexión a Supabase
│
├── components/                      # Componentes reutilizables
│   ├── __init__.py
│   └── sidebar.py                   # Barra lateral de navegación
│
└── pages/                           # Páginas de la aplicación
    ├── gerente/
    │   ├── 01_📊_Dashboard.py       # Dashboard gerencial
    │   └── 02_📋_Pedidos.py         # (Crear esta página)
    │
    ├── mesero/
    │   ├── 01_🕐_Mi_Turno.py        # Control de turnos
    │   └── 02_➕_Nuevo_Pedido.py    # Crear pedidos
    │
    └── cocina/
        ├── 01_📋_Pedidos_Pendientes.py  # Pedidos pendientes
        └── 02_🔥_En_Preparacion.py       # Pedidos en cocina
```

## 🗄️ Base de Datos

El proyecto requiere las siguientes tablas en Supabase:

- `usuarios` - Usuarios del sistema
- `turnos` - Control de turnos de meseros
- `pedidos` - Pedidos del restaurante
- `menu` - Menú del restaurante
- `inventario` - Control de inventario
- `notificaciones` - Sistema de notificaciones
- `configuracion` - Configuración del sistema

**Nota:** Si ejecutaste el script SQL que te proporcioné, ya tienes todas estas tablas creadas.

## 🔐 Seguridad

- Las contraseñas se almacenan hasheadas con bcrypt
- Autenticación basada en roles (RLS en Supabase)
- Variables de entorno para credenciales sensibles
- Validación de permisos en cada página

## 🚀 Despliegue en Producción

### Opción 1: Streamlit Cloud (Gratis)

1. Sube el código a GitHub
2. Ve a https://share.streamlit.io
3. Conecta tu repositorio
4. Configura los secretos en Settings → Secrets:

```toml
SUPABASE_URL = "tu_url"
SUPABASE_KEY = "tu_key"
```

5. Deploy automático

### Opción 2: Render.com

1. Crea cuenta en https://render.com
2. New → Web Service
3. Conecta tu repositorio de GitHub
4. Configura:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run Home.py --server.port $PORT --server.address 0.0.0.0`
   - Agrega variables de entorno

## 📝 Próximas Funcionalidades

- [ ] Página de gestión de empleados para gerente
- [ ] Módulo completo de inventario
- [ ] Sistema de reportes exportables
- [ ] Notificaciones push en tiempo real
- [ ] App móvil nativa (Flutter/React Native)
- [ ] Sistema de reservas
- [ ] Integración con sistemas de pago

## 🐛 Solución de Problemas

### Error: "No module named 'supabase'"
```bash
pip install supabase
```

### Error: "SUPABASE_URL not found"
Verifica que el archivo `.env` esté en la raíz del proyecto y contenga las variables correctas.

### La app no se actualiza en tiempo real
- Usa el botón "🔄 Actualizar" en cada página
- Activa "Auto-refresh" en las páginas de cocina

### Problemas de autenticación
Verifica que los usuarios existen en la tabla `usuarios` de Supabase:

```sql
SELECT * FROM usuarios;
```

## 📞 Soporte

Si tienes problemas o preguntas:
1. Revisa que todas las dependencias estén instaladas
2. Verifica las credenciales de Supabase
3. Revisa los logs en la consola

## 📄 Licencia

Este proyecto es de uso privado para tu restaurante.

---

