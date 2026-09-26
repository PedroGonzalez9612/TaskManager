// Superadmin dentro de una empresa: ve sus datos y cupos, la edita y crea sus administradores.

const empresaId = new URLSearchParams(window.location.search).get("id");
const tabla = document.getElementById("tabla-usuarios");
const estadoVacio = document.getElementById("estado-vacio");
const dialogoEditar = document.getElementById("dialogo-editar");
let empresa = null;

function pintarEmpresa() {
    const actuales = empresa.usuarios_actuales;
    document.getElementById("nombre-empresa").textContent = empresa.nombre;
    document.getElementById("migas-empresa").textContent = empresa.nombre;
    document.getElementById("dato-nit").textContent = empresa.nit;
    document.getElementById("dato-sector").textContent = empresa.sector;
    document.getElementById("dato-direccion").textContent = empresa.direccion;
    document.getElementById("dato-administradores").textContent =
        textoCupo(actuales.ADMINISTRADOR || 0, empresa.limite_administradores);
    document.getElementById("dato-operarios").textContent =
        textoCupo(actuales.OPERARIO || 0, empresa.limite_operarios);
    document.title = `${empresa.nombre} — GestLab`;

    const logo = document.getElementById("logo-empresa");
    logo.hidden = !empresa.tiene_logo;
    if (empresa.tiene_logo) {
        logo.src = urlLogo(empresa.id);
        logo.alt = `Logo de ${empresa.nombre}`;
    }

    // Si ya no hay cupo, el botón se desactiva y se explica por qué (prevención de errores, Nielsen #5).
    const lleno = cupoLleno(empresa, "ADMINISTRADOR");
    document.getElementById("aviso-cupo").hidden = !lleno;
    for (const boton of document.querySelectorAll("[data-abrir-dialogo]")) {
        boton.disabled = lleno;
    }
}

async function cargarEmpresa() {
    empresa = await pedirApi(`/empresas/${encodeURIComponent(empresaId)}`);
    pintarEmpresa();
}

function configurarEdicion() {
    const botonEditar = document.getElementById("boton-editar");
    const formulario = dialogoEditar.querySelector("form");
    const campoLogo = configurarCampoLogo(dialogoEditar, () => (empresa.tiene_logo ? urlLogo(empresa.id) : null));

    configurarDialogo([botonEditar], dialogoEditar);
    botonEditar.addEventListener("click", () => {
        formulario.nombre.value = empresa.nombre;
        formulario.sector.value = empresa.sector;
        formulario.direccion.value = empresa.direccion;
        formulario.limite_administradores.value = empresa.limite_administradores ?? "";
        formulario.limite_operarios.value = empresa.limite_operarios ?? "";
        campoLogo.mostrarActual();
    });

    const validar = (datos) => {
        if ([datos.nombre, datos.sector, datos.direccion].some((valor) => !valor.trim())) {
            return "Completa nombre, sector y dirección.";
        }
        for (const limite of [datos.limite_administradores, datos.limite_operarios]) {
            if (!Number.isInteger(Number(limite)) || Number(limite) < 1) {
                return "Los límites de usuarios deben ser números enteros mayores o iguales a 1.";
            }
        }
        return validarArchivoLogo(campoLogo.archivo());
    };

    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(dialogoEditar, validar, async (datos) => {
            await enviarJson(`/empresas/${encodeURIComponent(empresaId)}`, "PUT", datos);
            const archivo = campoLogo.archivo();
            if (archivo) {
                await subirLogo(empresaId, archivo);
            }
            await cargarEmpresa();
            return "Cambios guardados.";
        });
    });
}

async function iniciarPantalla() {
    await iniciarPaginaProtegida(["SUPERADMIN"]);

    if (!empresaId) {
        window.location.href = "/static/superadmin/empresas.html";
        return;
    }

    try {
        await cargarEmpresa();
    } catch (error) {
        document.getElementById("nombre-empresa").textContent = "No se pudo abrir la empresa";
        mostrarAviso(error.message);
        return;
    }

    configurarEdicion();
    const recargar = async () => {
        await cargarUsuarios(empresaId, tabla, estadoVacio);
        await cargarEmpresa();
    };
    configurarCreacionUsuario(
        document.querySelectorAll("[data-abrir-dialogo]"),
        document.getElementById("dialogo-usuario"),
        empresaId,
        recargar,
    );
    await cargarUsuarios(empresaId, tabla, estadoVacio);
}

iniciarPantalla();
