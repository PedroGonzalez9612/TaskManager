# GestLab — contexto del proyecto

Sistema web para la gestión y análisis de la carga laboral de operarios en empresas.
Responde tres preguntas: qué se debe hacer, quién lo está haciendo y cuánto trabajo hay en curso.

## Contexto académico

- Proyecto compartido por dos materias que se evalúan por separado:
  - **Diseño Orientado a Objetos (DOO):** Momento 2 en Semana 10 (cliente-servidor: persistencia,
    concurrencia, hilos, sockets, conexión a BD). Momento 3 en Semanas 15-16 (aplicación web en tres capas).
  - **Diseño de Interfaces (DI):** Semana 10 heurísticas de Nielsen (evaluación del Ser). Semana 15 presentación de la interfaz.
- Un avance técnico de backend NO cuenta automáticamente como avance de DI, ni al revés.
- Semana actual: 9 (actualizar esta línea cada semana).

## Fuentes de verdad (en orden)

1. Syllabus de cada materia: `docs/Syllabus/`. Enunciados de las entregas: `docs/enunciados/`.
2. Documento de alcance (vivo, con bitácora): `docs/alcance_proyecto.md`
   Explicación de cómo funciona el sistema, sin código: `docs/logica_de_negocio.md` (se actualiza
   cuando cambia una regla del alcance; si no coinciden, manda el alcance).
3. El código de este repositorio.
4. Lo que indique el usuario en la sesión, si no contradice lo anterior.

Lee `docs/alcance_proyecto.md` antes de implementar cualquier funcionalidad nueva.
El estado de lo construido (por etapa y por criterio del MVP) está en `docs/avance.md`; actualízalo al cerrar cada etapa.
Si una tarea contradice o amplía el alcance, detente y avísalo; no lo resuelvas por tu cuenta.
Las reglas viven en el alcance: este archivo y los agentes apuntan a sus secciones en lugar de copiarlas.
Cuando una regla cambie, se actualiza primero el alcance (con su entrada en la bitácora).

## Stack y ejecución

- Python 3.11+, Flask, MongoDB (pymongo), bcrypt. Docker Compose para desarrollo local.
- Levantar todo: `docker compose up --build` (la app se conecta a Mongo por el host `mongo`).
- Sin Docker: `python run.py` con MongoDB local (`mongodb://localhost:27017`).
- Verificación rápida: `GET /health`. La interfaz entra por `http://localhost:5000/` (redirige al login).
- El `.env` necesita `SECRET_KEY`, `SUPERADMIN_CORREO` y `SUPERADMIN_CONTRASENA` (ver `.env.example`).
  El primer Superadmin se crea solo al arrancar, si todavía no existe ninguno.

## Arquitectura (no romper la separación de capas)

- `app/models/`: clases de dominio y enums. Sin acceso a BD ni a Flask. Las clases con transiciones
  (`Actividad`, `Asignacion`, `Ejecucion`, `Pausa`) validan sus propios cambios de estado y reciben
  la hora como parámetro (`ahora`); se reconstruyen con `desde_documento`.
- `app/repositories/`: único lugar con consultas a MongoDB (patrón Repository).
- `app/services/`: reglas de negocio. Reciben repositorios por constructor. Los servicios de
  actividades se arman en un solo lugar, `composicion.py` (`construir_servicios`). El estado de una
  actividad se calcula en `estado_actividad.py`, a partir de las ejecuciones de sus operarios.
- `app/routes/`: blueprints que exponen la API REST en JSON. Sin consultas a Mongo ni reglas de negocio.
- `app/static/`: interfaz web. `login.html`; pantallas por rol en `superadmin/`, `admin/` y `operario/`
  (un `.html` y su `.js`); compartido en `js/api.js` (llamadas a la API, constantes),
  `js/layout.js` (menú por rol, diálogos, avisos) y `css/estilos.css` (colores y tipografía como variables
  en `:root`, con los valores de las Secciones 6.3 y 6.4 del alcance); archivos de fuentes en `fuentes/`.
  Sistema de composición (alcance, Sección 6.2): espacios solo con `--e1` a `--e7`; ancho de la columna con
  `ancho-angosto` o `ancho-medio` en `<body>` (la barra superior se alinea sola); cifras con la clase
  `cifra` (misma fuente, números de ancho fijo) y códigos con `codigo` (monoespaciada).
  Componentes repetidos en `js/componentes.js` (logo, avatar, medidor de límite).
  ESTADO DEL REDISEÑO "Calma operativa" (plan en `docs/plan_rediseno_calma_operativa.md`): Etapa 1
  (alcance) y Etapa 2 (base visual: colores, Figtree, sombras, logo del tablero) y Etapa 3 (Hoy del Operario como línea de tiempo, en `operario/hoy.js`, clases `linea-*` y `tarjeta-*`) hechas, pendientes del visto bueno del
  usuario. Etapa 4 (backend) a medias: ver "Próximos pasos" en `docs/avance.md`. Etapas 5 a 7
  pendientes. Ya existen turnos y asistencia (marca de entrada y salida en Hoy; turnos y validación
  en Usuarios del Administrador) y el calendario rediseñado. Hasta que se apliquen, las pantallas siguen con requerimientos en lugar de proyectos,
  Equipo como horario por columnas, y Hoy sin pausar, turnos, asistencia ni "Reportar actividad",
  aunque la API ya tiene pausar, reanudar, cancelar, devolver y proyectos.
  Se avanza etapa por etapa, con la aprobación del usuario.
