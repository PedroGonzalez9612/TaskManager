# Plan: rediseño del Operario v3 ("planificador sereno")

- **Fecha:** 23 de octubre de 2026
- **Materia:** Diseño de Interfaces (Fase 2: usabilidad, Gestalt, color y metáforas). La Etapa 4 puede tocar `programacion_dia.py`, que también interesa a DOO.
- **Reemplaza:** las partes visuales del plan "Calma operativa" (`docs/plan_rediseno_calma_operativa.md`) que choquen con este. Las reglas de negocio de ese plan (hora fija, orden del día, reprogramación, devolver, proyectos) se mantienen.
- **Referencias de diseño:**
  - `docs/disenos/operario_v3/`: el diseño final. PNG de cada pantalla y su fuente `.dc.html` (se abre en el navegador como referencia de medidas y colores).
  - `docs/disenos/stitch_v2/`: lo que generó Google Stitch y que se tomó como dirección. Es la evidencia del proceso para el informe.
  - Las pantallas de `operario_v3` mandan sobre las de Stitch cuando no coinciden.

---

## Decisiones ya tomadas (no se discuten, se aplican)

1. **Producto:** planificador de trabajo para equipos de cualquier área, no solo planta. Sin lenguaje industrial en la interfaz (ni "orden de trabajo", ni "lote" como término del sistema, ni referencias a planta en las metáforas).
2. **Inicio responde "¿qué hago ahora?":** saludo, estado del turno, lo que sigue o la actividad en curso, y una sola acción principal. **Ya no muestra la barra del turno ni la barra de la jornada:** eso vive en Hoy.
3. **Hoy es una línea de tiempo de solo lectura:** sin cronómetro y sin botones de ejecución. La fila de la actividad en curso dice "En curso, 16 min de 40". Toda fila abre el detalle.
4. **El detalle es donde se ejecuta:** iniciar, pausar, finalizar y devolver se hacen en el detalle de la actividad. En curso muestra "Registrando tiempo", el tiempo en minutos contra lo estimado, una barra de avance y el registro de pausas con su motivo.
5. **Tiempo en horas y minutos.** Nada de segundos corriendo en la pantalla del Operario (el tiempo exacto lo sigue guardando el servidor).
6. **Estilo:** separación por espacio y líneas finas. La superficie blanca con borde solo donde agrupa algo de verdad. Sin sombras en cada elemento, sin mayúsculas sostenidas, sin puntos medios, sin franjas de color a la izquierda.
7. **Etiquetas solo para excepciones:** Urgente, Hora fija, Retraso. La categoría y la prioridad Media o Baja van como texto (la Media con su ícono ámbar, para cumplir la regla 1 de la 6.3). En el alcance se extendió a la Alta (texto con su ícono naranja) y la Baja lleva su guion, por la misma regla.
8. **Paleta:** principal azul profundo `#2B5B84` en lugar del aqua `#16697A`.
9. **Tipografía:** Hanken Grotesk 400 y 600 en lugar de Figtree. Una sola familia, cifras con `tabular-nums`.

## Valores del sistema (para la 6.3, la 6.4 y `:root`)

| Token | Valor | Contraste medido |
|---|---|---|
| `--fondo` | `#F5F6F8` | — |
| `--superficie` | `#FFFFFF` | — |
| `--texto` | `#1B2230` | 14,7:1 sobre el fondo |
| `--texto-secundario` | `#566070` | 5,9:1 sobre el fondo, 6,4:1 sobre blanco |
| `--principal` | `#2B5B84` | 7,2:1 sobre blanco (y blanco sobre él) |
| `--principal-hover` | `#22496B` | — |
| `--principal-suave` | `#E8EEF4` | principal sobre él 6,1:1 |
| `--borde` | `#E1E5EA` | decorativo |
| `--borde-control` | `#7F8A99` | 3,5:1 sobre blanco, 3,2:1 sobre el fondo |
| Finalizada / en turno | texto `#25704A`, fondo `#E6F4EC` | 5,3:1 |
| Pausa / retraso / advertencia | texto `#8A5300`, fondo `#FFF3DD` | 5,8:1 |
| Urgente / error | texto `#B42318`, fondo `#FDECEA`; relleno `#B42318` con texto blanco | 5,8:1 y 6,6:1 |

