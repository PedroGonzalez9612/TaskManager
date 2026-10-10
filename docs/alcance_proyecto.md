# DOCUMENTO DE ALCANCE DEL PROYECTO
## GestLab
### Sistema web para la gestión y análisis de carga laboral
### Proyecto académico — Diseño Orientado a Objetos (POO) & Diseño de Interfaces

> **Estado:** Documento vivo. Versión base: v0.1 (original). Se actualiza de forma incremental a medida que avanzan ambas materias. La bitácora completa de cambios, con fecha y motivo de cada uno, se encuentra al final del documento.

---

## 1. Descripción general

El proyecto consiste en el desarrollo de un sistema web orientado a la gestión y análisis de las actividades laborales de operarios pertenecientes a diferentes empresas. Su propósito es dar orden y visibilidad a todo el ciclo de trabajo dentro de un área: desde que llega una necesidad o solicitud, hasta que esta se convierte en una actividad concreta, se asigna a una persona responsable, se ejecuta y finalmente se analiza en conjunto con el resto de la carga laboral del equipo.

En términos simples, el sistema busca responder tres preguntas que suelen ser difíciles de contestar en el día a día de un área de trabajo: **qué se debe hacer**, **quién lo está haciendo (o debería hacerlo)**, y **cuánto trabajo hay realmente en curso**. Para lograrlo, la solución centraliza el trabajo que llega al área en actividades claramente definidas, independientes o agrupadas en proyectos, permite asignarlas y priorizarlas según su importancia, registra su ejecución en tiempo real, y finalmente genera información útil sobre la carga laboral del personal — tanto la actual como una proyección de lo que viene.

De esta forma, el sistema no solo sirve como una herramienta operativa para gestionar el trabajo diario, sino también como una fuente de información para entender cómo se está distribuyendo la carga entre las personas del equipo y detectar a tiempo posibles situaciones de sobrecarga.

---

## 2. Problema que busca resolver

En diferentes entornos laborales, las solicitudes de trabajo pueden llegar por medios dispersos o de manera informal, dificultando conocer qué trabajo debe realizarse, quién es responsable, cuál es su prioridad, qué actividades están pendientes y qué capacidad tiene disponible cada operario.

La falta de información sobre los tiempos estimados y los tiempos reales de ejecución también limita la capacidad de analizar la distribución del trabajo y detectar situaciones de sobrecarga. El sistema busca centralizar esta información y proporcionar una visión tanto operativa como analítica.

---

## 3. Propósito del sistema

El sistema tendrá dos frentes principales: Gestión y Análisis. La gestión permitirá administrar proyectos, actividades, responsables, prioridades y ejecución. El análisis utilizará los datos generados durante la operación para conocer tiempos, ocupación y carga laboral actual y futura.

---

## 4. Usuarios del sistema

- **Superadmin:** rol técnico/operativo del sistema, no pertenece a ninguna empresa específica. Es responsable de dar de alta nuevas empresas en el sistema y crear el primer usuario Administrador de cada una. También define, para cada empresa, su logo (marca blanca) y la cantidad máxima de Administradores y de Operarios que puede tener. No participa en la gestión diaria de proyectos, actividades ni ejecución.
- **Administrador** (antes "Supervisor"): administra y da seguimiento a los proyectos y actividades del área, asigna responsables, establece prioridades y consulta la carga laboral del personal. Además, define los turnos de la empresa y asigna uno a cada operario, valida o corrige la asistencia diaria y reasigna actividades cuando un operario falta.
- **Operario** (antes "Empleado"): consulta sus actividades, conoce la información necesaria para ejecutarlas, registra su ejecución y puede reportar actividades solicitadas por otras áreas para conocimiento y gestión del administrador. Además, marca su entrada y salida de cada jornada.

---

## 5. Alcance funcional inicial

### 5.1 Gestión
- Registro y administración de empresas.
- Registro de empresas y creación del primer usuario Administrador de cada una, a cargo del Superadmin.
- Registro y administración de usuarios con perfiles de Administrador y Operario, dentro de su respectiva empresa.
- Límite de usuarios por empresa: el Superadmin define un máximo de Administradores y otro de Operarios. El sistema impide crear usuarios por encima del límite y reducir un límite por debajo de los usuarios que la empresa ya tiene.
- Marca blanca: el Superadmin puede cargar el logo de cada empresa (PNG, JPG o WEBP, máximo 512 KB). Los usuarios de esa empresa ven su logo y su nombre en la interfaz en lugar de la marca GestLab. La pantalla de inicio de sesión conserva la marca GestLab, porque antes de ingresar el sistema no sabe a qué empresa pertenece el usuario.
- Zona horaria: cada empresa tiene una zona horaria, que define el Superadmin (por defecto, `America/Bogota`). Con ella el servidor decide a qué día pertenece cada evento y cuándo termina la jornada.
- Organización del trabajo en actividades y proyectos. Una actividad es independiente o pertenece a un solo proyecto, nunca a los dos. Lo que antes se llamaba requerimiento es una actividad independiente.
- Proyectos: un proyecto es un conjunto de actividades. Solo el Administrador lo crea, lo planifica de entrada y le puede agregar actividades después. Las actividades de un proyecto y las independientes suman por igual a la carga y a los indicadores. El avance de un proyecto se mide en horas: horas estimadas de sus actividades finalizadas sobre horas estimadas totales del proyecto. Las actividades canceladas salen del total; las no realizadas se quedan en él.
- Creación y asignación de actividades a uno o varios operarios. La asignación es manual: el sistema solo sugiere reasignar cuando la carga de un operario supera la capacidad de su jornada.
- Información de la actividad: el Administrador elige qué bloques lleva cada actividad (pasos, herramientas y materiales, equipo, adjuntos, contacto). Los catálogos de esos bloques son listas desplegables con la opción "Otro", que se van llenando con lo que se registra. La actividad muestra "Lista para iniciar" cuando tiene todos los bloques que se le pidieron.
- Clasificación de actividades por categoría. Las categorías son fijas en esta versión: Producción, Mantenimiento, Calidad, Limpieza y Logística.
- Cada actividad recibe un código consecutivo por empresa (por ejemplo, `OT-0042`) y registra la ubicación donde se realiza (línea, máquina o área).
- Definición de prioridad de las actividades en cuatro niveles: Baja, Media, Alta y Urgente. El nivel Urgente indica que la actividad debe interrumpir la tarea que el operario tenga en curso. La excepción es una actividad de hora fija en curso, que no se interrumpe: el Operario ve el aviso de la urgente y la atiende al terminar, y mientras tanto el Administrador puede asignarla a otra persona.
- Definición de tiempo estimado de ejecución. El tiempo estimado corresponde a la actividad completa: si la actividad tiene varios operarios, no se reparte entre ellos (cada uno la suma completa a su carga).
- Definición de una fecha programada para cada actividad, que determina la jornada a la que pertenece. Además, cada actividad es de **hora fija** o de **horario flexible**. Con hora fija, el Administrador le pone una hora y esa hora no se mueve. Con horario flexible, queda asignada al día y el Operario decide en qué momento hacerla. La hora no cambia el cálculo de la carga, que sigue siendo por jornada.
- Una actividad no se puede programar ni mover a un día que ya pasó. El día de referencia es el de la empresa, según su zona horaria.
- Actividades sin operario: las que nunca se asignaron o fueron devueltas quedan marcadas como "Sin asignar", y el Administrador las puede consultar aparte para atenderlas.
- Orden del día del Operario: el sistema sugiere un orden inicial por prioridad y luego por hora. El Operario puede reordenar solo las actividades de horario flexible. Las de hora fija y las urgentes no se mueven; las urgentes van siempre arriba.
- Programación dinámica del día: la estimación y la ejecución son cosas distintas. El tiempo estimado sirve para planear; lo ejecutado se mide con sus horas reales de inicio y fin. Por eso la programación del día de cada operario se recalcula continuamente: lo terminado ocupa el tiempo que realmente tomó; lo que está en curso va desde su inicio real hasta un fin proyectado (lo que le falta del estimado); y lo pendiente se reacomoda a partir de ese momento. Si una actividad termina antes, las siguientes se adelantan; si se demora, se corren. Las de hora fija no se mueven. El orden que el Operario eligió se conserva.
- Hora fija que interrumpe: si el orden elegido no alcanza a terminar antes de una actividad de hora fija, el sistema lo avisa pero lo permite. Diez minutos antes de la hora fija el sistema avisa. Al llegar la hora, el Operario pausa la actividad que lleva, inicia la de hora fija y después retoma la otra. Esa pausa queda registrada con el motivo "Actividad de hora fija".
- Una actividad de hora fija se hace en su hora: una vez iniciada no se puede pausar, y no se reprograma para otro día.
- Consulta del estado y asignación de las actividades.
- Posibilidad de que un operario registre una actividad solicitada por otra área y la socialice con su administrador.
- Gestión de la ejecución de actividades, incluyendo inicio, pausa, reanudación y finalización. La ejecución pertenece a cada operario asignado: cada uno tiene su propio registro de tiempo, sus pausas y su observación final, así que la pausa de uno no pausa a los demás.
- Una actividad con varios operarios queda finalizada cuando todos los asignados la finalizan. Mientras tanto se muestra cuántos han finalizado (por ejemplo, "1 de 2 finalizaron"), y al operario que ya terminó le aparece como hecha en su día.
- Motivos de pausa: una lista desplegable por empresa. Trae cuatro motivos fijos (Actividad urgente, Actividad de hora fija, Fin de jornada y Otro) y se va llenando con lo que se escribe en "Otro".
- Fin de la jornada: el Operario debe pausar lo que no alcance a terminar. Si no lo hace, al terminar el día el sistema pausa la actividad con el motivo "Fin de jornada", para no dañar el tiempo real, y la reprograma para el día siguiente. Mientras no existan los turnos, la jornada termina con el día, en la zona horaria de la empresa.
- Registro automático de los tiempos asociados a la ejecución.
- Consideración de cambios de prioridad durante la jornada y posibilidad de interrumpir temporalmente una actividad para atender otra de mayor prioridad, conservando el historial de ejecución.
- Cada operario puede tener una sola actividad en ejecución a la vez. Para iniciar otra, debe pausar (registrando el motivo) o finalizar la actual de forma manual; el sistema bloquea el inicio de una segunda actividad mientras exista una en curso.

