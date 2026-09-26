# GestLab — contexto del proyecto

Sistema web para la gestión y análisis de la carga laboral de operarios en empresas.
Responde tres preguntas: qué se debe hacer, quién lo está haciendo y cuánto trabajo hay en curso.

## Contexto académico

- Proyecto compartido por dos materias que se evalúan por separado:
  - **Diseño Orientado a Objetos (DOO):** Momento 2 en Semana 10 (cliente-servidor: persistencia,
    concurrencia, hilos, sockets, conexión a BD). Momento 3 en Semanas 15-16 (aplicación web en tres capas).
  - **Diseño de Interfaces (DI):** Semana 10 heurísticas de Nielsen (evaluación del Ser). Semana 15 presentación de la interfaz.
- Un avance técnico de backend NO cuenta automáticamente como avance de DI, ni al revés.
- Semana actual: 8 (actualizar esta línea cada semana).

## Fuentes de verdad (en orden)

1. Syllabus de cada materia: `docs/syllabus/`
2. Documento de alcance (vivo, con bitácora): `docs/alcance_proyecto.md`
3. El código de este repositorio.
4. Lo que indique el usuario en la sesión, si no contradice lo anterior.

Lee `docs/alcance_proyecto.md` antes de implementar cualquier funcionalidad nueva.
Si una tarea contradice o amplía el alcance, detente y avísalo; no lo resuelvas por tu cuenta.

## Stack y ejecución

- Python 3.11+, Flask, MongoDB (pymongo), bcrypt. Docker Compose para desarrollo local.
- Levantar todo: `docker compose up --build` (la app se conecta a Mongo por el host `mongo`).
- Sin Docker: `python run.py` con MongoDB local (`mongodb://localhost:27017`).
- Verificación rápida: `GET /health`.

## Arquitectura (no romper la separación de capas)

- `app/models/`: clases de dominio y enums. Sin acceso a BD ni a Flask.
- `app/repositories/`: único lugar con consultas a MongoDB (patrón Repository).
- `app/services/`: reglas de negocio. Reciben repositorios por constructor.
- `app/routes/`: blueprints que exponen la API REST en JSON. Sin consultas a Mongo ni reglas de negocio.
- `app/static/`: interfaz web (HTML, CSS, JS). Propuesta de estructura: `app/static/operario/`,
  `app/static/admin/`, `app/static/css/`, `app/static/js/`.
- La interfaz es un cliente en el navegador: páginas HTML estáticas que consumen la API con `fetch`.
  Flask las sirve desde el mismo origen. NO se usan plantillas Jinja para generar pantallas.
- Autenticación con la sesión de Flask (cookie). Las rutas de la API también validan el rol.

## Reglas de dominio clave (detalle completo en el alcance)

- Roles: Superadmin (crea empresas y su primer Administrador), Administrador, Operario.
- Una actividad puede asignarse a uno o varios operarios.
- Prioridad en 4 niveles: BAJA, MEDIA, ALTA, URGENTE. URGENTE significa interrumpir la tarea actual.
  El orden se hace por un peso numérico del enum, nunca comparando textos.
- Un operario tiene una sola actividad en ejecución a la vez; para iniciar otra debe pausar o finalizar la actual.
- Cada pausa guarda su motivo. Al finalizar se puede dejar una observación. El historial de pausas es consultable.
- La hora de todo evento (ejecución, asistencia) la pone el servidor, nunca el cliente.
- Turnos: catálogo por empresa; un solo turno por operario, conservando la fecha de cada cambio.
- Jornada: pertenece al día en que inicia el turno. Capacidad = duración del turno menos descanso.
- La carga se calcula por jornada. Alerta cuando supera el 100% de la capacidad.
- Asistencia: el operario marca entrada/salida; el Administrador valida o corrige.
- Indicadores agregados: sumar tiempos y dividir al final; nunca promediar porcentajes.

## Decisiones de diseño abiertas (no implementar sin resolverlas con el agente diseno-oo)

- ¿La ejecución (pausas, tiempos) pertenece a la asignación (operario + actividad) o a la actividad?
- ¿Cómo se reparte el tiempo estimado cuando una actividad tiene varios operarios?

## Convenciones

- PEP 8. Nombres de clases, métodos y variables en español, como el código existente.
- Git: trabajar en ramas `feature/<tema>` desde `develop`; integrar a `develop` por Pull Request; `main` es estable.
- El README todavía dice "TaskManager"; el nombre del proyecto es GestLab.

## Forma de trabajo con el usuario

- El usuario está aprendiendo: explica qué hiciste y por qué, en pasos pequeños y revisables.
- Muestra el diff antes de guardar cambios en archivos existentes.
- No sobrescribas archivos sin preguntar si ya existen.
- Haz solo lo que se pidió; si ves algo más por corregir, repórtalo en vez de cambiarlo.

## Agentes disponibles (`.claude/agents/`)

- `diseno-oo`: diseño y revisión de clases (solo lectura).
- `backend-flask`: servicios y rutas de la API.
- `persistencia-mongo`: repositorios y esquemas de MongoDB.
- `frontend-web`: interfaz HTML/CSS/JS del cliente.
- `revisor-codigo`: revisión de calidad y capas (solo lectura).
- `profesor-doo` y `profesor-interfaces`: validan contra el syllabus de cada materia (solo lectura).
