// Marco común de las pantallas con sesión: barra superior, navegación por vistas, diálogos y avisos.
// Necesita que antes se carguen api.js y vendor/lucide/iconos.js.

// Vistas de cada rol. "rutas" indica en qué páginas se marca como activa (por ejemplo, el detalle
// de una empresa pertenece a "Empresas"). Una vista se agrega aquí solo cuando su pantalla existe.
const VISTAS_POR_ROL = {
    SUPERADMIN: [
        {
            texto: "Empresas",
            icono: "factory",
            destino: "/static/superadmin/empresas.html",
            rutas: ["/static/superadmin/empresas.html", "/static/superadmin/empresa.html"],
        },
    ],
    ADMINISTRADOR: [
        // Cuatro menús, por lo que más usa (alcance, Sección 6.2): Hoy, Planeación, Indicadores y Administración.
        { texto: "Hoy", icono: "house", destino: "/static/admin/hoy.html", rutas: ["/static/admin/hoy.html"], conPendientes: true },
        { texto: "Planeación", icono: "clipboard-check", destino: "/static/admin/actividades.html", rutas: ["/static/admin/actividades.html"] },
        { texto: "Indicadores", icono: "chart-column", destino: "/static/admin/indicadores.html", rutas: ["/static/admin/indicadores.html"] },
        { texto: "Administración", icono: "users", destino: "/static/admin/administracion.html", rutas: ["/static/admin/administracion.html"] },
    ],
    OPERARIO: [
        { texto: "Inicio", icono: "house", destino: "/static/operario/inicio.html", rutas: ["/static/operario/inicio.html"] },
        { texto: "Hoy", icono: "list-checks", destino: "/static/operario/index.html", rutas: ["/static/operario/index.html"] },
        { texto: "Semana", icono: "calendar-days", destino: "/static/operario/semana.html", rutas: ["/static/operario/semana.html"] },
        { texto: "Resumen", icono: "chart-column", destino: "/static/operario/resumen.html", rutas: ["/static/operario/resumen.html"] },
    ],
};

// Crea un elemento con su clase y su texto. El texto siempre entra con textContent,
// así un dato con etiquetas HTML nunca se ejecuta.
function crearElemento(etiqueta, clase = "", texto = "") {
    const elemento = document.createElement(etiqueta);
    if (clase) {
        elemento.className = clase;
    }
    if (texto !== "" && texto != null) {
        elemento.textContent = texto;
    }
    return elemento;
}

// Elemento con un ícono de Lucide delante del texto. El SVG es fijo (viene de iconos.js).
function crearConIcono(etiqueta, clase, nombreIcono, texto) {
    const elemento = crearElemento(etiqueta, clase);
    elemento.insertAdjacentHTML("afterbegin", icono(nombreIcono));
    if (texto) {
        elemento.append(crearElemento("span", "", texto));
    }
    return elemento;
}

// Logo de GestLab: el tablero del turno (tres barras en gris y la línea "Ahora" en el color principal).
// El dibujo vive en un solo archivo, favicon.svg; aquí y en el login solo se muestra.
function crearLogoGestLab() {
    const logo = crearElemento("img", "marca-icono");
    logo.src = "/static/favicon.svg";
    logo.alt = "";
    return logo;
}

// Marca de la barra superior. Los usuarios de una empresa ven el logo y el nombre de SU empresa
// (marca blanca); el Superadmin, que no pertenece a ninguna, ve la marca de GestLab.
// Una empresa sin logo propio muestra el del tablero junto a su nombre.
function crearMarca(usuario) {
    const marca = crearElemento("a", "marca");
    marca.href = "/";

    if (!usuario.empresa) {
        marca.append(crearLogoGestLab(), crearElemento("span", "marca-nombre", "GestLab"));
        return marca;
    }

    if (usuario.empresa.tiene_logo) {
        const logo = crearElemento("img", "marca-logo");
        logo.src = urlLogo(usuario.empresa_id);
        logo.alt = `Logo de ${usuario.empresa.nombre}`;
        marca.append(logo);
    } else {
        marca.append(crearLogoGestLab());
    }
    marca.append(crearElemento("span", "marca-nombre", usuario.empresa.nombre));
    return marca;
}