Tamaños en celular: título de pantalla 28 px, nombre de actividad en el detalle 26 px, nombre en la fila 17 px, texto 16 px, secundario 14–15 px, etiquetas 13 px (mínimo). Botón principal de 52 px de alto; toda zona tocable de 44 px o más.

## Decisiones que hay que confirmar con el usuario ANTES de la Etapa 1

Pregúntalas juntas, con tu recomendación, y espera la respuesta:

1. **Color de información:** el azul de información `#2F5DA8` queda casi igual al nuevo principal y rompe la regla "un color, un significado". Recomendado: los avisos de información pasan a gris neutro con su ícono "i", sin color propio.
2. **Coral de marca:** ya no se usa. ¿Qué marca la sobrecarga (lo que pasa de la hora de fin)? Recomendado: rayado en el rojo suave de alerta (`#FDECEA` con franjas `#B42318` al 25 %), con su texto. ¿Y el logo de GestLab? Recomendado: las mismas tres barras con la barra vertical en `--principal`.
3. **Código de la actividad:** el glosario dice `OT-0042` ("orden de trabajo"). Recomendado: `ACT-0042`, solo cambio de prefijo en la presentación, sin migrar datos si es posible.
4. **Detalle en celular:** el diseño lo muestra a pantalla completa con "Hoy" para volver. Hoy es un `<dialog>` compartido con el Administrador. Recomendado: mantener el `<dialog>`, pero en celular a pantalla completa, con las acciones fijas abajo.
5. **"Marcar salida":** la 6.1 la pone al final de Hoy y en Inicio. Recomendado: solo en Inicio, para no repetir.

**Respuestas del usuario (23 de octubre de 2026):**
1. Información en gris neutro con su ícono "i", sin color propio.
2. Sobrecarga rayada en el rojo suave de alerta, con su texto; logo con las tres barras y la barra vertical en `--principal`.
3. `ACT-` solo en las actividades nuevas: las que ya existen conservan `OT-` (sin migración).
4. Detalle en `<dialog>`, a pantalla completa en celular, con "Hoy" para volver y las acciones fijas abajo.
5. "Marcar salida" solo en Inicio.

---

## Etapas

Trabaja una etapa por vez. En cada una: propón el cambio, muestra el diff, espera aprobación, verifica y haz commit. Si algo contradice el alcance, detente y avísame.

### Etapa 0. Rama
- `git checkout -b feature/rediseno-operario-v3` desde `feature/avance-doo-momento-2-2026-10-17` (hecho el 23 de octubre). No sale de `develop` porque `develop` solo tiene el proyecto base y le faltan las Etapas 4 y 5 y el Inicio del Operario.
- Confirma que `docs/disenos/operario_v3/`, `docs/disenos/stitch_v2/` y este plan están en la rama.

### Etapa 1. Alcance (solo documentos)
Con las respuestas de las decisiones a confirmar, actualiza sección por sección, mostrando texto actual, texto propuesto y motivo:
- **6.1:** persona con un perfil menos industrial (o una segunda persona de oficina); pantallas mínimas 2 (Inicio), 3 (Hoy sin cronómetro ni ejecución) y 4 (Detalle: iniciar, pausar, finalizar, devolver; registro de pausas). Necesidades: cambiar "con cronómetro" por "tiempo en minutos contra lo estimado".
- **6.2:** fila del Operario en la tabla de vistas; el detalle a pantalla completa en celular; "Paneles con jerarquía" y "Bordes suaves y sombras" por la nueva regla de estilo (espacio y líneas finas; superficie solo para agrupar); Gestalt figura-fondo y cierre con la nueva línea de tiempo.
- **6.3:** fundamentos (quitar el argumento del aqua de Kwallek y el de "señalización de planta"; justificar el azul por calma y confianza), armonía y 60-30-10 con el nuevo principal, tabla de base con los valores de arriba, coral según la decisión 2, información según la decisión 1, conflictos de color actualizados, logo.
- **6.4:** Hanken Grotesk en lugar de Figtree, tabla de tamaños de arriba, quitar la fila y la regla del cronómetro, quitar "la planta puede no tener conexión".
- **6.5:** metáfora central "la planilla del turno" justificada desde la planificación de equipos en cualquier área; el reproductor (iniciar, pausar, finalizar) pasa al detalle; la fila del cronómetro se reemplaza por "barra de avance contra lo estimado"; franjas de "zona restringida" según la decisión 2; actualizar "Qué metáforas se ven hoy".
- **14:** Actividad (código), Inicio, Tarjeta (ahora "fila" en la línea de tiempo), Jornada (quitar "mientras no existan los turnos"), y agregar "Lo que sigue" y "Registro de ejecución" si se usan en pantalla.
- **Bitácora:** una entrada con fecha, secciones y motivo; copia el texto viejo en "Texto original".
- Después: `CLAUDE.md` (estado del rediseño, fuente, reglas de interfaz) y `.claude/agents/profesor-interfaces.md` y `frontend-web.md` si nombran Figtree, aqua o cronómetro.
- Verificación: el agente `profesor-interfaces` lee 6.1 a 6.5 y 14 y reporta contradicciones.

