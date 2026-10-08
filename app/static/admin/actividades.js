// Vista "Actividades" del Administrador: requerimientos a la izquierda y, a la derecha,
// las actividades del requerimiento elegido (o todas).

let requerimientos = [];
let actividades = [];
let operarios = [];
let seleccionado = null;    // id del requerimiento elegido; null = todas las actividades
let formulario = null;

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
    const lista = document.getElementById("lista-requerimientos");
    document.getElementById("sin-requerimientos").hidden = requerimientos.length > 0;
    lista.hidden = requerimientos.length === 0;
    lista.replaceChildren(
        crearBotonRequerimiento(null, "Todas las actividades", actividades.length),
        ...requerimientos.map((r) => crearBotonRequerimiento(r.id, r.titulo, r.actividades)),
    );
}

// ---------- Actividades ----------

function crearFilaActividad(actividad) {
    const fila = crearElemento("tr");
    fila.tabIndex = 0;

    const celda = (contenido, clase = "") => {
        const td = crearElemento("td", clase);
        td.append(contenido);
        return td;
    };
    const fecha = fechaCorta(fechaDesdeTexto(actividad.fecha_programada));
    const programada = actividad.hora_programada ? `${fecha} · ${actividad.hora_programada}` : fecha;

    const titulo = crearElemento("div");
    titulo.append(
        crearElemento("strong", "", actividad.titulo),
        crearElemento("div", "texto-suave", `${NOMBRE_CATEGORIA[actividad.categoria]} · ${actividad.ubicacion}`),
    );

    fila.append(
        celda(actividad.codigo, "cifra"),
        celda(titulo, "celda-principal"),
        celda(crearSenalPrioridad(actividad.prioridad)),
        celda(crearEtiquetaEstado(actividad.estado)),
        celda(programada, "cifra"),
        celda(duracionTexto(actividad.tiempo_estimado_min), "cifra"),
        celda(actividad.operarios.map((o) => o.nombre).join(", ") || "—"),
    );

    const abrir = () => formulario.abrirEdicion(actividad);
    fila.addEventListener("click", abrir);
    fila.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            abrir();
        }
    });
    return fila;
}

function pintarActividades() {
    const requerimiento = requerimientos.find((r) => r.id === seleccionado);
    const visibles = seleccionado ? actividades.filter((a) => a.requerimiento_id === seleccionado) : actividades;

    document.getElementById("titulo-requerimiento").textContent =
        requerimiento ? requerimiento.titulo : "Todas las actividades";
    document.getElementById("descripcion-requerimiento").textContent = requerimiento?.descripcion || "";

    const eliminar = document.getElementById("eliminar-requerimiento");
    eliminar.hidden = !requerimiento;
    delete eliminar.dataset.confirmar;
    eliminar.textContent = "Eliminar requerimiento";

    const tabla = document.getElementById("tabla-actividades");
    tabla.hidden = visibles.length === 0;
    document.getElementById("sin-actividades").hidden = visibles.length > 0;
    tabla.querySelector("tbody").replaceChildren(...ordenarActividades(visibles).map(crearFilaActividad));
}

function pintar() {
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
            eliminar.textContent = "Se borrarán sus actividades. Toca de nuevo";
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
