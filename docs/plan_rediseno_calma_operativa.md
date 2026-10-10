# Plan de cambios: rediseño "Calma operativa" y nuevas reglas de actividades

- **Fecha:** 10 de octubre de 2026
- **Materia principal:** Diseño de Interfaces, Fase 2 (usabilidad, Gestalt, color y metáforas). Las etapas 4 y 7 tocan el modelo de datos, así que también interesan a Diseño Orientado a Objetos.
- **Base:** `main` en `3147d87` (PR #7, 8 de octubre).
- **Dónde va este archivo:** `docs/plan_rediseno_calma_operativa.md`. Es una guía de trabajo, no una fuente de verdad. Las reglas se escriben en el alcance (etapa 1) y el código sigue al alcance, como dice `CLAUDE.md`.

---

## Cómo usar este plan en Visual Studio Code

1. Copia este archivo a `docs/plan_rediseno_calma_operativa.md`.
2. Trabaja una etapa por sesión de Claude Code, en el orden de abajo. Cada etapa trae:
   - qué cambia y por qué;
   - las decisiones que tienes que confirmar antes de empezar;
   - un **prompt** para pegar en Claude Code;
   - cómo verificar el resultado.
3. Al cerrar cada etapa:
   - revisa el diff;
   - corre la verificación;
   - haz commit;
   - pasa a la siguiente.
4. Si Claude Code encuentra algo que contradice el alcance, debe detenerse y avisarte (`CLAUDE.md` ya se lo exige). No lo dejes resolverlo solo.

**Las maquetas son referencia de composición, no de valores.** Las imágenes de `tentativo/` muestran qué va dónde y cómo se agrupa. Los tamaños, colores y espacios salen del alcance (6.2 a 6.4). Los valores de la 6.4 se actualizan en la etapa 1 con los de la tabla 1.1 bis.

**Maquetas de referencia** (cópialas a `docs/disenos/` para que Claude Code las pueda ver):

| Archivo | Qué muestra |
|---|---|
| `2_admin_equipo_tablero.png` | Equipo del Administrador: tablero del turno |
| `3_admin_proyecto.png` | Detalle de un proyecto |
| `4_operario_fila_del_tablero.png` | Hoy, urgente, detalle de la orden y devolver |
| `5_operario_ordenar_dia.png` | Hora fija, sin hora, "Viene de ayer" y Ordenar mi día |
| `6_operario_hora_fija_parte.png` | Actividad partida por una hora fija |
| `stitch_calma_operativa/` | Resultado de Google Stitch y su revisión (evidencia del proceso) |

---

## Etapa 0. Preparar el repositorio

**Antes de empezar, verifica tu push.** En GitHub, `main` sigue en `3147d87` (8 de octubre). Si subiste cambios después de esa fecha, no llegaron. En la terminal de VS Code:

```bash
git status
git log --oneline -5
git log --oneline origin/main -3
```

Si tienes commits locales que no aparecen en `origin/main`, súbelos primero.

**`develop` está atrasada.** Tiene 17 commits menos que `main`, porque el PR #7 entró directo a `main`. Tu convención (`CLAUDE.md`) dice que las ramas salen de `develop`. Ponla al día antes de abrir la rama nueva:

```bash
git checkout develop
git pull
git merge --ff-only origin/main
git push
git checkout -b feature/rediseno-calma-operativa
```

**Verificación:** `git log --oneline -1` en `develop` muestra `3147d87`.

---

## Etapa 1. Actualizar el alcance (solo documentos, sin código)

Es la etapa más importante. Las reglas viven en el alcance; si el código cambia antes, el agente `profesor-interfaces` auditará contra reglas viejas.

### 1.1 Lo que ya está decidido y se escribe tal cual

**Diseño visual (Diseño de Interfaces):**
- Fondo `#F4F6F5` (gris neutro) en lugar de `#EEF5F4`.
- Figtree en lugar de Lexend. Atkinson Hyperlegible Mono sigue solo para códigos.
- Sombras muy suaves en lugar de "sin sombras".
- Coral de marca: logo, avatar y sobrecarga (lo que pasa del turno, rayado).
- Sin franjas de color a la izquierda de las tarjetas.
- Logo nuevo: el tablero (tres barras y la marca coral).
- Metáfora central: el tablero de programación del turno, en lugar del tanque.

**Reglas de funcionamiento:** bloques C, D, E e I del punto 1.2 (orden del Operario, hora fija, pendientes, No realizada, cancelar, devolver, proyectos).

### 1.1 bis Valores decididos que cambian la 6.3 y la 6.4

| Punto | Valor |
|---|---|
| Texto secundario | `#5B6664`; ningún gris de texto más claro que `#66716E` (5,06:1). El `#8A9592` queda prohibido para texto (3,09:1) |
| Tamaños | Celular: texto de 16 px o más, títulos de 20 a 22 px. Escritorio: texto de 14 a 16 px. Ningún texto por debajo de 13 px. Solo dos pesos: regular y semibold |
| Cronómetro | Figtree con cifras de ancho fijo (`tabular-nums`). Atkinson Hyperlegible Mono solo para códigos (OT-0001) |
| Aviso de hora fija | 10 minutos antes |
| Avance del proyecto | Horas estimadas de actividades finalizadas / horas estimadas totales del proyecto |

### 1.2 Cambios por sección

**5.1 Gestión**
- Reemplazar "Registro y seguimiento de requerimientos" y "Conversión de requerimientos en actividades" por **Proyectos** (decisión E):
  - Un proyecto es un conjunto de actividades.
  - Solo el Administrador lo crea, lo planifica de entrada y le puede agregar actividades después.
  - Una actividad es suelta o pertenece a un solo proyecto (`proyecto_id` opcional). Nunca a los dos.
  - Lo que antes era "requerimiento" es una actividad suelta.
  - Todo suma con todo y es analizable; el avance del proyecto se mide en horas (1.1 bis).
- **Hora fija o sin hora** (I1):
  - Con hora fija: el Administrador pone hora y queda fija.
  - Sin hora: asignada al día, sin hora.
  - Reemplaza la frase "la hora solo sirve para ubicarla en el horario".
- **Orden del Operario** (I2):
  - El orden inicial se sugiere por prioridad y luego por hora.
  - El Operario reordena solo las que no tienen hora.
  - Las de hora fija y las urgentes no se mueven; las urgentes van siempre arriba.
- **Hora fija que interrumpe** (I7):
  - Si el orden no alcanza antes de una hora fija, la app avisa pero lo permite.
  - Al llegar la hora fija (con la anticipación de 1.1 bis (10 minutos)), el Operario pausa la que lleva, inicia la fija y después retoma la otra.
  - La pausa queda con motivo "Actividad de hora fija".
- **Pendientes** (I3, I4):
  - Sin hora y no se hizo: pasa sola a la siguiente jornada del mismo Operario y queda marcada como **pendiente arrastrada** para el Administrador, que puede reasignarla, cambiarle el día o cancelarla.
  - Con hora fija y no se hizo: estado **No realizada**, definitivo. No se cancela ni se reasigna; si el trabajo sigue haciendo falta, el Administrador crea una actividad nueva.
  - Unificar con la regla actual de reprogramación por ausencia (Turnos y asistencia), que ya pasa las actividades a la siguiente jornada.
- **Cancelar** (I5): solo el Administrador, con motivo en lista desplegable más "Otro" con texto. No se borra; queda en el historial.
- **Devolver una orden** (D):
  - Solo antes de iniciarla.
  - Motivo en lista desplegable (Falta información, Me la asignaron por error, Falta herramienta o material, El equipo no está disponible, Otro con texto).
  - Si hay varios operarios asignados, solo sale el que devuelve; si no queda nadie, vuelve al Administrador.
- **Información de la orden** (D):
  - El Administrador elige qué bloques lleva cada orden: pasos, herramientas y materiales, equipo, adjuntos, contacto.
  - Los catálogos son listas desplegables con "Otro", que se van llenando con lo que se registra.
  - La orden muestra "Lista para iniciar" cuando tiene los bloques pedidos.
- **Asignación:** manual. El sistema solo sugiere reasignar cuando alguien se pasa de su turno.

**5.2 Análisis**
- Agregar indicadores:
  - pendientes arrastradas (cuántas y cuántos días llevan);
  - no realizadas;
  - canceladas por motivo;
  - devoluciones por motivo.
  Todos por operario, por proyecto y por empresa.
- Precisar que "Cumplimiento de actividades" cuenta como incumplidas las no realizadas y como retraso las arrastradas.

**6.1 Persona (Operario)**
- Cambiar la necesidad "Ver sus actividades ordenadas por prioridad" por "Ver su día ordenado: lo fijo en su hora y lo demás en el orden que él elija, partiendo de uno sugerido por prioridad".
- Agregar las necesidades: devolver una orden incompleta o mal asignada; saber qué viene de días anteriores.
- **Pantallas mínimas:** la 2 (principal) y la 4 (ejecución) se unen en **Hoy**, porque la actividad en curso se ejecuta en su lugar del día.

**6.2 Vistas por rol**
- Administrador:
  - **Equipo:** tablero del turno, una fila por persona.
  - **Actividades.**
  - **Proyectos:** nueva.
  - **Usuarios.**
- Operario:
  - **Hoy:** su fila del tablero en vertical, con la actividad en curso abierta en su hora.
  - **Semana** y **Resumen** se mantienen.
- Sistema de composición: aplicar las sombras muy suaves y quitar "franjas de color".
- **Cierre (Gestalt):**
  - Ya se aplica en el riel del Operario, que se lee como una sola línea continua aunque esté punteado.
  - También en las fichas partidas: "Parte 1" y "Parte 2" se perciben como una sola actividad.
- **Continuidad:** el tablero de izquierda a derecha (Administrador) y el riel de arriba abajo (Operario) siguen el paso de las horas.

**6.3 Color y 6.4 Tipografía**
- Aplicar 1.1 y 1.1 bis.
- Toda cifra nueva se mide con `herramientas/contraste.py` y se escribe en la tabla con su relación.

**Nueva 6.5 Metáforas** (requisito que agregó el profesor a la Fase 2)
- **Central: el tablero de programación del turno** (reemplaza al tanque):
  - el Administrador ve el tablero completo, una fila por persona y las horas de izquierda a derecha;
  - el Operario ve su propia fila en vertical;
  - cada actividad es una ficha;
  - la línea "Ahora" en petróleo marca la hora actual;
  - lo que pasa de las 2:00 p. m. se raya como fuera del turno.
  - Por qué sale del mundo del usuario: es el tablero de programación de producción que se usa en planta.
- **De apoyo:**
  - el reloj de marcar tarjeta (entrada y salida);
  - el cronómetro de taller (actividad en curso);
  - la señalización de seguridad (colores de estado, ISO 3864);
  - la orden de trabajo (código OT y "devolver la orden");
  - el logo: tres barras del tablero con la marca de "Ahora".
- **Límites de la metáfora y cómo se compensan:**
  - el tablero no dice cuánto pesa una actividad para la persona, así que se suman las horas en texto;
  - el riel vertical se alarga en días cargados, así que los huecos se comprimen a una línea "Libre · 1 h 30 min".
- Falta el contenido del pptx de metáforas del profesor. Exportarlo a PDF o imágenes para completar esta sección con su vocabulario.

**Bitácora de cambios**
- Una entrada con fecha, secciones tocadas y motivo.
- Copiar el texto viejo de las secciones reemplazadas en "Texto original de las secciones modificadas", como ya se hace.

**Otros documentos**
- `docs/enunciados/diseno_interfaces_fase2.md`: agregar el requisito 4, Metáforas (sección en el PDF con la metáfora, la captura, la explicación y la justificación, más las metáforas aplicadas en el prototipo).
- `CLAUDE.md`:
  - en "Reglas de dominio clave", agregar hora fija o sin hora, orden del Operario, arrastre, No realizada, cancelar y devolver;
  - actualizar "ESTADO DEL REDISEÑO";
  - cambiar Lexend por Figtree;
  - agregar a "Decisiones abiertas" la H1 (la ejecución pertenece a la actividad o a la asignación).
- `.claude/agents/profesor-interfaces.md` y `frontend-web.md`: cambiar "Secciones 6.1 a 6.4" por "6.1 a 6.5" y quitar el nombre "Aqua de trabajo" si lo cambias.

### 1.3 Prompt para Claude Code (etapa 1)

```
Lee docs/plan_rediseno_calma_operativa.md, Etapa 1, y docs/alcance_proyecto.md completo.
Vamos a actualizar el alcance. Todo lo que hay que escribir está decidido en 1.1 y 1.1 bis; no hay puntos abiertos en esta etapa.
Trabaja sección por sección en este orden: 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, nueva 6.5, bitácora.
Para cada sección: muéstrame el texto actual, el texto propuesto y el motivo, y espera mi aprobación
antes de escribir. Conserva el estilo del documento (español, frases cortas, tablas donde ya hay tablas).
Mide con herramientas/contraste.py cada color nuevo antes de escribirlo en una tabla.
No toques código en esta etapa. Al terminar, actualiza el enunciado, CLAUDE.md y los dos agentes
según el punto "Otros documentos" del plan.
```

**Verificación:**
- Pídele al agente `profesor-interfaces` que lea la 6.1 a la 6.5 y diga si hay contradicciones entre secciones.
- Commit: `Actualizar alcance: Calma operativa, metáforas, proyectos y reglas de orden y pendientes`.

---

## Etapa 2. Base visual (tokens, fuente, logo)

**Qué cambia:**
- `app/static/css/estilos.css`, solo en `:root`:
  - colores según 1.1 y 1.1 bis;
  - variable `--sombra` (sombras muy suaves);
  - `--fuente-texto` con Figtree.
- `app/static/fuentes/`: agregar `figtree-400.woff2`, `figtree-600.woff2` y su licencia (OFL); quitar Lexend.
- `app/static/js/componentes.js`: logo nuevo (tres barras del tablero más la marca coral vertical) y `favicon.svg`.
- Quitar el borde lateral de color de las tarjetas.

**Prompt:**
```
Etapa 2 del plan. Aplica a estilos.css los valores que quedaron en las Secciones 6.2 a 6.4 del alcance.
Cambia solo variables de :root y las reglas que usan valores sueltos; muéstrame el diff antes de guardar.
Reemplaza el logo en componentes.js y favicon.svg por el del tablero (ver docs/disenos/2_admin_equipo_tablero.png,
arriba a la izquierda): cuadro redondeado en principal suave, tres barras horizontales en principal y una
barra vertical en coral. Quita el borde lateral de prioridad de las tarjetas.
```

**Verificación:**
- `python herramientas/contraste.py --css app/static/css/estilos.css` (o el modo de variables que ya tiene).
- `python herramientas/capturas.py` y revisar las capturas en grises y desenfocadas: la jerarquía tiene que seguir leyéndose.

---

## Etapa 3. Operario: Hoy como su fila del tablero (con los datos que ya existen)

Esta etapa usa solo lo que la API ya da: `hora_programada` opcional, prioridad, estado, ejecución con pausas y carga del día. Así el prototipo queda presentable aunque el backend de la etapa 4 no esté.

**Composición** (maqueta `4_operario_fila_del_tablero.png`, pantallas 1 y 2):
1. **Encabezado:**
   - fecha;
   - "En turno" con punto verde, sin caja;
   - saludo "Tu turno, Carlos";
   - una línea con trabajo y tiempo libre;
   - botón secundario "Reportar actividad".
2. **Riel vertical con las horas del turno:**
   - en petróleo hasta "Ahora" y punteado después;
   - un nodo por actividad en su hora: si tiene `hora_programada`, la hora en negrita; si no, una hora aproximada en gris con "~", calculada sumando duraciones desde la anterior.
3. **Actividad en curso abierta en su hora:**
   - bloque en principal con cronómetro, avance e historial de pausas;
   - **Pausar** (secundario) y **Finalizar** (principal).
   - La línea "Ahora" con la hora a la izquierda cruza el bloque.
4. **Huecos** como una sola línea, "Libre · 1 h 30 min", sin caja.
5. **Urgente:**
   - cae en la línea de "Ahora" como único bloque rojo lleno, con un botón;
   - la actividad en curso se compacta y explica que queda en pausa si la atiende.
6. **Fin del turno:** fila rayada con "Marcar salida".
7. **Barra inferior:** Hoy, Semana, Resumen.

**Archivos:**
- `app/static/operario/index.html`
- `hoy.js`
- `operario-comun.js`
- estilos nuevos en `estilos.css` (clases `riel`, `riel-nodo`, `ficha`, `ficha-en-curso`, `ahora`)

**Prompt:**
```
Etapa 3 del plan. Rediseña la pantalla Hoy del Operario (app/static/operario/) según la Sección 6.2 y 6.5
del alcance y la maqueta docs/disenos/4_operario_fila_del_tablero.png (pantallas 1 y 2).
Usa solo los datos que la API ya entrega; no cambies backend. Antes de escribir código, propón la estructura
del HTML y las clases CSS nuevas y espera mi visto bueno. Respeta el sistema de composición (espacios --e1 a --e7,
dos pesos, tamaños de la tabla 1.1 bis, crearElemento sin innerHTML con datos). La urgente sigue la regla de 6.1:
aviso visible en esta pantalla. Agrega la pantalla a herramientas/pantallas.json si cambia su ruta.
```

**Verificación:**
- Capturas en celular (390 px).
- Revisar con el agente `profesor-interfaces`: contraste, 48 px en botones del Operario, una sola acción principal por estado y la metáfora visible.

---

## Etapa 4. Backend de las reglas nuevas (Diseño Orientado a Objetos)

Antes de tocar código, pásale el diseño al agente `diseno-oo`. Hay decisiones de clases que todavía están abiertas.

**Cambios de modelo:**
- `EstadoActividad`: agregar `DEVUELTA`, `NO_REALIZADA` y `CANCELADA`.
- `Actividad`:
  - `proyecto_id` opcional;
  - `fecha_original` (para medir el arrastre);
  - `veces_arrastrada`;
  - bloques de información elegidos (lista de bloques con su contenido).
- **Orden del Operario por jornada:** dónde guardarlo (colección propia `orden_jornada` o campo en la asignación). Decisión para `diseno-oo`.
- **Eventos inmutables** (H2): asignada, devuelta (con motivo), arrastrada, no realizada, cancelada (con motivo), pausada por hora fija.
  - Nada se borra (H3).
  - `_reemplazar_asignaciones` hoy borra y reinserta; hay que cambiarlo para no perder el historial.
- **Proyecto:** clase, repositorio, servicio y rutas nuevas. El Requerimiento se retira con migración de datos (cada requerimiento con una actividad pasa a actividad suelta; con varias, a proyecto).
- **Proceso de cierre de jornada:**
  - las actividades sin hora no finalizadas se arrastran;
  - las de hora fija no iniciadas pasan a No realizada.
  - Decidir cuándo corre: al marcar salida, a una hora fija o al consultar.

**Prompt:**
```
Etapa 4 del plan. Primero usa el agente diseno-oo: con la Sección 5 del alcance actualizada, propón el diagrama de
clases y los cambios a Actividad, EstadoActividad, Ejecucion y la nueva clase Proyecto, y resuelve la decisión
abierta H1 de CLAUDE.md. No escribas código hasta que yo apruebe el diseño. Después implementa por capas:
modelos, repositorios (agente persistencia-mongo), servicios y rutas (agente backend-flask), con pruebas.
```

---

## Etapa 5. Operario: ordenar el día, hora fija y devolver

Depende de la etapa 4.

- **Ordenar mi día** (maqueta 5):
  - modo aparte con "Listo" y "Volver al orden sugerido";
  - solo las actividades sin hora se arrastran;
  - candado y "Hora fija" en las fijas;
  - etiqueta ámbar "Viene de ayer" en las arrastradas;
  - "Sigue" en la primera del orden elegido.
- **Aviso cuando no alcanza** (maqueta 6, pantalla 1): ámbar, sin bloquear.
- **Llegada de la hora fija** (maqueta 6, pantalla 2):
  - aparece en "Ahora" con la anticipación de 1.1 bis (10 minutos);
  - botón "Pausar e iniciar…";
  - la actividad partida se dibuja como "Parte 1" y "Parte 2".
- **Detalle de la orden** (maqueta 4, pantalla 3):
  - una sola hoja con filas que se abren;
  - "En tu día" con la mini fila del tablero;
  - "Lista para iniciar";
  - **Iniciar** y **Devolver**.
- **Devolver** (maqueta 4, pantalla 4): hoja inferior con motivo y texto opcional. Dice qué pasa después.
- **Orden incompleta:** pantalla que falta diseñar. Cuando falta un bloque pedido, no aparece "Lista para iniciar" y "Devolver" pasa a ser la acción sugerida.
- **Fuera de turno:** pantalla que falta diseñar. Se ve el riel pasado de las 2:00 p. m. y el tiempo adicional.

Las dos pantallas que faltan se diseñan conmigo antes de esta etapa.

---

## Etapa 6. Administrador: tablero del turno y proyectos

- **Equipo** (maqueta 2):
  - tablero con una fila por persona, horas de 6:00 a 3:00 p. m. y la línea "Ahora";
  - lo que pasa del turno, rayado en coral suave;
  - aviso "Necesita ayuda" con **Reasignar**.
  - **Por atender:** devueltas (con motivo), sin asignar con **Asignar**, pendientes arrastradas y no realizadas.
- **Proyectos** (maqueta 3):
  - lista y detalle con avance en horas (1.1 bis);
  - tabla de actividades;
  - disponibilidad semanal por persona.
- **Nueva actividad:**
  - formulario con hora fija opcional;
  - proyecto opcional;
  - bloques de información seleccionables con catálogos desplegables y "Otro".
- **Cancelar:** diálogo con motivo.
- **Métricas:** arrastradas, no realizadas, devueltas y canceladas (5.2).

---

## Etapa 7. Validación y evidencias para el informe

1. `herramientas/contraste.py` sobre todos los colores usados.
2. `herramientas/capturas.py` de todas las pantallas (normal, desenfocada y grises) para la sección de Gestalt y jerarquía.
3. Agente `profesor-interfaces`: auditoría contra 6.1 a 6.5 y contra el enunciado de la Fase 2 (usabilidad, Gestalt, color y metáforas).
4. Opcional: el Prompt B de `prompt_validacion_diseno_gestlab.md` en otra IA con las capturas, actualizado con la metáfora del tablero en lugar del tanque.
5. Para el PDF, la evolución del diseño:
   - primera versión;
   - propuesta del tanque;
   - Stitch y su revisión crítica;
   - tablero del turno.
   Muestra el porqué de cada cambio.

---

## Pendientes abiertos

- Pptx de metáforas del profesor exportado a PDF o imágenes (6.5).
- H1: la ejecución pertenece a la actividad o a la asignación (etapa 4).
- Diseño de las pantallas "orden incompleta" y "fuera de turno" (etapa 5).
- Qué se adopta de Stitch (G). Ya están en las maquetas: Reasignar, Asignar, códigos OT y resumen de capacidad.
