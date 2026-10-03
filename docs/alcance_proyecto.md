# DOCUMENTO DE ALCANCE DEL PROYECTO
## GestLab
### Sistema web para la gestión y análisis de carga laboral
### Proyecto académico — Diseño Orientado a Objetos (POO) & Diseño de Interfaces

> **Estado:** Documento vivo. Versión base: v0.1 (original). Se actualiza de forma incremental a medida que avanzan ambas materias. La bitácora completa de cambios, con fecha y motivo de cada uno, se encuentra al final del documento.

---

## 1. Descripción general

El proyecto consiste en el desarrollo de un sistema web orientado a la gestión y análisis de las actividades laborales de operarios pertenecientes a diferentes empresas. Su propósito es dar orden y visibilidad a todo el ciclo de trabajo dentro de un área: desde que llega una necesidad o solicitud, hasta que esta se convierte en una actividad concreta, se asigna a una persona responsable, se ejecuta y finalmente se analiza en conjunto con el resto de la carga laboral del equipo.

En términos simples, el sistema busca responder tres preguntas que suelen ser difíciles de contestar en el día a día de un área de trabajo: **qué se debe hacer**, **quién lo está haciendo (o debería hacerlo)**, y **cuánto trabajo hay realmente en curso**. Para lograrlo, la solución centraliza los requerimientos que llegan al área, los transforma en actividades de trabajo claramente definidas, permite asignarlas y priorizarlas según su importancia, registra su ejecución en tiempo real, y finalmente genera información útil sobre la carga laboral del personal — tanto la actual como una proyección de lo que viene.

De esta forma, el sistema no solo sirve como una herramienta operativa para gestionar el trabajo diario, sino también como una fuente de información para entender cómo se está distribuyendo la carga entre las personas del equipo y detectar a tiempo posibles situaciones de sobrecarga.

---

## 2. Problema que busca resolver

En diferentes entornos laborales, los requerimientos y actividades pueden llegar por medios dispersos o de manera informal, dificultando conocer qué trabajo debe realizarse, quién es responsable, cuál es su prioridad, qué actividades están pendientes y qué capacidad tiene disponible cada operario.

La falta de información sobre los tiempos estimados y los tiempos reales de ejecución también limita la capacidad de analizar la distribución del trabajo y detectar situaciones de sobrecarga. El sistema busca centralizar esta información y proporcionar una visión tanto operativa como analítica.

---

## 3. Propósito del sistema

El sistema tendrá dos frentes principales: Gestión y Análisis. La gestión permitirá administrar requerimientos, actividades, responsables, prioridades y ejecución. El análisis utilizará los datos generados durante la operación para conocer tiempos, ocupación y carga laboral actual y futura.

---

## 4. Usuarios del sistema

- **Superadmin:** rol técnico/operativo del sistema, no pertenece a ninguna empresa específica. Es responsable de dar de alta nuevas empresas en el sistema y crear el primer usuario Administrador de cada una. También define, para cada empresa, su logo (marca blanca) y la cantidad máxima de Administradores y de Operarios que puede tener. No participa en la gestión diaria de requerimientos, actividades ni ejecución.
- **Administrador** (antes "Supervisor"): administra y da seguimiento a los requerimientos y actividades del área, asigna responsables, establece prioridades y consulta la carga laboral del personal. Además, define los turnos de la empresa y asigna uno a cada operario, valida o corrige la asistencia diaria y reasigna actividades cuando un operario falta.
- **Operario** (antes "Empleado"): consulta sus actividades, conoce la información necesaria para ejecutarlas, registra su ejecución y puede reportar actividades solicitadas por otras áreas para conocimiento y gestión del administrador. Además, marca su entrada y salida de cada jornada.

---

## 5. Alcance funcional inicial

### 5.1 Gestión
- Registro y administración de empresas.
- Registro de empresas y creación del primer usuario Administrador de cada una, a cargo del Superadmin.
- Registro y administración de usuarios con perfiles de Administrador y Operario, dentro de su respectiva empresa.
- Límite de usuarios por empresa: el Superadmin define un máximo de Administradores y otro de Operarios. El sistema impide crear usuarios por encima del límite y reducir un límite por debajo de los usuarios que la empresa ya tiene.
- Marca blanca: el Superadmin puede cargar el logo de cada empresa (PNG, JPG o WEBP, máximo 512 KB). Los usuarios de esa empresa ven su logo y su nombre en la interfaz en lugar de la marca GestLab. La pantalla de inicio de sesión conserva la marca GestLab, porque antes de ingresar el sistema no sabe a qué empresa pertenece el usuario.
- Registro y seguimiento de requerimientos que llegan al área.
- Conversión y organización de requerimientos en actividades de trabajo.
- Creación y asignación de actividades a uno o varios operarios.
- Definición de información clara para cada actividad.
- Clasificación de actividades por tipo o categoría.
- Definición de prioridad de las actividades en cuatro niveles: Baja, Media, Alta y Urgente. El nivel Urgente indica que la actividad debe interrumpir la tarea que el operario tenga en curso.
- Definición de tiempo estimado de ejecución. El tiempo estimado corresponde a la actividad completa: si la actividad tiene varios operarios, no se reparte entre ellos (cada uno la suma completa a su carga).
- Definición de una fecha programada de ejecución para cada actividad.
- Consulta del estado y asignación de las actividades.
- Posibilidad de que un operario registre una actividad solicitada por otra área y la socialice con su administrador.
- Gestión de la ejecución de actividades, incluyendo inicio, pausa, reanudación y finalización.
- Registro automático de los tiempos asociados a la ejecución.
- Consideración de cambios de prioridad durante la jornada y posibilidad de interrumpir temporalmente una actividad para atender otra de mayor prioridad, conservando el historial de ejecución.
- Cada operario puede tener una sola actividad en ejecución a la vez. Para iniciar otra, debe pausar (registrando el motivo) o finalizar la actual de forma manual; el sistema bloquea el inicio de una segunda actividad mientras exista una en curso.

**Turnos y asistencia**
- Definición, por parte de cada empresa, de un catálogo de turnos. Cada turno tiene un identificador, nombre, hora de inicio, hora de fin y tiempo de descanso.
- Asignación de un único turno a cada operario. Cuando se cambia el turno de un operario, el sistema conserva la fecha del cambio, para que los indicadores de periodos anteriores se calculen con el turno vigente en ese momento.
- Una jornada pertenece al día en que inicia el turno, aunque el turno termine después de la medianoche.
- El turno no limita el trabajo: el operario puede ejecutar actividades fuera de su turno, y ese tiempo se registra como tiempo adicional.
- Registro de asistencia: el operario marca su entrada y su salida de cada jornada (la hora la registra el servidor), y el Administrador valida o corrige cada marca.
- Aviso de posible ausencia: si pasado un tiempo de tolerancia desde el inicio del turno (configurable por empresa) el operario no ha marcado entrada, el Administrador recibe un aviso con las actividades programadas de ese operario para la jornada.
- Ante una ausencia confirmada, el Administrador reasigna manualmente las actividades a otros operarios.
- Las actividades que no se reasignen se reprograman automáticamente a la siguiente jornada del operario. La reprogramación queda registrada como un evento (con la jornada de origen), y si la jornada de destino supera el 100% de la capacidad del operario, el Administrador recibe un aviso.

### 5.2 Análisis
- Comparación entre tiempo estimado y tiempo real de ejecución.
- Análisis de la carga laboral de los operarios.
- Visualización de la ocupación actual.
- Proyección de la ocupación futura a partir de las actividades programadas.
- Identificación de posibles situaciones de sobrecarga.
- Capacidad de cada operario por jornada, calculada a partir de su turno: duración del turno menos el tiempo de descanso.
- Cálculo de la carga por jornada: suma de los tiempos estimados de las actividades asignadas al operario y programadas para esa jornada.
- Alerta en pantalla al momento de asignar una actividad, cuando la carga del operario para la jornada programada de esa actividad supere el 100% de su capacidad.
- Análisis de la distribución de actividades por categoría.
- Consulta de información histórica generada por la ejecución de actividades.

**Indicadores de jornada y cumplimiento**
- Por cada jornada se registran: tiempo programado (turno menos descanso), tiempo presente (entre las marcas de entrada y salida validadas), tiempo en actividades (ejecución real sin pausas) y tiempo adicional (trabajo fuera del turno).
- **Cumplimiento de jornada:** tiempo en actividades dividido entre tiempo programado.
- **Aprovechamiento:** tiempo en actividades dividido entre tiempo presente.
- **Tiempo adicional:** se muestra como dato propio; no se clasifica como hora extra ni se calcula su valor (ver Sección 9).
- **Cumplimiento de actividades:** una actividad se considera cumplida si se finaliza en su jornada programada. Las actividades reprogramadas por ausencia cuentan como retraso.
- **Precisión de estimación:** comparación entre tiempo estimado y tiempo real de ejecución (se mantiene como indicador separado del cumplimiento).
- Todos los indicadores se consultan por operario, por categoría de actividad y para la empresa. Los valores agregados se calculan sumando los tiempos de todos los involucrados y dividiendo al final, no promediando porcentajes individuales.

---

## 6. Experiencia de uso

La aplicación será web y tendrá un diseño responsive. La interfaz para administradores estará orientada principalmente a la gestión y análisis, mientras que la experiencia del operario dará especial importancia al uso desde dispositivos móviles, debido a que la ejecución de actividades requiere iniciar, pausar, reanudar y finalizar tareas durante la jornada laboral.