### Etapa 2. Base visual
- `app/static/css/estilos.css`, solo `:root` y las reglas con valores sueltos: los tokens de la tabla. Mide cada color con `python herramientas/contraste.py` antes de escribirlo.
- `app/static/fuentes/`: agrega `hanken-grotesk-400.woff2`, `hanken-grotesk-600.woff2` y su licencia OFL (descárgalos de Google Fonts o de `@fontsource/hanken-grotesk`); cambia los `@font-face` y `--fuente-texto`. Quita Figtree, Bricolage y Atkinson si ya nada los usa.
- Logo y `favicon.svg` según la decisión 2.
- Ojo: los tokens son globales y también cambian Administrador y Superadmin. Corre `python herramientas/capturas.py` para los tres roles y revisa que nada quede ilegible.

### Etapa 3. Inicio (`operario/inicio.html`, `inicio.js`, `operario-comun.js`)
Referencia: `1_inicio_antes.png` y `2_inicio_en_turno.png`.
- Antes de la entrada: fecha, saludo, "Tu turno empieza a las 19:00, en 1 h 20 min", "Lo que sigue" (toda la fila abre el detalle, el texto pasa a otra línea en vez de cortarse), cuántas actividades y cuánto tiempo, "Marcar entrada" (principal, abajo) y "Ver mi día sin marcar la entrada" (enlace de 48 px de alto).
- En turno: "En turno hasta las 23:00" (punto verde más texto), bloque "Ahora" con la actividad en curso (nombre, "Desde las 19:05", "16 min de 40 estimados", barra, "Quedan unos 24 min"), la siguiente de hora fija en una línea, "Abrir actividad" (principal, sin ícono de reproducir) y "Marcar salida" desactivado con el motivo una sola vez.
- Sin actividad en curso: el bloque muestra lo que sigue con su acción.
- Quita la barra del turno y la de la jornada de Inicio. Conserva los avisos del turno (15 minutos antes, llegada tarde) como una línea con ícono.
- Después de la salida: el cierre de la jornada, con el mismo estilo (frases, sin tarjetas por número).

### Etapa 4. Hoy (`operario/index.html`, `hoy.js`)
Referencia: `3_hoy.png`.
- **Primero el error de orden:** hoy, si el turno no ha empezado, las actividades de horario flexible aparecen a la hora actual (por ejemplo, "~17:41") debajo de "19:00 Inicio del turno". La línea de tiempo debe ser cronológica: si el turno no ha empezado, la programación proyectada arranca en el inicio del turno. Busca dónde se calcula (`app/services/programacion_dia.py` o `hoy.js`), escribe primero la prueba que lo reproduce y luego corrige.
- Encabezado: fecha, "Tu día", "2 h 05 min de trabajo y 1 h 55 min disponibles", barra (trabajo en principal, disponible en blanco con borde de control) y "Turno de 19:00 a 23:00". Sin saludo.
- Riel: sólido en `--principal` hasta "Ahora", punteado en `--borde-control` después. Nodos llenos en lo hecho, anillo grueso en la actividad en curso, nodos abiertos en lo que viene. Línea "Ahora" con la hora a la izquierda.
- Filas en vez de tarjetas: hora (exacta y en semibold si es de hora fija; "~" y gris secundario si es de horario flexible), nombre, una línea de datos como frase y la flecha. La actividad en curso es la única fila con fondo `--principal-suave`.
- "Ordenar mi día" justo después de la línea "Ahora" (6.1). Intervalos disponibles como una línea de texto ("Disponible, 7 min").
- Sin cronómetro y sin botones de iniciar, pausar o finalizar. "Reportar actividad" como botón secundario al final.
- Urgente: sigue siendo el único bloque rojo lleno, sobre la línea "Ahora", con la acción de abrir el detalle para pausar y atenderla.