**Pendientes, cancelación y devolución**
- Reprogramación automática: una actividad de horario flexible que no se hizo, o que se empezó y no se terminó, pasa sola a la siguiente jornada y queda marcada como reprogramada, con sus días de retraso. Si tiene varios operarios, se reprograma para todos los asignados, porque la actividad tiene una sola fecha. Mientras no existan los turnos, la siguiente jornada es el día siguiente del calendario, incluidos sábados y domingos. El Administrador puede reasignarla, cambiarle el día o cancelarla; si le cambia el día, conserva la marca y su fecha original, porque el retraso ya ocurrió.
- No realizada: una actividad de hora fija que no se hizo, o que no se terminó en su día, queda en estado No realizada, que es definitivo. No se cancela ni se reasigna; si el trabajo sigue haciendo falta, el Administrador crea una actividad nueva. El tiempo que se haya trabajado en ella queda registrado.
- Cancelar: solo el Administrador puede cancelar una actividad, y solo si está sin iniciar o pausada; mientras alguien la tenga en curso no se puede. Indica el motivo en una lista desplegable por empresa, que empieza solo con "Otro" y se va llenando con lo que se escribe. La actividad cancelada no se borra; queda en el historial con su motivo, quién la canceló y cuándo. Las actividades ya no se eliminan: cancelar reemplaza al borrado.
- Devolver una actividad: el Operario puede devolver una actividad solo antes de iniciarla, indicando el motivo (Falta información, Me la asignaron por error, Falta herramienta o material, El equipo no está disponible, u Otro con texto). Si la actividad tiene varios operarios, solo sale el que la devuelve; si no queda ninguno, vuelve al Administrador.

**Turnos y asistencia**
- Definición, por parte de cada empresa, de un catálogo de turnos. Cada turno tiene un identificador, nombre, hora de inicio, hora de fin y tiempo de descanso.
- Asignación de un único turno a cada operario. Cuando se cambia el turno de un operario, el sistema conserva la fecha del cambio, para que los indicadores de periodos anteriores se calculen con el turno vigente en ese momento.
- Una jornada pertenece al día en que inicia el turno, aunque el turno termine después de la medianoche.
- El turno no limita el trabajo: el operario puede ejecutar actividades fuera de su turno, y ese tiempo se registra como tiempo adicional.
- Registro de asistencia: el operario marca su entrada y su salida de cada jornada (la hora la registra el servidor), y el Administrador valida o corrige cada marca.
- Aviso de posible ausencia: si pasado un tiempo de tolerancia desde el inicio del turno (configurable por empresa) el operario no ha marcado entrada, el Administrador recibe un aviso con las actividades programadas de ese operario para la jornada.
- Ante una ausencia confirmada, el Administrador reasigna manualmente las actividades a otros operarios.
- Las actividades que no se reasignen siguen la misma regla de las pendientes: las que no tienen hora pasan a la siguiente jornada del operario como actividades reprogramadas, y las de hora fija quedan como No realizadas. La reprogramación queda registrada como un evento (con la jornada de origen), y si la jornada de destino supera el 100 % de la capacidad del operario, el Administrador recibe un aviso.

### 5.2 Análisis
- Comparación entre tiempo estimado y tiempo real de ejecución. El tiempo real de una actividad es la suma del tiempo de cada operario, sin sus pausas, y se compara contra el estimado contado una vez por operario, igual que en la carga.
- Análisis de la carga laboral de los operarios.
- Visualización de la ocupación actual.
- Proyección de la ocupación futura a partir de las actividades programadas.
- Identificación de posibles situaciones de sobrecarga.
- Capacidad de cada operario por jornada, calculada a partir de su turno: duración del turno menos el tiempo de descanso. Mientras no existan los turnos (criterio 7 del MVP), se usa una capacidad provisional de 7 horas para todos los operarios.
- Tiempo disponible de la jornada: capacidad menos el tiempo real ya trabajado y menos el tiempo que falta de lo pendiente (el estimado de lo que no ha empezado y lo que resta de lo que está en curso o pausado). La carga, en cambio, es un dato de planeación y se calcula solo con estimados.
- Cálculo de la carga por jornada: suma de los tiempos estimados de las actividades asignadas al operario y programadas para esa jornada. Las canceladas no suman; las no realizadas sí, porque ocuparon su lugar en el día.
- Alerta en pantalla al momento de asignar una actividad, cuando la carga del operario para la jornada programada de esa actividad supere el 100% de su capacidad.
- Análisis de la distribución de actividades por categoría.
- Consulta de información histórica generada por la ejecución de actividades.

**Indicadores de jornada y cumplimiento**
- Por cada jornada se registran: tiempo programado (turno menos descanso), tiempo presente (entre las marcas de entrada y salida validadas), tiempo en actividades (ejecución real sin pausas) y tiempo adicional (trabajo fuera del turno).
- **Cumplimiento de jornada:** tiempo en actividades dividido entre tiempo programado.
- **Aprovechamiento:** tiempo en actividades dividido entre tiempo presente.
- **Tiempo adicional:** se muestra como dato propio; no se clasifica como hora extra ni se calcula su valor (ver Sección 9).
- **Cumplimiento de actividades:** una actividad se considera cumplida si se finaliza en su jornada programada. Las no realizadas cuentan como incumplidas y las reprogramadas, como retraso. Las canceladas no cuentan como cumplidas ni como incumplidas, y dejan de sumar a la carga del operario.
- **Precisión de estimación:** comparación entre tiempo estimado y tiempo real de ejecución (se mantiene como indicador separado del cumplimiento).

**Indicadores de pendientes, cancelaciones y devoluciones**
- **Actividades reprogramadas:** cuántas hay y cuántos días lleva cada una desde su fecha original.
- **No realizadas:** cuántas actividades de hora fija no se hicieron.
- **Canceladas:** cuántas, agrupadas por motivo.
- **Devoluciones:** cuántas, agrupadas por motivo.

- Todos los indicadores se consultan por operario, por proyecto, por categoría de actividad y para la empresa. Los valores agregados se calculan sumando los tiempos de todos los involucrados y dividiendo al final, no promediando porcentajes individuales.

---

## 6. Experiencia de uso

La aplicación será web y tendrá un diseño responsive. La interfaz para administradores estará orientada principalmente a la gestión y análisis, mientras que la experiencia del operario dará especial importancia al uso desde dispositivos móviles, debido a que la ejecución de actividades requiere iniciar, pausar, reanudar y finalizar tareas durante la jornada laboral.

### 6.1 Persona y decisiones de diseño de interfaz — Operario (Diseño de Interfaces)

Como parte del trabajo de Diseño de Interfaces, se construyó una ficha de usuario y un mapa de empatía para el rol Operario, y se definió la primera propuesta de wireframes de baja fidelidad para la interfaz web responsive de ese rol. Estos insumos no cambian el alcance funcional ya definido en la Sección 5, pero sí deben orientar cómo se prioriza y se presenta esa funcionalidad en la interfaz.

**Persona de referencia:** Carlos Andrés Ramírez, 34 años, operario de línea de producción, técnico en electrónica, turno rotativo. Usa únicamente celular durante su jornada.

**Perfil ampliado de los usuarios:** Carlos es la persona de referencia, pero no representa a todos los usuarios. Quienes usan GestLab son diversos: personas jóvenes y mayores, de todo género y con distintos niveles de familiaridad con la tecnología, en roles técnicos y administrativos. Además, la herramienta se usa durante gran parte de la jornada (el Operario la consulta en cada cambio de actividad y el Administrador trabaja en ella de forma continua). De este perfil se derivan cuatro exigencias de diseño que aplican a todas las vistas:
- **Legibilidad para vista cansada o envejecida:** alto contraste entre texto y fondo (ver 6.3) y tamaños de texto y controles generosos.
- **Bajo cansancio visual en uso prolongado:** fondo general sin blanco puro (las tarjetas, tablas y diálogos sí son blancos y se leen sobre ese fondo), texto sin negro puro y color intenso solo donde hay algo que atender.
- **Información que no depende solo del color:** todo estado o aviso se comunica con color, ícono y texto, por accesibilidad (daltonismo) y por la menor capacidad de distinguir tonos con la edad.
- **Interfaz amable y profesional para un público amplio:** sin estereotipos de género en el color y con un tono cercano (por ejemplo, saludo con el nombre del usuario), sin perder la seriedad de una herramienta de trabajo.

**Hallazgo central del mapa de empatía:** Carlos no necesita más control sobre su trabajo — necesita **evidencia y contexto**: poder demostrar lo que hizo (hoy depende solo de su palabra) y no perder el hilo cuando una tarea se interrumpe por otra más urgente.

**Necesidades identificadas que la interfaz debe resolver explícitamente:**
- Ver su día ordenado, sin tener que preguntar: lo fijo en su hora y lo demás en el orden que él elija, partiendo de uno sugerido por prioridad.
- Notar visualmente cuándo una prioridad cambió durante el turno.
- Registrar inicio/pausa/reanudación/finalización de una actividad de forma rápida.
- Ver el historial de pausas de la actividad en curso (para no perder contexto al retomarla).
- Dejar una constancia (observación) al finalizar una actividad, no solo cerrarla.
- Registrar un motivo/causa al pausar una actividad, no solo el hecho de que se pausó.
- Reportar una actividad solicitada por otra área sin que "quede en el aire".
- Ver un aviso claro y visible en la pantalla Hoy cuando tiene una actividad de prioridad Urgente pendiente, para que pueda pausar la actividad en curso y atenderla.
- Saber en todo momento si está dentro o fuera de su turno, mediante un indicador visible que combine color, ícono y texto (por ejemplo, "En turno" / "Fuera de turno: tiempo adicional"), sin depender solo del color.
- Marcar su entrada y su salida de la jornada desde el celular.
- Devolver una actividad que le llegó incompleta o mal asignada, antes de iniciarla, diciendo por qué.
- Saber qué actividades vienen de días anteriores.