### 6.1 Persona y decisiones de diseño de interfaz — Operario (Diseño de Interfaces)

Como parte del trabajo de Diseño de Interfaces, se construyó una ficha de usuario y un mapa de empatía para el rol Operario, y se definió la primera propuesta de wireframes de baja fidelidad para la interfaz web responsive de ese rol. Estos insumos no cambian el alcance funcional ya definido en la Sección 5, pero sí deben orientar cómo se prioriza y se presenta esa funcionalidad en la interfaz.

**Persona de referencia:** Carlos Andrés Ramírez, 34 años, operario de línea de producción, técnico en electrónica, turno rotativo. Usa únicamente celular durante su jornada.

**Perfil ampliado de los usuarios:** Carlos es la persona de referencia, pero no representa a todos los usuarios. Quienes usan GestLab son diversos: personas jóvenes y mayores, de todo género y con distintos niveles de familiaridad con la tecnología, en roles técnicos y administrativos. Además, la herramienta se usa durante gran parte de la jornada (el Operario la consulta en cada cambio de actividad y el Administrador trabaja en ella de forma continua). De este perfil se derivan cuatro exigencias de diseño que aplican a todas las vistas:
- **Legibilidad para vista cansada o envejecida:** alto contraste entre texto y fondo (ver 6.3) y tamaños de texto y controles generosos.
- **Bajo cansancio visual en uso prolongado:** fondos sin blanco puro, texto sin negro puro y color intenso solo donde hay algo que atender.
- **Información que no depende solo del color:** todo estado o aviso se comunica con color, ícono y texto, por accesibilidad (daltonismo) y por la menor capacidad de distinguir tonos con la edad.
- **Interfaz amable y profesional para un público amplio:** sin estereotipos de género en el color y con un tono cercano (por ejemplo, saludo con el nombre del usuario), sin perder la seriedad de una herramienta de trabajo.

**Hallazgo central del mapa de empatía:** Carlos no necesita más control sobre su trabajo — necesita **evidencia y contexto**: poder demostrar lo que hizo (hoy depende solo de su palabra) y no perder el hilo cuando una tarea se interrumpe por otra más urgente.

**Necesidades identificadas que la interfaz debe resolver explícitamente:**
- Ver sus actividades asignadas ordenadas por prioridad, sin tener que preguntar.
- Notar visualmente cuándo una prioridad cambió durante el turno.
- Registrar inicio/pausa/reanudación/finalización de una actividad de forma rápida.
- Ver el historial de pausas de la actividad en curso (para no perder contexto al retomarla).
- Dejar una constancia (observación) al finalizar una actividad, no solo cerrarla.
- Registrar un motivo/causa al pausar una actividad, no solo el hecho de que se pausó.
- Reportar una actividad solicitada por otra área sin que "quede en el aire".
- Ver un aviso claro y visible cuando tiene una actividad de prioridad Urgente pendiente, tanto en la pantalla principal como en la de ejecución, para que pueda pausar la actividad en curso y atenderla.
- Saber en todo momento si está dentro o fuera de su turno, mediante un indicador visible (banner) que combine color y texto (por ejemplo, "En turno" / "Fuera de turno: tiempo adicional"), sin depender solo del color.
- Marcar su entrada y su salida de la jornada desde el celular.

**Pantallas mínimas definidas para el flujo del Operario (sitio web responsive, vista móvil):**
1. Bienvenida + Inicio de sesión (unificadas — el Operario no se autoregistra, según Sección 4)
2. Pantalla principal (lista priorizada de actividades + acceso a reportar actividad externa)
3. Detalle de actividad (información completa antes de iniciar una tarea)
4. Ejecución de actividad (cronómetro, control de estado, historial de pausas, observación final)

**Principios de usabilidad que orientan el diseño de la interfaz** (Diseño de Interfaces, Semana 7):
- **Ley de Hick:** más opciones implican más tiempo para decidir; cada pantalla debe mostrar solo las opciones necesarias para el paso actual.
- **Ley de Fitts:** los elementos grandes y cercanos son más fáciles de seleccionar; los controles de ejecución deben ser fáciles de tocar en móvil.
- **Ley de Jakob:** los usuarios esperan que el sistema funcione como otros que ya conocen; se privilegian patrones de interacción familiares.
- **Ley de Miller:** la capacidad de procesar información es limitada; la información se presenta en bloques pequeños y priorizados.
- **Ley de Proximidad:** los elementos cercanos se perciben como relacionados; los controles y datos que van juntos se agrupan visualmente.
- **Efecto estético-usabilidad:** los diseños atractivos se perciben como más fáciles de usar; se cuida la consistencia visual sin sacrificar claridad.

**Nota para Diseño Orientado a Objetos:** dos de estas necesidades tienen implicación directa en el modelo de datos y conviene tenerlas presentes al diseñar las clases de Actividad/Ejecución:
- El **historial de pausas/reanudaciones** de una actividad debe quedar registrado como datos consultables (no solo el tiempo total), para poder mostrarlo en la interfaz.
- El **campo de observación al finalizar** una actividad debe existir como atributo opcional de la ejecución, no solo como una acción de cierre sin datos asociados.
- El **motivo de pausa** debe registrarse junto con cada evento de pausa (no es un campo global de la actividad, sino un dato asociado a cada pausa específica, ya que una actividad puede pausarse varias veces por razones distintas).

Esta subsección no reemplaza la Sección 5 (Alcance funcional) — la complementa desde la perspectiva de interfaz y experiencia de usuario.

### 6.2 Vistas por rol y diseño general de la interfaz (Diseño de Interfaces)

Cada rol ingresa por la misma pantalla de inicio de sesión y es llevado a su propia interfaz. Un usuario que intente abrir una pantalla de otro rol es redirigido a la suya.

| Rol | Dispositivo principal | Opciones del menú |
|---|---|---|
| Superadmin | Computador | Empresas (lista, registro, detalle con usuarios, edición de datos, límites y logo) |
| Administrador | Computador (también usable en celular) | Inicio (tablero del día) · Requerimientos y actividades · Usuarios / Operarios · Turnos y asistencia · Indicadores |
| Operario | Celular | Mis actividades (lista priorizada → detalle → ejecución), marca de entrada y salida |

Las opciones del menú se habilitan a medida que se construye cada pantalla; nunca se muestran enlaces a pantallas que aún no existen.

**Decisiones de diseño comunes a todas las vistas:**
- **Marco común:** menú lateral con las opciones del rol y, al pie, el nombre del usuario, su rol y "Cerrar sesión". En celular el menú se oculta detrás de un botón "Menú".
- **Primero la información:** cada pantalla muestra primero su lista o tabla. Crear o editar es una acción secundaria: un botón ("+ Nueva empresa", "+ Nuevo usuario") abre el formulario en una ventana (diálogo). Al guardar, la ventana se cierra y aparece una confirmación breve.
- **Estados vacíos y límites explicados:** cuando no hay datos, la pantalla explica qué hacer y ofrece el botón para hacerlo. Cuando una acción no está disponible (por ejemplo, se alcanzó el límite de usuarios), el botón se desactiva y un aviso explica por qué.
- **Paleta sobria con significado:** fondos casi neutros, un color principal para las acciones y un acento de marca usado solo en elementos de identidad. Los colores fuertes se reservan para lo que tiene significado (prioridades, estados, avisos) y siempre van acompañados de ícono y texto. El sistema de color completo se define en la Sección 6.3.
- **Tipografía legible:** Lexend para leer y Atkinson Hyperlegible Mono para códigos, tiempos y cifras, con base de 18 px y tamaños en rem. El sistema tipográfico completo se define en la Sección 6.4.

**Relación con los principios de usabilidad (6.1) y las heurísticas de Nielsen:**
- Pocas opciones de menú por rol (Ley de Hick) y patrón de menú lateral más tabla, habitual en sistemas administrativos (Ley de Jakob).
- Confirmación después de guardar y botones desactivados mientras se procesa (Nielsen 1: visibilidad del estado del sistema).
- "Cancelar", la tecla Esc y la "X" en todos los diálogos (Nielsen 3: control y libertad del usuario).
- Validación antes de enviar y acciones deshabilitadas cuando no son posibles (Nielsen 5: prevención de errores).
- Mensajes de error en lenguaje claro dentro del mismo formulario (Nielsen 9: ayudar a reconocer y corregir errores).

**Leyes de Gestalt aplicadas** (requerimiento 2 de la Fase 2; se listan solo las que ya se evidencian en las pantallas construidas):
- **Proximidad:** cada etiqueta va pegada a su campo y separada del siguiente; los dos límites de usuarios forman un grupo bajo un mismo título; "Cancelar" y la acción principal van juntos al pie del diálogo; el nombre del usuario, su rol y "Cerrar sesión" forman un bloque al pie del menú. Resuelve la duda de qué dato pertenece a qué control.
- **Semejanza:** todos los botones de acción principal comparten relleno y forma, los secundarios comparten borde, las etiquetas de rol y de prioridad comparten la forma de píldora y todos los enlaces comparten color. El usuario aprende un elemento una vez y lo reconoce en las demás pantallas.
- **Continuidad:** las tablas alinean cada dato en su columna para recorrerlo de arriba abajo; los formularios tienen una sola columna que termina en el botón de acción; las migas de pan ("Empresas / Metalicas SAS") muestran el camino recorrido.
- **Figura y fondo:** los paneles blancos se separan del fondo tintado; al abrir un diálogo o el menú en celular, el resto de la pantalla se oscurece para que solo quede en primer plano lo que se está atendiendo.
- **Cierre:** todavía no se aplica en las pantallas construidas; se evaluará en la pantalla de ejecución del Operario (por ejemplo, el avance de la jornada).