// Navegación entre vistas: pestañas arriba en computador y barra fija abajo en celular (lo decide el CSS).
function construirNavegacion(usuario) {
    const navegacion = crearElemento("nav", "navegacion");
    navegacion.setAttribute("aria-label", "Vistas");

    for (const vista of VISTAS_POR_ROL[usuario.rol] || []) {
        const enlace = crearConIcono("a", "", vista.icono, vista.texto);
        enlace.href = vista.destino;
        if (vista.conPendientes) {
            enlace.dataset.pendientes = "";
        }
        if (vista.rutas.includes(window.location.pathname)) {
            enlace.setAttribute("aria-current", "page");
        }
        navegacion.append(enlace);
    }
    return navegacion;
}

const RUTA_PERFIL = "/static/perfil.html";

function construirBloqueUsuario(usuario) {
    const bloque = crearElemento("div", "usuario");
    // El avatar, el nombre y el rol llevan a Mi perfil (alcance, Sección 6.2: marco común).
    const perfil = crearElemento("a", "usuario-perfil");
    perfil.href = RUTA_PERFIL;
    perfil.title = "Mi perfil";
    perfil.setAttribute("aria-label", `Mi perfil, ${usuario.nombre}`);
    if (window.location.pathname === RUTA_PERFIL) {
        perfil.setAttribute("aria-current", "page");
    }

    // Avatar con la inicial: junto con el logo, es donde aparece el color de marca.
    const avatar = crearElemento("span", "avatar", usuario.nombre.charAt(0).toUpperCase());
    avatar.setAttribute("aria-hidden", "true");

    const textos = crearElemento("div", "usuario-textos");
    const rol = NOMBRE_ROL[usuario.rol] || usuario.rol;
    textos.append(crearElemento("strong", "", usuario.nombre));
    // Si el nombre ya dice el rol (el Superadmin inicial se llama "Superadmin"), no se repite.
    if (rol.toLowerCase() !== usuario.nombre.trim().toLowerCase()) {
        textos.append(crearElemento("span", "usuario-rol", rol));
    }

    // En computador dice "Cerrar sesión"; en celular queda la puerta, con el texto para el lector (6.5).
    const salir = crearConIcono("button", "boton-icono boton-salir", "log-out", "Cerrar sesión");
    salir.type = "button";
    salir.addEventListener("click", async () => {
        await pedirApi("/auth/logout", { method: "POST" });
        window.location.href = RUTA_LOGIN;
    });

    perfil.append(avatar, textos);
    bloque.append(perfil, salir);
    return bloque;
}

// ---------- Pestañas de un submenú (alcance, Sección 6.2) ----------
// Botones role="tab" con data-vista y aria-controls dentro de un role="tablist". La pestaña elegida
// queda en la dirección (por ejemplo #proyectos), para volver a ella o enlazarla desde otra pantalla.
// Las flechas izquierda y derecha pasan de una a otra (patrón de pestañas de WAI-ARIA). "alCambiar"
// recibe el nombre de la vista elegida.
function iniciarPestanas(lista, alCambiar) {
    const pestanas = [...lista.querySelectorAll('[role="tab"]')];
    function elegir(pestana, conFoco = false) {
        for (const otra of pestanas) {
            const elegida = otra === pestana;
            otra.setAttribute("aria-selected", String(elegida));
            otra.tabIndex = elegida ? 0 : -1;
            document.getElementById(otra.getAttribute("aria-controls")).hidden = !elegida;
        }
        if (conFoco) {
            pestana.focus();
        }
        history.replaceState(null, "", `#${pestana.dataset.vista}`);
        alCambiar?.(pestana.dataset.vista);
    }
    pestanas.forEach((pestana, indice) => {
        pestana.addEventListener("click", () => elegir(pestana));
        pestana.addEventListener("keydown", (evento) => {
            const paso = { ArrowRight: 1, ArrowLeft: -1 }[evento.key];
            if (paso) {
                evento.preventDefault();
                elegir(pestanas[(indice + paso + pestanas.length) % pestanas.length], true);
            }
        });
    });
    elegir(pestanas.find((pestana) => `#${pestana.dataset.vista}` === location.hash) || pestanas[0]);
}