**Pantallas mínimas definidas para el flujo del Operario (sitio web responsive, vista móvil):**
1. Bienvenida + Inicio de sesión (unificadas — el Operario no se autoregistra, según Sección 4)
2. Hoy (su día ordenado y acceso a reportar una actividad externa). La actividad en curso se ejecuta en su lugar del día, con cronómetro, control de estado, historial de pausas y observación final; ya no hay una pantalla aparte de ejecución.
3. Detalle de actividad (información completa antes de iniciar una tarea; desde aquí se inicia o se devuelve)

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
| Administrador | Computador (también usable en celular) | **Equipo** (el tablero del turno: una fila por persona y las horas de izquierda a derecha, con lo que está por atender; el Administrador reasigna una actividad moviendo su tarjeta a la fila de otra persona, sin cambiarle la hora) · **Actividades** (todas, independientes o de un proyecto) · **Proyectos** (lista y detalle, con su avance en horas) · **Usuarios**. Pendientes: Turnos y asistencia · Indicadores |
| Operario | Celular | **Hoy** (su fila del tablero en vertical: el día sobre una línea de tiempo, con la actividad en curso abierta en su hora) · **Semana** (horario por día, semana o lista) · **Resumen** (carga de la semana e indicadores propios). Pendiente: marca de entrada y salida |

Las vistas se habilitan a medida que se construye cada pantalla; nunca se muestran enlaces a pantallas que aún no existen.

**Varias vistas de la misma información.** Las actividades se pueden ver de tres maneras, y cada una responde una pregunta distinta: como **día** (qué sigue y a qué hora, en la línea de tiempo de Hoy), como **horario** (cuándo y cuánto ocupa) y como **resumen** (cuánto trabajo hay). El detalle de una actividad se abre en una ventana sobre la vista en la que se esté, sin cambiar de pantalla.

**Decisiones de diseño comunes a todas las vistas:**
- **Marco común:** barra superior con la marca, las vistas del rol como pestañas y, a la derecha, el avatar del usuario con su nombre, su rol y el botón de cerrar sesión. En celular las vistas pasan a una barra fija en la parte inferior, al alcance del pulgar. Reemplaza el menú lateral de la primera versión.
- **Primero la información:** cada pantalla muestra primero su lista o tabla. Crear o editar es una acción secundaria: un botón ("+ Nueva empresa", "+ Nuevo usuario") abre el formulario en una ventana (diálogo). Al guardar, la ventana se cierra y aparece una confirmación breve.
- **Estados vacíos y límites explicados:** cuando no hay datos, la pantalla explica qué hacer y ofrece el botón para hacerlo. Cuando una acción no está disponible (por ejemplo, se alcanzó el límite de usuarios), el botón se desactiva y un aviso explica por qué.
- **Paleta sobria con significado:** fondos casi neutros, un color principal para las acciones y un acento de marca (coral) reservado para el logo, el avatar y la sobrecarga. Los colores fuertes se reservan para lo que tiene significado (prioridades, estados, avisos) y siempre van acompañados de ícono y texto. El sistema de color completo se define en la Sección 6.3.
- **Tipografía legible:** Figtree para todo lo que se lee, incluidas las cifras y el cronómetro (con números de ancho fijo), y Atkinson Hyperlegible Mono solo para los códigos de actividad y el NIT. Los tamaños dependen del dispositivo y se expresan en rem. El sistema tipográfico completo se define en la Sección 6.4.

**Sistema de composición** (para que la interfaz transmita calma y orden; aplica a todas las pantallas):
- **Una sola escala de espacios:** todo relleno y toda separación sale de siete pasos (4, 8, 12, 16, 24, 32 y 48 px sobre la base de 16 px; en la interfaz se expresan en rem). No se usan valores sueltos.
- **Una sola columna alineada:** la barra superior y el contenido comparten el mismo borde izquierdo y derecho. El ancho de la columna depende de lo que se muestra (angosto para leer una lista, medio para fichas y listados, amplio para horarios), nunca del ancho de la pantalla.
- **Dos pesos de letra:** 600 para lo que identifica (título de la pantalla, nombre de la empresa o de la persona, acción) y 400 para todo lo demás. Los encabezados de tabla y las etiquetas de dato van en 400 y en el color de texto secundario.
- **Una familia de letra por fila:** las cifras usan la misma fuente del texto; la fuente monoespaciada se reserva para los códigos de actividad y el NIT.
- **Bordes suaves y sombras muy suaves:** los paneles se separan del fondo por el contraste de color, un borde tenue y una sombra apenas visible. Los controles (campos y botones secundarios) llevan un borde más marcado, con contraste de al menos 3:1.
- **Filas de la misma altura:** en una lista, todas las filas miden lo mismo, tengan o no logo, límite o datos opcionales.
- **Un solo botón principal por pantalla;** las demás acciones son secundarias.
- **El color solo donde significa algo:** el estado normal no lleva color. Una advertencia se dice con un ícono y una frase, sin franjas de color que ocupen todo el ancho ni franjas de color a la izquierda de las tarjetas. El aviso de actividad Urgente (Sección 6.3) es un bloque acotado dentro de la columna, no una franja.

**Relación con los principios de usabilidad (6.1) y las heurísticas de Nielsen:**
- Pocas opciones de menú por rol (Ley de Hick) y patrón de pestañas arriba y barra inferior en celular, habitual en aplicaciones web y móviles (Ley de Jakob).
- Confirmación después de guardar y botones desactivados mientras se procesa (Nielsen 1: visibilidad del estado del sistema).
- "Cancelar", la tecla Esc y la "X" en todos los diálogos (Nielsen 3: control y libertad del usuario).
- Validación antes de enviar y acciones deshabilitadas cuando no son posibles (Nielsen 5: prevención de errores).
- Mensajes de error en lenguaje claro dentro del mismo formulario (Nielsen 9: ayudar a reconocer y corregir errores).

**Leyes de Gestalt aplicadas** (requerimiento 2 de la Fase 2; las del tablero y la línea de tiempo se evidenciarán cuando se construyan esas pantallas):
- **Proximidad:** cada etiqueta va pegada a su campo y separada del siguiente; los dos límites de usuarios forman un grupo bajo un mismo título; "Cancelar" y la acción principal van juntos al pie del diálogo; el avatar, el nombre del usuario, su rol y el botón de cerrar sesión forman un bloque en la barra superior; en el tablero, cada persona tiene su fila y sus actividades quedan dentro de ella. Resuelve la duda de qué dato pertenece a qué control.
- **Semejanza:** todos los botones de acción principal comparten relleno y forma, los secundarios comparten borde, las etiquetas de rol y de prioridad comparten la forma de píldora y todos los enlaces comparten color. El usuario aprende un elemento una vez y lo reconoce en las demás pantallas.
- **Continuidad:** el tablero del Administrador, de izquierda a derecha, y la línea de tiempo del Operario, de arriba abajo, siguen el paso de las horas; las tablas alinean cada dato en su columna para recorrerlo de arriba abajo; los formularios tienen una sola columna que termina en el botón de acción; las migas de pan ("Empresas / Metalicas SAS") muestran el camino recorrido.
- **Figura y fondo:** los paneles blancos se separan del fondo gris neutro; al abrir un diálogo o el menú en celular, el resto de la pantalla se oscurece para que solo quede en primer plano lo que se está atendiendo.
- **Cierre:** la línea de tiempo del Operario se lee como una sola línea continua aunque esté punteado después de "Ahora". Una actividad partida por una hora fija se muestra como "Parte 1" y "Parte 2" y se percibe como una sola actividad.


### 6.3 Identidad visual: sistema de color "Calma operativa" (Diseño de Interfaces)

Esta subsección define la propuesta cromática del producto, exigida en la Fase 2 del Proyecto Integrador de Diseño de Interfaces. Reemplaza la paleta inicial de la interfaz (acento verde azulado `#0f766e` en `estilos.css`). El color se eligió por su función y por el contexto de uso, no por gusto estético: cada color tiene un único significado y ese significado es el mismo en todas las pantallas de los tres roles.

**Fundamentos de la propuesta:**
- **Estudios de color y trabajo.** En el estudio de Nancy Kwallek (Universidad de Texas), las personas cometieron más errores en una oficina blanca que en una de color, y el espacio aqua (verde azulado) resultó el más agradable y productivo; las personas sensibles al entorno se sintieron abrumadas en espacios de colores intensos. Mehta y Zhu (Universidad de British Columbia, *Science*, 2009) mostraron que el rojo induce una motivación de alerta y evitación que mejora las tareas que exigen atención al detalle, mientras que el azul favorece la calma. De aquí salen tres decisiones: fondo general de color suave en lugar de una pantalla toda blanca, color principal aqua profundo y rojo reservado para lo que exige atención inmediata. Estos estudios se usan como respaldo, no como verdad absoluta: sus efectos varían según la persona.
- **Normas de color de la industria.** Los significados de los colores de estado siguen la norma ISO 3864 (rojo: peligro o prohibición; amarillo: precaución; verde: condición segura; azul: indicación u obligación), que los operarios ya conocen por la señalización de planta. La escala de prioridades sigue la jerarquía de riesgo de ANSI Z535 (amarillo para precaución, naranja para advertencia, rojo para peligro). Lo que está en estado normal va en gris, según el principio de la norma ISA-101 para interfaces de operación industrial: el color se reserva para lo que requiere acción.
- **Visión de personas mayores.** Con la edad, el cristalino se vuelve amarillento, el azul se percibe más oscuro y cuesta distinguir azules de verdes. Por eso se usan colores de saturación media, el azul no se usa en texto pequeño y el verde de "finalizada" se inclina hacia el amarillo para separarse del aqua principal.
- **Contraste (WCAG 2.1).** Todo texto cumple al menos 4,5:1 contra su fondo y los componentes de interfaz al menos 3:1. Los textos principales superan 7:1 (nivel AAA).