### 6.3 Identidad visual: sistema de color "Aqua de trabajo" (Diseño de Interfaces)

Esta subsección define la propuesta cromática del producto, exigida en la Fase 2 del Proyecto Integrador de Diseño de Interfaces. Reemplaza la paleta inicial de la interfaz (acento verde azulado `#0f766e` en `estilos.css`). El color se eligió por su función y por el contexto de uso, no por gusto estético: cada color tiene un único significado y ese significado es el mismo en todas las pantallas de los tres roles.

**Fundamentos de la propuesta:**
- **Estudios de color y trabajo.** En el estudio de Nancy Kwallek (Universidad de Texas), las personas cometieron más errores en una oficina blanca que en una de color, y el espacio aqua (verde azulado) resultó el más agradable y productivo; las personas sensibles al entorno se sintieron abrumadas en espacios de colores intensos. Mehta y Zhu (Universidad de British Columbia, *Science*, 2009) mostraron que el rojo induce una motivación de alerta y evitación que mejora las tareas que exigen atención al detalle, mientras que el azul favorece la calma. De aquí salen tres decisiones: fondo con tinte aqua en lugar de blanco, color principal aqua profundo y rojo reservado para lo que exige atención inmediata. Estos estudios se usan como respaldo, no como verdad absoluta: sus efectos varían según la persona.
- **Normas de color de la industria.** Los significados de los colores de estado siguen la norma ISO 3864 (rojo: peligro o prohibición; amarillo: precaución; verde: condición segura; azul: indicación u obligación), que los operarios ya conocen por la señalización de planta. La escala de prioridades sigue la jerarquía de riesgo de ANSI Z535 (amarillo para precaución, naranja para advertencia, rojo para peligro). Lo que está en estado normal va en gris, según el principio de la norma ISA-101 para interfaces de operación industrial: el color se reserva para lo que requiere acción.
- **Visión de personas mayores.** Con la edad, el cristalino se vuelve amarillento, el azul se percibe más oscuro y cuesta distinguir azules de verdes. Por eso se usan colores de saturación media, el azul no se usa en texto pequeño y el verde de "finalizada" se inclina hacia el amarillo para separarse del aqua principal.
- **Contraste (WCAG 2.1).** Todo texto cumple al menos 4,5:1 contra su fondo y los componentes de interfaz al menos 3:1. Los textos principales superan 7:1 (nivel AAA).

**Teoría del color aplicada:**
- **Armonía complementaria:** el aqua principal (tono 190°) y el coral de marca (tono 9°) están separados 181° en la rueda de color. Siguiendo lo visto en clase, esta armonía se usa para destacar: el coral ocupa muy poca superficie y marca la identidad.
- **Jerarquía por saturación y luminosidad:** el fondo es casi neutro (26 % de saturación, 95 % de luminosidad), el principal es firme (69 % de saturación, 28 % de luminosidad) y los estados intensos aparecen solo cuando hay algo que atender.
- **Proporción 60-30-10:** alrededor de 60 % de fondo y superficies, 30 % de texto y color principal, y 10 % de acento de marca y colores de estado.

**Base e identidad:**

| Rol | HEX | Uso | Contraste |
|---|---|---|---|
| Fondo | `#EEF5F4` | Fondo general de todas las pantallas (tinte aqua, sin blanco puro) | — |
| Superficie | `#FFFFFF` | Tarjetas, tablas, diálogos (separa figura y fondo) | — |
| Principal | `#16697A` | Botones de acción principal, enlace activo, foco, actividad en curso | Texto blanco sobre principal 6,3:1 |
| Principal (hover/presionado) | `#0F5563` | Estado del botón principal al pasar el cursor o presionar | 7,1:1 sobre su fondo suave |
| Principal suave | `#E0EFF0` | Fondo de la etiqueta "En curso" y de elementos seleccionados | — |
| Acento de marca (coral) | `#E9806E` | Solo identidad: logo, avatar del usuario, barra de progreso de la jornada. Nunca en texto ni en estados | No se usa para texto |
| Texto principal | `#1F2A2E` | Títulos y texto (sin negro puro) | 14,7:1 sobre blanco |
| Texto secundario | `#4E5B60` | Textos de apoyo, metadatos | 7,0:1 sobre blanco |

**Colores de estado** (cada uno con tres variantes: base para rellenos y bordes, fondo suave para etiquetas y avisos, y texto oscuro para escribir sobre ese fondo):

| Significado | Base | Fondo suave | Texto sobre fondo | Ícono | Norma | Contraste texto/fondo |
|---|---|---|---|---|---|---|
| Error, prioridad Urgente | `#A8322A` | `#FBE9E7` | `#8A2620` | ⚠ | ISO 3864 (peligro, prohibición) | 7,5:1 |
| Prioridad Alta | `#B34F0B` | `#FDEBDD` | `#8A3D08` | ▲ | ANSI Z535 (advertencia) | 6,6:1 |
| Advertencia, prioridad Media, actividad pausada, cambio de prioridad | `#E3A32B` | `#FBF1D9` | `#6B4A0E` | ! / ❚❚ / ↑ | ISO 3864 (precaución) | 7,2:1 |
| Confirmación, actividad finalizada, en turno | `#3E7B3A` | `#E6F0E2` | `#2F5F2C` | ✓ / ● | ISO 3864 (condición segura) | 6,4:1 |
| Información | `#2F5DA8` | `#E6EDF8` | `#24498A` | i | ISO 3864 (azul, indicación) | 7,5:1 |
| Normal: prioridad Baja, actividad pendiente, fuera de turno | `#6B7478` | `#ECEFEF` | `#4E5B60` | • / ○ | ISA-101 (lo normal en gris) | 6,1:1 |

**Asignación por elemento de la interfaz:**
- **Prioridades:** Urgente (bloque o etiqueta rojo lleno con texto blanco), Alta (naranja con texto blanco), Media (ámbar con texto oscuro, ver regla 7), Baja (gris). La intensidad del color crece con la urgencia y la etiqueta siempre muestra el nombre del nivel.
- **Estados de actividad:** Pendiente (gris), En curso (principal aqua), Pausada (ámbar), Finalizada (verde).
- **Jornada:** En turno (verde con punto ●), Fuera de turno (gris con texto que lo indica).
- **Errores:** el error de formulario y la prioridad Urgente comparten el rojo porque significan lo mismo, "algo requiere tu atención", y se diferencian por la forma: el error de formulario es un borde rojo en el campo con el mensaje debajo; la alerta de Urgente pendiente es un bloque rojo lleno con ícono ⚠ y texto.
- **Información:** avisos que no exigen acción (por ejemplo, la hora de fin de turno), siempre como fondo suave con el ícono "i", nunca como botón lleno, para no confundirse con una acción.

**Reglas obligatorias del sistema de color:**
1. Todo estado, prioridad o aviso se comunica con **color, ícono y texto**; nunca solo con color.
2. Cada color tiene **un solo significado** en todo el producto.
3. El **color intenso** (bloques llenos) se reserva para lo que exige atención inmediata; lo normal se muestra en gris.
4. El **coral de marca** nunca se usa en texto, etiquetas de estado ni botones de acción.
5. El **azul de información** nunca se usa en texto pequeño ni como relleno de botón.
6. Todos los colores se definen como **variables CSS** en un único lugar (`:root` de `estilos.css`) para garantizar la consistencia entre pantallas.
7. El **ámbar base** (`#E3A32B`) es un color claro y tiene dos restricciones: sobre blanco solo alcanza 2,2:1, así que nunca se usa como borde, ícono o texto sobre superficies claras (para eso se usa su texto oscuro `#6B4A0E`, 8,0:1 sobre blanco); y como relleno lleva siempre texto principal oscuro `#1F2A2E` (6,7:1), nunca blanco. Los demás colores base admiten texto blanco como relleno (rojo 6,7:1; naranja 5,2:1; verde 5,1:1; gris 4,8:1).

**Conflictos identificados y cómo se resuelven:**
- **Coral de marca (9°) frente a rojo de Urgente (4°) y naranja de Alta (25°):** son tonos cálidos cercanos. Se separan por luminosidad (el coral es claro y rosado, el rojo y el naranja son oscuros), por uso (el coral nunca aparece en estados) y porque las prioridades siempre llevan su texto.
- **Aqua principal (190°) frente a azul de información (217°) y verde de finalizada (116°):** se separan por tono, por forma de uso (el principal es relleno de botón; información y finalizada son fondos suaves) y por el ícono que acompaña a cada estado.
- **Ámbar compartido** entre advertencia, prioridad Media, pausada y cambio de prioridad: comparten el significado de "precaución, atención no urgente"; el ícono y el texto indican de cuál se trata.

**Relación con la marca blanca (Sección 4):** cuando una empresa carga su logo, este reemplaza la marca GestLab, pero el sistema de color no cambia. Los colores de estado deben significar lo mismo en todas las empresas para no perder la consistencia ni la accesibilidad.


### 6.4 Tipografía (Diseño de Interfaces)