- La interfaz es un cliente en el navegador: páginas HTML estáticas que consumen la API con `fetch`.
  Flask las sirve desde el mismo origen. NO se usan plantillas Jinja para generar pantallas.
- Autenticación con la sesión de Flask (cookie): `/auth/login`, `/auth/logout`, `/auth/sesion`.
  Cada ruta se protege con `@requiere_rol(...)` (`app/utils/seguridad.py`); las reglas de "a qué empresa
  puede acceder" van en los servicios, que reciben el usuario de la sesión como `solicitante`.
- Protección contra CSRF: toda petición que cambia datos debe traer el encabezado
  `X-Requested-With: GestLab` (lo pone `pedirApi` en `js/api.js`; lo exige `exigir_peticion_propia` en
  `app/utils/seguridad.py`). Cualquier llamada nueva a la API debe pasar por `pedirApi`.
- Errores de negocio: lanzar subclases de `ErrorApi` (`app/utils/errors.py`); un solo manejador las
  convierte en JSON con su código HTTP.
- Bibliotecas de interfaz copiadas en `app/static/vendor/` (sin CDN ni compilación): EventCalendar
  (horarios), Chart.js (gráficas) y Lucide (íconos, solo los usados, en `vendor/lucide/iconos.js`).
- Piezas compartidas de la interfaz: `js/actividades-comun.js` (señales de prioridad y estado, detalle
  de actividad, opciones del calendario, modo de color) y `js/formulario-actividad.js` (crear y editar).

## Reglas de dominio clave (detalle completo en el alcance)

- Roles: Superadmin (crea empresas y sus Administradores), Administrador (crea Operarios y
  Administradores de su empresa), Operario.
- Cada empresa tiene un límite de Administradores y otro de Operarios, definido por el Superadmin.
- Marca blanca: los usuarios de una empresa ven su logo y nombre en lugar de GestLab (no en el login).
- El trabajo se organiza en actividades y proyectos; una actividad es independiente o de un solo proyecto.
  Ya no hay requerimientos.
- Una actividad puede asignarse a uno o varios operarios.
- Cada actividad es de hora fija (no se mueve) o de horario flexible (el Operario decide cuándo).
- Orden del día: sugerido por prioridad y luego por hora. El Operario reordena solo las que no tienen
  hora; las urgentes van siempre arriba.
- Al llegar una hora fija, el Operario pausa la que lleva, con motivo "Actividad de hora fija", y la
  retoma después. El aviso sale 10 minutos antes.
- Lo que no se hizo: de horario flexible, se reprograma a la siguiente jornada (actividad reprogramada); con hora
  fija, queda No realizada, que es definitivo.
- Solo el Administrador cancela, con motivo. El Operario puede devolver una actividad antes de iniciarla,
  con motivo. Nada se borra.
- El tiempo estimado es de la actividad completa; no se divide entre los operarios asignados.
- Prioridad en 4 niveles: BAJA, MEDIA, ALTA, URGENTE. URGENTE significa interrumpir la tarea actual.
  El orden se hace por un peso numérico del enum, nunca comparando textos.
- Un operario tiene una sola actividad en ejecución a la vez; para iniciar otra debe pausar o finalizar la actual.
  Lo garantiza un índice único en la base de datos, además del servicio.
- La ejecución pertenece a la asignación (operario + actividad): cada operario tiene su tiempo, sus
  pausas y su observación. Una actividad con varios operarios termina cuando todos finalizan.
- Nada se borra: las asignaciones se retiran o se devuelven, y las actividades se cancelan con motivo.
- Una actividad de hora fija no se pausa ni se reprograma; la urgente no la interrumpe.
- Motivos de pausa y de cancelación: listas por empresa que se llenan con lo escrito en "Otro".
- Capacidad de la jornada: la del turno vigente del operario (duración menos descanso). Sin turno, 7 h
  (`CAPACIDAD_JORNADA_MIN` en `carga_service.py`).
- Cada pausa guarda su motivo. Al finalizar se puede dejar una observación. El historial de pausas es consultable.
- La hora de todo evento (ejecución, asistencia) la pone el servidor, nunca el cliente.
- Turnos: catálogo por empresa; un solo turno por operario, conservando la fecha de cada cambio.
- Jornada: pertenece al día en que inicia el turno. Capacidad = duración del turno menos descanso.
- La carga se calcula por jornada. Alerta cuando supera el 100% de la capacidad.
- Asistencia: el operario marca entrada/salida; el Administrador valida o corrige.
- Indicadores agregados: sumar tiempos y dividir al final; nunca promediar porcentajes.

