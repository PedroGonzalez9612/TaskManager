# Resultado de Google Stitch: "Calma Operativa" (GestLab)

- **Fecha:** 9 de octubre de 2026
- **Proyecto en Stitch:** https://stitch.withgoogle.com/projects/12958732149388753685 (requiere la cuenta de Google del autor)
- **Prompt usado:** `prompt_usado.md`, Prompt A. Se adjuntaron las maquetas `operario_hoy_3_estados.png` y `calma_operativa_v2.png`.
- **Para qué sirve:** evidencia del proceso de diseño de la Fase 2 de Diseño de Interfaces (sección "Evolución de la propuesta") y material para presentarlo en clase.

## Contenido

| Archivo | Qué es |
|---|---|
| `DESIGN.md` | Sistema de diseño que generó Stitch (tokens de color y tipografía, y reglas de componentes) |
| `01_admin_equipo_escritorio.png` | "Equipo" del Administrador, 1440 px |
| `02_operario_hoy_normal.png` | "Hoy" del Operario, estado normal en turno |
| `03_operario_hoy_urgente.png` | "Hoy" del Operario, llega una actividad urgente |
| `04_operario_hoy_fuera_de_turno.png` | "Hoy" del Operario, fuera de turno |
| `prompt_usado.md` | Prompts A (Stitch) y B (auditoría) con los criterios de evaluación |

## Revisión crítica

Stitch genera diseños; no los audita. Su resumen afirma que todo cumple, pero esas afirmaciones son de la herramienta y no mediciones. Los contrastes de abajo se midieron con `herramientas/contraste.py` sobre colores tomados de las capturas.

### Lo que aporta y vale la pena adoptar
- **Mismo concepto, mejor acabado.** Respeta el tanque, la sobrecarga como rebose coral, el único bloque rojo para lo urgente y el orden por prioridad.
- **Botón "Reasignar"** en la actividad que termina fuera de turno, y **"Asignar"** en cada tarea sin asignar. Hace accionable la frase "Luz necesita ayuda", con asignación manual (coherente con la Sección 9).
- **Códigos de orden** (OT-1042…) visibles en la jornada y en "Sin asignar": facilitan la trazabilidad.
- **Resumen de capacidad** del equipo ("14 h 35 min disponibles"), con el cálculo correcto: 28 h − 13 h 25 min.
- **Cifras tabulares** en cronómetros y horas.

### Problemas encontrados

| # | Problema | Evidencia | Severidad |
|---|---|---|---|
| 1 | **"Media" en ámbar sobre blanco no cumple contraste** | Estado 1: `#E19C00` sobre blanco = **2,34:1** (mínimo 4,5:1). Contradice la afirmación de Stitch de cumplir WCAG AA | Mayor |
| 2 | **Los tokens del `DESIGN.md` no coinciden con su propio texto** | El encabezado YAML trae una paleta generada automáticamente (`primary #003d48`, `error #ba1a1a`, `surface #f0fcf9`) distinta de la que describe el texto (`#16697A`, `#A8322A`, `#F4F6F5`) | Mayor (si se usara como código) |
| 3 | **Prioridad Alta asignada al ámbar** | El `DESIGN.md` dice "Prioridad Alta / Precaución: ámbar". En el sistema aprobado, Alta es naranja (`#8A3D08`) y el ámbar es para Media, advertencia y pausa | Mayor |
| 4 | **Capacidad de 8 h** | El `DESIGN.md` habla de sobrecarga "si supera las 8 horas". La jornada del sistema es de 7 h | Menor (error de texto) |
| 5 | **Textos de 12 y 13 px** | Tokens `label-md`, `code-sm` (12 px) y `body-sm` (13 px), por debajo de los mínimos del alcance para personas mayores | Mayor |
| 6 | **Tipografías distintas a las del sistema** | Usa Manrope y Geist. Las horas y códigos del escritorio salen con cero tachado (06:00, 30). Ninguna de las dos fuentes está aprobada | Por decidir |
| 7 | **Logo e íconos inconsistentes** | El logo cambia entre pantallas (cápsula, maletín y otros); los íconos de prioridad varían (^, ▲ o punto) | Mayor (consistencia) |
| 8 | **Funciones inventadas, fuera del alcance** | "Telemetría en tiempo real activa", "Manual de Procedimientos", "Ver balance semanal", "Planta central Ubaté", "Jefe de Producción", checkboxes de "control sanitario" y litros | Menor, pero no deben presentarse como funciones del producto |
| 9 | **"Necesita ayuda" en ámbar en el tanque y en rosado en el panel** | El mismo estado usa dos colores distintos | Menor (consistencia) |
| 10 | **Barra de estado de un celular simulada** (14:20, wifi, batería) solo en el estado 3 | Inconsistente con las otras pantallas | Menor |

### Conclusión para la clase
Stitch sirve como **acelerador visual**: tomó el concepto y lo pulió rápido. Pero **no reemplaza la validación**: afirmó cumplir WCAG y no lo hace, contradijo reglas del sistema de color e inventó funciones. El diseño final debe tomar sus aciertos (reasignar, asignar, códigos y acabado) y corregir los problemas de la tabla, midiendo de nuevo.

## Pendiente
- Decidir qué se adopta (está en el registro de decisiones del chat, sección G).
- No usar los tokens YAML del `DESIGN.md` como código sin corregirlos (problema 2).