Esta subsección define el sistema tipográfico del producto como parte de la identidad visual de la Fase 2 del Proyecto Integrador de Diseño de Interfaces. Reemplaza la fuente del sistema (`system-ui`) usada en la versión inicial de `estilos.css`. Igual que el color (6.3), la tipografía se eligió por su función y por el perfil de los usuarios (6.1): personas jóvenes y mayores que leen la interfaz durante gran parte de la jornada, en celular y en computador.

**Criterios de selección:**
- **Sin serifas:** la evidencia sobre serifas en pantalla no es concluyente, pero hay indicios de que dificultan la lectura a personas con trastornos de lectura; por eso la buena práctica en web es usar fuentes sin serifas.
- **Tamaño mínimo:** 16 px es el mínimo recomendado para texto web, y para públicos con personas mayores se recomienda acercarse a 19 px.
- **Interlineado:** entre 130 % y 150 % del tamaño de la letra, para no perder el renglón.
- **Grosor:** evitar pesos delgados, sobre todo en tamaños pequeños.
- **Caracteres inconfundibles:** en un sistema donde se leen códigos de actividad y referencias de equipos ("Sensor B2", "Línea 1"), la `l` minúscula, la `I` mayúscula y el `1`, así como la `O` y el `0`, no deben confundirse.
- **Licencia libre para uso comercial:** ambas fuentes se distribuyen con la licencia SIL Open Font License 1.1, que permite usarlas en un producto comercial sin costo.

**Fuentes elegidas y función de cada una:**

| Fuente | Función | Motivo |
|---|---|---|
| **Lexend** | Todo lo que se *lee*: títulos, textos, botones, etiquetas, tablas y menús | Fuente sin serifas diseñada para facilitar la fluidez de lectura; formas redondeadas que dan una apariencia amable y moderna para un público amplio, sin perder seriedad |
| **Atkinson Hyperlegible Mono** | Todo lo que se *identifica carácter por carácter*: cronómetro, códigos de actividad, referencias de equipos y cifras | Diseñada por el Braille Institute para mejorar la legibilidad en personas con baja visión, con formas que diferencian cada carácter (la `l` con cola, el `1` con gancho, el `0` con barra). Al ser monoespaciada, todos los dígitos ocupan el mismo ancho y el cronómetro no "salta" mientras corre |

**Conflicto identificado y cómo se resuelve:** en Lexend, la `I` mayúscula y la `l` minúscula se parecen. Por eso el contenido donde una confusión de caracteres causaría un error real (códigos, referencias, tiempos y cifras) se escribe siempre en Atkinson Hyperlegible Mono.

**Escala tipográfica:** proporción 1,2 (tercera menor) sobre una base de 18 px. Cada nivel es 1,2 veces el anterior (15 → 18 → 22 → 26 → 31 px), lo que da una jerarquía clara sin saltos bruscos en pantallas pequeñas.

| Rol | Fuente | Tamaño | Peso | Interlineado | Dónde se usa |
|---|---|---|---|---|---|
| Título de pantalla (H1) | Lexend | 26 px móvil / 31 px escritorio (1,444 rem / 1,722 rem) | 600 | 1,25 | Título principal o saludo de cada pantalla |
| Título de sección (H2) | Lexend | 22 px (1,222 rem) | 600 | 1,3 | Encabezados de bloque ("Mis actividades", "Usuarios") |
| Título de tarjeta (H3) | Lexend | 18 px (1 rem) | 600 | 1,35 | Nombre de la actividad en tarjetas, títulos de diálogos |
| Texto principal | Lexend | 18 px (1 rem) | 400 | 1,5 | Descripciones, observaciones, formularios |
| Texto secundario | Lexend | 16 px (0,889 rem) | 400 | 1,45 | Metadatos (línea, estimado, asignado por), ayudas de campo |
| Tablas | Lexend | 16 px (0,889 rem) | 400 | 1,45 | Tablas del Administrador y del Superadmin |
| Etiquetas y estados | Lexend | 15 px (0,833 rem) | 600 | 1,2 | Etiquetas de prioridad, estado y jornada (siempre con ícono y color, ver 6.3) |
| Botones | Lexend | 18 px (1 rem) | 600 | — | Todos los botones |
| Cronómetro | Atkinson Hyperlegible Mono | 44 px (2,444 rem) | 600 | — | Tiempo en ejecución de la actividad |
| Códigos y cifras | Atkinson Hyperlegible Mono | 16 px (0,889 rem) | 500 | — | Códigos de actividad, referencias de equipos, porcentajes y horas en tablas |

Los valores en rem se calculan sobre una base de 18 px. Esa base se declara en la raíz del documento como `112,5 %` del tamaño del navegador (16 px por defecto), no como 18 px fijos, para que respete el tamaño de letra que cada usuario tenga configurado en su dispositivo.

**Reglas obligatorias del sistema tipográfico:**
1. **Solo dos pesos en Lexend:** 400 para leer y 600 para jerarquía y acción. No se usan pesos por debajo de 400.
2. **Ningún texto por debajo de 15 px;** ese mínimo se reserva para etiquetas cortas en negrita. El texto corrido nunca baja de 16 px.
3. **Tamaños en rem, no en px fijos:** si el usuario agranda la letra en su dispositivo, toda la interfaz crece en proporción sin romperse (WCAG 2.1, criterio 1.4.4, cambio de tamaño del texto hasta 200 %).
4. **El diseño soporta ajustes de espaciado del usuario** (interlineado 1,5, espacio entre párrafos de 2 veces el tamaño, espaciado entre letras de 0,12 y entre palabras de 0,16) sin perder contenido (WCAG 2.1, criterio 1.4.12).
5. **Códigos, referencias, tiempos y cifras siempre en Atkinson Hyperlegible Mono.**
6. **Texto alineado a la izquierda,** sin justificar, para mantener espacios regulares entre palabras.
7. Todos los estilos se definen como **variables CSS** en un único lugar (`:root` de `estilos.css`), igual que el color.

**Relación con los principios de diseño de la Fase 2:**
- **Jerarquía visual (usabilidad):** la diferencia de tamaño y peso permite distinguir de un vistazo el título, la información principal y la secundaria, y las acciones.
- **Consistencia (usabilidad):** los mismos roles tipográficos se usan en las vistas de los tres roles.
- **Semejanza (Gestalt):** todos los elementos del mismo tipo comparten estilo (por ejemplo, todos los títulos de tarjeta), así el usuario los reconoce como equivalentes.

**Implementación:** como el despliegue es local (Sección 7) y la planta puede no tener conexión estable a internet, los archivos de ambas fuentes se incluyen dentro del proyecto (en formato `.woff2`, en la carpeta `app/static/fuentes/`) en lugar de cargarse desde Google Fonts. Si una fuente no carga, el sistema usa como respaldo la fuente sin serifas del dispositivo (`system-ui, sans-serif`) para Lexend y una monoespaciada del sistema (`ui-monospace, monospace`) para Atkinson Hyperlegible Mono.

---

## 7. Alcance técnico

- Python como lenguaje principal.
- Flask como framework para el desarrollo de la aplicación web.
- MongoDB como sistema de persistencia de datos.
- HTML, CSS y JavaScript para la interfaz web. La interfaz funciona como un cliente en el navegador que consume la API REST del sistema (intercambio de datos en JSON). Los archivos de la interfaz los entrega el mismo servidor Flask (mismo origen), y la autenticación se maneja con la sesión de Flask mediante cookie.
- Programación Orientada a Objetos como paradigma principal para el diseño de la lógica del sistema.
- Arquitectura en capas, manteniendo separadas la presentación, la lógica de negocio y la persistencia.
- Git y un repositorio remoto para el control de versiones y trabajo colaborativo.
- Despliegue de la aplicación en un entorno local, con la posibilidad de desplegarla en un servidor independiente si las condiciones lo permiten, utilizando Docker como mecanismo de containerización para empaquetar y ejecutar la aplicación de forma consistente entre entornos.
- **SonarQube** como herramienta de análisis estático y control de calidad de código, integrado al repositorio de GitHub, para monitorear de forma continua aspectos como cobertura de pruebas, code smells, duplicación y cumplimiento de buenas prácticas de diseño (por ejemplo, principios SOLID).
- **Herramientas de revisión del diseño (solo desarrollo)**, en la carpeta `herramientas/`: un script que calcula el contraste WCAG entre colores (`contraste.py`) y otro que toma capturas de las pantallas en tamaño celular y escritorio con Playwright, junto con versiones desenfocada y en escala de grises para revisar la jerarquía visual y la independencia del color (`capturas.py`, con la lista de pantallas en `pantallas.json`). Sus dependencias (Playwright y Pillow) van en `requirements-dev.txt`, separadas de las del producto, y no forman parte de la imagen de Docker. Las credenciales de los usuarios de prueba se leen del archivo `.env`. Las capturas pueden tomarse con un navegador basado en Chromium que ya esté instalado (Brave, Edge o Chrome), indicando su ejecutable en `CAPTURAS_NAVEGADOR`, o con el Chromium que descarga Playwright. Las imágenes generadas no se suben al repositorio.

---

## 8. Alcance del MVP

La primera versión funcional deberá demostrar el flujo principal del sistema de extremo a extremo:

**Empresa → usuarios → requerimiento → actividad → asignación → prioridad → ejecución → registro de tiempo → análisis de carga laboral.**

El MVP se considerará cumplido cuando el sistema permita verificar, de forma concreta, lo siguiente:

