// Vista "Actividades" del Administrador: requerimientos a la izquierda y, a la derecha,
// las actividades del requerimiento elegido (o todas).

let requerimientos = [];
let actividades = [];
let operarios = [];
let seleccionado = null;    // id del requerimiento elegido; null = todas las actividades
let formulario = null;

const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;

// ---------- Requerimientos ----------

function crearBotonRequerimiento(id, titulo, cantidad) {
    const boton = crearElemento("button", "requerimiento");
    boton.type = "button";
    boton.setAttribute("aria-pressed", String(seleccionado === id));
    boton.append(
        crearElemento("span", "requerimiento-titulo", titulo),
        crearElemento("span", "requerimiento-cantidad cifra", String(cantidad)),
    );
    boton.addEventListener("click", () => {
        seleccionado = id;
        pintar();
    });
    return boton;
}

function pintarRequerimientos() {
    document.getElementById("lista-requerimientos").replaceChildren(
        crearBotonRequerimiento(null, "Todas las actividades", actividades.length),
        ...requerimientos.map((r) => crearBotonRequerimiento(r.id, r.titulo, r.actividades)),
    );
}

// ---------- Actividades ----------

// Celda de dos renglones: el dato principal arriba y uno de apoyo, en gris, debajo.
function crearDatoDoble(principal, apoyo) {
    const celda = crearElemento("span", "dato-doble");
    celda.append(crearElemento("span", "cifra", principal), crearElemento("span", "fila-meta cifra", apoyo));
    return celda;
}

function crearFilaActividad(actividad) {
    const elemento = crearElemento("li");
    const fila = crearElemento("button", "fila-actividad-admin");
    fila.type = "button";

    const titulo = crearElemento("span", "dato-doble");
    const meta = crearElemento("span", "fila-meta");
    meta.append(
        crearElemento("span", "codigo", actividad.codigo),
        ` · ${NOMBRE_CATEGORIA[actividad.categoria]} · ${actividad.ubicacion}`,
    );
    titulo.append(crearElemento("span", "fila-nombre", actividad.titulo), meta);

    const fecha = fechaCorta(fechaDesdeTexto(actividad.fecha_programada));
    const nombres = actividad.operarios.map((o) => o.nombre.split(" ")[0]);
    const operariosTexto = nombres.length ? nombres.slice(0, 2).join(", ") : "Sin asignar";

    fila.append(
        titulo,
        crearSenalPrioridad(actividad.prioridad),
        crearDatoDoble(
            actividad.hora_programada ? `${fecha} · ${actividad.hora_programada}` : fecha,
            duracionTexto(actividad.tiempo_estimado_min),
        ),
        crearDatoDoble(operariosTexto, nombres.length > 2 ? `y ${nombres.length - 2} más` : ""),
        crearEtiquetaEstado(actividad.estado),
    );
    fila.addEventListener("click", () => formulario.abrirEdicion(actividad));
    elemento.append(fila);
    return elemento;
}

function pintarActividades() {
    const requerimiento = requerimientos.find((r) => r.id === seleccionado);
    const visibles = seleccionado ? actividades.filter((a) => a.requerimiento_id === seleccionado) : actividades;

    const titulo = document.getElementById("titulo-requerimiento");
    titulo.replaceChildren(
        requerimiento ? requerimiento.titulo : "Todas las actividades",
        crearElemento("span", "cantidad cifra", visibles.length ? String(visibles.length) : ""),
    );
    const descripcion = document.getElementById("descripcion-requerimiento");
    descripcion.textContent = requerimiento?.descripcion || "";
    descripcion.hidden = !requerimiento?.descripcion;

    const eliminar = document.getElementById("eliminar-requerimiento");
    eliminar.hidden = !requerimiento;
    delete eliminar.dataset.confirmar;
    eliminar.textContent = "Eliminar requerimiento";

    const lista = document.getElementById("lista-actividades");
    lista.hidden = visibles.length === 0;
    document.getElementById("encabezado-lista").hidden = visibles.length === 0;
    document.getElementById("sin-actividades").hidden = visibles.length > 0;
    document.getElementById("sin-actividades-titulo").textContent =
        requerimientos.length ? "Sin actividades" : "Empieza por un requerimiento";
    document.getElementById("sin-actividades-texto").textContent = requerimientos.length
        ? "Crea una actividad y asígnala a uno o varios operarios."
        : "Registra el primer requerimiento con “Nuevo”; después podrás crearle actividades.";
    lista.replaceChildren(...ordenarActividades(visibles).map(crearFilaActividad));
}

function pintarResumen() {
    const sinAsignar = actividades.filter((a) => a.operarios.length === 0).length;
    const partes = [
        plural(requerimientos.length, "requerimiento", "requerimientos"),
        plural(actividades.length, "actividad", "actividades"),
    ];
    if (sinAsignar) {
        partes.push(`${sinAsignar} sin asignar`);
    }
    document.getElementById("resumen").textContent = partes.join(" · ");
}

function pintar() {
    pintarResumen();
    pintarRequerimientos();
    pintarActividades();
}

// ---------- Carga de datos ----------

async function cargar() {
    try {
        [requerimientos, actividades] = await Promise.all([pedirApi("/requerimientos"), pedirApi("/actividades")]);
        if (seleccionado && !requerimientos.some((r) => r.id === seleccionado)) {
            seleccionado = null;
        }
        pintar();
    } catch (error) {
        mostrarAviso(`No se pudieron cargar las actividades: ${error.message}`, "advertencia");
    }
}

async function cargarOperarios(usuario) {
    const usuarios = await pedirApi(`/usuarios?empresa_id=${encodeURIComponent(usuario.empresa_id)}`);
    operarios = usuarios.filter((u) => u.rol === "OPERARIO");
}

function configurarRequerimientos() {
    const dialogo = document.getElementById("dialogo-requerimiento");
    configurarDialogo(document.querySelectorAll("[data-abrir-requerimiento]"), dialogo);
    dialogo.querySelector("form").addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(
            dialogo,
            (datos) => (datos.titulo.trim() ? null : "Escribe el título del requerimiento."),
            async (datos) => {
                const requerimiento = await enviarJson("/requerimientos", "POST", datos);
                seleccionado = requerimiento.id;
                await cargar();
                return `Requerimiento "${requerimiento.titulo}" registrado. Ya puedes crearle actividades.`;
            },
        );
    });

    // Eliminar pide una segunda confirmación en el mismo botón, porque también borra sus actividades.
    const eliminar = document.getElementById("eliminar-requerimiento");
    eliminar.addEventListener("click", async () => {
        if (eliminar.dataset.confirmar !== "si") {
            eliminar.dataset.confirmar = "si";
            eliminar.textContent = "Se borrarán sus actividades. Confirmar";
            return;
        }
        try {
            await pedirApi(`/requerimientos/${seleccionado}`, { method: "DELETE" });
            seleccionado = null;
            await cargar();
            mostrarAviso("Requerimiento eliminado.");
        } catch (error) {
            mostrarAviso(error.message, "advertencia");
        }
    });
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(async (usuario) => {
    configurarRequerimientos();
    formulario = crearFormularioActividad({
        obtenerRequerimientos: () => requerimientos,
        obtenerOperarios: () => operarios,
        alGuardar: cargar,
    });
    document.getElementById("nueva-actividad").addEventListener("click", () =>
        formulario.abrirNueva({ requerimiento_id: seleccionado || undefined }));

    await Promise.all([cargar(), cargarOperarios(usuario)]);
});
