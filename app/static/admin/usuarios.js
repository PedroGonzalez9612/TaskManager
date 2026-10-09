// Administrador: ve y crea los usuarios (operarios y administradores) de su propia empresa,
// dentro de los límites que el Superadmin definió.

function pintarCupos(empresa) {
    document.getElementById("cupos").replaceChildren(...crearMedidoresEmpresa(empresa, true).reverse());

    // Los roles sin cupo no se ofrecen en el formulario (prevención de errores, Nielsen 5).
    const selectorRol = document.getElementById("rol");
    for (const opcion of selectorRol.options) {
        const lleno = cupoLleno(empresa, opcion.value);
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

    const aviso = document.getElementById("aviso-cupo");
    aviso.hidden = Boolean(disponible);
    aviso.replaceChildren(crearConIcono("span", "", "circle-alert", ""),
        "Tu empresa alcanzó el límite de usuarios. Para crear más, pide al Superadmin que lo amplíe.");
    for (const boton of document.querySelectorAll("[data-abrir-dialogo]")) {
        boton.disabled = !disponible;
    }
}

async function iniciarPantalla() {
    const usuario = await iniciarPaginaProtegida(["ADMINISTRADOR"]);
    const lista = document.getElementById("lista-usuarios");
    const estadoVacio = document.getElementById("estado-vacio");

    const recargar = async () => {
        const usuarios = await cargarUsuarios(usuario.empresa_id, lista, estadoVacio);
        const contar = (rol) => usuarios.filter((u) => u.rol === rol).length;
        const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;
        document.getElementById("subtitulo").textContent = [
            plural(contar("OPERARIO"), "operario", "operarios"),
            plural(contar("ADMINISTRADOR"), "administrador", "administradores"),
        ].join(" · ");
        pintarCupos(await pedirApi(`/empresas/${encodeURIComponent(usuario.empresa_id)}`));
    };
    configurarCreacionUsuario(
        document.querySelectorAll("[data-abrir-dialogo]"),
        document.getElementById("dialogo-usuario"),
        usuario.empresa_id,
        recargar,
    );
    await recargar();
}

iniciarPantalla();