// ---------- Repintar sin perder el foco (WCAG 2.4.3 y 4.1.3) ----------
// Las pantallas que muestran minutos se repintan cada medio minuto. Para no mover a quien navega con
// teclado ni repetir avisos al lector de pantalla: con "soloSiCambia", no se toca lo que dice lo mismo;
// y si se repinta, el foco vuelve al elemento con el mismo "data-foco".
function reemplazarSiCambia(contenedor, nodos, soloSiCambia = false) {
    const firma = nodos.map((nodo) => nodo.textContent).join("␞");
    if (soloSiCambia && contenedor.dataset.firma === firma) {
        return false;
    }
    const enfocado = document.activeElement;
    const clave = enfocado && contenedor.contains(enfocado) ? enfocado.dataset.foco : null;
    contenedor.replaceChildren(...nodos);
    contenedor.dataset.firma = firma;
    if (clave) {
        contenedor.querySelector(`[data-foco="${CSS.escape(clave)}"]`)?.focus();
    }
    return true;
}

// ---------- Estado del turno en la barra superior (Operario; observación 13 del usuario) ----------
// El Operario ve en cualquier pantalla si está en turno y la hora, sin volver a Inicio. Los textos
// son los de Inicio (alcance, Sección 6.1). El Administrador y el Superadmin no tienen turno propio.