**Teoría del color aplicada:**
- **Armonía complementaria:** el aqua principal (tono 190°) y el coral de marca (tono 9°) están separados 181° en la rueda de color. Siguiendo lo visto en clase, esta armonía se usa para destacar: el coral ocupa muy poca superficie: marca la identidad y, rayado, la sobrecarga.
- **Jerarquía por saturación y luminosidad:** el fondo es casi neutro (10 % de saturación, 96 % de luminosidad), el principal es firme (69 % de saturación, 28 % de luminosidad) y los estados intensos aparecen solo cuando hay algo que atender.
- **Proporción 60-30-10:** alrededor de 60 % de fondo y superficies, 30 % de texto y color principal, y 10 % de acento de marca y colores de estado.

**Base e identidad:**

| Rol | HEX | Uso | Contraste |
|---|---|---|---|
| Fondo | `#F4F6F5` | Fondo general de todas las pantallas (gris neutro; evita la pantalla toda blanca) | — |
| Superficie | `#FFFFFF` | Tarjetas, tablas, diálogos (separa figura y fondo) | — |
| Principal | `#16697A` | Botones de acción principal, enlace activo, foco, actividad en curso, la línea "Ahora" y el tramo ya recorrido de la línea de tiempo | Texto blanco sobre principal 6,3:1; principal sobre el fondo 5,8:1 |
| Principal (hover/presionado) | `#0F5563` | Estado del botón principal al pasar el cursor o presionar | 7,1:1 sobre su fondo suave |
| Principal suave | `#E0EFF0` | Fondo de la etiqueta "En curso" y de elementos seleccionados | — |
| Acento de marca (coral) | `#E9806E` | Logo, avatar del usuario y sobrecarga (lo programado después de la hora de fin del turno, con un rayado). Nunca en texto | No se usa para texto |
| Texto principal | `#1F2A2E` | Títulos y texto (sin negro puro) | 14,7:1 sobre blanco |
| Texto secundario | `#5B6664` | Textos de apoyo, metadatos | 5,95:1 sobre blanco y 5,48:1 sobre el fondo |

**Colores de estado** (cada uno con tres variantes: base para rellenos y bordes, fondo suave para etiquetas y avisos, y texto oscuro para escribir sobre ese fondo):

| Significado | Base | Fondo suave | Texto sobre fondo | Ícono | Norma | Contraste texto/fondo |
|---|---|---|---|---|---|---|
| Error, prioridad Urgente | `#A8322A` | `#FBE9E7` | `#8A2620` | ⚠ | ISO 3864 (peligro, prohibición) | 7,5:1 |
| Prioridad Alta | `#B34F0B` | `#FDEBDD` | `#8A3D08` | ▲ | ANSI Z535 (advertencia) | 6,6:1 |
| Advertencia, prioridad Media, actividad pausada, cambio de prioridad | `#E3A32B` | `#FBF1D9` | `#6B4A0E` | ! / ❚❚ / ↑ | ISO 3864 (precaución) | 7,2:1 |
| Confirmación, actividad finalizada, en turno | `#3E7B3A` | `#E6F0E2` | `#2F5F2C` | ✓ / ● | ISO 3864 (condición segura) | 6,4:1 |
| Información | `#2F5DA8` | `#E6EDF8` | `#24498A` | i | ISO 3864 (azul, indicación) | 7,5:1 |
| Normal: prioridad Baja, actividad por iniciar, fuera de turno (el fondo suave solo se usa en "Fuera de turno") | `#6B7478` | `#ECEFEF` | `#5B6664` | • / ○ | ISA-101 (lo normal en gris) | 5,15:1 (sin fondo, 5,95:1 sobre blanco) |

**Asignación por elemento de la interfaz:**
- **Prioridades:** Urgente (bloque o etiqueta rojo lleno con texto blanco), Alta (fondo naranja suave con su texto oscuro), Media (fondo ámbar suave con su texto oscuro), Baja (texto gris, sin fondo). Solo lo urgente usa un bloque lleno. La intensidad del color crece con la urgencia y la etiqueta siempre muestra el nombre del nivel.
- **Estados de actividad:** Sin asignar y Por iniciar (texto gris con su ícono, sin fondo, porque son lo normal), En curso (fondo principal suave), Pausada (ámbar suave), Finalizada (verde suave).
- **Estados nuevos** (colores provisionales, pendientes de validar con las pantallas construidas): Reprogramada (ámbar suave, con el texto "Retraso: 1 día" o los días que lleva), Devuelta (ámbar suave: espera una decisión del Administrador), No realizada (rojo suave con su texto oscuro: cuenta como incumplida), Cancelada (texto gris, sin fondo).
- **Jornada:** En turno (verde con punto ●), Fuera de turno (fondo gris suave con texto que lo indica). Lo programado después de la hora de fin del turno se marca con el rayado coral de sobrecarga. La alerta de carga por encima del 100 % de la capacidad (Sección 5.2) es una señal distinta: va en texto, con ícono de advertencia, junto a las horas de la persona, porque con el descanso se puede superar la capacidad sin pasar de la hora de salida.
- **Errores:** el error de formulario y la prioridad Urgente comparten el rojo porque significan lo mismo, "algo requiere tu atención", y se diferencian por la forma: el error de formulario es un borde rojo en el campo con el mensaje debajo; la alerta de Urgente pendiente es un bloque rojo lleno con ícono ⚠ y texto.
- **Información:** avisos que no exigen acción (por ejemplo, la hora de fin de turno), siempre como fondo suave con el ícono "i", nunca como botón lleno, para no confundirse con una acción.

**Reglas obligatorias del sistema de color:**
1. Todo estado, prioridad o aviso se comunica con **color, ícono y texto**; nunca solo con color.
2. Cada color tiene **un solo significado** en todo el producto.
3. El **color intenso** (bloques llenos) se reserva para lo que exige atención inmediata; lo normal se muestra en gris.
4. El **coral de marca** nunca se usa en texto, etiquetas de estado ni botones de acción. Fuera de la identidad tiene un solo uso: marcar la sobrecarga, es decir, lo programado después de la hora de fin del turno. Ahí va siempre rayado y con su texto, nunca como relleno liso.
5. El **azul de información** nunca se usa en texto pequeño ni como relleno de botón.
6. Todos los colores se definen como **variables CSS** en un único lugar (`:root` de `estilos.css`) para garantizar la consistencia entre pantallas.
7. El **ámbar base** (`#E3A32B`) es un color claro y tiene dos restricciones: sobre blanco solo alcanza 2,2:1, así que nunca se usa como borde, ícono o texto sobre superficies claras (para eso se usa su texto oscuro `#6B4A0E`, 8,0:1 sobre blanco); y como relleno lleva siempre texto principal oscuro `#1F2A2E` (6,7:1), nunca blanco. Los demás colores base admiten texto blanco como relleno (rojo 6,7:1; naranja 5,2:1; verde 5,1:1; gris 4,8:1).
8. Ningún **gris de texto** es más claro que `#66716E` (5,06:1 sobre blanco y 4,66:1 sobre el fondo). El `#8A9592` queda prohibido para texto: solo alcanza 3,09:1.

**Precisiones de la implementación** (valores que el sistema necesitaba y que las tablas anteriores no definían):
- **Bordes:** el borde de paneles y tablas es decorativo y tenue (`#E1E5E3`, gris neutro como el fondo). El borde de los controles (campos de formulario y botones secundarios) es `#7F8A87`: 3,57:1 sobre blanco y 3,29:1 sobre el fondo.
- **Sombra:** los paneles y tarjetas llevan una sombra muy suave (1 px de desplazamiento, 2 px de difuminado, texto principal al 6 % de opacidad). Los diálogos y avisos flotantes usan una más amplia (16 px y 40 px, al 18 %) para separarse de lo que tienen detrás.
- **Rayado de sobrecarga:** franjas diagonales de coral `#E9806E` sobre un fondo coral suave `#FBE5E0`. El texto que va encima es el principal `#1F2A2E` (12,2:1 sobre el fondo suave).
- **Logo:** un cuadro redondeado en principal suave `#E0EFF0`, con tres barras horizontales escalonadas en principal `#16697A`, como las tarjetas del tablero del turno, y una barra vertical coral `#E9806E` que representa la línea "Ahora". El dibujo está en un solo archivo (`app/static/favicon.svg`) y se usa en la pestaña del navegador, en la barra superior y en el inicio de sesión. Una empresa sin logo propio muestra este logo junto a su nombre.
- **Texto sobre el coral de marca:** la inicial del logo y del avatar se escribe con el texto principal `#1F2A2E` (5,4:1). El coral sigue sin usarse como color de texto.
- **Ícono de "En curso":** ▶, sobre el fondo principal suave con texto `#0F5563`.
- **Tarjetas sin borde lateral de color:** la prioridad de una actividad se indica solo con su etiqueta (color, ícono y texto).
- **Etiquetas de rol** (Administrador, Operario): van en gris neutro, porque el rol no es un estado ni una prioridad y no debe tomar un color con significado.

**Conflictos identificados y cómo se resuelven:**
- **Coral de marca (9°) frente a rojo de Urgente (4°) y naranja de Alta (25°):** son tonos cálidos cercanos. Se separan por luminosidad (el coral es claro y rosado, el rojo y el naranja son oscuros), por uso (el coral nunca aparece en etiquetas de estado) y porque las prioridades siempre llevan su texto.
- **Coral en la identidad y en la sobrecarga:** se distinguen por la forma. En el logo y el avatar es un relleno liso; en la sobrecarga es un rayado con texto.
- **Aqua principal (190°) frente a azul de información (217°) y verde de finalizada (116°):** se separan por tono, por forma de uso (el principal es relleno de botón; información y finalizada son fondos suaves) y por el ícono que acompaña a cada estado.
- **Ámbar compartido** entre advertencia, prioridad Media, pausada y cambio de prioridad: comparten el significado de "precaución, atención no urgente"; el ícono y el texto indican de cuál se trata.

**Paleta de categorías (solo para el horario).** Los bloques del horario pueden colorearse de dos maneras, a elección del usuario: por **prioridad** (los colores de estado de esta sección; es el modo por defecto) o por **categoría**. La paleta de categorías es un conjunto aparte, de tonos que no coinciden con ningún color de estado, y se usa únicamente en los bloques del horario y en el ícono de la etiqueta de categoría:

