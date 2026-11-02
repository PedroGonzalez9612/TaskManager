// Administración del Administrador (alcance, Sección 6.2): la configuración de su empresa. Pestañas:
// Usuarios (crear, desactivar, reactivar y cambiar el turno), Turnos y Empresa (límites de usuarios).

const FILTROS_USUARIOS = [
    { nombre: "Operarios", incluye: (u) => u.rol === "OPERARIO" && u.activo !== false },
    { nombre: "Administradores", incluye: (u) => u.rol === "ADMINISTRADOR" && u.activo !== false },
    { nombre: "Desactivados", incluye: (u) => u.activo === false },
];

let usuarios = [];
let filtroUsuarios = FILTROS_USUARIOS[0];
let usuarioActual = null;
let recargar = null;

const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;

function pintarLimites(empresa) {
    document.getElementById("limites").replaceChildren(...crearMedidoresEmpresa(empresa, true).reverse());

    // Los roles que alcanzaron su límite no se ofrecen en el formulario (prevención de errores, Nielsen 5).
    const selectorRol = document.getElementById("rol");
    for (const opcion of selectorRol.options) {
        const lleno = limiteAlcanzado(empresa, opcion.value);
        opcion.disabled = lleno;
        opcion.textContent = `${NOMBRE_ROL[opcion.value]}${lleno ? " (límite alcanzado)" : ""}`;
    }
    const disponible = [...selectorRol.options].find((opcion) => !opcion.disabled);
    if (disponible) {
        selectorRol.value = disponible.value;
        // Al cerrar el diálogo, el formulario se reinicia a esta opción.
        for (const opcion of selectorRol.options) {
            opcion.defaultSelected = opcion === disponible;
        }
    }

    const aviso = document.getElementById("aviso-limite");
    aviso.hidden = Boolean(disponible);
    aviso.replaceChildren(...crearConIcono("span", "", "info",
        "Tu empresa alcanzó el límite de usuarios. Para crear más, pide al Superadmin que lo amplíe.").childNodes);
    document.getElementById("nuevo-usuario").disabled = !disponible;
}

function pintarEmpresa(empresa) {
    const datos = document.getElementById("datos-empresa");
    const filas = [["Nombre", empresa.nombre], ["NIT", empresa.nit], ["Sector", empresa.sector],
        ["Dirección", empresa.direccion], ["Zona horaria", empresa.zona_horaria]];
    datos.replaceChildren(...filas.filter(([, valor]) => valor).flatMap(([nombre, valor]) =>
        [crearElemento("dt", "", nombre), crearElemento("dd", "", valor)]));
}

function pintarUsuarios() {
    document.getElementById("filtros-usuarios").replaceChildren(...FILTROS_USUARIOS.map((filtro) => {
        const boton = crearElemento("button", "filtro-linea");
        boton.type = "button";
        boton.setAttribute("aria-pressed", String(filtro === filtroUsuarios));
        boton.append(crearElemento("span", "", filtro.nombre),
            crearElemento("span", "filtro-cantidad cifra", String(usuarios.filter(filtro.incluye).length)));
        boton.addEventListener("click", () => {
            filtroUsuarios = filtro;
            pintarUsuarios();
        });
        return boton;
    }));
    const busqueda = document.getElementById("buscar-usuario").value.trim().toLowerCase();
    const visibles = usuarios
        .filter((u) => filtroUsuarios.incluye(u) && `${u.nombre} ${u.correo}`.toLowerCase().includes(busqueda))
        .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    const lista = document.getElementById("lista-usuarios");
    lista.hidden = visibles.length === 0;
    document.getElementById("estado-vacio").hidden = visibles.length > 0;
    lista.replaceChildren(...visibles.map((u) => crearFilaUsuario(u, abrirAsignarTurno,
        { usuarioActualId: usuarioActual.id, alCambiar: recargar })));
}

function pintarSubtitulo() {
    const activos = (rol) => usuarios.filter((u) => u.rol === rol && u.activo !== false).length;
    document.getElementById("subtitulo").textContent = [
        plural(activos("OPERARIO"), "operario", "operarios"),
        plural(activos("ADMINISTRADOR"), "administrador", "administradores"),
    ].join(" y ");
}

async function iniciarPantalla() {
    usuarioActual = await iniciarPaginaProtegida(["ADMINISTRADOR"]);
    const empresaId = usuarioActual.empresa_id;
    recargar = async () => {
        try {
            const [lista, empresa] = await Promise.all([
                pedirApi(`/usuarios?empresa_id=${encodeURIComponent(empresaId)}`),
                pedirApi(`/empresas/${encodeURIComponent(empresaId)}`),
            ]);
            usuarios = lista;
            pintarSubtitulo();
            pintarUsuarios();
            pintarLimites(empresa);
            pintarEmpresa(empresa);
            await cargarTurnos(usuarios);
        } catch (error) {
            mostrarAviso(`No se pudo cargar la administración: ${error.message}`, "advertencia");
        }
    };
    configurarCreacionUsuario([document.getElementById("nuevo-usuario")], document.getElementById("dialogo-usuario"),
        empresaId, recargar);
    configurarTurnos(recargar);
    document.getElementById("buscar-usuario").addEventListener("input", pintarUsuarios);
    // El botón de arriba cambia con la pestaña: crear un usuario o un turno; Empresa no crea nada.
    iniciarPestanas(document.querySelector(".pestanas"), (vista) => {
        document.getElementById("nuevo-usuario").hidden = vista !== "usuarios";
        document.getElementById("nuevo-turno").hidden = vista !== "turnos";
    });
    await recargar();
}

iniciarPantalla();