function horaDeLaBarra(momento) {
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

// Devuelve [clase, ícono o null, texto] según el turno y la asistencia de la jornada vigente.
function estadoDelTurnoEnLaBarra(programacion) {
    const { presencia, turno } = programacion;
    if (!presencia || (presencia.estado === "SIN_TURNO" && !turno)) {
        return null;
    }
    const clase = { EN_TURNO: "barra-turno-en-turno", LLEGADA_TARDE: "barra-turno-tarde" }[presencia.estado] || "barra-turno-neutro";
    return [clase, presencia.estado === "LLEGADA_TARDE" ? "clock" : null, textoDePresencia(presencia, turno)];
}

// El estado se anuncia solo cuando cambia (está en su propia región "aria-live"); la hora, que cambia
// cada minuto, no se anuncia: es un reloj visual.
function pintarEstadoDelTurno(contenedor, programacion) {
    const estado = estadoDelTurnoEnLaBarra(programacion);
    let region = contenedor.querySelector(".barra-turno-estado");
    let hora = contenedor.querySelector(".barra-turno-hora");
    if (!region) {
        region = crearElemento("span", "barra-turno-estado");
        region.setAttribute("aria-live", "polite");
        hora = crearElemento("span", "barra-turno-hora cifra");
        hora.setAttribute("aria-hidden", "true");
        contenedor.replaceChildren(region, hora);
    }
    hora.textContent = horaDeLaBarra(Date.now());
    const contenido = [];
    if (estado) {
        const [clase, nombreIcono, texto] = estado;
        contenido.push(nombreIcono ? crearConIcono("span", clase, nombreIcono, texto) : crearElemento("span", clase, texto));
    }
    reemplazarSiCambia(region, contenido, true);
}

async function construirEstadoDelTurno(contenedor) {
    try {
        const programacion = await pedirApi("/programacion-del-dia");
        let actual = programacion;
        pintarEstadoDelTurno(contenedor, actual);
        // La hora se repinta cada medio minuto (sin segundos). El estado lo calcula el servidor: se le
        // vuelve a pedir cada minuto, para que pase solo de "Por llegar" a "Llegada tarde", por ejemplo.
        setInterval(() => pintarEstadoDelTurno(contenedor, actual), 30000);
        setInterval(async () => {
            try {
                actual = await pedirApi("/programacion-del-dia");
            } catch {
                // Sin conexión se conserva el último estado conocido.
            }
        }, 60000);
    } catch {
        contenedor.hidden = true;     // Sin la programación, la barra sigue funcionando sin el estado.
    }
}

// Cuántos pendientes tiene el Administrador, junto a "Hoy" en el menú (alcance, Sección 6.2). Sin
// pendientes no se muestra nada.
function pintarCantidadDelMenu(total) {
    const enlace = document.querySelector("[data-pendientes]");
    if (!enlace) {
        return;
    }
    enlace.querySelector(".menu-cantidad")?.remove();
    if (total > 0) {
        const cantidad = crearElemento("span", "menu-cantidad cifra", String(total));
        cantidad.setAttribute("aria-label", plural_(total, "pendiente", "pendientes"));
        enlace.append(cantidad);
    }
}

function plural_(cantidad, uno, varios) {
    return `${cantidad} ${cantidad === 1 ? uno : varios}`;
}

// Protege una página: comprueba la sesión y el rol, arma el marco y devuelve el usuario.
async function iniciarPaginaProtegida(rolesPermitidos) {
    const usuario = await pedirApi("/auth/sesion");

    if (!rolesPermitidos.includes(usuario.rol)) {
        window.location.href = INICIO_POR_ROL[usuario.rol] || RUTA_LOGIN;
        throw new Error("Rol sin acceso a esta página");
    }

    const barra = crearElemento("header", "barra-superior");
    barra.append(crearMarca(usuario), construirNavegacion(usuario));
    if (usuario.rol === "OPERARIO") {
        const estado = crearElemento("div", "barra-turno");
        barra.append(estado);
        construirEstadoDelTurno(estado);
    }
    barra.append(construirBloqueUsuario(usuario));
    document.body.prepend(barra);
    // En las demás pantallas del Administrador, el menú también dice cuántos pendientes hay (Hoy los pinta solo).
    if (usuario.rol === "ADMINISTRADOR" && window.location.pathname !== "/static/admin/hoy.html") {
        pedirApi("/hoy/pendientes").then((pendientes) => pintarCantidadDelMenu(pendientes.total)).catch(() => {});
    }
    document.body.classList.remove("cargando");
    return usuario;
}

// Conecta un botón con un <dialog> que contiene un formulario.
// Al cerrarse, el formulario y su mensaje de error se limpian.
function configurarDialogo(botonesAbrir, dialogo) {
    const formulario = dialogo.querySelector("form");
    const mensaje = dialogo.querySelector(".mensaje-formulario");

    for (const boton of botonesAbrir) {
        boton.addEventListener("click", () => {
            dialogo.showModal();
            formulario?.querySelector("input:not([type=hidden]), select, textarea")?.focus();
        });
    }
    for (const cerrar of dialogo.querySelectorAll("[data-cerrar]")) {
        cerrar.addEventListener("click", () => dialogo.close());
    }
    dialogo.addEventListener("close", () => {
        formulario?.reset();
        if (mensaje) {
            mensaje.hidden = true;
        }
    });
}

// Una ventana con un formulario corto: un subtítulo (sobre qué se actúa), sus campos, la salida y una
// sola acción principal (alcance, Sección 6.2). "alConfirmar" lanza un error con el mensaje que se
// muestra si algo falla; si termina bien, la ventana se cierra.
function abrirDialogoAccion({ titulo, subtitulo = "", campos = [], textoConfirmar, iconoConfirmar = "check",
    textoCerrar = "Cancelar", alConfirmar }) {
    const dialogo = crearElemento("dialog", "dialogo");
    const encabezado = crearElemento("div", "dialogo-encabezado");
    const cerrar = crearElemento("button", "boton-cerrar", "×");
    cerrar.type = "button";
    cerrar.setAttribute("aria-label", "Cerrar");
    cerrar.addEventListener("click", () => dialogo.close());
    encabezado.append(crearElemento("h2", "", titulo), cerrar);

    const formulario = crearElemento("form", "formulario");
    formulario.noValidate = true;
    const error = crearElemento("p", "mensaje-formulario");
    error.setAttribute("role", "alert");
    error.hidden = true;
    const salir = crearElemento("button", "boton-secundario", textoCerrar);
    salir.type = "button";
    salir.addEventListener("click", () => dialogo.close());
    const confirmar = crearConIcono("button", "boton", iconoConfirmar, textoConfirmar);
    confirmar.type = "submit";
    const acciones = crearElemento("div", "dialogo-acciones");
    acciones.append(salir, confirmar);
    if (subtitulo) {
        formulario.append(crearElemento("p", "dialogo-actividad", subtitulo));
    }
    formulario.append(...campos, error, acciones);

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        confirmar.disabled = true;
        try {
            await alConfirmar();
            dialogo.close();
        } catch (error_) {
            mostrarErrorFormulario(error, error_.message);
            confirmar.disabled = false;
        }
    });
    dialogo.append(encabezado, formulario);
    dialogo.addEventListener("close", () => dialogo.remove());
    document.body.append(dialogo);
    dialogo.showModal();
    formulario.querySelector("select, textarea, input")?.focus();
}

