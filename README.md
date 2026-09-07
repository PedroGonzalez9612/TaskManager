# TaskManager

API REST en Flask + MongoDB para la gestión de tareas de una empresa, siguiendo el flujo:

**Empresa → Usuarios → Requerimiento → Actividad → Asignación → Prioridad → Ejecución → Registro de tiempo → Análisis**

## Arquitectura

Diseño por capas orientado a objetos:

- `app/models`: clases de dominio (Empresa, Usuario, Requerimiento, Actividad, Asignacion, Ejecucion, RegistroTiempo) y enums (Prioridad, EstadoActividad, EstadoEjecucion, EstadoRequerimiento).
- `app/repositories`: acceso a MongoDB (patrón Repository) por entidad.
- `app/services`: reglas de negocio (validaciones, transiciones de estado, orquestación entre repositorios).
- `app/routes`: blueprints de Flask que exponen la API REST.

## Requisitos

- Python 3.11+
- MongoDB corriendo localmente (`mongodb://localhost:27017` por defecto)

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Ejecución

Asegúrate de tener MongoDB corriendo localmente, luego:

```bash
python run.py
```

La API queda disponible en `http://localhost:5000`. Verifica con `GET /health`.

## Flujo de uso (endpoints principales)

1. `POST /empresas` — crear empresa
2. `POST /usuarios` — crear usuario (requiere `empresa_id`)
3. `POST /requerimientos` — crear requerimiento (requiere `empresa_id`)
4. `POST /actividades` — crear actividad (requiere `requerimiento_id`, `prioridad`: ALTA/MEDIA/BAJA)
5. `POST /actividades/<id>/asignar` — asignar actividad a un usuario (`usuario_id`)
6. `POST /actividades/<id>/iniciar` — iniciar ejecución (requiere asignación previa)
7. `POST /actividades/<id>/registros-tiempo` — registrar horas trabajadas (`usuario_id`, `horas`)
8. `POST /actividades/<id>/finalizar` — finalizar ejecución
9. `GET /analisis/horas-por-actividad`, `/analisis/horas-por-usuario`, `/analisis/actividades-por-estado`, `/analisis/requerimientos/<id>/resumen` — reportes

Cada entidad también tiene `GET`, `PUT` y `DELETE` estándar (`/empresas/<id>`, `/usuarios/<id>`, etc.).
