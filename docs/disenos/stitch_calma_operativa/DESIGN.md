---
name: Calma Operativa Industrial
colors:
  surface: '#f0fcf9'
  surface-dim: '#d1dcda'
  surface-bright: '#f0fcf9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#ebf6f3'
  surface-container: '#e5f0ed'
  surface-container-high: '#dfebe8'
  surface-container-highest: '#d9e5e2'
  on-surface: '#131d1c'
  on-surface-variant: '#40484b'
  inverse-surface: '#283231'
  inverse-on-surface: '#e8f3f0'
  outline: '#70787b'
  outline-variant: '#bfc8cb'
  surface-tint: '#286675'
  primary: '#003d48'
  on-primary: '#ffffff'
  primary-container: '#0f5563'
  on-primary-container: '#8dc8d8'
  inverse-primary: '#94d0e0'
  secondary: '#136778'
  on-secondary: '#ffffff'
  secondary-container: '#a4ebfe'
  on-secondary-container: '#1a6c7d'
  tertiary: '#671d12'
  on-tertiary: '#ffffff'
  tertiary-container: '#853326'
  on-tertiary-container: '#ffa99a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b0ecfd'
  primary-fixed-dim: '#94d0e0'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#004e5c'
  secondary-fixed: '#abedff'
  secondary-fixed-dim: '#8ad1e4'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#ffb4a7'
  on-tertiary-fixed: '#400200'
  on-tertiary-fixed-variant: '#7c2d20'
  background: '#f0fcf9'
  on-background: '#131d1c'
  surface-variant: '#d9e5e2'
typography:
  display-lg:
    fontFamily: Manrope
    fontSize: 3rem
    fontWeight: '700'
    lineHeight: 3.5rem
    letterSpacing: -0.03em
  display-timer:
    fontFamily: Geist
    fontSize: 2.5rem
    fontWeight: '600'
    lineHeight: 2.75rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 2rem
    fontWeight: '700'
    lineHeight: 2.5rem
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 1.5rem
    fontWeight: '700'
    lineHeight: 2rem
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Manrope
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Manrope
    fontSize: 1rem
    fontWeight: '600'
    lineHeight: 1.5rem
  body-lg:
    fontFamily: Geist
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: 1.75rem
  body-md:
    fontFamily: Geist
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: 1.45rem
  body-sm:
    fontFamily: Geist
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.25rem
  label-lg:
    fontFamily: Geist
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.25rem
    letterSpacing: 0.01em
  label-md:
    fontFamily: Geist
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.02em
  code-sm:
    fontFamily: Geist
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

Este sistema de diseño estructura la experiencia de control de planta para operaciones industriales lácteas, donde la fatiga cognitiva, el ruido ambiental y la velocidad de decisión son factores críticos de seguridad y rendimiento. La filosofía fundamental es la **Calma Operativa**: una arquitectura visual que reduce la fricción instrumental mediante neutralidad compositiva, activando la atención cromática únicamente cuando un proceso está activo o requiere intervención directa.

El estilo fusiona la precisión técnica de los tableros de laboratorio suizos con la solidez instrumental de planta:
- **Claridad silenciosa:** La interfaz permanece serena y ordenada en condiciones nominales. Los datos se jerarquizan mediante espaciado milimétrico y tipografía nítida en lugar de ornamentos.
- **Metáfora del tanque de carga:** El volumen de jornada laboral y el progreso de los procesos se representan a través de cápsulas líquidas verticales ("tanques"), donde el llenado comunica capacidad disponible, trabajo programado y sobrecarga de manera física y tangible.
- **Acceso táctil industrial:** Componentes dimensionados para operación física real en planta con objetivos táctiles generosos (mínimo 48px), alta legibilidad y retroalimentación inmediata sin falsas alarmas.

## Colors

La paleta cromática traduce el estado físico y operativo de la planta en señales de alta fidelidad, asegurando contraste funcional contra fondos claros y asépticos.

### Paleta Base y Superficie
- **Fondo General (`#F4F6F5`):** Gris verdoso técnico, ultra bajo reflejo, diseñado para entornos industriales iluminados.
- **Superficies (`#FFFFFF`):** Contenedores limpios, paneles de instrumentos y tarjetas de trabajo.
- **Texto Principal (`#1F2A2E`):** Pizarra oscuro de alta legibilidad técnica.
- **Texto Secundario (`#5B6664`):** Matiz neutro medio para metadatos, unidades y rótulos secundarios.