| Categoría | Color | Fondo del bloque | Ícono |
|---|---|---|---|
| Producción | `#5B4B9A` | `#E8E3F4` | Fábrica |
| Mantenimiento | `#7A5038` | `#EFE4DB` | Llave |
| Calidad | `#A33D72` | `#F6E1EC` | Lista de verificación |
| Limpieza | `#5C6B24` | `#E9EDD3` | Destellos |
| Logística | `#3D5A6C` | `#DFE8EC` | Camión |

El texto de los bloques es siempre el texto principal `#1F2A2E` (al menos 11,7:1 sobre cada fondo) y cada color supera 5,8:1 sobre blanco. Las reglas 1 y 2 se mantienen: la categoría siempre lleva ícono y nombre, la prioridad sigue visible por su ícono dentro del bloque, y una actividad Urgente conserva un borde rojo completo, alrededor de todo el bloque y no solo a un lado, también en el modo categoría.

**Íconos.** Los íconos de prioridad, estado, categoría y navegación son de la colección Lucide (trazo uniforme, licencia ISC) y reemplazan los símbolos de texto de la tabla de estados: Urgente (triángulo de alerta), Alta (flecha hacia arriba), Media (círculo de alerta), Baja (guion), En curso (reproducir), Finalizada (visto bueno), Por iniciar (círculo).

**Relación con la marca blanca (Sección 4):** cuando una empresa carga su logo, este reemplaza la marca GestLab, pero el sistema de color no cambia. Los colores de estado deben significar lo mismo en todas las empresas para no perder la consistencia ni la accesibilidad.


### 6.4 Tipografía (Diseño de Interfaces)

Esta subsección define el sistema tipográfico del producto como parte de la identidad visual de la Fase 2 del Proyecto Integrador de Diseño de Interfaces. Reemplaza la fuente del sistema (`system-ui`) usada en la versión inicial de `estilos.css`. Igual que el color (6.3), la tipografía se eligió por su función y por el perfil de los usuarios (6.1): personas jóvenes y mayores que leen la interfaz durante gran parte de la jornada, en celular y en computador.

**Criterios de selección:**
- **Sin serifas:** la evidencia sobre serifas en pantalla no es concluyente, pero hay indicios de que dificultan la lectura a personas con trastornos de lectura; por eso la buena práctica en web es usar fuentes sin serifas.
- **Tamaño según la distancia de lectura:** en celular, 16 px es el mínimo recomendado para texto y es el que usa el Operario. En escritorio, donde la pantalla está más cerca y hay más datos por vista, el texto va de 14 a 16 px.
- **Interlineado:** entre 130 % y 150 % del tamaño de la letra, para no perder el renglón.
- **Grosor:** evitar pesos delgados, sobre todo en tamaños pequeños.
- **Caracteres inconfundibles:** en un sistema donde se leen códigos de actividad y el NIT de las empresas, la `l` minúscula, la `I` mayúscula y el `1`, así como la `O` y el `0`, no deben confundirse.
- **Licencia libre para uso comercial:** ambas fuentes se distribuyen con la licencia SIL Open Font License 1.1, que permite usarlas en un producto comercial sin costo.

**Fuentes elegidas y función de cada una:**

| Fuente | Función | Motivo |
|---|---|---|
| **Figtree** | Todo lo que se *lee*: títulos, textos, botones, etiquetas, tablas y menús; también las cifras y el cronómetro | Fuente sin serifas de formas simples y aspecto neutro y amable. Es más angosta que Lexend, la fuente anterior, así que caben más datos por renglón en fichas y tablas. Licencia SIL Open Font License |
| **Atkinson Hyperlegible Mono** | Solo lo que se *identifica carácter por carácter*: los códigos de actividad y el NIT | Diseñada por el Braille Institute para mejorar la legibilidad en personas con baja visión, con formas que diferencian cada carácter (la `l` con cola, el `1` con gancho, el `0` con barra) |

**Conflicto identificado y cómo se resuelve:** en Figtree, la `I` mayúscula y la `l` minúscula se parecen. Por eso el contenido donde una confusión de caracteres causaría un error real (códigos de actividad y NIT) se escribe en Atkinson Hyperlegible Mono. Las cifras (cantidades, porcentajes, duraciones, horas y el cronómetro) y las referencias de equipos ("Sensor B2", "Línea 1"), que son texto corriente, no tienen ese riesgo y se quedan en Figtree, con números de ancho fijo (`tabular-nums`) para que se alineen en columnas y el cronómetro no "salte" mientras corre.

**Tamaños por dispositivo.** El Operario lee en celular, de pie y a un brazo de distancia; el Administrador y el Superadmin leen en computador, sentados y con más información por pantalla. Por eso los tamaños no son los mismos:

| Elemento | Celular | Escritorio |
|---|---|---|
| Título de pantalla | 22 px | 26 px |
| Título de sección | 20 px | 18 px |
| Título de tarjeta | 16 px, semibold | 16 px, semibold |
| Texto | 16 px | 15 px |
| Texto secundario | 14 px | 14 px |
| Etiquetas | 13 px | 13 px |
| Cronómetro | 40 px | 40 px |

En escritorio el título de sección es más pequeño que en celular porque encabeza paneles dentro de una pantalla con más información. Interlineados: 1,25 en el título de pantalla, 1,3 en el de sección, 1,35 en el de tarjeta, 1,5 en el texto, 1,45 en el texto secundario y 1,2 en las etiquetas.

La raíz del documento usa el tamaño que el usuario tenga configurado en su navegador (16 px por defecto), y todos los tamaños se expresan en rem.

**Reglas obligatorias del sistema tipográfico:**
1. **Solo dos pesos en Figtree:** regular (400) para leer y semibold (600) para jerarquía y acción.
2. **Ningún texto por debajo de 13 px.** En celular el texto corrido no baja de 16 px.
3. **Tamaños en rem, no en px fijos:** si el usuario agranda la letra en su dispositivo, toda la interfaz crece en proporción sin romperse (WCAG 2.1, criterio 1.4.4, cambio de tamaño del texto hasta 200 %).
4. **El diseño soporta ajustes de espaciado del usuario** (interlineado 1,5, espacio entre párrafos de 2 veces el tamaño, espaciado entre letras de 0,12 y entre palabras de 0,16) sin perder contenido (WCAG 2.1, criterio 1.4.12).
5. **Los códigos de actividad y el NIT van en Atkinson Hyperlegible Mono; las cifras y el cronómetro, en Figtree con números de ancho fijo.** Nunca se mezclan dos familias de letra para escribir un mismo dato.
6. **Texto alineado a la izquierda,** sin justificar, para mantener espacios regulares entre palabras.
7. Todos los estilos se definen como **variables CSS** en un único lugar (`:root` de `estilos.css`), igual que el color.

**Relación con los principios de diseño de la Fase 2:**
- **Jerarquía visual (usabilidad):** la diferencia de tamaño y peso permite distinguir de un vistazo el título, la información principal y la secundaria, y las acciones.
- **Consistencia (usabilidad):** los mismos roles tipográficos se usan en las vistas de los tres roles.
- **Semejanza (Gestalt):** todos los elementos del mismo tipo comparten estilo (por ejemplo, todos los títulos de tarjeta), así el usuario los reconoce como equivalentes.

**Implementación:** como el despliegue es local (Sección 7) y la planta puede no tener conexión estable a internet, los archivos de ambas fuentes se incluyen dentro del proyecto (en formato `.woff2`, en la carpeta `app/static/fuentes/`) en lugar de cargarse desde Google Fonts. Si una fuente no carga, el sistema usa como respaldo la fuente sin serifas del dispositivo (`system-ui, sans-serif`) para Figtree y una monoespaciada del sistema (`ui-monospace, monospace`) para Atkinson Hyperlegible Mono.

### 6.5 Metáforas de la interfaz (Diseño de Interfaces)

Una metáfora de interfaz representa objetos, acciones o conceptos conocidos del mundo real para facilitar la comprensión y el uso de una interfaz digital (clase de la Semana 11). Es el requisito 4 de la Fase 2. En GestLab cada metáfora es un objeto que el usuario ya conoce, convertido en un elemento de la pantalla.

**Metáfora central: la planilla del turno** (organizacional). Es la planilla que se pega en la pared de la planta para saber quién hace qué y a qué hora. En la interfaz se llama tablero del turno. Se ve en Equipo (Administrador) y en Hoy (Operario).
- El Administrador ve la planilla completa: una fila por persona y las horas de izquierda a derecha.
- El Operario ve su propio renglón, en vertical: las horas de arriba abajo.
- Cada actividad es una tarjeta puesta en su hora.
- La línea "Ahora", en el color principal, marca la hora actual.
- Lo que pasa de la hora de fin del turno se raya, como tiempo fuera del turno.

Reemplaza la metáfora del tanque de carga, que se probó en una propuesta intermedia (`docs/disenos/stitch_calma_operativa/`). El tanque decía cuánto trabajo había, pero no cuándo; la planilla responde las dos preguntas.

**Metáforas de apoyo:**

| Del mundo real | En GestLab | Tipo | Dónde se ve |
|---|---|---|---|
| Candado | Actividad de hora fija: está cerrada, no se puede mover | Visual | Hoy (Operario) y Equipo (Administrador), en la tarjeta de la actividad |
| Carpeta | Proyecto: guarda un grupo de actividades | Organizacional | Proyectos y Actividades (Administrador) |
| Botones de un reproductor (reproducir, pausa y visto bueno) | Iniciar, pausar y finalizar una actividad | Funcional | Hoy (Operario), en la actividad en curso |
| Cronómetro | El tiempo que lleva la actividad en curso | Visual | Hoy (Operario), en la actividad en curso |
| Flecha de devolver, como al devolver un paquete | Devolver la actividad al Administrador | Funcional | Detalle de actividad (Operario) |
| Lista de chequeo numerada | Los pasos de la actividad | Organizacional | Detalle de actividad (los dos roles) |
| Clip | Adjuntos de la actividad | Visual | Detalle de actividad (los dos roles) |
| Teléfono | Contacto de la actividad | Visual | Detalle de actividad (los dos roles) |
| Marcador de mapa | Ubicación donde se hace el trabajo | Visual | Detalle de actividad y tarjeta de la actividad (los dos roles) |
| Franjas diagonales de zona restringida, como las de seguridad industrial | Lo que queda fuera del turno | Visual | Equipo (Administrador) y Hoy (Operario), después de la hora de fin |
| Puerta de salida | Cerrar sesión | Visual | Barra superior (los tres roles) |
| Reorganizar tarjetas sobre una mesa (arrastrar y soltar) | Ordenar mi día; pasar una actividad a otra persona | Funcional | Hoy (Operario) y Equipo (Administrador) |

