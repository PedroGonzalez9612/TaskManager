# Prompts para validar el diseño de GestLab (Fase 2 — Diseño de Interfaces)

> **Origen de las reglas:** este archivo copia criterios de `docs/alcance_proyecto.md` (Secciones 6.1 a 6.4) y del
> enunciado de la Fase 2, porque las herramientas externas no pueden leer el repositorio. Es una copia derivada:
> si el alcance cambia, este archivo se actualiza. Ante cualquier diferencia, manda el alcance.
>
> **Valores en evaluación:** las maquetas usan Figtree y fondo gris neutro `#F4F6F5`. El alcance aprobado dice
> Lexend y fondo aqua `#EEF5F4`. Ese cambio está pendiente de decisión; los prompts evalúan la propuesta.

## Cómo usarlos

**Capturas que se adjuntan:**
- `operario_hoy_3_estados.png`: pantalla "Hoy" del Operario en celular, en tres estados (normal, urgente pendiente y fuera de turno).
- `calma_operativa_v2.png`: "Hoy" del Operario y "Equipo" del Administrador en escritorio.

**Prompt A, en Google Stitch.**
- Usa el **modo Experimental**: es el único que acepta imágenes.
- Adjunta las dos capturas y pega el prompt.
- Stitch no audita, genera. Compara su versión con la tuya: lo que cambie sin violar las restricciones es lo que considera mejorable.
- Refina con instrucciones cortas, sin empezar de nuevo.

**Prompt B, en un chat con imágenes** (Gemini, ChatGPT o Claude).
- Adjunta las mismas capturas y pega el prompt.
- Devuelve un informe de hallazgos con severidad y evidencias para el documento.

---

## Prompt A — Google Stitch (rediseño restringido para validar)

```
Eres diseñador de producto senior. Te adjunto dos capturas de GestLab, una aplicación web responsive para gestionar y analizar la carga laboral de operarios en plantas industriales (Colombia, interfaz en español). Quiero validar y refinar este diseño: genera una versión mejorada de las MISMAS pantallas que cumpla todas las restricciones de abajo. No cambies el concepto; mejora la ejecución.

CONTEXTO Y USUARIOS
- Operario (celular, de pie en planta, uso durante toda la jornada): ve qué hacer ahora, qué sigue y registra su trabajo. Persona de referencia: Carlos, 34 años, técnico de línea de producción, turno rotativo, solo usa celular. Su necesidad central no es más control, sino evidencia y contexto: demostrar lo que hizo y no perder el hilo cuando lo interrumpe algo más urgente.
- Administrador (escritorio): ve la carga de cada operario del día y reparte el trabajo.
- Público diverso: personas jóvenes y mayores (vista cansada), de todo género y nivel tecnológico.

SENSACIÓN BUSCADA
Calma, orden y confianza. Debe ser amigable, no generar ansiedad, verse pensado y profesional, y ser original, no una plantilla genérica de SaaS. Evita: tarjetas idénticas por todas partes, franjas de color a la izquierda, rojo en todo lo importante, degradados decorativos, etiquetas en mayúsculas y exceso de negrita.

PANTALLAS A RESOLVER
1. "Hoy" del Operario (celular, 390 px), en tres estados:
   a) Normal, en turno.
   b) Llega una actividad urgente mientras trabaja en otra.
   c) Fuera de turno (tiempo adicional).
   Orden de arriba hacia abajo: barra de turno ("En turno" o "Fuera de turno", con la acción Marcar entrada o Marcar salida) → aviso de urgente, solo si existe → "Ahora": actividad en curso con cronómetro, avance, acceso al historial de pausas, Pausar (secundario) y Finalizar (principal) → "Siguientes": ordenadas por prioridad y, dentro de cada prioridad, por hora, con marca discreta cuando una prioridad cambió ("Subió a Alta a las 9:40") → carga del día, pequeña → botón secundario "Reportar actividad" → barra inferior Hoy / Semana / Resumen.
2. "Equipo" del Administrador (escritorio, 1440 px): una columna por operario con su "tanque" de carga del día, qué está haciendo ahora, horas libres y un aviso calmado si se pasa de su turno ("Necesita ayuda"). Panel lateral con la jornada de la persona seleccionada y la lista "Sin asignar". Un solo botón principal: "Nueva actividad".

METÁFORAS (obligatorias, mantenlas visibles)
- Central: el tanque. La jornada de cada persona es un recipiente que se llena hasta una línea de capacidad; lo que rebosa es sobrecarga. El logo es ese mismo tanque.
- De apoyo: el reloj de marcar tarjeta (barra de turno), el cronómetro de taller (actividad en curso), la señalización de seguridad de planta (colores de estado) e íconos simples y lineales (pausa, check, reloj, historial).

COLOR (respeta los HEX y su único significado)
- Fondo #F4F6F5. Superficies #FFFFFF. Texto #1F2A2E. Texto secundario #5B6664 (no más claro que #66716E).
- Principal (acciones y actividad en curso) #16697A; presionado #0F5563.
- Acento de marca coral #E9806E: solo logo, avatar y sobrecarga suave. Nunca en texto ni en botones.
- Urgente y error #A8322A (texto #8A2620): el único color lleno de la pantalla, y solo para lo urgente.
- Prioridad Alta, texto #8A3D08. Advertencia, Media, pausa y cambio de prioridad: #E3A32B con fondo #FBF1D9 y texto #6B4A0E.
- Confirmación, finalizada y en turno: #3E7B3A con fondo #E6F0E2 y texto #2F5F2C.
- Información #2F5DA8, solo como fondo suave con ícono "i".
- Lo normal (prioridad Baja, pendiente) va en gris, sin color.
- Todo estado se comunica con color, ícono y texto, nunca solo con color.

TIPOGRAFÍA
- Figtree para el texto. Atkinson Hyperlegible Mono solo para códigos de actividad (OT-0001).
- Cifras con números de ancho fijo.
- Celular: texto de al menos 16 px y títulos de 20 a 22 px.
- Escritorio: texto de 14 a 16 px.
- Ningún texto por debajo de 13 px. Solo dos pesos: regular y semibold. Alineado a la izquierda.

ACCESIBILIDAD Y USABILIDAD
- Contraste WCAG 2.1 AA: al menos 4,5:1 en texto y 3:1 en bordes de controles.
- Botones del Operario de al menos 48 px de alto, al alcance del pulgar.
- Un solo botón principal por pantalla o estado.
- Retroalimentación visible en cada acción. Mensajes en lenguaje claro que dicen qué pasa y qué hacer, sin alarmar.
- Separación por espacio y sombras muy suaves en lugar de bordes y líneas. Una escala de espaciado de 4, 8, 12, 16, 24, 32 y 48 px.

QUÉ NO DEBES CAMBIAR
El tanque como metáfora central, el orden por prioridad, el único bloque de color lleno para lo urgente, el significado de cada color y los textos de las acciones (Pausar, Finalizar, Marcar entrada, Marcar salida, Reportar actividad, Nueva actividad).

ENTREGA
Genera las 3 variantes de "Hoy" del Operario y la pantalla "Equipo", con el mismo sistema visual en todas. Usa datos realistas de una planta de lácteos colombiana.
```