### Estados Operativos y Semánticos
- **Operación en Curso / Primario:** Base `#16697A`, con estados interactivos `hover/pressed` en `#0F5563`. Identifica tareas activas, cronómetros en marcha y ejecuciones prioritarias.
- **Acento Instrumental / Sobrecarga (`#E9806E`):** Tono coral reservado para isotipos de planta, avatares y la fracción de desborde cuando el tanque excede el 100% de la capacidad de turno.
- **Urgente / Alerta Crítica:** Superficie de impacto `#A8322A` con texto de contraste `#8A2620` sobre fondos suaves o `#FFFFFF` sobre bloque completo, activado únicamente ante bloqueos de línea o alarmas operativas.
- **Prioridad Alta / Precaución:** Tono ámbar `#E3A32B` con fondo tonal `#FBF1D9` y texto informativo `#6B4A0E`.
- **Conforme / En Turno:** Tono verde `#3E7B3A` con fondo `#E6F0E2` y texto `#2F5F2C`, comunicando estabilidad de parámetros y personal activo sin saturar.
- **Informativo / Técnico:** `#2F5DA8` tenue para trazabilidad INVIMA, normas sanitarias y registros de apoyo.

## Typography

La arquitectura tipográfica combina la sobriedad equilibrada de **Manrope** para cabeceras y nombres de sección con la exactitud técnica de **Geist** para bloques de datos, métricas de proceso y cuerpo de texto.

- **Cifras tabulares:** Todos los contadores de tiempo, cronómetros y volúmenes de litros deben renderizarse con la propiedad CSS `font-variant-numeric: tabular-nums` para evitar saltos de línea y desalineación óptica durante actualizaciones en vivo.
- **Escala de cronómetros:** El token `display-timer` mantiene un peso semicompacto legible a distancia de brazo extendido o montado en panel de máquina.
- **Contraste de información:** Los metadatos de operario, lotes de pasteurización y códigos de válvula emplean pesos medianos con ajuste estricto de interlineado para maximizar el área útil del panel.

## Layout & Spacing

El ritmo espacial sigue un módulo estricto de 8px (con submódulo de 4px para densidades de instrumentación). Se estructura para responder a dos tipos de interfaz: terminal de mano para operario y tablero de monitoreo central para jefatura de planta.

- **Terminal Móvil (Operario en Planta):** Cuadrícula de 4 columnas fluidas con márgenes externos de `1rem`. Prioriza apilamiento vertical con agrupaciones de tarjetas operativas. Toda acción de control mantiene separación mínima de `space-md` para prevenir toques involuntarios.
- **Consola Desktop / Tablet (Supervisión):** Sistema de 12 columnas con margen de `2rem` y canaleta (`gutter-desktop`) de `1.5rem`. La vista se divide en cuadrante de carga global, columnas de tanques por operario y panel lateral de contingencias.
- **Régimen de Relleno:** Los contenedores principales usan `space-lg` interno, mientras que los registros de eventos de línea usan `space-sm` vertical para mantener alta densidad sin pérdida de escaneabilidad.

## Elevation & Depth

La tridimensionalidad se resuelve mediante estratificación tonal y bordes de contención suaves en lugar de sombras profundas, preservando la estética higiénica y aséptica del entorno de producción láctea:

- **Nivel Base (Suelo Técnico):** Superficie `#F4F6F5`. Libre de sombras, actúa como plano neutro.
- **Nivel Contenedor / Tarjeta:** Superficie `#FFFFFF` delimitada por un borde perimetral sutil (`rgba(31, 42, 46, 0.08)`) y una elevación ambiental ultra suave (`0 1px 3px rgba(31, 42, 46, 0.04)`).
- **Nivel Urgencia / Alerta Activa:** Sin desenfoque difuso; se proyecta mediante saturación cromática directa sobre plano pleno (`#A8322A`), obligando a la concentración sin ensuciar la jerarquía espacial.
- **Superficies Flotantes y Modales:** Elevación contenida (`0 8px 24px rgba(31, 42, 46, 0.08)`) con borde perimetral nítido de 1px en `#0F5563` atenuado.