La captura de cada metáfora se toma en la Etapa 7 del rediseño, cuando las pantallas estén construidas, y va en el documento de diseño de la Fase 2.

**Buenas prácticas de la clase que se aplican:**
- **Usar metáforas universales:** cada objeto de la tabla se reconoce sin explicación.
- **Pensar en el usuario y su contexto:** la planilla del turno y las franjas de zona restringida son objetos de la planta.
- **Mantener la consistencia:** los dos roles ven la misma metáfora central; uno la planilla completa y el otro su renglón. Cada objeto significa lo mismo en todas las pantallas.
- **Combinar íconos y texto:** ningún ícono va solo; siempre lo acompaña su nombre o su dato (regla 1 de la Sección 6.3).
- **Priorizar la claridad sobre el realismo:** todo se dibuja plano, sin imitar texturas ni relieves de los objetos físicos.

**Límites de la metáfora central y cómo se compensan:**
- La planilla muestra cuándo se hace cada actividad, pero no cuánto pesa el día para la persona. Por eso se suman las horas en texto (por ejemplo, "2 h 55 min de trabajo · 4 h 05 min disponibles").
- El renglón vertical del Operario se alarga en los días cargados. Por eso los espacios sin actividad se comprimen a una línea (por ejemplo, "Disponible · 1 h 30 min").

---

## 7. Alcance técnico

- Python como lenguaje principal.
- Flask como framework para el desarrollo de la aplicación web.
- MongoDB como sistema de persistencia de datos.
- HTML, CSS y JavaScript para la interfaz web. La interfaz funciona como un cliente en el navegador que consume la API REST del sistema (intercambio de datos en JSON). Los archivos de la interfaz los entrega el mismo servidor Flask (mismo origen), y la autenticación se maneja con la sesión de Flask mediante cookie.
- Bibliotecas de interfaz, todas de licencia libre y copiadas dentro del proyecto (carpeta `app/static/vendor/`) para no depender de internet ni de un proceso de compilación: **EventCalendar** (MIT) para el horario por día, por semana, en lista y por operario; **Chart.js** (MIT) para las gráficas; e íconos de **Lucide** (ISC).
- Programación Orientada a Objetos como paradigma principal para el diseño de la lógica del sistema.
- Arquitectura en capas, manteniendo separadas la presentación, la lógica de negocio y la persistencia.
- Git y un repositorio remoto para el control de versiones y trabajo colaborativo.
- Despliegue de la aplicación en un entorno local, con la posibilidad de desplegarla en un servidor independiente si las condiciones lo permiten, utilizando Docker como mecanismo de containerización para empaquetar y ejecutar la aplicación de forma consistente entre entornos.
- **SonarQube** como herramienta de análisis estático y control de calidad de código, integrado al repositorio de GitHub, para monitorear de forma continua aspectos como cobertura de pruebas, code smells, duplicación y cumplimiento de buenas prácticas de diseño (por ejemplo, principios SOLID).
- **Herramientas de revisión del diseño (solo desarrollo)**, en la carpeta `herramientas/`: un script que calcula el contraste WCAG entre colores (`contraste.py`) y otro que toma capturas de las pantallas en tamaño celular y escritorio con Playwright, junto con versiones desenfocada y en escala de grises para revisar la jerarquía visual y la independencia del color (`capturas.py`, con la lista de pantallas en `pantallas.json`). Sus dependencias (Playwright y Pillow) van en `requirements-dev.txt`, separadas de las del producto, y no forman parte de la imagen de Docker. Las credenciales de los usuarios de prueba se leen del archivo `.env`. Las capturas pueden tomarse con un navegador basado en Chromium que ya esté instalado (Brave, Edge o Chrome), indicando su ejecutable en `CAPTURAS_NAVEGADOR`, o con el Chromium que descarga Playwright. Las imágenes generadas no se suben al repositorio.

---

## 8. Alcance del MVP

La primera versión funcional deberá demostrar el flujo principal del sistema de extremo a extremo:

**Empresa → usuarios → actividad (independiente o de un proyecto) → asignación → prioridad → ejecución → registro de tiempo → análisis de carga laboral.**

El MVP se considerará cumplido cuando el sistema permita verificar, de forma concreta, lo siguiente:

1. **Empresa y usuarios:** el Superadmin puede registrar al menos una empresa y crear su primer usuario Administrador; ese Administrador puede a su vez crear usuarios Operario dentro de su empresa, y cada uno de los tres roles (Superadmin, Administrador, Operario) accede a una interfaz distinta según su rol.
2. **Actividades y proyectos:** un Administrador puede crear una actividad independiente, y crear un proyecto con una o más actividades.
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
- Automatización completa de decisiones de asignación o priorización. La asignación es manual. Las únicas acciones automáticas son la reprogramación de las actividades de horario flexible que no se hicieron y el paso a No realizada de las de hora fija (Sección 5.1); ambas quedan registradas y son visibles para el Administrador.
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

Los agentes son herramientas de trabajo del equipo: no forman parte del producto ni de los entregables de las materias. Aun así, `CLAUDE.md` y la carpeta `.claude/agents/` **se versionan en el repositorio**, para que los dos integrantes trabajen con las mismas instrucciones y para no perderlos: al no estar en Git, un cambio de rama los borró del computador.

**Archivos que no se suben al repositorio:** el `.env` (claves y contraseñas; el repositorio solo incluye `.env.example` con valores de ejemplo), la configuración personal de Claude Code (`.claude/settings.local.json`), las capturas de `herramientas/capturas/` y los entornos virtuales de Python.

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

---

## 14. Glosario

Términos que usa el sistema en sus pantallas, en este documento y en el código. Cada cosa se llama de una sola manera.

