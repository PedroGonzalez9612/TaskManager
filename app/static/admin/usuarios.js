// Administrador: ve y crea los usuarios (operarios y administradores) de su propia empresa,
// dentro de los límites que el Superadmin definió.

function pintarCupos(empresa) {
    const actuales = empresa.usuarios_actuales;
    document.getElementById("cupo-operarios").textContent =
        textoCupo(actuales.OPERARIO || 0, empresa.limite_operarios);
    document.getElementById("cupo-administradores").textContent =
        textoCupo(actuales.ADMINISTRADOR || 0, empresa.limite_administradores);

    // Los roles sin cupo no se ofrecen en el formulario (prevención de errores, Nielsen #5).
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

    document.getElementById("aviso-cupo").hidden = Boolean(disponible);
    for (const boton of document.querySelectorAll("[data-abrir-dialogo]")) {
        boton.disabled = !disponible;
    }
}

async function iniciarPantalla() {
    const usuario = await iniciarPaginaProtegida(["ADMINISTRADOR"]);
    const tabla = document.getElementById("tabla-usuarios");
    const estadoVacio = document.getElementById("estado-vacio");

    const cargarEmpresa = async () => {
        const empresa = await pedirApi(`/empresas/${encodeURIComponent(usuario.empresa_id)}`);
        document.getElementById("subtitulo").textContent = `Operarios y administradores de ${empresa.nombre}.`;
        pintarCupos(empresa);
    };

    const recargar = async () => {
        await cargarUsuarios(usuario.empresa_id, tabla, estadoVacio);
        await cargarEmpresa();
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