## Shapes

El sistema implementa un lenguaje geométrico técnico contenido (`roundedness: 1`), que comunica robustez mecánica y precisión analítica.

- **Células, Tarjetas y Paneles:** Radio base de 8px (`0.5rem`), ofreciendo esquinas compactas que maximizan el volumen interior y refuerzan el orden ortogonal.
- **Controles de Entrada y Botones:** Radio de 6px a 8px, garantizando una silueta limpia y delimitada que simula mandos mecánicos de control.
- **Píldoras de Estado y Tanques de Capacidad:** Excepción geométrica funcional mediante radio esférico completo (`9999px`) exclusivamente para etiquetas de turno, chips de prioridad y las cápsulas de fluido del tanque de jornada, evocando visualmente el perfil de tanques de almacenamiento y reactores CIP.

## Components

### 1. Botones Táctiles de Planta
- **Área mínima:** 48px de alto garantizado en pantallas operativas para pulsar con guantes de planta.
- **Botón Primario / En curso:** Fondo `#16697A`, texto `#FFFFFF`, hover `#0F5563`. Tipografía `label-lg`, icono alineado a la izquierda.
- **Botón Secundario / Pausa:** Fondo blanco, borde 1px en `#5B6664` al 30%, texto `#1F2A2E`.
- **Botón Crítico:** Fondo `#A8322A`, texto `#FFFFFF`. Reservado para detener ciclos, desvíos o emergencias sanitarias.

### 2. El Tanque de Carga (Metáfora Líquida)
- **Estructura:** Contenedor cilíndrico en píldora vertical de ancho constante (ej. 48px o 64px) con fondo `#F4F6F5` y borde delimitador de 1px.
- **Nivel en Curso:** Bloque inferior relleno con `#16697A`, animado suavemente en su cúspide según el tiempo transcurrido.
- **Nivel Programado:** Tramo intermedio en gris técnico (`#D5DBD9`).
- **Nivel Sobrecarga:** Si la jornada supera las 8 horas asignadas, el extremo superior del tanque tiñe su cápsula en `#E9806E` comunicando saturación física del operario.
- **Micro-Tanque:** Versión miniatura para tarjetas móviles individuales que acompaña el porcentaje de carga diaria.

### 3. Tarjetas de Actividad
- **Fondo:** `#FFFFFF` con padding de `1.25rem`.
- **Cabecera:** Píldora de estado a la izquierda (`• Ahora` en `#16697A`, `• Fuera de turno` en `#E3A32B`), etiqueta de prioridad a la derecha (`Urgente`, `Alta`, `Media`, `Baja`).
- **Bloque Central:** Título de la tarea en `headline-md`, subtítulo técnico con localización de planta (ej. *Planta 1, línea 3*).
- **Módulo de Tiempo:** Cronómetro de gran escala con dígitos monoespaciados junto a la estimación total del ciclo.

### 4. Chips y Píldoras de Estado
- **En Turno:** Fondo `#E6F0E2`, borde ninguno, texto `#2F5F2C`, dot verde `#3E7B3A`.
- **Prioridad Ámbar:** Fondo `#FBF1D9`, texto `#6B4A0E`, dot `#E3A32B`.
- **Urgente:** Fondo `#FBEAE8`, texto `#8A2620`, icono de advertencia.
- **Forma:** Altura 28px, esquinas redondeadas en píldora (`9999px`), tipografía `label-md`.

### 5. Listas y Cronología de Turno
- **Estructura:** Filas separadas por bordes inferiores ultra delgados (`#ECEFED`).
- **Horarios:** Bloque izquierdo en tipografía tabular (`09:00`, `11:30`) seguido de la descripción técnica de la tarea y su duración aproximada.
- **Microindicador:** Flecha de navegación derecha (`>`) con área táctil accesible para abrir la ficha técnica o protocolo INVIMA asociado.

### 6. Controles de Formulario e Inspección
- **Inputs:** Altura 48px, fondo `#FFFFFF`, borde 1.5px `#D5DBD9`, foco con anillo de 2px en `#16697A` sin desplazamiento de layout.
- **Checkboxes de Control Sanitario:** Cuadrantes de 24x24px, borde 2px, check nítido al activar con relleno `#16697A`.