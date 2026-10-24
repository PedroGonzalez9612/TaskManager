# Prompt para Google Stitch: rediseño del Operario de GestLab (v3)

## Cómo usarlo
1. Crea un proyecto NUEVO en Stitch (no uses el anterior: tiene mezcladas las versiones del tanque y la planta, y eso confunde al agente).
2. Modo App. Adjunta las 5 capturas de la app actual: 1_inicio, 2_hoy, 3_detalle_actividad, 4_semana, 5_resumen.
3. Pega la PARTE 1 sola. Espera a que Stitch responda con su dirección visual (sin pantallas).
4. Si la dirección te gusta, pega la PARTE 2. Si no, pídele "Propón otra dirección visual distinta".
5. Después pega la PARTE 3.

Dividirlo así evita que Stitch corte el prompt o ignore partes.

---

## PARTE 1 · Rol, producto, conceptos y dirección visual

```
ROL
Actúa como un diseñador senior de interfaces y producto, con más de 15 años diseñando herramientas de trabajo que la gente usa todo el día. Cada decisión visual tuya tiene una razón, y tus diseños se reconocen como de autor, no de plantilla. Eres el director de arte de este producto.

EL PRODUCTO
"GestLab" es una app web responsive para planificar y medir el trabajo de equipos de cualquier área (oficina, servicios, operación, proyectos). Un Administrador planifica actividades y proyectos, las asigna y ve la ocupación de cada persona. El Operario ve su día, ejecuta sus actividades y registra inicio, pausas y fin; así se mide cuánto tarda realmente cada tarea. NO es una app de mantenimiento ni de fábrica. Todo el texto de la interfaz en español. Es marca blanca: arriba se ve el logo y el nombre de la empresa del cliente.

EL USUARIO DEL OPERARIO
Carlos, 34 años, usa solo el celular en su jornada. Hallazgo de su mapa de empatía: no necesita más control, necesita evidencia y contexto. Quiere demostrar lo que hizo y no perder el hilo cuando una tarea se interrumpe.

LA SENSACIÓN
Calma, organización, claridad, planificación. Lo contrario de trabajar bajo presión. Moderno, profesional y con personalidad, pero simple y fácil de usar. Nada rimbombante. El estilo sale de la precisión (tipografía, alineación, ritmo, proporción), no de efectos.

PRINCIPIOS
1. Calma antes que urgencia: base neutra, un solo color de marca; el color de estado solo cuando significa algo. Rojo solo para urgente o sobrecarga.
2. Claro a primera vista: cada pantalla responde una pregunta y tiene UNA acción principal.
3. El tiempo es la estructura: la línea de tiempo del día es la firma visual del producto. La personalidad va ahí, no en adornos.
4. Simple de usar, cuidado en el detalle.

CONCEPTOS DE DISEÑO QUE DEBES APLICAR Y QUE SE DEBEN NOTAR
- Metáfora central: la línea de tiempo del día (versión vertical del tablero de planificación que ve el Administrador). Dale una forma propia y memorable: riel, nodos, línea "Ahora", diferencia entre tiempo recorrido y por venir.
- Gestalt: proximidad (hora, nombre y estado juntos), continuidad (el riel se lee como una sola línea), semejanza (mismo estado, misma apariencia), figura-fondo (la actividad en curso destaca sin caja pesada), cierre (una actividad pausada y retomada se percibe como una sola).
- Jerarquía visual: un solo punto focal por pantalla; jerarquía por tamaño, peso y espacio antes que por color.
- Leyes de UX: Fitts (acción principal grande y abajo, al alcance del pulgar; filas completas tocables), Hick (pocas opciones por pantalla), Miller (información en bloques cortos), Jakob (patrones conocidos: hoja inferior, barra de pestañas, volver arriba a la izquierda), Von Restorff (solo lo urgente rompe el patrón).
- Heurísticas de Nielsen: visibilidad del estado del sistema (siempre se sabe qué corre y que se está registrando), correspondencia con el mundo real (lenguaje cotidiano), prevención de errores, reconocer antes que recordar (historial visible), diseño estético y minimalista.
- Teoría del color: paleta casi neutra, un color de marca, estados con significado constante. El color nunca va solo: siempre con texto o ícono.
- Tipografía: una sola familia con carácter, escala clara (por ejemplo 13/15/17/22/28), solo dos pesos, cifras tabulares en horas y tiempos.
- Iconografía: un solo set, mismo grosor de trazo en todas las pantallas.
- Consistencia: retícula de 8 px, mismos radios y componentes en todas las pantallas.
- Accesibilidad WCAG 2.1 AA: texto 4,5:1, controles 3:1, zonas táctiles de 48 px o más, texto de lectura de 16 px o más y nunca menos de 13 px.

QUE NO SE VEA HECHO POR IA (prohibido)
- El kit SaaS genérico: todo en tarjetas redondeadas idénticas con la misma sombra gris.
- Degradados decorativos, brillos, glassmorphism, ilustraciones 3D, emojis, mascotas.
- Tarjetas con franja de color a la izquierda.
- Etiquetas pequeñas en MAYÚSCULAS espaciadas encima de cada sección.
- Textos separados con puntos medios en todas partes ("A · B · C").
- Resaltar una sola palabra del título con otro color.
- Fuentes por defecto: Inter, Roboto, Figtree, Manrope, Geist, Poppins.
- Iconos de distintos estilos, o logo distinto en cada pantalla.
- Cronómetros grandes de segundos, anillos de progreso y gráficas decorativas.
- Funciones inventadas: chat, telemetría, gamificación, puntos, mapas, manuales, notificaciones push.
- Barras de estado del teléfono simuladas.
- Lenguaje de fábrica: órdenes de trabajo, códigos OT, maquinaria, cascos.
Si una decisión es la que tomaría cualquier plantilla, cámbiala por una que solo tenga sentido en GestLab.

PALETA BASE (afina tonos si lo justificas; conserva roles y contraste)
Fondo #F5F6F8, superficie #FFFFFF, bordes #D9DDE3. Texto #1B2230, secundario #566070. Marca y acción principal: azul profundo #2B5B84. Estados (texto / fondo): Finalizada #25704A / #E6F4EC; En pausa #8A5300 / #FFF3DD; Urgente #B42318 / #FDECEA.

TE ADJUNTO 5 CAPTURAS DE LA APP ACTUAL
Muestran qué hace hoy la app y qué información tiene cada pantalla. Su diseño visual NO me gusta: se ve plano, genérico y sin personalidad. Úsalas solo como inventario funcional, no como referencia de estilo.

ENTREGA DE ESTA PARTE (todavía sin pantallas)
En pocas líneas: tu concepto visual para GestLab, la tipografía que eliges y por qué, cómo se ve la línea de tiempo y qué la hace propia, y cómo aplicarás los conceptos de arriba.
```