| Término | Significado |
|---|---|
| Actividad | Unidad de trabajo que se programa, se asigna y se ejecuta. Su código es el de su orden de trabajo (por ejemplo, `OT-0042`); en los textos siempre se dice "actividad", no "orden" |
| Actividad independiente | Actividad que no pertenece a ningún proyecto |
| Proyecto | Conjunto de actividades. Su avance se mide en horas |
| Hora fija | La actividad se hace a la hora que definió el Administrador. No se pausa ni se reprograma |
| Horario flexible | La actividad queda asignada al día y el Operario decide en qué momento hacerla |
| Jornada | El día de trabajo de un operario. Mientras no existan los turnos, coincide con el día calendario en la zona horaria de la empresa |
| Capacidad | Tiempo de trabajo disponible en una jornada: duración del turno menos el descanso |
| Carga | Suma del tiempo estimado de las actividades de un operario en una jornada. Sobrecarga: carga por encima del 100 % de la capacidad |
| Asignación | Vínculo entre una actividad y un operario. No se borra: termina cuando el operario la devuelve o el Administrador se la retira |
| Ejecución | Registro del tiempo de un operario en una actividad: inicio, pausas con su motivo, fin y observación |
| Tiempo real | Tiempo trabajado en una actividad, sin contar las pausas |
| Programación del día | Secuencia de las actividades de un operario en una jornada, con la hora de inicio y de fin de cada una: reales para lo ejecutado, proyectadas para lo pendiente. Se recalcula continuamente |
| Orden del día | El orden que el Operario eligió para sus actividades de horario flexible. Si no eligió ninguno, vale el sugerido: urgentes, prioridad y hora |
| Fin proyectado | Hora en la que terminaría una actividad en curso o pendiente, según el tiempo estimado que le falta |
| Turno | Horario de trabajo del catálogo de la empresa: hora de inicio, hora de fin y descanso. Cada operario tiene uno a la vez |
| Asistencia | Marca de entrada y de salida de un operario en una jornada. Estados: Por validar, Validada, Corregida; "Sin marca" si tiene turno y no marcó entrada |
| Tiempo presente | Tiempo entre la entrada y la salida de una jornada |
| Cierre de jornada | Lo que hace el sistema cuando termina el día: pausa lo que quedó en curso, reprograma lo de horario flexible y marca como No realizado lo de hora fija |
| Reprogramación automática | Paso de una actividad de horario flexible a la jornada siguiente porque no se terminó. La actividad queda **reprogramada** |
| Días de retraso | Días entre la fecha para la que se programó una actividad y la fecha en que está ahora |
| Cambio de fecha | Cuando el Administrador mueve una actividad a otro día. No es una reprogramación automática |
| Devolver | El Operario regresa al Administrador una actividad que no ha iniciado, con su motivo. Estado: Devuelta |
| No realizada | Actividad de hora fija que no se terminó en su día. Es definitivo |
| Cancelada | Actividad que el Administrador anuló, con su motivo. Es definitivo |
| Sin asignar | Actividad que no tiene operario: nunca se asignó o fue devuelta. El Administrador las consulta aparte |
| Límite de usuarios | Máximo de Administradores y de Operarios que puede tener una empresa |
| Tablero del turno | Vista del Administrador: una fila por persona y las horas de izquierda a derecha |
| Línea de tiempo | Vista del Operario: las horas del día de arriba abajo, con sus actividades |
| Tarjeta | Recuadro que representa una actividad en el tablero o en la línea de tiempo |
| Intervalo disponible | Tiempo sin actividades entre dos tarjetas de la línea de tiempo |

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
| 2026-10-03 | Ambas | Sección 11 — Trabajo colaborativo | Se listan los archivos que no se versionan (`.env`, configuración personal de Claude Code, capturas, entornos virtuales). `CLAUDE.md` y `.claude/agents/` se mantienen en el repositorio | Se probó dejarlos fuera de Git, pero un cambio de rama los borró del computador y dejaban de compartirse entre los integrantes; se decidió conservarlos versionados |
| 2026-10-07 | Diseño de Interfaces | Sección 6.3 | Se agrega el bloque "Precisiones de la implementación": colores de borde, texto sobre el coral, ícono de "En curso", borde lateral de la tarjeta en prioridad Media y etiquetas de rol en gris | Al aplicar las Secciones 6.3 y 6.4 a `estilos.css` aparecieron valores que las tablas no definían; se documentan para que el código no tenga colores sin respaldo en el alcance |
| 2026-10-07 | POO | Sección 5.1 | Se agregan a la actividad el código consecutivo por empresa, la ubicación, la hora programada opcional y la lista fija de cinco categorías | Necesarios para construir la creación de actividades y las vistas de horario. La hora es opcional y no altera el cálculo de la carga, que sigue siendo por jornada |
| 2026-10-07 | POO | Sección 5.2 | Capacidad provisional de 7 horas por jornada mientras no existan los turnos | La alerta de sobrecarga y las vistas de carga se construyeron antes que los turnos; se evita bloquearlas con un valor provisional y documentado |
| 2026-10-07 | Diseño de Interfaces | Sección 6.2 | Se reemplaza el menú lateral por una barra superior con pestañas (barra inferior en celular), se definen las vistas reales de cada rol (Equipo, Actividades y Usuarios; Hoy, Semana y Resumen) y el principio de "varias vistas de la misma información" | La estructura anterior (menú lateral, tablas y tarjetas) se veía genérica y sin identidad propia. El equipo tomó como referencia aplicaciones de agenda con vistas de lista, horario y resumen |
| 2026-10-07 | Diseño de Interfaces | Sección 6.3 | Se agrega la paleta de categorías (solo para los bloques del horario, como modo alterno al color por prioridad) y se adoptan los íconos de Lucide en lugar de símbolos de texto | El horario por bloques se lee mejor con color; se resolvió con una paleta aparte y un modo elegible para no romper la regla de que cada color de estado tiene un solo significado |
| 2026-10-07 | Ambas | Sección 7 — Alcance técnico | Se incorporan EventCalendar, Chart.js y Lucide, copiados dentro del proyecto | Se descartó FullCalendar (las vistas por recurso son de pago), ApexCharts (licencia con restricción por ingresos) y los marcos Bootstrap, Material y Tailwind (traen un aspecto propio o exigen compilación) |
| 2026-10-07 | Diseño de Interfaces | Sección 6.2 | Se agrega el "Sistema de composición": escala única de espacios, columna alineada con la barra superior, dos pesos de letra, bordes suaves, filas de igual altura, un botón principal por pantalla y color solo donde significa algo. Primera aplicación: pantallas del Superadmin | La interfaz usaba los colores y las fuentes definidos, pero se veía desordenada e improvisada: la barra y el contenido no estaban alineados, casi todo iba en negrita y los espacios no seguían una regla |
| 2026-10-07 | Diseño de Interfaces | Sección 6.4 (regla 5 y tabla) y 6.2 | La fuente monoespaciada se limita a códigos y cronómetro; las cifras pasan a Lexend con números de ancho fijo | En las tablas, la fuente monoespaciada tan espaciada cortaba la lectura (tres tipos de letra en una misma fila). El riesgo de confundir caracteres solo existe en los códigos |
| 2026-10-07 | Diseño de Interfaces | Sección 6.3 — Asignación por elemento | Las etiquetas de prioridad Alta y Media pasan de bloque lleno a fondo suave; Baja y los estados normales (Sin asignar, Por iniciar) quedan como texto gris con ícono, sin fondo. Solo Urgente conserva el bloque lleno | En una lista de muchas actividades, tantos bloques de color lleno competían entre sí y restaban calma. Se aplica la regla 3: el color intenso se reserva para lo que exige atención inmediata |
| 2026-10-10 | POO | Secciones 5.1, 1 a 4 y 8 | Los proyectos reemplazan a los requerimientos. Una actividad es suelta o pertenece a un solo proyecto. El avance del proyecto se mide en horas estimadas. Cambia el criterio 2 del MVP | Rediseño "Calma operativa", decisión E: un requerimiento con una sola actividad no aportaba nada, y uno con varias es, en la práctica, un proyecto |
| 2026-10-10 | POO | Sección 5.1 | Cada actividad es de hora fija o sin hora. Se define el orden del día del Operario y qué pasa cuando llega una hora fija, con aviso 10 minutos antes | Decisiones I1, I2 e I7: el Operario organiza lo que no tiene hora y el sistema respeta lo que sí la tiene |
| 2026-10-10 | POO | Secciones 5.1 y 9 | Se definen la pendiente arrastrada, el estado No realizada, la cancelación con motivo y la devolución de una orden. La reprogramación por ausencia se unifica con la regla de las pendientes | Decisiones I3, I4, I5 y D: definir qué pasa con lo que no se hizo, sin borrar nada del historial |
| 2026-10-10 | POO | Sección 5.1 | La información de la orden se arma por bloques con catálogos, y la orden avisa cuando está "Lista para iniciar". Se aclara que la asignación es manual | Decisión D: que la orden llegue completa y el Operario sepa si puede iniciarla |
| 2026-10-10 | POO | Sección 5.2 | Indicadores de pendientes arrastradas, no realizadas, canceladas y devoluciones; consulta por proyecto; las canceladas no cuentan en el cumplimiento ni en la carga | Consecuencia de las reglas nuevas de la Sección 5.1 |
| 2026-10-10 | Diseño de Interfaces | Sección 6.1 | Cambian las necesidades del Operario (día ordenado, devolver una orden, saber qué viene de días anteriores). La pantalla principal y la de ejecución se unen en Hoy | En el diseño nuevo la actividad en curso se ejecuta en su lugar del día, no en una pantalla aparte |
| 2026-10-10 | Diseño de Interfaces | Sección 6.2 | Equipo pasa a ser el tablero del turno, se agrega la vista Proyectos y Hoy es la fila del Operario. Sombras muy suaves y sin franjas de color a la izquierda de las tarjetas. Gestalt: cierre y continuidad | Rediseño "Calma operativa", construido sobre la metáfora de la planilla del turno |
| 2026-10-10 | Diseño de Interfaces | Sección 6.3 | El sistema de color pasa a llamarse "Calma operativa". Fondo `#F4F6F5`, texto secundario `#5B6664`, regla 8 sobre los grises de texto, coral también para la sobrecarga y estados nuevos con color provisional. Los valores de bordes, sombra y rayado se fijan en la Etapa 2 | Fondo neutro para bajar el cansancio visual. Todos los colores nuevos se midieron con `herramientas/contraste.py` |
| 2026-10-10 | Diseño de Interfaces | Sección 6.4 | Figtree reemplaza a Lexend. Tamaños por dispositivo, mínimo de 13 px y cronómetro en Figtree con cifras de ancho fijo. Atkinson Hyperlegible Mono queda solo para códigos | Más datos por renglón en escritorio y una sola familia de letra para todo lo que se lee. En los puntos que chocaban con la versión anterior prima el diseño nuevo |
| 2026-10-10 | Diseño de Interfaces | Nueva Sección 6.5 | Metáforas de la interfaz: la planilla del turno como metáfora central y doce de apoyo, con las buenas prácticas de la clase y los límites de la metáfora | Requisito 4 que el profesor agregó a la Fase 2. Se eligieron objetos que el usuario reconoce sin explicación |
| 2026-10-10 | Ambas | Secciones 5.1 y 6.1 a 6.5 | Correcciones tras revisar contradicciones entre secciones: el rayado de sobrecarga marca lo programado después de la hora de fin del turno y la alerta del 100 % va en texto; el Administrador reasigna arrastrando la ficha en el tablero; "Por iniciar" como único nombre del estado; la fuente monoespaciada es para los códigos de actividad y el NIT; se aclara el blanco de las superficies, el borde y el aviso de Urgente; se describe el logo y se agrega a las metáforas la columna "Dónde se ve" | Revisión del agente `profesor-interfaces` al cerrar la Etapa 1. No cambia ninguna decisión del rediseño; unifica la redacción |
| 2026-10-10 | Diseño de Interfaces | Secciones 6.3 y 6.4 | Se fijan los valores que quedaron para la Etapa 2: borde decorativo `#E1E5E3`, borde de controles `#7F8A87`, sombras, fondo del rayado de sobrecarga `#FBE5E0`, dibujo del logo y tabla de tamaños de letra por elemento y dispositivo | Etapa 2 del rediseño "Calma operativa". El borde de controles anterior (`#869295`) solo alcanzaba 2,95:1 sobre el fondo nuevo. Valores medidos con `herramientas/contraste.py` |
| 2026-10-10 | POO | Secciones 5.1 y 5.2 | Se resuelve la decisión abierta H1: la ejecución pertenece a cada operario asignado. Una actividad con varios operarios finaliza cuando todos finalizan. La hora fija no se pausa ni se arrastra, y la urgente no la interrumpe. Fin de jornada: el sistema pausa y arrastra lo que quedó en curso. Cancelar solo sin iniciar o pausada; ya no se borran actividades. Motivos de pausa y de cancelación como listas por empresa que se van llenando. Zona horaria por empresa. Avance del proyecto sin canceladas; carga con no realizadas; tiempo real por operario | Etapa 4 del rediseño. Diseño propuesto por el agente `diseno-oo` y reglas decididas por el usuario. Con una sola ejecución por actividad, la pausa de un operario pausaba a todos y un operario quedaba bloqueado por lo que hacía su compañero |
| 2026-10-10 | POO | Sección 5.1 | No se puede programar ni mover una actividad a un día que ya pasó. El Administrador consulta aparte las actividades sin operario (nunca asignadas o devueltas) | Decisiones del usuario al revisar el cierre de jornada |
| 2026-10-10 | Ambas | Todo el documento y nueva Sección 14 | Se unifica el vocabulario y se agrega un glosario. "Arrastre" y "pendiente arrastrada" pasan a "reprogramación automática" y "actividad reprogramada", con "días de retraso"; "actividad suelta" pasa a "actividad independiente"; "sin hora" pasa a "horario flexible"; "la orden" pasa a "la actividad"; "riel", "ficha" y "hueco" pasan a "línea de tiempo", "tarjeta" e "intervalo disponible". Los mismos términos se aplican en las pantallas, en la API y en el código | Decisión del usuario: que todos los términos sean técnicos y entendibles, sin palabras coloquiales. Las filas anteriores de esta bitácora y el anexo conservan los términos de su momento |
| 2026-10-10 | POO | Secciones 5.1, 5.2 y 14 | Programación dinámica del día: lo ejecutado se mide con sus horas reales de inicio y fin, no con el estimado, y lo pendiente se reacomoda cuando una actividad termina antes o se demora. Se define el tiempo disponible de la jornada. La carga sigue siendo un dato de planeación, con estimados | Decisión del usuario: la estimación es una cosa y la ejecución es otra |
| 2026-10-10 | Ambas | Sección 14 | Se agregan al glosario Turno, Asistencia (con sus estados) y Tiempo presente | Construcción del criterio 7 del MVP (turnos y asistencia) |

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

