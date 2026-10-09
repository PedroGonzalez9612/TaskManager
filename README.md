# GestLab

Sistema web para la gestión y análisis de la carga laboral de operarios en empresas: qué se debe hacer, quién lo está haciendo y cuánto trabajo hay en curso.

Proyecto académico de las materias Diseño Orientado a Objetos y Diseño de Interfaces (UCC).

- Alcance del proyecto: [docs/alcance_proyecto.md](docs/alcance_proyecto.md)
- Estado del avance: [docs/avance.md](docs/avance.md)

## Arquitectura

Aplicación web en tres capas, con Flask y MongoDB:

- `app/static/`: interfaz web (HTML, CSS y JavaScript). Es un cliente en el navegador que consume la API REST con `fetch`.
- `app/routes/`: blueprints de Flask que exponen la API REST en JSON y validan la sesión y el rol.
- `app/services/`: reglas de negocio.
- `app/repositories/`: acceso a MongoDB (patrón Repository).
- `app/models/`: clases de dominio y enums.

## Ejecución con Docker (recomendado)

1. Copia el archivo de ejemplo y edita los valores:

   ```bash
   copy .env.example .env
   ```

   Variables importantes:

   | Variable | Para qué sirve |
   |---|---|
   | `SECRET_KEY` | Firma la cookie de sesión. Usa un texto largo y aleatorio. |
   | `SUPERADMIN_CORREO` / `SUPERADMIN_CONTRASENA` | Datos del primer Superadmin, que se crea solo al arrancar si todavía no existe ninguno. |

2. Levanta la aplicación y la base de datos:

   ```bash
   docker compose up --build
   ```

3. Abre `http://localhost:5000` e inicia sesión con el correo y la contraseña del Superadmin.

Para borrar la base de datos de desarrollo y empezar de cero: `docker compose down -v`.

## Ejecución sin Docker

Requiere Python 3.11+ y MongoDB corriendo en `mongodb://localhost:27017`.

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env
python run.py
```

## Roles y primer uso

1. El **Superadmin** registra una empresa (con su logo y sus límites de usuarios) y le crea un Administrador.
2. El **Administrador** entra con su correo y crea a los Operarios de su empresa.
3. El **Administrador** registra requerimientos, crea actividades y las asigna en las vistas *Actividades* y *Equipo*.
4. El **Operario** entra desde el celular y ve su trabajo en tres vistas: *Hoy*, *Semana* y *Resumen*.

Cada rol ve su propia interfaz. Los usuarios de una empresa ven el logo de su empresa en lugar del de GestLab.

## API principal

Todas las rutas (salvo `/auth/login` y `/health`) requieren sesión iniciada.

| Método y ruta | Quién | Descripción |
|---|---|---|
| `POST /auth/login` | Todos | Inicia sesión (`correo`, `contraseña`) |
| `POST /auth/logout` | Todos | Cierra sesión |
| `GET /auth/sesion` | Todos | Usuario actual y datos de su empresa |
| `GET, POST /empresas` | Superadmin | Lista y registra empresas (con `limite_administradores` y `limite_operarios`) |
| `GET, PUT /empresas/<id>` | Superadmin (y Administrador, solo lectura de la suya) | Consulta o edita una empresa |
| `GET, PUT /empresas/<id>/logo` | Ver: usuarios de la empresa · Cambiar: Superadmin | Logo de la empresa (PNG, JPG o WEBP, máx. 512 KB) |
| `GET, POST /usuarios` | Superadmin, Administrador | Lista y crea usuarios de una empresa |
| `GET, POST /requerimientos` · `GET, PUT, DELETE /requerimientos/<id>` | Administrador | Requerimientos de su empresa |
| `GET /actividades` · `GET /actividades/<id>` | Administrador, Operario | Actividades de la empresa (el Operario solo ve las suyas). Filtros: `requerimiento_id`, `fecha_desde`, `fecha_hasta` |
| `POST /actividades` · `PUT, DELETE /actividades/<id>` | Administrador | Crea, edita (incluida la asignación con `operario_ids`) o elimina |
| `POST /actividades/<id>/iniciar` · `/finalizar` | Operario | Ejecución de una actividad asignada |
| `GET /analisis/carga?desde=&hasta=` | Administrador, Operario | Carga por jornada de cada operario |
| `GET /health` | Público | Verificación del servidor |

Las bibliotecas de interfaz (EventCalendar, Chart.js y Lucide) y las fuentes están copiadas dentro de `app/static/`, con sus licencias; la aplicación no descarga nada de internet.
