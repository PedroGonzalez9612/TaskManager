// Marco común de las pantallas con sesión: menú lateral según el rol, diálogos y avisos.

const ICONOS = {
    empresas: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 9h1M14 9h1M9 13h1M14 13h1M10 21v-4h4v4"/></svg>',
    usuarios: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6M16 4.5a3.5 3.5 0 0 1 0 7M18 14.2c2.1.7 3.5 2.8 3.5 5.8"/></svg>',
    actividades: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/></svg>',
};

// Opciones del menú de cada rol. "rutas" indica en qué páginas se marca como activa
// (por ejemplo, el detalle de una empresa pertenece a la opción "Empresas").
// Se agregan opciones a medida que se construyen sus pantallas.
const MENU_POR_ROL = {
    SUPERADMIN: [
        {
            texto: "Empresas",
            icono: "empresas",
            destino: "/static/superadmin/empresas.html",
            rutas: ["/static/superadmin/empresas.html", "/static/superadmin/empresa.html"],
        },
    ],
    ADMINISTRADOR: [
        {
            texto: "Usuarios",
            icono: "usuarios",
            destino: "/static/admin/usuarios.html",
            rutas: ["/static/admin/usuarios.html"],
        },
    ],
    OPERARIO: [
        {
            texto: "Mis actividades",
            icono: "actividades",
            destino: "/static/operario/index.html",
            rutas: ["/static/operario/index.html"],
        },
    ],
};

// Marca del menú. Los usuarios de una empresa ven el logo y el nombre de SU empresa (marca blanca);
// el Superadmin, que no pertenece a ninguna, ve la marca de GestLab.
function crearMarca(usuario) {
    const marca = document.createElement("a");
    marca.className = "marca";
    marca.href = "/";

    if (!usuario.empresa) {
        marca.innerHTML = '<span class="marca-icono" aria-hidden="true">G</span>GestLab';
        return marca;
    }

    const nombre = document.createElement("span");
    nombre.className = "marca-nombre";
    nombre.textContent = usuario.empresa.nombre;

    if (usuario.empresa.tiene_logo) {
        const logo = document.createElement("img");
        logo.className = "marca-logo";
        logo.src = urlLogo(usuario.empresa_id);
        logo.alt = `Logo de ${usuario.empresa.nombre}`;
        marca.append(logo, nombre);
    } else {
        const inicial = document.createElement("span");
        inicial.className = "marca-icono";
        inicial.setAttribute("aria-hidden", "true");
        inicial.textContent = usuario.empresa.nombre.charAt(0).toUpperCase();
        marca.append(inicial, nombre);
    }
    return marca;
}

function construirMenu(usuario) {
    const menu = document.createElement("nav");
    menu.className = "menu-lateral";
    menu.id = "menu-lateral";
    menu.setAttribute("aria-label", "Menú principal");

    const opciones = document.createElement("ul");
    opciones.className = "menu-opciones";
    for (const opcion of MENU_POR_ROL[usuario.rol] || []) {
        const item = document.createElement("li");
        const enlace = document.createElement("a");
        enlace.href = opcion.destino;
        // El icono es un texto fijo del código; el nombre va con textContent.
        enlace.innerHTML = ICONOS[opcion.icono] || "";
        enlace.append(opcion.texto);
        if (opcion.rutas.includes(window.location.pathname)) {
            enlace.setAttribute("aria-current", "page");
        }
        item.append(enlace);
        opciones.append(item);
    }

    const bloqueUsuario = document.createElement("div");
    bloqueUsuario.className = "menu-usuario";
    // Avatar con la inicial del usuario: junto con el logo, es donde aparece el color de marca.
    const avatar = document.createElement("span");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = usuario.nombre.charAt(0).toUpperCase();
    const nombre = document.createElement("strong");
    nombre.textContent = usuario.nombre;
    const rol = document.createElement("span");
    rol.className = "usuario-rol";
    rol.textContent = NOMBRE_ROL[usuario.rol] || usuario.rol;
    const textos = document.createElement("div");
    textos.append(nombre, rol);
    const datos = document.createElement("div");
    datos.className = "usuario-datos";
    datos.append(avatar, textos);
    const salir = document.createElement("button");
    salir.type = "button";
    salir.className = "boton-secundario boton-pequeno boton-bloque";
    salir.textContent = "Cerrar sesión";
    salir.addEventListener("click", async () => {
        await pedirApi("/auth/logout", { method: "POST" });
        window.location.href = RUTA_LOGIN;
    });
    bloqueUsuario.append(datos, salir);

    menu.append(crearMarca(usuario), opciones, bloqueUsuario);
    return menu;
}

// Barra superior que solo aparece en celular, con el botón para abrir el menú.
function construirBarraMovil(usuario) {
    const barra = document.createElement("header");
    barra.className = "barra-movil";

    const botonMenu = document.createElement("button");
    botonMenu.type = "button";
    botonMenu.className = "boton-secundario boton-pequeno";
    botonMenu.textContent = "Menú";
    botonMenu.setAttribute("aria-controls", "menu-lateral");
    botonMenu.setAttribute("aria-expanded", "false");

    const fondo = document.createElement("div");
    fondo.className = "fondo-menu";
    fondo.hidden = true;

    const alternar = (abrir) => {
        document.body.classList.toggle("menu-abierto", abrir);
        botonMenu.setAttribute("aria-expanded", String(abrir));
        fondo.hidden = !abrir;
    };
    botonMenu.addEventListener("click", () => alternar(!document.body.classList.contains("menu-abierto")));
    fondo.addEventListener("click", () => alternar(false));

    barra.append(crearMarca(usuario), botonMenu);
    return [barra, fondo];
}

// Protege una página: comprueba la sesión y el rol, arma el menú y devuelve el usuario.
async function iniciarPaginaProtegida(rolesPermitidos) {
    const usuario = await pedirApi("/auth/sesion");

    if (!rolesPermitidos.includes(usuario.rol)) {
        window.location.href = INICIO_POR_ROL[usuario.rol] || RUTA_LOGIN;
        throw new Error("Rol sin acceso a esta página");
    }

    const [barraMovil, fondoMenu] = construirBarraMovil(usuario);
    document.body.prepend(barraMovil, construirMenu(usuario), fondoMenu);
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
            formulario.querySelector("input, select")?.focus();
        });
    }
    for (const cerrar of dialogo.querySelectorAll("[data-cerrar]")) {
        cerrar.addEventListener("click", () => dialogo.close());
    }
    dialogo.addEventListener("close", () => {
        formulario.reset();
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

// Confirmación breve que desaparece sola (visibilidad del estado del sistema).
function mostrarAviso(texto) {
    const aviso = document.createElement("div");
    aviso.className = "aviso-flotante";
    aviso.setAttribute("role", "status");
    aviso.textContent = texto;
    document.body.append(aviso);
    setTimeout(() => aviso.remove(), 4000);
}

// Envía un formulario de un diálogo: valida, desactiva el botón mientras guarda,
// muestra el error dentro del diálogo o lo cierra si todo salió bien.
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
        const textoExito = await guardar(datos);
        dialogo.close();
        mostrarAviso(textoExito);
    } catch (error) {
        mostrarErrorFormulario(mensaje, error.message);
    } finally {
        boton.disabled = false;
    }
}
