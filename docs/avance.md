# GestLab — Avance del proyecto

Registro de lo construido, por etapas. El **qué** del sistema está en [alcance_proyecto.md](alcance_proyecto.md); este documento dice **cuánto de eso ya funciona** y cómo verificarlo.

Leyenda: ✅ terminado · 🟡 parcial · ⬜ pendiente

## Estado de los criterios del MVP (Sección 8 del alcance)

| # | Criterio | Estado | Observaciones |
|---|---|---|---|
| 1 | Empresa y usuarios (tres roles, cada uno con su interfaz) | ✅ | Además: límites de usuarios por empresa y marca blanca |
| 2 | Actividades y proyectos | 🟡 | La API ya permite actividades independientes y proyectos con su avance en horas. Las pantallas del Administrador todavía crean las actividades dentro de requerimientos (Etapa 6 del rediseño) |
| 3 | Asignación y prioridad | ✅ | Uno o varios operarios, cuatro prioridades, tiempo estimado, fecha y hora programada, con alerta de sobrecarga |
| 4 | Ejecución (iniciar, pausar, reanudar, finalizar) | 🟡 | La API hace las cuatro acciones por operario, con motivo en cada pausa y observación al finalizar. En pantalla solo están iniciar y finalizar; faltan pausar y reanudar (Etapa 5 del rediseño) |
| 5 | Registro de tiempo | 🟡 | El servidor registra inicio, pausas y fin de cada operario y calcula el tiempo real sin pausas. Falta mostrarlo en pantalla y compararlo con el estimado |
| 6 | Análisis de carga laboral | 🟡 | Carga por jornada de cada operario y alerta al superar el 100 %. La capacidad es provisional (7 h) hasta que existan los turnos |
| 7 | Turnos y asistencia | 🟡 | El Administrador crea turnos, los asigna y valida o corrige la asistencia (pantalla Usuarios); el Operario marca entrada y salida en Hoy; la capacidad sale del turno. Falta el aviso de posible ausencia por tolerancia y la reasignación por ausencia |
| 8 | Indicadores de cumplimiento | ⬜ | |

## Etapa 1 — Inicio de sesión, empresas y usuarios (2026-09-26) ✅

