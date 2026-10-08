# GestLab — Avance del proyecto

Registro de lo construido, por etapas. El **qué** del sistema está en [alcance_proyecto.md](alcance_proyecto.md); este documento dice **cuánto de eso ya funciona** y cómo verificarlo.

Leyenda: ✅ terminado · 🟡 parcial · ⬜ pendiente

## Estado de los criterios del MVP (Sección 8 del alcance)

| # | Criterio | Estado | Observaciones |
|---|---|---|---|
| 1 | Empresa y usuarios (tres roles, cada uno con su interfaz) | ✅ | Además: límites de usuarios por empresa y marca blanca |
| 2 | Requerimiento → Actividad | ⬜ | Existe API básica sin sesión; falta la interfaz del Administrador |
| 3 | Asignación y prioridad | ⬜ | El código tiene 3 prioridades (faltan URGENTE), una sola persona por actividad, sin fecha programada ni tiempo estimado |
| 4 | Ejecución (iniciar, pausar, reanudar, finalizar) | ⬜ | Existe iniciar/finalizar sin pausas; falta resolver a quién pertenece la ejecución |
| 5 | Registro de tiempo | ⬜ | |
| 6 | Análisis de carga laboral | ⬜ | |
| 7 | Turnos y asistencia | ⬜ | |
| 8 | Indicadores de cumplimiento | ⬜ | |

## Etapa 1 — Inicio de sesión, empresas y usuarios (2026-09-26) ✅

Rama: `feature/interfaz-operario`, integrada a `main` (Pull Request #4).

### Qué se puede hacer

- **Todos:** iniciar sesión con correo y contraseña; cada rol llega a su propia pantalla. Cerrar sesión.
- **Superadmin:** registrar empresas (con límites de usuarios y logo opcional), ver la lista con los cupos usados, entrar a cada empresa, editar sus datos, límites y logo, y crear sus Administradores.
- **Administrador:** ver los usuarios de su empresa y sus cupos, y crear Operarios u otros Administradores dentro del límite.
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
| Servicios | Nuevo `AuthService` (login y Superadmin inicial). `UsuarioService` aplica quién crea a quién y los cupos. `EmpresaService` valida límites y logo. |
| Rutas | Nuevo `/auth` (`login`, `logout`, `sesion`). Decorador `requiere_rol` en `app/utils/seguridad.py`. Rutas `PUT/GET /empresas/<id>/logo`. |
| Errores | Jerarquía `ErrorApi` → `ValidationError` (400), `NoAutorizadoError` (401), `ProhibidoError` (403), `NotFoundError` (404), con un solo manejador. |
| Interfaz | Marco común (`js/layout.js`), cliente de la API (`js/api.js`), pantallas en `superadmin/`, `admin/` y `operario/`, estilos en `css/estilos.css`. |

### Cómo se verificó

- 16 pruebas contra la API (curl) del flujo completo de roles y permisos, y 16 más de límites y logo, todas con el resultado esperado.
- Recorrido en navegador (Edge automatizado) de cada pantalla en computador y en celular (390 px de ancho), sin errores de JavaScript.

### Pendientes conocidos de esta etapa

- Las rutas de requerimientos, actividades, asignaciones, registros de tiempo y análisis **todavía no exigen sesión**. Se protegerán al construir cada una.
- No hay pruebas automatizadas en el repositorio (las verificaciones se hicieron manualmente).
- No existe todavía cambio de contraseña ni recuperación de contraseña.
- Usuarios creados antes de esta etapa (con campo `email` y sin contraseña) no son compatibles: hay que borrar la base de datos de desarrollo (`docker compose down -v`).

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
- NIT y cupos de usuarios usan la fuente monoespaciada (clase `cifra`).
- Avatar con la inicial del usuario en el menú; junto con el logo, es el único lugar donde aparece el coral de marca.
- Verificación: 18 pares de color medidos con `contraste.py` sobre las variables del CSS, todos por encima del mínimo; 10 capturas revisadas en celular y escritorio, incluida la versión en grises.

### Pendientes de esta fase

- La prioridad Urgente y los estados Pausada y Finalizada ya tienen estilo, pero todavía no se pueden ver con datos reales: el backend aún no tiene la prioridad URGENTE ni las pausas (Etapa 2 en adelante).
- Validar el diseño de las pantallas con una herramienta externa de diseño.
- Elaborar el documento de diseño en PDF que pide el enunciado (evolución, usabilidad, Gestalt, color, conclusiones) con las capturas como evidencia.

## Estado del repositorio (2026-10-03)

- `main` contiene la Etapa 1 y la Fase 2. `develop` está atrasada respecto a `main` y debe sincronizarse (Pull Request `main` → `develop`) antes de abrir la siguiente rama.
- `CLAUDE.md` y `.claude/agents/` se versionan en el repositorio (Sección 11 del alcance).

## Decisiones abiertas

- ¿La ejecución (pausas y tiempos) pertenece a la asignación (operario + actividad) o a la actividad? Se debe resolver antes de construir la ejecución (criterio 4).
- ¿El login debe mostrar la marca de cada empresa? Requeriría una dirección por empresa (por ejemplo `/metalicas`). Por ahora el login muestra GestLab.

## Próxima etapa

**Cierre de la Fase 2 de Diseño de Interfaces:** validar las pantallas y preparar el documento de diseño.

**Etapa 2 — Requerimientos y actividades (Administrador):** menú del Administrador, registro de requerimientos, conversión en actividades con prioridad de 4 niveles, tiempo estimado, fecha programada, categoría y asignación a uno o varios operarios (criterios 2 y 3).