### Etapa 5. Detalle de actividad (`js/actividades-comun.js`, `hoy.js`)
Referencias: `4_detalle_antes.png`, `5_detalle_en_curso.png`, `6_pausar.png`, `7_finalizar.png`.
- En celular, el `<dialog>` del detalle ocupa toda la pantalla, con "Hoy" para volver arriba y las acciones fijas abajo (según la decisión 4).
- Título = nombre de la actividad; el código, pequeño y secundario, arriba a la derecha.
- Antes de iniciar: estado y excepciones, nombre, descripción, datos en lista (hora, estimado, prioridad, categoría, ubicación, proyecto, asignada por), "Lista para iniciar" como una línea con ícono, pasos, herramientas y materiales, precaución (siempre el mismo componente: fondo ámbar suave, ícono de advertencia, sin franja), contacto con "Llamar". Acciones: "Iniciar actividad" (principal) y "Devolver actividad" (botón terciario de 44 px).
- En curso: "Registrando tiempo", minutos contra lo estimado con barra, "Desde las 19:05. Quedan unos 24 min", registro de pausas (reusa `crearRegistroEjecucion`), precaución y pasos. Acciones: "Pausar" (secundario) y "Finalizar" (principal).
- Pausar: hoja inferior con los motivos de la empresa como opciones de radio de 52 px, "Otro motivo" con texto, "Pausar actividad" arriba y "Cancelar" debajo.
- Finalizar: hoja inferior con trabajados, estimados y pausas, "Observación (opcional)", "Agregar fotos o archivos" (hasta 5 de 5 MB) y "Finalizar actividad".
- El Administrador sigue viendo el mismo detalle con "Editar"; revisa que no se rompa.

### Etapa 6. Semana y Resumen
- Alinea colores y tipografía con los nuevos tokens. En Semana, renombra el botón "Hoy" del calendario a "Volver a hoy" y dale `aria-label` a los botones anterior y siguiente de EventCalendar ("Día anterior", "Día siguiente").
- En Resumen: los indicadores en una franja con frases ("23 % de la jornada"), sin una tarjeta por número; `aria-label` en la gráfica.

### Etapa 7. Validación y evidencias
1. `python herramientas/contraste.py` sobre todos los colores usados.
2. `python herramientas/capturas.py` de todas las pantallas (normal, desenfocada y grises).
3. Agente `profesor-interfaces`: auditoría contra 6.1 a 6.5, el glosario y el enunciado de la Fase 2.
4. `python -m pytest` y la puerta de SonarQube si cambiaron Python o la lógica de JS.
5. Actualiza `docs/avance.md` y el estado del rediseño en `CLAUDE.md`.
6. Para el informe: la evolución (primera versión, tanque, Calma operativa, Stitch v2 y su revisión, v3 final) con el porqué de cada cambio.

## Checklist de "no se ve hecho por IA" (revisar en cada pantalla)
- [ ] Sin mayúsculas sostenidas en etiquetas ni fechas.
- [ ] Sin puntos medios como separador.
- [ ] Sin tarjetas con sombra en cada elemento; sin franjas de color a la izquierda.
- [ ] Un solo botón principal.
- [ ] Ningún texto cortado con "…" en datos importantes.
- [ ] Todo texto con 4,5:1 o más; controles con 3:1 o más.
- [ ] Ningún término de fábrica en la interfaz.