---

## Prompt B — Auditoría (chat con imágenes)

```
Actúa como evaluador experto en diseño de interfaces y usabilidad. Te adjunto capturas de GestLab, aplicación web responsive para gestionar la carga laboral de operarios en plantas industriales. Evalúa el diseño contra TODOS los criterios de abajo y entrega un informe. No rediseñes; evalúa y propone correcciones concretas.

CONTEXTO
[Pega aquí la sección "CONTEXTO Y USUARIOS" del Prompt A.]

CRITERIOS A EVALUAR

1. Necesidades del Operario. Para cada una, indica si la pantalla la cubre, la cubre en parte o no la cubre, y dónde:
   - Ver sus actividades ordenadas por prioridad.
   - Notar cuándo cambió una prioridad durante el turno.
   - Iniciar, pausar, reanudar y finalizar rápido.
   - Ver el historial de pausas de la actividad en curso.
   - Registrar el motivo al pausar y una observación al finalizar.
   - Reportar una actividad solicitada por otra área.
   - Ver un aviso claro de actividad urgente pendiente, en la pantalla principal y en la de ejecución.
   - Saber si está en turno o fuera de turno, con color y texto.
   - Marcar entrada y salida.
   - Ver la carga del día.

2. Principios de usabilidad (enunciado de la Fase 2):
   - Visibilidad y claridad de las opciones.
   - Consistencia de componentes, estilos y comportamientos.
   - Retroalimentación ante las acciones.
   - Prevención y manejo de errores.
   - Facilidad de aprendizaje.
   - Claridad de navegación y estructura.
   - Jerarquía visual entre acciones principales y secundarias.

3. Leyes de UX: Hick, Fitts, Jakob, Miller, Proximidad y efecto estético-usabilidad. Y las heurísticas de Nielsen que apliquen.

4. Gestalt:
   - Proximidad, semejanza, continuidad, cierre y figura-fondo.
   - Indica dónde se evidencia cada una y dónde falla.

5. Teoría del color:
   - Paleta principal y secundaria.
   - Color de las acciones principales.
   - Colores de estados, alertas, errores, confirmaciones e información.
   - Contraste entre texto, componentes y fondos.
   - Justificación funcional, no estética.
   - Consistencia entre pantallas.
   Usa los HEX y significados de la sección "COLOR" del Prompt A [pégala aquí]. Señala cualquier color que se use con un significado distinto al asignado.

6. Metáforas:
   - Metáfora central: el tanque de carga, con la capacidad como línea y la sobrecarga como rebose. El logo es el tanque.
   - Metáforas de apoyo: reloj de marcar tarjeta, cronómetro, señalización de seguridad e íconos.
   Evalúa en cada una:
   - Si sale del mundo del usuario.
   - Si es coherente con las demás.
   - Si se entiende sin explicación.
   - Cuáles son sus límites, es decir, qué no comunica y cómo se compensa.

7. Tipografía:
   - Legibilidad para personas mayores: tamaños mínimos, pesos y contraste.
   - Jerarquía y uso correcto de la monoespaciada (solo códigos).

8. Accesibilidad (WCAG 2.1 AA):
   - Contraste de 4,5:1 en texto y 3:1 en componentes.
   - Objetivos táctiles de 44 a 48 px o más.
   - Información que no depende solo del color.

9. Respuesta emocional:
   - ¿Transmite calma o ansiedad? Señala los elementos concretos que generan tensión.
   - ¿Se ve original o genérico? Señala los recursos que lo hacen ver como plantilla.

FORMATO DEL INFORME
A. Resumen de 3 líneas con el estado general.
B. Tabla de cumplimiento por bloque (1 a 9): Cumple / Parcial / No cumple, con una línea de motivo.
C. Hallazgos ordenados por severidad (Crítico, Mayor, Menor). Cada uno con: criterio incumplido, pantalla y zona, problema, por qué afecta al usuario y corrección propuesta.
D. Evidencias para el documento: dónde el diseño sí aplica bien cada principio, ley de Gestalt, decisión de color y metáfora. Indica la captura, la zona y por qué es una buena aplicación.
E. Lo que no se puede evaluar con capturas estáticas (interacción, retroalimentación, diálogos) y cómo verificarlo.
```