1. **Empresa y usuarios:** el Superadmin puede registrar al menos una empresa y crear su primer usuario Administrador; ese Administrador puede a su vez crear usuarios Operario dentro de su empresa, y cada uno de los tres roles (Superadmin, Administrador, Operario) accede a una interfaz distinta según su rol.
2. **Requerimiento → Actividad:** un Administrador puede registrar un requerimiento y convertirlo en una o más actividades de trabajo.
3. **Asignación y prioridad:** cada actividad puede asignarse a uno o varios Operarios, y se le puede definir una prioridad, un tiempo estimado de ejecución y una fecha programada.
4. **Ejecución:** un Operario puede iniciar, pausar, reanudar y finalizar una actividad asignada, y el sistema registra automáticamente los tiempos reales de cada una de esas acciones.
5. **Registro de tiempo:** al finalizar una actividad, el sistema almacena el tiempo real de ejecución y permite compararlo con el tiempo estimado.
6. **Análisis de carga laboral:** el Administrador puede consultar, para al menos un Operario, su ocupación actual (actividades en curso/pendientes) con base en los datos generados en los pasos anteriores.
7. **Turnos y asistencia:** el Administrador puede definir al menos un turno y asignarlo a un Operario; el Operario puede marcar entrada y salida, y el Administrador puede validarlas o corregirlas. Si el Operario no marca entrada dentro de la tolerancia, el Administrador recibe el aviso y puede reasignar sus actividades; las que no reasigne quedan reprogramadas en la siguiente jornada del Operario, con el evento registrado.
8. **Indicadores de cumplimiento:** el Administrador puede consultar, para al menos un Operario y para la empresa, el cumplimiento de jornada, el aprovechamiento, el tiempo adicional y el cumplimiento de actividades, calculados con los datos generados en los pasos anteriores.

El MVP priorizará el funcionamiento completo y verificable de este flujo sobre la incorporación de funcionalidades avanzadas (ver Sección 9 y Sección 13).

---

## 9. Funcionalidades fuera del alcance obligatorio inicial

- Inteligencia Artificial como componente obligatorio del MVP. Se considera una posible ampliación sujeta a validación.
- Aplicación móvil nativa para Android o iOS; la primera versión será una aplicación web responsive.
- Sistemas avanzados de nómina o remuneración. El sistema registra la asistencia y el tiempo adicional para los indicadores, pero no calcula pagos, horas extra ni descuentos.
- Automatización completa de decisiones de asignación o priorización, salvo la reprogramación automática por ausencia definida en la Sección 5.1, que queda registrada y es visible para el Administrador.
- Integraciones empresariales externas que no sean necesarias para demostrar el funcionamiento del MVP.

---

## 10. Referencias normativas

El proyecto tomará como referencia principios de normas internacionales relacionadas con sistemas de trabajo, interacción humano-sistema y gestión de calidad. Estas referencias se utilizarán como orientación para el diseño y no implican certificación o conformidad formal.

- **ISO 6385:2016** – Ergonomics principles in the design of work systems. Referencia para considerar la relación entre personas, tecnología y organización del trabajo, especialmente en el diseño de la experiencia de ejecución y el análisis de carga laboral.
- **ISO 9241-210:2019** – Ergonomics of human-system interaction – Part 210: Human-centred design for interactive systems. Referencia para el diseño centrado en el usuario y la interacción con la aplicación, particularmente en el uso desde dispositivos móviles.
- **ISO 10006:2017** – Quality management – Guidelines for quality management in projects. Referencia conceptual para aspectos relacionados con recursos, medición, análisis y mejora.
- **PEP 8** – Guía de estilo oficial para código Python. Se utilizará como referencia de buenas prácticas de escritura de código (nombres, indentación, formato), y su cumplimiento se verificará de forma automática mediante SonarQube (ver Sección 7).
- **Clean Code (Robert C. Martin)** – Conjunto de principios y buenas prácticas de programación (nombres significativos, funciones pequeñas y con una sola responsabilidad, entre otros). Se utilizará como referencia conceptual complementaria a los principios SOLID y la Ley de Demeter trabajados en la materia de Diseño Orientado a Objetos.
- **ISO 3864-1:2011** – Graphical symbols – Safety colours and safety signs – Part 1: Design principles. Referencia para el significado de los colores de estado de la interfaz (Sección 6.3).
- **ANSI Z535** – Norma estadounidense de señalización de seguridad. Referencia para la escala de color de las prioridades por nivel de riesgo (Sección 6.3).
- **ANSI/ISA-101.01-2015** – Human Machine Interfaces for Process Automation Systems. Referencia para el uso de fondos neutros y la reserva del color para lo que requiere acción (Sección 6.3).
- **WCAG 2.1** – Pautas de Accesibilidad para el Contenido Web (W3C). Referencia para los niveles mínimos de contraste entre texto, componentes y fondos (Sección 6.3), el cambio de tamaño del texto hasta 200 % (criterio 1.4.4) y el espaciado del texto (criterio 1.4.12) (Sección 6.4).
- **Especificación de Requisitos de Software (ERS)** – Documento complementario del Alcance, basado en el estándar IEEE Std 830-1998, elaborado por el equipo del proyecto (Pedro González y Sebastián Vargas). Detalla los requisitos funcionales (RF01-RF12) y no funcionales, así como casos de uso específicos, que amplían y formalizan lo definido en este documento de Alcance.

---

## 11. Trabajo colaborativo y control de versiones

El desarrollo será realizado por un equipo de dos integrantes mediante Git y un repositorio remoto compartido. Se propone mantener una rama estable para el producto, una rama de integración y ramas de funcionalidades para desarrollar cambios de manera independiente.

- `main`: versión estable.
- `develop`: integración del trabajo del equipo.
- `feature/*`: desarrollo de funcionalidades específicas.

Los cambios deberán integrarse mediante Pull Requests, los cuales deberán pasar la revisión automática de **SonarQube** antes de ser aprobados e integrados, con el fin de validar la calidad del código (cumplimiento de PEP 8, principios SOLID, ausencia de code smells, entre otros). Los cambios deberán mantenerse documentados para facilitar la colaboración y reducir conflictos entre los integrantes.

**Documento de alcance como fuente única de reglas.** Las reglas del proyecto (dominio, alcance funcional, diseño de interfaz, color y tipografía) se escriben una sola vez, en este documento. Los archivos de apoyo que guían el trabajo (`CLAUDE.md` y los agentes de `.claude/agents/`) apuntan a las secciones de este documento en lugar de copiar su contenido. Cuando una regla cambia, se actualiza primero este documento con su entrada en la bitácora, y después el código. Así se evita mantener versiones distintas de una misma regla. Los enunciados de las entregas de cada materia se guardan en `docs/enunciados/` como referencia; ante cualquier diferencia, manda el enunciado original de la docente.

**Agentes de apoyo con Claude Code.** El equipo usa agentes de Claude Code definidos en `.claude/agents/`, cada uno con una responsabilidad acotada:

| Agente | Responsabilidad | Permisos |
|---|---|---|
| `diseno-oo` | Diseño y revisión del modelo de clases | Solo lectura |
| `backend-flask` | Servicios y rutas de la API | Lectura y escritura |
| `persistencia-mongo` | Repositorios y esquemas de MongoDB | Lectura y escritura |
| `frontend-web` | Interfaz HTML, CSS y JavaScript, aplicando las Secciones 6.1 a 6.4 | Lectura y escritura en `app/static/` (y la lista de pantallas de `herramientas/pantallas.json`) |
| `revisor-codigo` | Calidad del código, separación de capas y seguridad básica | Solo lectura |
| `profesor-doo` | Verificación contra el syllabus de Diseño Orientado a Objetos | Solo lectura |
| `profesor-interfaces` | Verificación contra el syllabus de Diseño de Interfaces y auditoría del diseño de las pantallas (Secciones 6.1 a 6.4, normas citadas, capturas); propone correcciones sin aplicarlas | Solo lectura, más la ejecución de los scripts de `herramientas/` |

Los agentes son herramientas de trabajo del equipo: no forman parte del producto ni de los entregables de las materias. Por eso `CLAUDE.md` y la carpeta `.claude/` **no se suben al repositorio**: están en el `.gitignore` y se mantienen solo en el computador de cada integrante. Al no viajar por Git, cada integrante es responsable de conservar su propia copia.

**Archivos que no se suben al repositorio:** el `.env` (claves y contraseñas; el repositorio solo incluye `.env.example` con valores de ejemplo), los archivos de apoyo de IA (`CLAUDE.md`, `.claude/`), las capturas de `herramientas/capturas/` y los entornos virtuales de Python.

---

## 12. Arquitectura inicial propuesta

- **Capa de presentación:** interfaz web responsive construida como un cliente en el navegador (HTML, CSS y JavaScript), separada de las rutas del servidor. Se comunica con el backend únicamente a través de la API REST.
- **Servidor web (Flask):** expone la API REST y entrega los archivos estáticos de la interfaz; no genera pantallas.
- **Capa de lógica de negocio:** reglas de gestión, priorización, ejecución, tiempos y análisis implementadas en Python mediante POO.
- **Capa de persistencia:** acceso y almacenamiento de información en MongoDB.

La definición detallada de clases, relaciones y patrones de diseño se realizará después de cerrar el dominio y las reglas de negocio.

---

## 13. Posibles ampliaciones futuras