## Decisiones de diseño abiertas (no implementar sin resolverlas con el agente diseno-oo)

- Ninguna por ahora. H1 quedó resuelta el 2026-10-10: la ejecución pertenece a la asignación
  (operario + actividad). Las reglas que salen de esa decisión están en la Sección 5.1 del alcance.

## Convenciones

- PEP 8. Nombres de clases, métodos y variables en español, como el código existente.
- Vocabulario: el glosario está en la Sección 14 del alcance. Cada cosa se llama de una sola manera en
  pantallas, API, código y documentos (por ejemplo: actividad reprogramada, días de retraso, actividad
  independiente, horario flexible, línea de tiempo, tarjeta). Términos técnicos y claros; nada coloquial.
  Antes de introducir un término nuevo, agrégalo al glosario.
- Git: trabajar en ramas `feature/<tema>` desde `develop`; integrar a `develop` por Pull Request; `main` es estable.
- Interfaz (detalle en la Sección 6.2 del alcance): toda pantalla con sesión usa el marco de
  `layout.js` (`iniciarPaginaProtegida`): barra superior con pestañas, barra inferior en celular.
  Cada pantalla muestra primero su información; crear o editar se hace en un `<dialog>`. Una vista se
  agrega en `VISTAS_POR_ROL` solo cuando su pantalla existe. Los elementos se crean con `crearElemento`
  y `crearConIcono` (texto siempre con `textContent`, nunca `innerHTML` con datos del usuario).
- La interfaz no debe verse genérica: antes de construir una pantalla nueva, proponer su composición.
- Construir en el orden lógico del flujo (lo que el Administrador crea es lo que el Operario usa):
  primero lo que genera los datos, después lo que los consume.

## Forma de trabajo con el usuario

- El usuario está aprendiendo: explica qué hiciste y por qué, en pasos pequeños y revisables.
- Muestra el diff antes de guardar cambios en archivos existentes.
- No sobrescribas archivos sin preguntar si ya existen.
- Haz solo lo que se pidió; si ves algo más por corregir, repórtalo en vez de cambiarlo.

## Herramientas de desarrollo (`herramientas/`)

- Dependencias solo de desarrollo en `requirements-dev.txt` (no van en la imagen de Docker).
  Navegador para las capturas: uno Chromium ya instalado (Brave, Edge, Chrome) con `CAPTURAS_NAVEGADOR`
  en el `.env`, o el de Playwright con `python -m playwright install chromium`.
- `contraste.py`: contraste WCAG entre colores (HEX o variables de `:root`).
- `capturas.py`: capturas de las pantallas listadas en `pantallas.json`, en celular y escritorio, con
  versiones desenfocada y en grises. Usa los usuarios de prueba `CAPTURAS_*` del `.env`.
  Las capturas quedan en `herramientas/capturas/` (fuera de Git).
- Al crear una pantalla nueva, agrégala en `herramientas/pantallas.json`.
- Pruebas automáticas en `tests/` (pytest y mongomock, sin MongoDB real): `python -m pytest`.
  Toda regla nueva de modelos o servicios lleva su prueba.
- Análisis de calidad con SonarQube (servidor local en `http://localhost:9000`, proyecto `GestLab`,
  configuración en `sonar-project.properties`, token en `SONAR_TOKEN` del `.env`). Tres pasos, desde la raíz:
  `python -m pytest --cov=app --cov-report=xml`, luego `pysonar` con `SONAR_TOKEN` en el entorno, y
  `python herramientas/sonar_resumen.py` para ver la puerta de calidad y los hallazgos en la terminal.
  La puerta exige 0 hallazgos nuevos y 80 % de cobertura: antes de dar una etapa por terminada debe pasar.
  No se corrigen (están aceptados en SonarQube con su motivo): nombres con "ñ" y `await` de nivel superior.
- `migrar_etapa4.py`: migración de una sola vez para bases con datos anteriores a la Etapa 4
  (sin argumentos muestra lo que haría; con `--aplicar` lo hace).

## Agentes disponibles (`.claude/agents/`)

- `diseno-oo`: diseño y revisión de clases (solo lectura).
- `backend-flask`: servicios y rutas de la API.
- `persistencia-mongo`: repositorios y esquemas de MongoDB.
- `frontend-web`: interfaz HTML/CSS/JS del cliente.
- `revisor-codigo`: revisión de calidad y capas (solo lectura).
- `profesor-doo`: valida contra el syllabus de DOO (solo lectura).
- `profesor-interfaces`: valida contra el syllabus de Diseño de Interfaces y audita el diseño de las
  pantallas (Secciones 6.1 a 6.5 del alcance) con el código y capturas; propone correcciones sin
  modificar archivos (solo lectura más los scripts de `herramientas/`).