**Sección 5.1 (fragmentos previos al rediseño "Calma operativa", 2026-10-10):**
> - "Registro y seguimiento de requerimientos que llegan al área."
> - "Conversión y organización de requerimientos en actividades de trabajo."
> - "Definición de información clara para cada actividad."
> - "Definición de una fecha programada de ejecución para cada actividad y, de forma opcional, una hora programada. La fecha determina la jornada a la que pertenece la actividad; la hora solo sirve para ubicarla en el horario y no cambia el cálculo de la carga."
> - "Las actividades que no se reasignen se reprograman automáticamente a la siguiente jornada del operario. La reprogramación queda registrada como un evento (con la jornada de origen), y si la jornada de destino supera el 100% de la capacidad del operario, el Administrador recibe un aviso."

**Sección 5.2 (fragmento previo al 2026-10-10):**
> - "**Cumplimiento de actividades:** una actividad se considera cumplida si se finaliza en su jornada programada. Las actividades reprogramadas por ausencia cuentan como retraso."

**Sección 8 (previo al 2026-10-10):**
> "Empresa → usuarios → requerimiento → actividad → asignación → prioridad → ejecución → registro de tiempo → análisis de carga laboral."
> "2. **Requerimiento → Actividad:** un Administrador puede registrar un requerimiento y convertirlo en una o más actividades de trabajo."

**Sección 9 (fragmento previo al 2026-10-10):**
> - "Automatización completa de decisiones de asignación o priorización, salvo la reprogramación automática por ausencia definida en la Sección 5.1, que queda registrada y es visible para el Administrador."

**Sección 6.1 (pantallas mínimas del Operario, previas al 2026-10-10):**
> 2. Pantalla principal (lista priorizada de actividades + acceso a reportar actividad externa)
> 3. Detalle de actividad (información completa antes de iniciar una tarea)
> 4. Ejecución de actividad (cronómetro, control de estado, historial de pausas, observación final)

**Sección 6.2 (fragmentos previos al 2026-10-10):**
> | Administrador | Computador (también usable en celular) | **Equipo** (el día de cada operario en columnas, con su carga) · **Actividades** (requerimientos y sus actividades) · **Usuarios**. Pendientes: Turnos y asistencia · Indicadores |
> | Operario | Celular | **Hoy** (actividad en curso, carga del día y agenda) · **Semana** (horario por día, semana o lista) · **Resumen** (carga de la semana e indicadores propios). Pendiente: marca de entrada y salida |
> - **Bordes suaves y sin sombras:** los paneles se separan del fondo por el contraste de color y un borde tenue. Los controles (campos y botones secundarios) llevan un borde más marcado, con contraste de al menos 3:1.
> - **Cierre:** todavía no se aplica en las pantallas construidas; se evaluará en la pantalla de ejecución del Operario (por ejemplo, el avance de la jornada).

**Sección 6.3 (previo al 2026-10-10, cuando el sistema se llamaba "Aqua de trabajo"):**
> | Fondo | `#EEF5F4` | Fondo general de todas las pantallas (tinte aqua, sin blanco puro) | — |
> | Acento de marca (coral) | `#E9806E` | Solo identidad: logo, avatar del usuario, barra de progreso de la jornada. Nunca en texto ni en estados | No se usa para texto |
> | Texto secundario | `#4E5B60` | Textos de apoyo, metadatos | 7,0:1 sobre blanco |
> 4. El **coral de marca** nunca se usa en texto, etiquetas de estado ni botones de acción.
> - **Bordes:** el borde de paneles y tablas es decorativo y usa un tinte claro del fondo (`#D3DEDD`). El borde de los controles (campos de formulario y botones secundarios) debe distinguirse como componente, así que usa el gris base `#6B7478` (4,8:1 sobre blanco).
> - **Borde lateral de la tarjeta de actividad:** toma el color base de la prioridad, salvo en Media, donde usa el ámbar oscuro `#6B4A0E` por la regla 7.

**Sección 6.4 (escala tipográfica y reglas con Lexend, previas al 2026-10-10):**
> - **Tamaño mínimo:** 16 px es el mínimo recomendado para texto web, y para públicos con personas mayores se recomienda acercarse a 19 px.
> **Escala tipográfica:** proporción 1,2 (tercera menor) sobre una base de 18 px. Cada nivel es 1,2 veces el anterior (15 → 18 → 22 → 26 → 31 px), lo que da una jerarquía clara sin saltos bruscos en pantallas pequeñas.
>
> | Rol | Fuente | Tamaño | Peso | Interlineado | Dónde se usa |
> |---|---|---|---|---|---|
> | Título de pantalla (H1) | Lexend | 26 px móvil / 31 px escritorio (1,444 rem / 1,722 rem) | 600 | 1,25 | Título principal o saludo de cada pantalla |
> | Título de sección (H2) | Lexend | 22 px (1,222 rem) | 600 | 1,3 | Encabezados de bloque ("Mis actividades", "Usuarios") |
> | Título de tarjeta (H3) | Lexend | 18 px (1 rem) | 600 | 1,35 | Nombre de la actividad en tarjetas, títulos de diálogos |
> | Texto principal | Lexend | 18 px (1 rem) | 400 | 1,5 | Descripciones, observaciones, formularios |
> | Texto secundario | Lexend | 16 px (0,889 rem) | 400 | 1,45 | Metadatos (línea, estimado, asignado por), ayudas de campo |
> | Tablas | Lexend | 16 px (0,889 rem) | 400 | 1,45 | Tablas del Administrador y del Superadmin |
> | Etiquetas y estados | Lexend | 15 px (0,833 rem) | 600 | 1,2 | Etiquetas de prioridad, estado y jornada (siempre con ícono y color, ver 6.3) |
> | Botones | Lexend | 18 px (1 rem) | 600 | — | Todos los botones |
> | Cronómetro | Atkinson Hyperlegible Mono | 44 px (2,444 rem) | 600 | — | Tiempo en ejecución de la actividad |
> | Códigos | Atkinson Hyperlegible Mono | 92 % del texto que acompaña | 500 | — | Códigos de actividad y NIT |
> | Cifras | Lexend, números de ancho fijo | El del texto que acompaña | 400 | — | Cantidades, porcentajes, duraciones y horas |
> Los valores en rem se calculan sobre una base de 18 px. Esa base se declara en la raíz del documento como `112,5 %` del tamaño del navegador (16 px por defecto), no como 18 px fijos, para que respete el tamaño de letra que cada usuario tenga configurado en su dispositivo.
> 1. **Solo dos pesos en Lexend:** 400 para leer y 600 para jerarquía y acción. No se usan pesos por debajo de 400.
> 2. **Ningún texto por debajo de 15 px;** ese mínimo se reserva para etiquetas cortas en negrita. El texto corrido nunca baja de 16 px.
> 5. **Los códigos van en Atkinson Hyperlegible Mono; las cifras, en Lexend con números de ancho fijo.** Nunca se mezclan dos familias de letra para escribir un mismo dato.

**Secciones 5.1 y 5.2 (fragmentos previos a las reglas de ejecución del 2026-10-10):**
> - Proyectos: un proyecto es un conjunto de actividades. Solo el Administrador lo crea, lo planifica de entrada y le puede agregar actividades después. Las actividades de un proyecto y las sueltas suman por igual a la carga y a los indicadores. El avance de un proyecto se mide en horas: horas estimadas de sus actividades finalizadas sobre horas estimadas totales del proyecto.
> - Definición de prioridad de las actividades en cuatro niveles: Baja, Media, Alta y Urgente. El nivel Urgente indica que la actividad debe interrumpir la tarea que el operario tenga en curso.
> - Hora fija que interrumpe: si el orden elegido no alcanza a terminar antes de una actividad de hora fija, el sistema lo avisa pero lo permite. Diez minutos antes de la hora fija el sistema avisa. Al llegar la hora, el Operario pausa la actividad que lleva, inicia la de hora fija y después retoma la otra. Esa pausa queda registrada con el motivo "Actividad de hora fija".
> - Gestión de la ejecución de actividades, incluyendo inicio, pausa, reanudación y finalización.
> - Pendiente arrastrada: una actividad sin hora que no se hizo pasa sola a la siguiente jornada y queda marcada como pendiente arrastrada. Si tiene varios operarios, se arrastra para todos los asignados, porque la actividad tiene una sola fecha. El Administrador puede reasignarla, cambiarle el día o cancelarla.
> - No realizada: una actividad de hora fija que no se hizo queda en estado No realizada, que es definitivo. No se cancela ni se reasigna; si el trabajo sigue haciendo falta, el Administrador crea una actividad nueva.
> - Cancelar: solo el Administrador puede cancelar una actividad, indicando el motivo en una lista desplegable con la opción "Otro" y texto. La actividad cancelada no se borra; queda en el historial.
> - Comparación entre tiempo estimado y tiempo real de ejecución.
> - Cálculo de la carga por jornada: suma de los tiempos estimados de las actividades asignadas al operario y programadas para esa jornada.