- Uso de datos históricos para mejorar la estimación de duración de actividades.
- Funciones de Inteligencia Artificial para apoyar la estimación, clasificación o análisis de actividades.
- Notificaciones avanzadas (por ejemplo, fuera de la aplicación: correo electrónico, push, mensajería). No incluye alertas simples dentro de la misma interfaz, como la de sobrecarga definida en la Sección 5.2.
- Análisis y reportes más especializados.
- Integración con otras herramientas empresariales.
- Trabajo sin conexión: guardar en el dispositivo los eventos de ejecución (inicio, pausa, reanudación, fin) cuando se pierda la red y sincronizarlos automáticamente al recuperarla (ERS, CU01, excepción E1). Se excluye del MVP por su complejidad (cola de eventos, confiabilidad de la hora del dispositivo, duplicados y conflictos); en el MVP la hora de cada evento la registra el servidor.
- Consideración para la comercialización: al registrar asistencia de trabajadores, cada empresa cliente necesitará una política de tratamiento de datos personales (en Colombia, Ley 1581 de 2012). No es un requisito del proyecto académico.

---

## Bitácora de cambios

| Fecha | Materia | Sección(es) | Cambio realizado | Motivo |
|---|---|---|---|---|
| 2026-09-05 | POO | Sección 7 — Alcance técnico | Se agrega Docker como mecanismo de containerización para el despliegue | Instrucción de clase: Docker se usará de forma transversal para desplegar todo el proyecto, no estaba contemplado en la v0.1 |
| 2026-09-05 | POO | Sección 1 — Descripción general | Se amplía el texto original para dar más claridad sobre el propósito del sistema, sin agregar detalle técnico | Solicitud de mejorar la redacción para que sea más entendible, manteniendo el mismo contenido |
| 2026-09-05 | POO | Secciones 1, 2, 4, 5.1, 5.2, 6 | Cambio de terminología de roles: "Supervisor" → "Administrador", "Empleado" → "Operario" (y sus variantes: empleados, supervisores) | Ajuste de nomenclatura solicitado para alinear los roles del sistema con los términos que se van a usar en el proyecto |
| 2026-09-05 | POO | Sección 7 — Alcance técnico (punto 8) | Se cambia el tipo de despliegue: de "servidor o plataforma en la nube" a "entorno local, con posibilidad de servidor independiente" | El plan de presentación es local, con un servidor aparte como opción deseable si es posible; se descarta por ahora la nube |
| 2026-09-05 | POO | Sección 8 — Alcance del MVP | Se transforma el flujo general en 6 criterios de aceptación medibles (verificables como sí/no), incluyendo explícitamente los roles Administrador/Operario en cada paso | Se buscaba que el MVP fuera medible y no solo descriptivo, para usarlo como checklist de aceptación en la sustentación |
| 2026-09-05 | POO | Sección 7 — Alcance técnico | Se agrega análisis estático de calidad con SonarQube integrado a GitHub | Instrucción de clase: se debe interactuar con SonarQube de forma transversal en el proyecto; no se agregan pytest ni Postman porque no fueron solicitados |
| 2026-09-05 | POO | Sección 10 — Referencias normativas | Se agregan PEP 8 (guía de estilo Python) y Clean Code (Robert C. Martin) como referencias de buenas prácticas de programación | Se buscaba alinear el proyecto con buenas prácticas de código; PEP 8 se aprovecha directamente con SonarQube y Clean Code refuerza SOLID/Ley de Demeter ya vistos en POO |
| 2026-09-05 | POO | Sección 11 — Trabajo colaborativo y control de versiones | Se especifica que los Pull Requests deben pasar la revisión automática de SonarQube antes de ser aprobados e integrados | Se necesitaba definir en qué punto del flujo de Git se ejecuta SonarQube |
| 2026-09-05 | POO | Sección 14 — Criterio de cierre del alcance inicial | Se elimina la sección completa | Su contenido quedó duplicado y superado por los 6 criterios medibles ya definidos en la Sección 8 (Alcance del MVP) |
| 2026-09-06 | Diseño de Interfaces | Título del documento; nueva Sección 6.1 | Se agrega el nombre definitivo del proyecto ("GestLab") y una nueva subsección 6.1 con la persona (Carlos), el hallazgo del mapa de empatía y las 4 pantallas mínimas definidas para el Operario | Documentar en el alcance los insumos de investigación de usuario y wireframes trabajados en Diseño de Interfaces (Semana 6, personas/mapa de empatía + wireframes combinados), para que informen tanto el diseño de interfaz como el modelo de datos en POO |
| 2026-09-06 | Diseño de Interfaces | Sección 8 — Alcance del MVP (sin cambio) | Se decide explícitamente NO agregar un criterio verificable de interfaz a la Sección 8 | Se prefiere mantener el MVP con criterios solo de datos/flujo por ahora; queda como decisión registrada, no como omisión |
| 2026-09-06 | POO | Secciones 5.1 y 8 | Se cambia la relación actividad-operario de "uno a uno" a "uno o varios operarios" por actividad | Insumo del documento ERS (IEEE 830) del equipo: RF05 permite asignar una actividad a varios empleados; implica una relación muchos-a-muchos entre Actividad y Operario en el modelo de clases |
| 2026-09-06 | Diseño de Interfaces | Secciones 5.2 y 9 | Se agrega una alerta en pantalla (no notificación externa) cuando la asignación supera el 100% de capacidad del operario; se aclara en la Sección 9 que esto no es lo mismo que "notificaciones avanzadas" | Insumo del ERS (RF12): se decidió implementarlo como validación simple en pantalla, no como sistema de notificaciones externo (que sigue fuera de alcance) |
| 2026-09-06 | Diseño de Interfaces | Sección 6.1 | Se agrega la necesidad de registrar un motivo/causa al pausar una actividad, y su implicación como dato asociado a cada evento de pausa | Insumo del ERS (RF09): al pausar, el sistema debe solicitar un motivo de interrupción |
| 2026-09-06 | Ambas | Sección 10 — Referencias normativas | Se agrega el documento ERS (IEEE 830) del equipo como referencia complementaria del Alcance | El equipo elaboró un ERS formal que detalla RF/RNF y casos de uso; se documenta como referencia, sin fusionar su contenido completo al Alcance |
| 2026-09-12 | POO | Sección 4 — Usuarios del sistema | Se agrega un tercer rol, Superadmin, no contemplado en la v0.1 ni en el ERS | Al diseñar la Etapa 1 (Empresa + usuarios) surgió una ambigüedad no resuelta: ningún documento definía quién registra una empresa nueva. Se decidió introducir un rol técnico separado de Administrador/Operario para dar de alta empresas y su primer Administrador |
| 2026-09-12 | POO | Sección 5.1 | Se separa "registro de empresa y primer Administrador" (a cargo del Superadmin) de "administración de usuarios Administrador/Operario dentro de la empresa" | Consecuencia directa de introducir el rol Superadmin: la Sección 5.1 quedaba inconsistente si no distinguía quién hace qué |
| 2026-09-12 | POO | Sección 8, criterio 1 | Se reescribe el criterio de "Empresa y usuarios" para reflejar los tres roles y quién crea a quién (Superadmin → Administrador → Operario) | Mantener el MVP medible y consistente con el nuevo rol Superadmin |
| 2026-09-26 | POO | Sección 5.1 | Se definen cuatro niveles de prioridad (Baja, Media, Alta, Urgente); Urgente significa interrumpir la actividad en curso | Insumo del ERS (CU01), que usa cuatro niveles; el código tenía tres y el alcance no lo definía. Se decidió que Urgente tenga un comportamiento propio, alineado con la interrupción de actividades ya prevista en 5.1 y la necesidad de notar cambios de prioridad (6.1) |
| 2026-09-26 | POO | Sección 5.1 | Se agrega la regla de una sola actividad en ejecución por operario, con pausa manual | Insumo del ERS (CU01, FA1). Evita contar tiempo real doble y protege la calidad del dato de carga laboral. Se eligió pausa manual (no automática) para que el operario decida y registre el motivo |
| 2026-09-26 | POO | Secciones 5.1, 5.2 y 8 (criterio 3) | Se agregan la fecha programada de cada actividad, la capacidad diaria por operario y el cálculo de carga por día; la alerta del 100% compara contra la capacidad del día programado | La alerta de sobrecarga (RF12) no tenía definidos capacidad ni carga. Capacidad por operario porque la persona de referencia tiene turno rotativo; fecha programada para dar sustento a la "proyección a partir de actividades programadas" de 5.2 |
| 2026-09-26 | Diseño de Interfaces | Sección 6.1 | Se agrega la necesidad de un aviso visible de actividad Urgente pendiente | Consecuencia de las decisiones de prioridad Urgente y pausa manual: el operario necesita enterarse para poder pausar su actividad actual |
| 2026-09-26 | Diseño de Interfaces | Sección 6.1 | Se agregan las 6 leyes de usabilidad (Hick, Fitts, Jakob, Miller, Proximidad, estético-usabilidad) como principios de diseño | Insumo de la clase de Semana 7. Los indicadores de evaluación de esa clase no se incorporan al alcance: se usan como material de evaluación de la materia, ya que varios están pensados para portales de contenido |
| 2026-09-26 | Ambas | Secciones 7 y 12 | Se define la interfaz como cliente HTML/CSS/JS que consume la API REST, servido por el mismo Flask | Separación clara cliente-servidor y de tres capas (Momentos 2 y 3 de DOO), retroalimentación inmediata sin recargar (heurísticas de Nielsen) y reutilización de la API por futuros clientes, como una app móvil |
| 2026-09-26 | POO | Sección 13 | Se registra el trabajo sin conexión con sincronización como ampliación futura | Insumo del ERS (CU01, E1). Se excluye del MVP por su complejidad y porque ninguno de los dos syllabus lo exige |
| 2026-09-26 | Diseño de Interfaces | Ninguna (decisión registrada) | Se decide presentar en Diseño de Interfaces la interfaz construida en código (HTML/CSS/JS), sin prototipo previo en Penpot | Decisión del equipo. **Discrepancia pendiente:** el syllabus asigna a las semanas 8 y 9 wireframes de media fidelidad y prototipos interactivos, y cita Penpot. Pendiente confirmar con el profesor antes de la evaluación de Semana 10 |
| 2026-09-26 | POO | Secciones 4 y 5.1 | Se agregan turnos (catálogo por empresa, un turno por operario con fecha de cambio) y registro de asistencia (marca del operario, validación del Administrador) | Nueva necesidad del equipo: medir el tiempo que el operario debió trabajar contra el que dedicó a actividades. Se eligió validación por el Administrador para que la asistencia tenga dos fuentes y sirva como evidencia |
| 2026-09-26 | POO | Sección 5.1 | Se agregan el aviso de posible ausencia por tolerancia, la reasignación manual y la reprogramación automática de actividades no reasignadas, con registro del evento y aviso de sobrecarga | Nueva necesidad del equipo: reaccionar a tiempo ante ausencias. El evento de reprogramación evita que el incumplimiento desaparezca de las métricas |
| 2026-09-26 | POO | Sección 5.2 | La capacidad deja de ser un valor fijo por operario y pasa a calcularse desde su turno; "carga por día" pasa a ser "carga por jornada" (la jornada pertenece al día de inicio del turno) | Modifica la decisión tomada el mismo día sobre capacidad. Los turnos nocturnos cruzan la medianoche y se decidió no partir una jornada en dos días |
| 2026-09-26 | POO | Sección 5.2 | Se agregan los indicadores de cumplimiento de jornada, aprovechamiento, tiempo adicional, cumplimiento de actividades y precisión de estimación, por operario, categoría y empresa | Nueva necesidad del equipo: estadísticas personales y generales. Se definen dos indicadores separados para distinguir asistencia de productividad, y los agregados se calculan sumando tiempos para no distorsionar el resultado |
| 2026-09-26 | Diseño de Interfaces | Sección 6.1 | Se agrega el banner de "en turno / fuera de turno" (color y texto) y la marca de entrada y salida desde el celular | Aplicación de la heurística de visibilidad del estado del sistema; no depender solo del color, por accesibilidad |
| 2026-09-26 | Ambas | Sección 8 | Se agregan los criterios 7 (turnos y asistencia) y 8 (indicadores de cumplimiento) al MVP | Decisión del equipo de incluir toda la nueva funcionalidad en el MVP |
| 2026-09-26 | POO | Sección 9 | Se retira "control de asistencia laboral" de lo excluido (nómina y remuneración siguen fuera) y se agrega la excepción de reprogramación automática por ausencia | Consecuencia de incluir asistencia en el alcance. Se mantiene la frontera con la nómina para no convertir el producto en un software de pagos |
| 2026-09-26 | POO | Sección 5.1 | El tiempo estimado corresponde a la actividad completa y no se reparte entre los operarios asignados | Decisión del equipo; resuelve la ambigüedad que dejó la asignación a varios operarios |
| 2026-09-26 | Diseño de Interfaces | Ninguna (aclaración) | Se cierra la discrepancia sobre Penpot: los wireframes y prototipos del syllabus ya se entregaron en un primer momento; desde ahora el trabajo de interfaz es en código | Aclaración del equipo |
| 2026-09-26 | Ambas | Secciones 4 y 5.1 | Marca blanca: el Superadmin puede cargar el logo de cada empresa (PNG, JPG o WEBP, máximo 512 KB), y los usuarios de esa empresa ven su logo y nombre en lugar de la marca GestLab | Decisión del equipo: que cada cliente sienta el sistema como propio |
| 2026-09-26 | POO | Secciones 4 y 5.1 | El Superadmin define por empresa un límite de Administradores y otro de Operarios; el sistema impide crear usuarios por encima del límite y reducir un límite por debajo de los usuarios existentes | Decisión del equipo: controlar el tamaño de cada cliente (base para un futuro esquema de planes) |
| 2026-09-26 | Diseño de Interfaces | Nueva Sección 6.2 | Se definen las vistas y el menú de cada rol, y las decisiones de diseño comunes: marco con menú lateral, formularios en diálogos detrás de un botón, estados vacíos, paleta sobria y su relación con las heurísticas de Nielsen | La primera versión de la interfaz mostraba formularios de creación siempre abiertos y sin menú de navegación; se reorganizó para que cada pantalla muestre primero la información |
| 2026-09-26 | Ambas | Sección 13 | Se anota como consideración de comercialización la política de tratamiento de datos personales de asistencia | La asistencia es un dato personal de trabajadores; no afecta el proyecto académico |
| 2026-10-02 | Diseño de Interfaces | Sección 6.1 | Se agrega el perfil ampliado de los usuarios (jóvenes y mayores, de todo género y nivel tecnológico, uso durante gran parte de la jornada) y cuatro exigencias de diseño derivadas: legibilidad, bajo cansancio visual, información que no depende solo del color e interfaz amable y profesional | Al definir la paleta de la Fase 2 se aclaró que la persona de referencia (Carlos, 34 años) no representa a todos los usuarios; las decisiones de color y tipografía deben servir a un público amplio |
| 2026-10-02 | Diseño de Interfaces | Nueva Sección 6.3 | Se define el sistema de color "Aqua de trabajo": base con tinte aqua, principal `#16697A`, acento de marca coral `#E9806E` en armonía complementaria, colores de estado con tres variantes, asignación por elemento, reglas obligatorias y conflictos resueltos. Reemplaza la paleta inicial de `estilos.css` (acento `#0f766e`) | Requerimiento 3 de la Fase 2 del Proyecto Integrador (propuesta cromática definida y justificada). Se eligió tras varias rondas de opciones; se fundamenta en estudios de color y trabajo (Kwallek; Mehta y Zhu, 2009), en normas de color industrial y en la visión de personas mayores |
| 2026-10-02 | Diseño de Interfaces | Sección 6.2 | Se ajusta la decisión "Paleta sobria": ahora incluye un acento de marca solo para identidad, exige ícono además de texto en los estados y remite a la Sección 6.3 | Consecuencia de la nueva Sección 6.3 |
| 2026-10-02 | Diseño de Interfaces | Sección 10 — Referencias normativas | Se agregan ISO 3864-1, ANSI Z535, ANSI/ISA-101.01-2015 y WCAG 2.1 como referencias del sistema de color | Las decisiones de la Sección 6.3 se apoyan en estas normas; se documentan como orientación, sin implicar certificación |
| 2026-10-02 | Diseño de Interfaces | Nueva Sección 6.4 | Se define el sistema tipográfico: Lexend para todo lo que se lee y Atkinson Hyperlegible Mono para cronómetro, códigos, referencias y cifras; escala de proporción 1,2 sobre base de 18 px con tamaños en rem, dos pesos (400 y 600), interlineados, siete reglas obligatorias, relación con los principios de la Fase 2 e implementación con fuentes incluidas en el proyecto. Reemplaza la fuente del sistema (`system-ui`) | Identidad visual de la Fase 2 del Proyecto Integrador. Se eligió Lexend entre tres opciones (Atkinson Hyperlegible Next, Bricolage Grotesque + Atkinson, Lexend) por su apariencia amable y moderna para un público amplio; su debilidad (`I` y `l` parecidas) se compensa usando Atkinson Hyperlegible Mono donde una confusión causaría un error. Fuentes incluidas en el proyecto porque el despliegue es local |
| 2026-10-02 | Diseño de Interfaces | Sección 6.2 | Se agrega la decisión común "Tipografía legible" con remisión a la Sección 6.4 | Consecuencia de la nueva Sección 6.4 |
| 2026-10-02 | Diseño de Interfaces | Sección 10 — Referencias normativas | Se amplía la referencia a WCAG 2.1 con los criterios 1.4.4 (cambio de tamaño del texto) y 1.4.12 (espaciado del texto) | Las reglas de la Sección 6.4 se apoyan en estos criterios |
| 2026-10-03 | Diseño de Interfaces | Sección 7 — Alcance técnico | Se agregan las herramientas de revisión del diseño (`herramientas/contraste.py`, `herramientas/capturas.py` con `pantallas.json`) y sus dependencias de desarrollo (Playwright y Pillow en `requirements-dev.txt`, fuera de la imagen de Docker) | Se necesitaba verificar de forma objetiva el contraste y revisar la jerarquía visual y Gestalt sobre capturas reales de la aplicación, como apoyo a la Fase 2 |
| 2026-10-03 | Ambas | Sección 11 — Trabajo colaborativo | Se establece el documento de alcance como fuente única de reglas (CLAUDE.md y los agentes apuntan a él), se crea `docs/enunciados/` para los enunciados de las entregas y se documentan los siete agentes de Claude Code con su responsabilidad y permisos | Evitar actualizar varios documentos por separado cuando cambia una regla. Al ampliar el agente `profesor-interfaces` con la auditoría de diseño (opción elegida: un solo agente que enseña y audita) se actualizaron todos los agentes para que lean el alcance, y se corrigió la ruta del syllabus (`docs/Syllabus/`) en los agentes que la tenían mal escrita |
| 2026-10-03 | Diseño de Interfaces | Sección 6.4 — Implementación | Se precisa la carpeta de las fuentes: `app/static/fuentes/` | Los agentes `frontend-web` y `profesor-interfaces` necesitan una ubicación concreta para construir y verificar |
| 2026-10-03 | Diseño de Interfaces | Sección 6.3 — Reglas y asignación por elemento | Se agrega la regla 7 sobre el ámbar base `#E3A32B` (no se usa como borde, ícono o texto sobre superficies claras; como relleno lleva texto oscuro) y se precisa el color del texto de las etiquetas de prioridad Alta y Media | Al medir con `herramientas/contraste.py`, el ámbar sobre blanco da 2,2:1 (por debajo del 3:1 exigido a componentes) y no admite texto blanco; los demás colores base sí |
| 2026-10-03 | Diseño de Interfaces | Sección 6.2 | Se agrega el bloque "Leyes de Gestalt aplicadas" (proximidad, semejanza, continuidad, figura y fondo; cierre pendiente) con el lugar donde se evidencia cada una | Requerimiento 2 de la Fase 2: el alcance documentaba usabilidad y color, pero de Gestalt solo mencionaba la semejanza |
| 2026-10-03 | Diseño de Interfaces | Sección 7 — Alcance técnico (sin cambio de texto) | Se actualiza Playwright de 1.47.0 a 1.63.0 en `requirements-dev.txt` | La versión 1.47.0 depende de una versión de `greenlet` sin instalador para Python 3.13, que es la que usa el equipo fuera de Docker |
| 2026-10-03 | Diseño de Interfaces | Sección 7 — Alcance técnico | Las capturas pueden tomarse con un navegador Chromium ya instalado (`CAPTURAS_NAVEGADOR`), además del Chromium de Playwright | Evitar la descarga del navegador de Playwright cuando el equipo ya tiene Brave, Edge o Chrome |
| 2026-10-03 | Ambas | Sección 11 — Trabajo colaborativo | `CLAUDE.md` y la carpeta `.claude/` dejan de subirse al repositorio (se agregan al `.gitignore`), y se listan los archivos que no se versionan | Decisión del equipo: el repositorio público contiene solo el producto y su documentación; las herramientas de apoyo quedan en el computador de cada integrante |