---

## PARTE 2 · Pantallas principales del Operario (celular, 390 px)

```
Con la dirección visual que propusiste, diseña estas pantallas del Operario en celular (390 px). Mismo sistema en todas. Barra inferior en todas: Inicio, Hoy, Semana, Resumen. Arriba: logo y nombre de la empresa cliente (ejemplo: "Café La Montaña"), avatar con iniciales y salir.

1. INICIO, antes de marcar la entrada
- Fecha y saludo ("Buenas tardes, Daniela").
- Hora actual y "Tu turno empieza a las 19:00".
- Barra del turno (19:00 a 23:00) con las actividades programadas a escala.
- "1 h 35 min de 4 h programadas" con trabajado, por hacer y libre.
- "0 de 3 actividades finalizadas".
- Lo que sigue: la próxima actividad con su prioridad, tocable.
- Acción principal: "Marcar entrada". Enlace secundario: "Ver mi día sin marcar la entrada".

2. INICIO, en turno
- Igual, pero con la actividad en curso resumida y la acción "Marcar salida" como secundaria. Si hay una actividad en curso, no se puede marcar salida: hay que pausarla o finalizarla.

3. HOY, línea de tiempo del día
- Resumen corto del día arriba (trabajo y tiempo libre).
- Si no ha marcado la entrada: aviso tranquilo "Estás viendo tu día. Para iniciar actividades, marca la entrada en Inicio".
- Línea de tiempo vertical: inicio del turno, línea "Ahora", una fila por actividad con hora (aproximada con "~" si es de horario flexible, exacta si es de hora fija), nombre, duración, prioridad, categoría con ícono y estado. Huecos libres como línea discreta "Libre, 1 h 20 min". Al final, "Fin del turno".
- Marcas especiales: "Siguiente" en la próxima; "Hora fija" con candado en las que no se mueven; "Retraso: 7 días" en las reprogramadas de días anteriores.
- La actividad en curso muestra "En curso" y "1 h 24 min de 2 h", sin cronómetro y sin botones.
- Toda la fila abre el detalle.
- Acción secundaria discreta: "Reportar actividad" (algo que le pidió otra área).
- Acción secundaria: "Ordenar mi día".

4. DETALLE, antes de iniciar (pantalla completa u hoja grande)
- Volver. Código corto, prioridad, estado, categoría.
- Nombre de la actividad.
- Datos: ubicación, programada (día, hora fija u horario flexible), tiempo estimado, asignada a, proyecto o "Actividad independiente".
- Descripción.
- "Para hacer el trabajo", en bloques que se abren: pasos, herramientas y materiales, equipo, precauciones, contacto, adjuntos. Solo aparecen los bloques que tiene la actividad.
- Aviso "Lista para iniciar" cuando tiene todo lo necesario.
- Acción principal: "Iniciar actividad". Secundaria: "Devolver" (solo antes de iniciar).

5. DETALLE, en curso
- Indicador tranquilo "Registrando tiempo", tiempo en horas y minutos contra el estimado, lo que queda, barra de avance.
- Historial: iniciada, cada pausa con motivo y duración, reanudada.
- La información de la actividad sigue disponible debajo.
- Acciones: "Pausar" (secundaria) y "Finalizar" (principal).

Mantén todas las reglas de la Parte 1. Contenido realista y consistente entre pantallas.
```

