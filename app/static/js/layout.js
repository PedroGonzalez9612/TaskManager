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
        { texto: "Equipo", icono: "calendar-days", destino: "/static/admin/equipo.html", rutas: ["/static/admin/equipo.html"] },
        { texto: "Actividades", icono: "clipboard-check", destino: "/static/admin/actividades.html", rutas: ["/static/admin/actividades.html"] },
        { texto: "Usuarios", icono: "users", destino: "/static/admin/usuarios.html", rutas: ["/static/admin/usuarios.html"] },
    ],
    OPERARIO: [
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

// Logo de GestLab: el tablero del turno (tres barras y la marca coral de "Ahora").
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
        if (vista.rutas.includes(window.location.pathname)) {
            enlace.setAttribute("aria-current", "page");
        }
        navegacion.append(enlace);
    }
    return navegacion;
}

function construirBloqueUsuario(usuario) {
    const bloque = crearElemento("div", "usuario");

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

    const salir = crearConIcono("button", "boton-icono", "log-out", "");
    salir.type = "button";
    salir.title = "Cerrar sesión";
    salir.setAttribute("aria-label", "Cerrar sesión");
    salir.addEventListener("click", async () => {
        await pedirApi("/auth/logout", { method: "POST" });
        window.location.href = RUTA_LOGIN;
    });

    bloque.append(avatar, textos, salir);
    return bloque;
}

// Protege una página: comprueba la sesión y el rol, arma el marco y devuelve el usuario.
async function iniciarPaginaProtegida(rolesPermitidos) {
    const usuario = await pedirApi("/auth/sesion");

    if (!rolesPermitidos.includes(usuario.rol)) {
        window.location.href = INICIO_POR_ROL[usuario.rol] || RUTA_LOGIN;
        throw new Error("Rol sin acceso a esta página");
    }

    const barra = crearElemento("header", "barra-superior");
    barra.append(crearMarca(usuario), construirNavegacion(usuario), construirBloqueUsuario(usuario));
    document.body.prepend(barra);
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