### Texto original de las secciones modificadas (para referencia)

**Sección 6.2, decisión "Paleta sobria" (previo al sistema de color, 2026-10-02):**
> - "**Paleta sobria:** fondos neutros y un solo color de acento. Los colores fuertes se reservan para lo que tiene significado (prioridades, avisos) y siempre van acompañados de texto."

**Sección 4, Superadmin (previo a marca blanca y límites de usuarios, 2026-09-26):**
> "Es responsable de dar de alta nuevas empresas en el sistema y crear el primer usuario Administrador de cada una." (sin logo ni límites de usuarios)

**Sección 5.1 (fragmento previo a la aclaración del tiempo estimado, 2026-09-26):**
> - "Definición de tiempo estimado de ejecución." (sin definir cómo se trata cuando hay varios operarios)

**Sección 1 (v0.1 original):**
> "El proyecto consiste en el desarrollo de un sistema web orientado a la gestión y análisis de las actividades laborales de empleados pertenecientes a diferentes empresas. La solución busca centralizar los requerimientos que llegan a un área, convertirlos en actividades de trabajo, asignarlas y priorizarlas, registrar su ejecución y generar información sobre la carga laboral del personal."

**Sección 4 (v0.1 original):**
> - "Supervisor: administra y da seguimiento a los requerimientos y actividades del área, asigna responsables, establece prioridades y consulta la carga laboral del personal."
> - "Empleado: consulta sus actividades, conoce la información necesaria para ejecutarlas, registra su ejecución y puede reportar actividades solicitadas por otras áreas para conocimiento y gestión del supervisor."

