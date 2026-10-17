// Superadmin dentro de una empresa: ve sus datos y límites, la edita y crea sus administradores.

const empresaId = new URLSearchParams(window.location.search).get("id");
const lista = document.getElementById("lista-usuarios");
const estadoVacio = document.getElementById("estado-vacio");
const dialogoEditar = document.getElementById("dialogo-editar");
let empresa = null;

function pintarEmpresa() {
    const titulo = document.getElementById("nombre-empresa");
    titulo.textContent = empresa.nombre;
    if (empresa.activa === false) {
        titulo.append(" ", crearConIcono("span", "etiqueta", "minus", "Desactivada"));
    }
    const activa = document.getElementById("boton-activa");
    activa.textContent = empresa.activa === false ? "Reactivar empresa" : "Desactivar empresa";
    activa.classList.toggle("peligro", empresa.activa !== false);
    document.getElementById("migas-empresa").textContent = empresa.nombre;
    document.getElementById("meta-empresa").textContent = empresa.sector;
    document.getElementById("dato-nit").textContent = empresa.nit;
    document.getElementById("dato-sector").textContent = empresa.sector;
    document.getElementById("dato-direccion").textContent = empresa.direccion;
    document.title = `${empresa.nombre} — GestLab`;

    document.getElementById("logo-empresa").replaceChildren(crearLogoCuadro(empresa, true));
    document.getElementById("limites").replaceChildren(...crearMedidoresEmpresa(empresa, true));

    // Con el límite alcanzado, el botón se desactiva y una nota explica por qué (prevención de errores, Nielsen 5).
    const lleno = limiteAlcanzado(empresa, "ADMINISTRADOR");
    const aviso = document.getElementById("aviso-limite");
    aviso.hidden = !lleno;
    aviso.replaceChildren(crearConIcono("span", "", "circle-alert", ""),
        "Se alcanzó el límite de administradores. Para crear otro, amplía el límite en “Editar empresa”.");
    for (const boton of document.querySelectorAll("[data-abrir-dialogo]")) {
        boton.disabled = lleno;
    }
}

async function cargarEmpresa() {
    empresa = await pedirApi(`/empresas/${encodeURIComponent(empresaId)}`);
    pintarEmpresa();
}

async function cargarListaUsuarios() {
    const usuarios = await cargarUsuarios(empresaId, lista, estadoVacio, null, {
        alCambiar: async () => {
            await cargarListaUsuarios();
            await cargarEmpresa();
        },
    });
    document.getElementById("cantidad-usuarios").textContent = usuarios.length || "";
}

// Una empresa no se borra: se desactiva y se puede reactivar (alcance, Sección 4).
function configurarActiva() {
    const boton = document.getElementById("boton-activa");
    boton.addEventListener("click", async () => {
        if (empresa.activa === false) {
            boton.disabled = true;
            try {
                await pedirApi(`/empresas/${encodeURIComponent(empresaId)}/reactivar`, { method: "POST" });
                await cargarEmpresa();
                mostrarAviso(`Se reactivó ${empresa.nombre}.`);
            } catch (error) {
                mostrarAviso(error.message, "advertencia");
            }
            boton.disabled = false;
            return;
        }
        abrirDialogoAccion({
            titulo: `Desactivar ${empresa.nombre}`,
            campos: [crearElemento("p", "dialogo-actividad",
                "Ninguno de sus usuarios podrá iniciar sesión. Sus datos y su historial se conservan, "
                + "y la puedes reactivar cuando quieras.")],
            textoConfirmar: "Desactivar empresa",
            iconoConfirmar: "minus",
            alConfirmar: async () => {
                await pedirApi(`/empresas/${encodeURIComponent(empresaId)}/desactivar`, { method: "POST" });
                await cargarEmpresa();
                mostrarAviso(`Se desactivó ${empresa.nombre}.`);
            },
        });
    });
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
        mostrarAviso(error.message, "advertencia");
        return;
    }

    configurarEdicion();
    configurarActiva();
    configurarCreacionUsuario(
        document.querySelectorAll("[data-abrir-dialogo]"),
        document.getElementById("dialogo-usuario"),
        empresaId,
        async () => {
            await cargarListaUsuarios();
            await cargarEmpresa();
        },
    );
    await cargarListaUsuarios();
}

iniciarPantalla();