---

## PARTE 3 · Momentos del flujo y pantallas de apoyo

```
Mismo sistema visual y mismas reglas. Diseña estos momentos del Operario en celular:

6. PAUSAR: hoja inferior que pide el motivo (Atender otra actividad, Reunión o llamada, Falta información, Descanso, Fin de jornada, Otro con texto). Acción: "Pausar actividad".

7. FINALIZAR: hoja inferior con resumen (tiempo real vs. estimado, número de pausas) y evidencia opcional: observación, fotos y adjuntos (hasta 5). Acción: "Finalizar actividad".

8. LLEGA UNA URGENTE: en Hoy aparece en la línea "Ahora" como el único elemento rojo, con la acción "Pausar y atender". La actividad en curso se compacta y dice que quedará en pausa.

9. AVISO DE HORA FIJA: 10 minutos antes de una actividad de hora fija, aviso tranquilo en Hoy con la acción "Pausar e iniciar [nombre]". La actividad interrumpida se verá después como Parte 1 y Parte 2 de la misma.

10. DEVOLVER: hoja inferior con motivo (Falta información, Me la asignaron por error, Falta herramienta o material, El equipo no está disponible, Otro con texto) y una línea que explica qué pasa después.

11. ORDENAR MI DÍA: modo de edición donde solo las actividades de horario flexible se arrastran; las de hora fija (candado) y las urgentes no se mueven. Acciones: "Listo" y "Volver al orden sugerido". Si el orden no alcanza antes de una hora fija, aviso ámbar que no bloquea.

12. MARCAR SALIDA Y CIERRE DE JORNADA: resumen del día (trabajado, finalizadas, pendientes que pasan a mañana) y acción "Marcar salida".

13. SEMANA: horario de la semana con vistas Día, Semana y Lista; las actividades de horario flexible en una franja "Flexible" arriba y las de hora fija en su hora. Leyenda de colores discreta.

14. RESUMEN: semana con navegación; actividades y finalizadas, tiempo programado contra jornada, día de mayor carga, gráfica de tiempo programado por día con la línea de la jornada, distribución por estado y por categoría. Sin gráficas decorativas.
```

---

## Después de Stitch: revisión obligatoria
- Medir el contraste real de cada color de texto con `herramientas/contraste.py`.
- Revisar tamaños mínimos de texto y botones.
- Buscar funciones inventadas o lenguaje de fábrica.
- Revisar que logo, íconos y colores de estado sean iguales en todas las pantallas.
- Comparar los tokens del DESIGN.md con lo que muestran las pantallas.
- Repasar la lista "Que no se vea hecho por IA" punto por punto.