**Sección 5.1 (fragmentos v0.1 originales):**
> - "Registro y administración de usuarios con perfiles de Supervisor y Empleado."
> - "Creación y asignación de actividades a empleados."
> - "Posibilidad de que un empleado registre una actividad solicitada por otra área y la socialice con su supervisor."

**Sección 5.2 (fragmento v0.1 original):**
> - "Análisis de la carga laboral de los empleados."

**Sección 6 (v0.1 original):**
> "La aplicación será web y tendrá un diseño responsive. La interfaz para supervisores estará orientada principalmente a la gestión y análisis, mientras que la experiencia del empleado dará especial importancia al uso desde dispositivos móviles, debido a que la ejecución de actividades requiere iniciar, pausar, reanudar y finalizar tareas durante la jornada laboral."

**Sección 7, último punto (v0.1 original):**
> "Despliegue de la aplicación en un servidor o plataforma en la nube."

**Sección 8 (v0.1 original):**
> "La primera versión funcional deberá demostrar el flujo principal del sistema:
> Empresa → usuarios → requerimiento → actividad → asignación → prioridad → ejecución → registro de tiempo → análisis de carga laboral.
> El MVP priorizará el funcionamiento completo de este flujo sobre la incorporación de funcionalidades avanzadas."

**Sección 5.1 (fragmento previo a este cambio):**
> - "Creación y asignación de actividades a operarios." (relación uno a uno)

**Sección 8, criterio 3 (previo a este cambio):**
> "Asignación y prioridad: cada actividad puede asignarse a un Operario y se le puede definir una prioridad y un tiempo estimado de ejecución."

**Sección 5.2 (fragmento previo a este cambio):**
> - "Identificación de posibles situaciones de sobrecarga." (sin mecanismo de alerta definido)

**Sección 9 (fragmento previo a este cambio):**
> - "Notificaciones avanzadas." (sin distinción entre alertas simples en interfaz y notificaciones externas)

**Sección 4 (previo a este cambio, sin Superadmin):**
> - "Administrador (antes "Supervisor"): administra y da seguimiento a los requerimientos y actividades del área, asigna responsables, establece prioridades y consulta la carga laboral del personal."
> - "Operario (antes "Empleado"): consulta sus actividades, conoce la información necesaria para ejecutarlas, registra su ejecución y puede reportar actividades solicitadas por otras áreas para conocimiento y gestión del administrador."

**Sección 5.1 (fragmento previo a este cambio):**
> - "Registro y administración de usuarios con perfiles de Administrador y Operario." (sin distinguir quién registra la empresa)

**Sección 8, criterio 1 (previo a este cambio):**
> "Empresa y usuarios: es posible registrar al menos una empresa y crear usuarios con los dos perfiles definidos (Administrador y Operario), y cada uno accede a una interfaz distinta según su rol."

**Sección 10 (v0.1 original):**
> "El proyecto tomará como referencia principios de normas internacionales relacionadas con sistemas de trabajo, interacción humano-sistema y gestión de calidad... ISO 6385:2016... ISO 9241-210:2019... ISO 10006:2017..." (sin PEP 8 ni Clean Code)

**Sección 11 (v0.1 original):**
> "Los cambios deberán integrarse mediante Pull Requests y mantenerse documentados para facilitar la colaboración y reducir conflictos entre los integrantes." (sin mención a SonarQube)

**Sección 14 (v0.1 original, eliminada):**
> "El alcance inicial se considerará cumplido cuando un usuario pueda registrar o gestionar una empresa, operar con los perfiles definidos, registrar y asignar actividades, establecer prioridades y tiempos estimados, ejecutar actividades desde una interfaz web adaptable a móviles, registrar sus tiempos reales y consultar información básica sobre carga y ocupación del personal."

**Sección 5.1 (fragmentos previos a los cambios del 2026-09-26):**
> - "Definición de prioridad de las actividades." (sin niveles definidos)
> - Sin fecha programada de actividades ni regla de una sola actividad en ejecución.

**Sección 5.2 (fragmento previo a los cambios del 2026-09-26):**
> - "Alerta en pantalla al momento de asignar una actividad, cuando la carga proyectada del operario supere el 100% de su capacidad disponible." (sin definir capacidad ni forma de calcular la carga)

**Sección 7 (fragmento previo a los cambios del 2026-09-26):**
> - "HTML, CSS y JavaScript para la interfaz web, según las necesidades de implementación."

**Sección 8, criterio 3 (previo a los cambios del 2026-09-26):**
> "Asignación y prioridad: cada actividad puede asignarse a uno o varios Operarios, y se le puede definir una prioridad y un tiempo estimado de ejecución."

**Sección 12 (fragmento previo a los cambios del 2026-09-26):**
> - "Capa de presentación: interfaz web responsive."

**Sección 4 (previo a los cambios de turnos y asistencia del 2026-09-26):**
> Administrador y Operario sin funciones de turnos ni asistencia.

**Sección 5.2 (fragmento previo a los cambios de turnos del 2026-09-26):**
> - "Definición de una capacidad diaria propia para cada operario, expresada en horas por día."
> - "Cálculo de la carga por día: suma de los tiempos estimados de las actividades asignadas al operario y programadas para ese día."

**Sección 8 (previo a los cambios de turnos y asistencia del 2026-09-26):**
> Seis criterios de aceptación, sin turnos, asistencia ni indicadores de cumplimiento.

**Sección 9 (fragmentos previos al 2026-09-26):**
> - "Sistemas avanzados de nómina, remuneración o control de asistencia laboral."
> - "Automatización completa de decisiones de asignación o priorización."