Rama: `feature/interfaz-operario`, integrada a `main` (Pull Request #4).

### Qué se puede hacer

- **Todos:** iniciar sesión con correo y contraseña; cada rol llega a su propia pantalla. Cerrar sesión.
- **Superadmin:** registrar empresas (con límites de usuarios y logo opcional), ver la lista con los límites usados, entrar a cada empresa, editar sus datos, límites y logo, y crear sus Administradores.
- **Administrador:** ver los usuarios de su empresa y sus límites, y crear Operarios u otros Administradores dentro del límite.
- **Operario:** ver su lista de actividades ordenada por prioridad (sin datos todavía, porque aún no se crean actividades desde la interfaz).
- **Marca blanca:** los usuarios de una empresa ven el logo y el nombre de su empresa en el menú.

### Reglas que aplica el servidor

- Contraseñas guardadas con bcrypt; el hash nunca se devuelve en la API.
- Mismo mensaje de error si el correo no existe o si la contraseña es incorrecta (no revela qué correos están registrados).
- Cada ruta valida la sesión y el rol. Un Administrador solo ve y crea usuarios de su propia empresa, aunque el navegador envíe otra.
- El Superadmin solo crea Administradores; el Administrador crea Operarios y Administradores.
- El NIT de una empresa no se puede repetir. El correo de un usuario no se puede repetir.
- No se puede crear un usuario si la empresa alcanzó su límite para ese rol, ni bajar un límite por debajo de los usuarios existentes.
- El logo se valida por su contenido real (PNG, JPG o WEBP, máximo 512 KB); se rechazan SVG y archivos disfrazados.
- El primer Superadmin se crea automáticamente al arrancar, con los datos de `SUPERADMIN_CORREO` y `SUPERADMIN_CONTRASENA` del archivo `.env`.

### Cambios técnicos principales

| Capa | Cambio |
|---|---|
| Modelos | Nuevo enum `Rol`. `Usuario` ahora hereda de `Autenticable` (correo + hash de contraseña). `Empresa` tiene límites de usuarios. |
| Repositorios | Búsqueda de usuarios por correo y conteo por rol. `EmpresaRepository` no carga el logo en las consultas normales (solo cuando se pide). |
| Servicios | Nuevo `AuthService` (login y Superadmin inicial). `UsuarioService` aplica quién crea a quién y los límites. `EmpresaService` valida límites y logo. |
| Rutas | Nuevo `/auth` (`login`, `logout`, `sesion`). Decorador `requiere_rol` en `app/utils/seguridad.py`. Rutas `PUT/GET /empresas/<id>/logo`. |
| Errores | Jerarquía `ErrorApi` → `ValidationError` (400), `NoAutorizadoError` (401), `ProhibidoError` (403), `NotFoundError` (404), con un solo manejador. |
| Interfaz | Marco común (`js/layout.js`), cliente de la API (`js/api.js`), pantallas en `superadmin/`, `admin/` y `operario/`, estilos en `css/estilos.css`. |

### Cómo se verificó

- 16 pruebas contra la API (curl) del flujo completo de roles y permisos, y 16 más de límites y logo, todas con el resultado esperado.
- Recorrido en navegador (Edge automatizado) de cada pantalla en computador y en celular (390 px de ancho), sin errores de JavaScript.

### Pendientes conocidos de esta etapa

- ~~Las rutas de requerimientos, actividades, asignaciones, registros de tiempo y análisis no exigían sesión.~~ Resuelto en la Etapa 2.
- No hay pruebas automatizadas en el repositorio (las verificaciones se hicieron manualmente).
- No existe todavía cambio de contraseña ni recuperación de contraseña.
- Usuarios creados antes de esta etapa (con campo `email` y sin contraseña) no son compatibles: hay que borrar la base de datos de desarrollo (`docker compose down -v`).

## Etapa 2 — Actividades y vistas (2026-10-07) ✅

Rama: `feature/actividades-y-vistas`.

### Qué se puede hacer

- **Administrador, vista "Actividades":** registrar requerimientos, crearles actividades (categoría, prioridad, ubicación, fecha, hora opcional, tiempo estimado) y asignarlas a uno o varios operarios. Editar y eliminar.
- **Administrador, vista "Equipo":** ver el día de cada operario en columnas, con su carga de la jornada. Un clic en un espacio libre abre una actividad nueva con la fecha, la hora y el operario ya puestos.
- **Alerta de sobrecarga:** el formulario muestra la carga de cada operario antes de asignar; al guardar, avisa quién supera el 100 %, y la vista "Equipo" lo mantiene visible.
- **Operario, vista "Hoy":** actividad en curso con cronómetro, carga del día, aviso de actividad urgente y agenda agrupada por día (con las atrasadas arriba).
- **Operario, vista "Semana":** sus actividades en un horario por día, por semana o en lista.
- **Operario, vista "Resumen":** actividades y tiempo programado de la semana, gráfica de carga por día y reparto por estado y por categoría.
- **Ejecución:** el Operario inicia y finaliza sus actividades desde el detalle; la hora la pone el servidor.
- **Color de los bloques:** por prioridad o por categoría, a elección del usuario (se recuerda en el navegador).

### Reglas que aplica el servidor

- Todas las rutas exigen sesión y rol. Cada consulta se limita a la empresa del usuario; el Operario solo ve y ejecuta las actividades que tiene asignadas.
- Prioridad en cuatro niveles (Baja, Media, Alta, Urgente) con un peso numérico para ordenar.
- Solo se asigna a usuarios con rol Operario de la misma empresa.
- El tiempo estimado se suma completo a la carga de cada operario asignado (no se divide).
- Un operario no puede iniciar una actividad si ya tiene otra en curso, ni reiniciar una finalizada.
- El código de cada actividad es un consecutivo por empresa que no se repite aunque se creen dos a la vez.
- Al eliminar un requerimiento se eliminan sus actividades, asignaciones y ejecuciones.

### Cambios técnicos principales

| Capa | Cambio |
|---|---|
| Modelos | `Prioridad` con URGENTE y propiedad `peso`. Nuevo enum `Categoria`. `Actividad` con código, empresa, categoría, ubicación, tiempo estimado, fecha y hora programadas. |
| Repositorios | Búsqueda de actividades por empresa, fechas e identificadores. `AsignacionRepository` admite varias asignaciones por actividad. Consecutivo atómico en `EmpresaRepository`. |
| Servicios | `ActividadService` y `RequerimientoService` reescritos con permisos por empresa. Nuevo `CargaService` (carga por jornada y sobrecargas). `EjecucionService` valida la asignación y la actividad en curso. |
| Rutas | `/requerimientos`, `/actividades` y `/analisis/carga` protegidas con `requiere_rol`. |
| Eliminado | Rutas y código de asignaciones independientes, registros de tiempo manuales y análisis antiguo: no pedían sesión, mezclaban empresas y registraban horas a mano, contra lo que pide el alcance. |
| Interfaz | Marco nuevo (barra superior con pestañas, barra inferior en celular). Piezas compartidas en `js/actividades-comun.js` y `js/formulario-actividad.js`. Bibliotecas en `app/static/vendor/`: EventCalendar, Chart.js y Lucide. |

### Cómo se verificó

- 36 pruebas contra la API: permisos por rol, validaciones de cada campo, URGENTE, varios operarios, consecutivos, alerta de sobrecarga, carga por jornada y reglas de ejecución. Todas con el resultado esperado.
- Recorrido en navegador (Brave automatizado) de las siete pantallas en computador y celular, y de los flujos: crear una actividad que sobrecarga, cambiar el modo de color, editar, abrir el detalle, iniciar y finalizar. Sin errores de JavaScript.
- Contraste de la paleta de categorías medido con `herramientas/contraste.py`.

### Pendientes conocidos de esta etapa

- **Pausar y reanudar** una actividad, con motivo e historial de pausas (criterio 4). Depende de la decisión abierta sobre a quién pertenece la ejecución.
- La **capacidad de la jornada** es un valor fijo de 7 horas; pasará a calcularse desde el turno de cada operario (criterio 7).
- Las **categorías** son una lista fija; no se administran por empresa.
- El Operario todavía no puede **reportar una actividad de otra área**.
- No hay pruebas automatizadas en el repositorio.

## Fase 2 de Diseño de Interfaces — Identidad visual (2026-10-02 y 2026-10-03) 🟡

Rama: `feature/interfaz-operario`, integrada a `main` (Pull Request #5). Esa rama **definió** la identidad visual y las herramientas para revisarla; la aplicación en pantalla se hizo después (ver "Implementación en la aplicación").

### Qué quedó definido (en el alcance)

- **Perfil ampliado de los usuarios** (Sección 6.1) y las cuatro exigencias de diseño que se derivan.
- **Leyes de Gestalt aplicadas** (Sección 6.2): proximidad, semejanza, continuidad y figura y fondo, con el lugar donde se evidencia cada una. Cierre queda pendiente.
- **Sistema de color "Aqua de trabajo"** (Sección 6.3): base, principal, acento de marca, colores de estado con sus tres variantes, reglas obligatorias y conflictos resueltos.
- **Sistema tipográfico** (Sección 6.4): Lexend y Atkinson Hyperlegible Mono, escala 1,2 sobre base de 18 px y reglas de uso.
- Enunciado de la Fase 2 guardado en `docs/enunciados/`.

### Qué quedó construido

- `herramientas/contraste.py`: contraste WCAG entre colores (HEX o variables de `:root`).
- `herramientas/capturas.py`: capturas de cada pantalla por rol, en celular y escritorio, con versiones desenfocada y en grises. Funciona con un navegador ya instalado (`CAPTURAS_NAVEGADOR`).
- `requirements-dev.txt`: dependencias de desarrollo, separadas de las del producto.

### Cómo se verificó

- Los 10 contrastes declarados en la Sección 6.3 se midieron con `contraste.py` y coinciden. La medición mostró que el ámbar base no sirve sobre blanco ni con texto blanco, y se agregó la regla 7.
- `capturas.py` generó las 10 capturas (5 pantallas × 2 tamaños) con sus variantes, usando Brave.

### Implementación en la aplicación (2026-10-07)

Rama: `feature/identidad-visual`.

- `app/static/css/estilos.css` reescrito con los valores de las Secciones 6.3 y 6.4: todos los colores y la tipografía son variables en `:root`, y los tamaños están en rem sobre una base de 112,5 %.
- Fuentes Lexend (400 y 600) y Atkinson Hyperlegible Mono (500 y 600) incluidas en `app/static/fuentes/` con su licencia; la aplicación no depende de internet para mostrarlas.
- Prioridades, estados y avisos se muestran con color, ícono y texto. El ícono lo pone el CSS.
- NIT y límites de usuarios usan la fuente monoespaciada (clase `cifra`).
- Avatar con la inicial del usuario en el menú; junto con el logo, es el único lugar donde aparece el coral de marca.
- Verificación: 18 pares de color medidos con `contraste.py` sobre las variables del CSS, todos por encima del mínimo; 10 capturas revisadas en celular y escritorio, incluida la versión en grises.

### Pendientes de esta fase

- La prioridad Urgente y los estados Pausada y Finalizada ya tienen estilo, pero todavía no se pueden ver con datos reales: el backend aún no tiene la prioridad URGENTE ni las pausas (Etapa 2 en adelante).
- Validar el diseño de las pantallas con una herramienta externa de diseño.
- Elaborar el documento de diseño en PDF que pide el enunciado (evolución, usabilidad, Gestalt, color, conclusiones) con las capturas como evidencia.

## Rediseño por pantallas (en curso, 2026-10-07) 🟡

Ramas: `feature/diseno-superadmin` y `feature/diseno-administrador`. La interfaz usaba los colores y fuentes definidos, pero se veía desordenada. Se definió un **sistema de composición** (alcance, Sección 6.2) y se aplica pantalla por pantalla.

| Pantallas | Estado |
|---|---|
| Bases compartidas: escala de espacios, barra superior alineada con el contenido, cifras en la fuente del texto, formularios | ✅ |
| Superadmin: lista de empresas, ficha de empresa y sus formularios | ✅ Aprobado por el equipo |
| Administrador: Equipo, Actividades y Usuarios | ✅ Pendiente del visto bueno del equipo |
| Operario: Hoy, Semana y Resumen | ⬜ Heredan las bases; falta su rediseño |
| Inicio de sesión | ⬜ |

Verificación de las pantallas del Superadmin: la marca y el título comparten el borde izquierdo, y el usuario y el contenido el derecho (medido en el navegador); todas las filas de la lista miden lo mismo; sin desbordes a 1440, 1024 y 390 px; sin errores de JavaScript.

## Rediseño "Calma operativa" (en curso, 2026-10-10) 🟡

Plan: [plan_rediseno_calma_operativa.md](plan_rediseno_calma_operativa.md). Cambia la identidad visual, organiza la interfaz sobre la metáfora de la planilla del turno y agrega reglas nuevas de actividades (proyectos, hora fija, orden del día, pendientes, cancelación y devolución). Mientras no se apliquen las etapas 2 a 7, el código sigue con el diseño anterior.

| Etapa | Estado |
|---|---|
| 1. Actualizar el alcance (Secciones 5.1, 5.2, 6.1 a 6.5, 8 y 9, con su bitácora) | ✅ |
| 2. Base visual (tokens, fuente, logo): fondo y grises nuevos, Figtree, sombras muy suaves, logo del tablero y tarjetas sin borde lateral de color | ✅ Pendiente del visto bueno del equipo |
| 3. Operario: Hoy como su fila del tablero, con los datos que ya existen: línea de tiempo, tarjetas, actividad en curso abierta en su hora con cronómetro y avance, espacios libres, urgente en la línea "Ahora" y lo que viene de días anteriores | ✅ Pendiente del visto bueno del equipo |
| 4. Backend de las reglas nuevas | 🟡 Hecho: decisión H1 (la ejecución pertenece a la asignación), asignaciones que no se borran, y ejecución por operario con iniciar, pausar con motivo, reanudar y finalizar con observación; proyectos con avance en horas y actividades independientes; catálogos de motivos por empresa que se van llenando; cancelar con motivo; devolver una actividad; zona horaria por empresa; cierre de jornada (reprogramación automática de las de horario flexible, No realizada para las de hora fija y pausa por "Fin de jornada"); programación dinámica del día y orden del día del Operario. Falta: bloques de información de la actividad, indicadores de pendientes, y retirar los requerimientos y el borrado de actividades cuando la pantalla nueva los reemplace |
| 5. Operario: ordenar el día, hora fija y devolver | ⬜ |
| 6. Administrador: tablero del turno y proyectos | ⬜ |
| 7. Validación y evidencias para el informe | ⬜ |

Pendiente que deja la Etapa 1: validar los colores provisionales de los estados nuevos (Actividad reprogramada, Devuelta, No realizada y Cancelada).

Verificación de la Etapa 2: 15 pares de color medidos con `herramientas/contraste.py` sobre las variables del CSS, todos por encima de su mínimo; 18 capturas (9 pantallas en celular y escritorio) tomadas con `herramientas/capturas.py`. Los espacios escritos a mano en las pantallas del Operario no se tocaron: esas pantallas se rehacen en la Etapa 3.

Lo que la Etapa 3 deja fuera de Hoy porque la API todavía no lo entrega (entra con la Etapa 4 y con los turnos y la asistencia): pausar y el historial de pausas, "En turno" y la fila de fin del turno, la marca de entrada y de salida, "Reportar actividad" y la hora en que llegó una urgente. Mientras no existan los turnos, la línea de tiempo va de la primera a la última actividad del día y el tiempo libre se calcula con la capacidad provisional de 7 horas. Verificación: capturas en celular (390 px) y escritorio con y sin urgente pendiente, sin desbordes ni errores de JavaScript; todos los botones de la línea de tiempo miden 48 px de alto o más.

Rutas nuevas de la Etapa 4 hasta ahora: `POST /actividades/<id>/pausar`, `/reanudar`, `/cancelar` y `/devolver`; `POST`, `GET` y `PUT /proyectos`; `GET /catalogos/motivos-pausa`, `/motivos-cancelacion` y `/motivos-devolucion`; `GET /actividades` acepta `proyecto_id` y `independientes=1`. Segundo recorrido contra MongoDB real: crear un proyecto con actividades y una independiente, cancelar con un motivo nuevo que queda en la lista de la empresa, devolver con uno y con varios operarios, reasignar una devuelta, y comprobar que una actividad en curso no se cancela y una pausada sí. Con este bloque son 154 pruebas automáticas.

Verificación de lo hecho en la Etapa 4: 70 pruebas automáticas (`python -m pytest`) de las clases `Ejecucion`, `Pausa` y `Asignacion`, de la regla que calcula el estado de la actividad, y de los servicios y rutas sobre una base en memoria. Además, un recorrido contra la aplicación con MongoDB real: dos operarios comparten una actividad, uno la inicia, la pausa con motivo, inicia otra, la finaliza con observación, reanuda y finaliza la primera, y al compañero le sigue apareciendo por iniciar ("1 de 2 finalizaron"); una de hora fija no se deja pausar. Antes de usar estas reglas con datos anteriores hay que ejecutar una vez `python herramientas/migrar_etapa4.py --aplicar`. Pendiente en la interfaz: la pantalla Hoy todavía no tiene los botones de pausar y reanudar ni muestra las actividades pausadas (Etapa 5).

Cierre de jornada (tercer bloque de la Etapa 4): no hay proceso en segundo plano; se ejecuta cuando alguien de la empresa consulta o cambia algo, es rápido si no hay nada que cerrar y está protegido para que dos consultas simultáneas no reprogramen dos veces. Las pausas y cierres automáticos quedan con la hora de la medianoche de la empresa, no con la hora de la consulta, para no inflar el tiempo real. Verificación: 245 pruebas automáticas (38 de este bloque) y la base de prueba, donde diez actividades de hora fija de días anteriores quedaron como No realizadas y una de horario flexible se reprogramó a hoy con sus dos días de retraso. La pantalla Hoy ya muestra las reprogramadas con los días que calcula el servidor, y las pausadas con la opción de reanudar.

Programación dinámica del día (cuarto bloque de la Etapa 4): la estimación sirve para planear y lo ejecutado se mide con sus horas reales. El servidor calcula la programación de cada operario (`GET /programacion-del-dia`): lo terminado ocupa el tiempo que realmente tomó, lo que está en curso va de su inicio real a un fin proyectado, y lo pendiente se reacomoda desde ahí; si algo termina antes, lo siguiente se adelanta. El Operario puede guardar su orden del día para las actividades de horario flexible (`PUT` y `DELETE /orden-del-dia`). La pantalla Hoy ya no calcula nada por su cuenta: pinta esa programación, muestra en lo terminado cuánto tomó frente al estimado, y su cronómetro descuenta las pausas. Verificación: 333 pruebas automáticas (83 de este bloque) y recorrido en la aplicación de prueba con actividades terminadas, una en curso, una de hora fija y dos de horario flexible.

## Turnos, asistencia, pantalla Hoy completa y calendario (2026-10-10) 🟡

- **Turnos y asistencia (criterio 7):** catálogo de turnos por empresa, un turno por operario con historial de cambios, marca de entrada y salida con la hora del servidor, validación y corrección con motivo (las marcas originales se conservan), y la capacidad de cada jornada calculada con el turno. Rutas: `/turnos`, `PUT /usuarios/<id>/turno`, `/asistencia/entrada`, `/asistencia/salida`, `/asistencia/hoy`, `/asistencias` (validar y corregir).
- **Pantalla Hoy:** la línea de tiempo cubre todo el turno: arriba "Marcar entrada" (o la hora en que se marcó), abajo el fin del turno con "Marcar salida", y el estado "En turno" o "Fuera de turno" en el encabezado. Las actividades de hora fija llevan candado. El botón "Ordenar mi día" abre un modo para subir y bajar las de horario flexible, guardar el orden o volver al sugerido.
- **Usuarios del Administrador:** panel de turnos (crear), turno de cada operario (asignar o cambiar desde una fecha) y asistencia de hoy (validar o corregir, y los operarios con turno que no marcaron aparecen como "Sin marca").
- **Calendario (Semana y Equipo):** bloques con aire y texto que no se corta, ubicados por su hora real cuando ya se ejecutaron, finalizadas en gris con su visto bueno, canceladas fuera del horario, rango de 06:00 a 20:00, fila Flexible con alto máximo y barra de herramientas ordenada.
- **Documentos:** `docs/logica_de_negocio.md` explica cómo funciona el sistema sin hablar de código.
- Verificación: 421 pruebas automáticas, SonarQube en verde (0 hallazgos, 98 % de cobertura) y recorrido en la aplicación de prueba de Hoy, Semana, Equipo y Usuarios, en celular y escritorio, sin errores de JavaScript.

## Calidad del código: análisis de SonarQube (2026-10-10) ✅

El análisis del proyecto no pasaba la puerta de calidad: 3 vulnerabilidades, 44 detalles de mantenimiento y 0 % de cobertura (SonarQube no recibía el reporte de las pruebas). Después de las correcciones **pasa**: 0 bugs, 0 vulnerabilidades, 0 hallazgos abiertos, 0 % de duplicación y 96,9 % de cobertura, con calificación A en fiabilidad, seguridad y mantenimiento.

| Qué se corrigió | Cómo |
|---|---|
| Sin protección contra CSRF | Toda petición que cambia datos exige el encabezado `X-Requested-With: GestLab`, y la cookie de sesión es `SameSite=Lax` y `HttpOnly` |
| El contenedor corría como administrador y copiaba todo el proyecto | El `Dockerfile` crea un usuario sin privilegios y copia solo `run.py` y `app/`; `.dockerignore` ampliado |
| Cobertura en 0 % | Reporte de cobertura conectado a SonarQube y 44 pruebas nuevas de la aplicación completa (arranque, sesión, empresas, logo, usuarios, requerimientos y carga). En total, 198 pruebas |
| Dos funciones demasiado complejas | `armarDia` (pantalla Hoy) y la validación de campos de una actividad se partieron en funciones pequeñas |
| `Actividad.__init__` con 18 parámetros | Quedó en 13: el historial lo pone `desde_documento` al leer de la base |
| Accesibilidad del HTML | `<output>` y `<fieldset>` en lugar de `role`, y descripción en texto para la gráfica |
| Otros | Selectores CSS repetidos, una expresión regular lenta, pruebas con varias llamadas dentro de un mismo bloque |

No se corrigen, y quedaron aceptados en SonarQube con su justificación: los nombres con "ñ" (convención del proyecto) y el `await` de nivel superior (la interfaz no usa módulos). El hallazgo de CSRF quedó marcado como falso positivo, porque SonarQube solo reconoce la biblioteca Flask-WTF y la protección se hizo sin ella. La cobertura no cuenta la interfaz (`app/static/`), que se verifica en el navegador con capturas, ni las herramientas de desarrollo.

Cómo repetir el análisis: ver "Herramientas de desarrollo" en `CLAUDE.md`.

## Comparación con el proyecto inicial (2026-10-10)

Cómo vamos frente a lo que se propuso: el MVP de la Sección 8 del alcance, las entregas de las dos materias y el plan de rediseño.

### Criterios del MVP

| # | Criterio | Estado | Qué falta |
|---|---|---|---|
| 1 | Empresa y usuarios, tres roles con su interfaz | ✅ | Nada |
| 2 | Actividades independientes y proyectos | 🟡 | Funciona en la API. Las pantallas del Administrador todavía crean actividades dentro de requerimientos (Etapa 6) |
| 3 | Asignación a uno o varios, prioridad, estimado y fecha | ✅ | Nada |
| 4 | Iniciar, pausar, reanudar y finalizar con tiempos reales | 🟡 | Funciona en la API. En pantalla falta el botón de pausar (Etapa 5) |
| 5 | Tiempo real y comparación con el estimado | 🟡 | Se guarda y se calcula. En Hoy se ve "Tomó X · estimado Y"; falta la comparación para el Administrador (indicador de precisión de la estimación) |
| 6 | Ocupación actual de un operario | ✅ | Carga por jornada y programación del día. El tablero del turno la mostrará mejor (Etapa 6) |
| 7 | Turnos y asistencia | 🟡 | Hecho: turnos, asignación con historial, marca de entrada y salida, validación y corrección, capacidad desde el turno. Falta el aviso de posible ausencia por tolerancia y la reasignación por ausencia |
| 8 | Indicadores de cumplimiento | ⬜ | Cumplimiento de jornada, aprovechamiento, tiempo adicional y cumplimiento de actividades. Dependen de la asistencia |

En resumen: **3 criterios completos, 4 a medias y 1 sin empezar** (el 7 avanzó casi completo el mismo día). Lo que falta en los criterios 2, 4 y 5 ya está hecho en el servidor y solo le falta pantalla.

### Entregas de las materias

| Materia y entrega | Qué piden | Cómo vamos |
|---|---|---|
| DOO, Momento 2 (Semana 10) | Cliente-servidor con persistencia, concurrencia, hilos, sockets y conexión a base de datos, más documentación técnica del diseño | Cliente-servidor, persistencia y conexión a MongoDB: hechos. Concurrencia: resuelta con índices únicos y actualizaciones condicionadas, con pruebas que lo demuestran. **Hilos y sockets: no hay evidencia propia** (la aplicación usa HTTP, que corre sobre TCP, pero no hay un componente con hilos ni sockets programados). Documentación técnica: `logica_de_negocio.md`, alcance y diagramas del agente de diseño. **Es el punto de mayor riesgo, por la fecha** |
| DOO, Momento 3 (Semanas 15 y 16) | Aplicación web en tres capas con modelado estructural | Bien encaminado: tres capas separadas (modelos, repositorios, servicios y rutas), 300+ pruebas y SonarQube en verde |
| DI, Semana 10 (elementos del Ser) | Heurísticas de Nielsen | Las heurísticas aplicadas están documentadas en la Sección 6.2 del alcance. Falta preparar la evaluación con evidencias en pantalla |
| DI, Fase 2 | Documento en PDF con usabilidad, Gestalt, color y metáforas, y prototipo | Las reglas están definidas (Secciones 6.1 a 6.5). Faltan las capturas finales y el documento (Etapa 7) |

### Plan de rediseño "Calma operativa"

| Etapa | Estado |
|---|---|
| 1. Alcance | ✅ |
| 2. Base visual | ✅ |
| 3. Hoy del Operario | ✅ (con mejoras pendientes de la Etapa 5) |
| 4. Backend de las reglas nuevas | 🟡 Falta: información de la actividad y "Lista para iniciar", e indicadores de pendientes |
| 5. Operario: ordenar el día, hora fija, devolver | ⬜ |
| 6. Administrador: tablero del turno y proyectos | ⬜ |
| 7. Validación y evidencias | ⬜ |

### Lo que se agregó y no estaba en la propuesta inicial

Programación dinámica del día, cierre de jornada con reprogramación automática, zona horaria por empresa, motivos que se aprenden, protección contra CSRF, análisis con SonarQube y el glosario. Todo está registrado en la bitácora del alcance.

## Estado del repositorio (2026-10-10)

- Las ramas de funcionalidades anteriores ya están integradas en `main` (Pull Request #7) y se borraron.
- Todo el trabajo del rediseño "Calma operativa" (Etapas 1 a 3 y lo hecho de la Etapa 4) está en la copia local de `main`, **sin confirmar en Git** por decisión del equipo: se sube cuando se termine. Incluye archivos nuevos sin seguimiento: `tests/`, `docs/disenos/`, `docs/plan_rediseno_calma_operativa.md`, los modelos, repositorios, servicios y rutas nuevos, las fuentes Figtree y `herramientas/migrar_etapa4.py`.
- `develop` está atrasada respecto a `main` y debe sincronizarse (Pull Request `main` → `develop`).

## Decisiones abiertas

- ¿El login debe mostrar la marca de cada empresa? Requeriría una dirección por empresa (por ejemplo `/metalicas`). Por ahora el login muestra GestLab.
- Validar los colores provisionales de los estados nuevos (Actividad reprogramada, Devuelta, No realizada y Cancelada) con las pantallas construidas.
- Si el Administrador le cambia la fecha a una actividad que nunca se reprogramó automáticamente, ¿cambia su fecha original? Hoy no cambia.
- Al cambiar la zona horaria de una empresa cambia de inmediato qué día es "hoy" para ella. ¿Debe quedar registro del cambio?
- Tiempo trabajado "hoy" de una actividad que se empezó ayer: hoy se suma todo su tiempo real, también el de ayer. ¿Debe contarse solo lo trabajado en la jornada?
- Una actividad pausada que se trabajó hoy solo muestra en la línea de tiempo lo que le falta, no el rato ya trabajado.
- Si lo que está en curso se proyecta más allá del inicio de una de hora fija, las dos tarjetas se cruzan en la línea de tiempo sin un aviso de choque.
- Calendario: las finalizadas se muestran en gris con su ícono verde, y la Sección 6.3 dice "Finalizada (verde suave)". ¿Se aprueba el gris para el horario? Las canceladas no se dibujan en el horario (siguen en Actividades).
- Turno de noche: "En turno" y la línea de tiempo miran el turno que empieza hoy; quien trabaja de 22:00 a 06:00 y consulta a las 02:00 ve el turno de esta noche. Hay que definir la regla.
- La salida cierra cualquier asistencia abierta, aunque sea de hace varios días; el tiempo presente queda grande y el Administrador lo corrige. ¿Se limita a la jornada anterior?
- El Administrador no puede crear la asistencia de un operario que quedó "Sin marca" (solo corregir una existente).
- El cierre de jornada sigue a la medianoche de la empresa, no al fin del turno.
- Aviso al Administrador cuando una reprogramación automática deja una jornada por encima del 100 % (lo pide el alcance; hoy solo se ve en la carga del día).
- ¿El tiempo de un operario retirado de una actividad suma al tiempo real de esa actividad? Hoy queda guardado pero no se suma; se recomienda sumarlo al construir los indicadores.

Resuelta el 2026-10-10: la ejecución pertenece a la asignación (operario + actividad). Ver la Sección 5.1 del alcance.

## Pendientes técnicos conocidos

- Mientras las pantallas del Administrador usen requerimientos, una actividad puede tener requerimiento y proyecto a la vez, y sigue existiendo el borrado de actividades. Las dos cosas contradicen el alcance y se retiran con la pantalla nueva (Etapa 6).
- Si un operario inicia una actividad en el mismo instante en que el Administrador la cancela, puede quedar una ejecución en curso sobre una actividad cancelada. El cierre de jornada debe limpiarlo.
- La pantalla Hoy ya muestra las pausadas, permite reanudarlas desde el detalle y ordenar el día, pero todavía no tiene el botón de pausar ni el aviso de hora fija (Etapa 5).
- El formulario de empresa del Superadmin todavía no tiene el campo de zona horaria; por ahora solo se cambia por la API.
- El botón de la actividad urgente lleva a un "Iniciar" desactivado cuando hay otra en curso; se resuelve con "Pausar y atender" (Etapa 5).
- Espacios escritos a mano en reglas compartidas de `estilos.css` (`.aviso`, `.etiqueta`, `.boton`, navegación), fuera de la escala `--e1` a `--e7`.
- Los usuarios de prueba `CAPTURAS_ADMINISTRADOR_*` y `CAPTURAS_OPERARIO_*` no están en el `.env`; sin ellos `herramientas/capturas.py` solo captura el login y el Superadmin.
- En una base con datos anteriores a la Etapa 4 hay que ejecutar una vez `python herramientas/migrar_etapa4.py --aplicar`.

## Próximos pasos

En este orden (plan completo en [plan_rediseno_calma_operativa.md](plan_rediseno_calma_operativa.md)):

1. **Terminar la Etapa 4 (backend):**
   - bloques de información de la actividad (pasos, herramientas y materiales, equipo, adjuntos, contacto) y "Lista para iniciar";
   - indicadores de pendientes (reprogramadas, no realizadas, canceladas y devoluciones por motivo).
2. **Etapa 5 — Operario:** pausar y reanudar con motivo, ordenar el día, aviso de hora fija, devolver una actividad y detalle de la orden.
3. **Etapa 6 — Administrador:** tablero del turno y pantalla de proyectos; retirar los requerimientos y el borrado de actividades.
4. **Etapa 7 — Validación y evidencias:** auditoría de todas las pantallas y capturas para el documento de la Fase 2 de Diseño de Interfaces (usabilidad, Gestalt, color y metáforas).
5. **Turnos y asistencia** (criterio 7 del MVP), de los que depende la capacidad real de cada jornada, e **indicadores de cumplimiento** (criterio 8).
