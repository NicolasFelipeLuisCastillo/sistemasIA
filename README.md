# Sistema de Restaurante - Aplicación Completa

Sistema integral de gestión para restaurantes con roles para Gerente, Meseros y Cocineros.

## Características

### Gerente
- Dashboard completo con KPIs
- Gestión de pedidos en tiempo real
- Control de empleados
- Gestión de inventario
- Administración del menú

### Meseros
- Sistema de turnos (entrada/salida)
- Crear y gestionar pedidos
- Ver historial de ventas personales
- Seguimiento de mesas

### Cocineros
- Ver pedidos pendientes
- Marcar pedidos en preparación
- Completar pedidos
- Estadísticas de tiempos de cocina

## Instalación

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

## Usuarios de Prueba

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

## Estructura del Proyecto

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
    │   ├── 01_Dashboard.py       # Dashboard gerencial
    │   └── 02_Pedidos.py         # (Crear esta página)
    │
    ├── mesero/
    │   ├── 01_Mi_Turno.py        # Control de turnos
    │   └── 02_Nuevo_Pedido.py    # Crear pedidos
    │
    └── cocina/
        ├── 01_Pedidos_Pendientes.py  # Pedidos pendientes
        └── 02_En_Preparacion.py       # Pedidos en cocina
```

## Base de Datos

El proyecto requiere las siguientes tablas en Supabase:

- `usuarios` - Usuarios del sistema
- `turnos` - Control de turnos de meseros
- `pedidos` - Pedidos del restaurante
- `menu` - Menú del restaurante
- `inventario` - Control de inventario
- `notificaciones` - Sistema de notificaciones
- `configuracion` - Configuración del sistema

**Nota:** Si ejecutaste el script SQL que te proporcioné, ya tienes todas estas tablas creadas.

## Seguridad

- Las contraseñas se almacenan hasheadas con bcrypt
- Autenticación basada en roles (RLS en Supabase)
- Variables de entorno para credenciales sensibles
- Validación de permisos en cada página

## Próximas Funcionalidades

- [ ] Página de gestión de empleados para gerente
- [ ] Módulo completo de inventario
- [ ] Sistema de reportes exportables
- [ ] Notificaciones push en tiempo real
- [ ] App móvil nativa (Flutter/React Native)
- [ ] Sistema de reservas
- [ ] Integración con sistemas de pago


Este proyecto es de uso privado para tu restaurante.

---