// Muestra la imagen elegida antes de subirla, y la limpia cuando se cierra el diálogo.
// "urlActual" permite mostrar el logo que ya tiene la empresa (al editar).
function configurarCampoLogo(dialogo, urlActual = null) {
    const campo = dialogo.querySelector('input[type="file"]');
    const vistaPrevia = dialogo.querySelector(".vista-previa-logo");

    const mostrar = (url) => {
        vistaPrevia.hidden = !url;
        if (url) {
            vistaPrevia.src = url;
        } else {
            vistaPrevia.removeAttribute("src");
        }
    };

    campo.addEventListener("change", () => {
        const archivo = campo.files[0];
        mostrar(archivo && !validarArchivoLogo(archivo) ? URL.createObjectURL(archivo) : urlActual());
    });
    dialogo.addEventListener("close", () => mostrar(null));
    return {
        archivo: () => campo.files[0] || null,
        mostrarActual: () => mostrar(urlActual()),
    };
}

function mostrarErrorFormulario(mensaje, texto) {
    mensaje.textContent = texto;
    mensaje.hidden = false;
}

// Aviso breve que desaparece solo (visibilidad del estado del sistema).
// tipo "exito" confirma una acción; "advertencia" avisa algo que conviene revisar y dura más.
function mostrarAviso(texto, tipo = "exito") {
    const aviso = crearConIcono(
        "div", `aviso-flotante aviso-flotante-${tipo}`, tipo === "exito" ? "check" : "circle-alert", texto,
    );
    aviso.setAttribute("role", tipo === "exito" ? "status" : "alert");
    document.body.append(aviso);
    setTimeout(() => aviso.remove(), tipo === "exito" ? 4000 : 9000);
}

// Envía un formulario de un diálogo: valida, desactiva el botón mientras guarda,
// muestra el error dentro del diálogo o lo cierra si todo salió bien.
// "guardar" devuelve el texto de confirmación, o { texto, tipo } para avisar con otro tono.
async function enviarFormularioDialogo(dialogo, validar, guardar) {
    const formulario = dialogo.querySelector("form");
    const mensaje = dialogo.querySelector(".mensaje-formulario");
    const datos = datosFormulario(formulario);

    const error = validar(datos);
    if (error) {
        mostrarErrorFormulario(mensaje, error);
        return;
    }

    const boton = formulario.querySelector('button[type="submit"]');
    boton.disabled = true;
    try {
        const resultado = await guardar(datos);
        dialogo.close();
        if (typeof resultado === "string") {
            mostrarAviso(resultado);
        } else {
            mostrarAviso(resultado.texto, resultado.tipo);
        }
    } catch (error) {
        mostrarErrorFormulario(mensaje, error.message);
    } finally {
        boton.disabled = false;
    }
}
