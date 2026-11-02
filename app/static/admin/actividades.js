// Menú "Planeación" del Administrador (alcance, Sección 6.2): el trabajo de cualquier día. Pestañas: las
// actividades del filtro elegido agrupadas por día y los proyectos con su avance en horas. El detalle de
// una actividad o de un proyecto se abre en el panel lateral.

const ESTADOS_TERMINADOS = new Set(["COMPLETADA", "NO_REALIZADA", "CANCELADA"]);
const terminada = (actividad) => ESTADOS_TERMINADOS.has(actividad.estado);

// Cada filtro responde una pregunta del Administrador. El primero es el de todos los días.
const FILTROS = [
    { id: "por-hacer", nombre: "Por hacer", incluye: (a) => !terminada(a), recientesPrimero: false },
    { id: "sin-asignar", nombre: "Sin asignar", incluye: (a) => !terminada(a) && a.operarios.length === 0, recientesPrimero: false },
    { id: "en-curso", nombre: "En curso o pausadas", incluye: (a) => ["EN_EJECUCION", "PAUSADA"].includes(a.estado), recientesPrimero: false },
    { id: "terminadas", nombre: "Terminadas", incluye: terminada, recientesPrimero: true },
    { id: "todas", nombre: "Todas", incluye: () => true, recientesPrimero: true },
];

// Lo que hace el botón de arriba en cada pestaña.
const ACCION_POR_VISTA = {
    actividades: { texto: "Nueva actividad", alHacer: () => formulario.abrirNueva() },
    proyectos: { texto: "Nuevo proyecto", alHacer: () => abrirFormularioProyecto() },
};

let actividades = [];
let operarios = [];
let proyectos = [];
let filtroElegido = FILTROS[0];
let formulario = null;
let vista = "actividades";

const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;

// La fila cuyo detalle está en el panel lateral queda marcada mientras esté abierto.
function abrirEnPanel(fila, abrir) {
    document.querySelectorAll(".lista-admin [aria-current]").forEach((otra) => otra.removeAttribute("aria-current"));
    fila.setAttribute("aria-current", "true");
    abrir({ volverA: "Planeación", alCerrar: () => fila.removeAttribute("aria-current") });
}

// ---------- Pestaña Actividades ----------

function crearBotonFiltro(filtro) {
    const boton = crearElemento("button", "filtro-linea");
    boton.type = "button";
    boton.setAttribute("aria-pressed", String(filtro === filtroElegido));
    boton.append(
        crearElemento("span", "", filtro.nombre),
        crearElemento("span", "filtro-cantidad cifra", String(actividades.filter((a) => filtro.incluye(a)).length)),
    );
    boton.addEventListener("click", () => {
        filtroElegido = filtro;
        pintarActividades();
    });
    return boton;
}

// Los datos como frase: "Operación, Línea 2, horario flexible, 40 min" (como las filas del Operario).
function fraseDeDatos(actividad) {
    const partes = [NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria, actividad.ubicacion];
    if (!actividad.hora_programada) {
        partes.push("horario flexible");
    }
    partes.push(duracionTexto(actividad.tiempo_estimado_min));
    return partes.filter(Boolean).join(", ");
}

// Una fila: nombre con sus excepciones (Urgente, Hora fija, Retraso) y la frase de datos; después la
// prioridad como texto, quién la tiene y el estado como texto. Toda la fila abre el detalle.
function crearFilaActividad(actividad) {
    const elemento = crearElemento("li");
    const fila = crearElemento("button", "fila-admin");
    fila.type = "button";
    fila.dataset.foco = `actividad-${actividad.id}`;

    const textos = crearElemento("span", "fila-admin-textos");
    const nombre = crearElemento("span", "fila-admin-nombre");
    nombre.append(crearElemento("strong", "", actividad.titulo),
        ...crearEtiquetasDeExcepcion(actividad, { conHora: true }).filter((e) => !e.classList.contains("prioridad-urgente")));
    const datos = crearElemento("span", "fila-admin-datos texto-secundario");
    datos.append(crearElemento("span", "codigo", actividad.codigo), ` ${fraseDeDatos(actividad)}`);
    textos.append(nombre, datos);

    const prioridad = actividad.prioridad === "URGENTE" && !terminada(actividad)
        ? crearSenalPrioridad("URGENTE")
        : crearPrioridadComoTexto(actividad.prioridad);
    const nombres = actividad.operarios.map((o) => o.nombre.split(" ")[0]);
    const quien = crearElemento("span", nombres.length ? "fila-admin-quien" : "fila-admin-quien texto-secundario",
        nombres.length ? nombres.join(", ") : "Sin asignar");
    const estado = crearElemento("span", "fila-admin-estado");
    estado.append(crearEstadoComoTexto(actividad.estado));
    if (!actividad.lista_para_iniciar && !terminada(actividad)) {
        estado.append(crearConIcono("span", "linea-info", "info", "Falta información"));
    }
    fila.append(textos, prioridad, quien, estado);
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.addEventListener("click", () => abrirEnPanel(fila, (opciones) => formulario.abrirDetalle(actividad, opciones)));
    elemento.append(fila);
    return elemento;
}

// "Hoy, sábado 31 de octubre": el día que agrupa sus actividades (Gestalt: proximidad).
function crearEncabezadoDia(fecha, cantidad) {
    const hoy = fechaTexto(new Date());
    const texto = fechaLarga(fechaDesdeTexto(fecha));
    const encabezado = crearElemento("li", "grupo-dia-admin");
    encabezado.append(
        crearElemento("span", "", fecha === hoy ? `Hoy, ${texto}` : texto.charAt(0).toUpperCase() + texto.slice(1)),
        crearElemento("span", "cantidad cifra", String(cantidad)),
    );
    return encabezado;
}

function agruparPorDia(visibles) {
    const grupos = new Map();
    for (const actividad of visibles) {
        if (!grupos.has(actividad.fecha_programada)) {
            grupos.set(actividad.fecha_programada, []);
        }
        grupos.get(actividad.fecha_programada).push(actividad);
    }
    const fechas = [...grupos.keys()].sort((a, b) => a.localeCompare(b));
    if (filtroElegido.recientesPrimero) {
        fechas.reverse();
    }
    return fechas.map((fecha) => [fecha, ordenarActividades(grupos.get(fecha))]);
}

function pintarActividades() {
    document.getElementById("lista-filtros").replaceChildren(...FILTROS.map(crearBotonFiltro));
    const visibles = actividades.filter((a) => filtroElegido.incluye(a));
    const lista = document.getElementById("lista-actividades");
    lista.hidden = visibles.length === 0;
    document.getElementById("sin-actividades").hidden = visibles.length > 0;
    document.getElementById("sin-actividades-titulo").textContent = actividades.length
        ? `Nada en "${filtroElegido.nombre}"`
        : "Todavía no hay actividades";
    document.getElementById("sin-actividades-texto").textContent = actividades.length
        ? "Elige otro filtro para ver las demás actividades."
        : "Crea una actividad con \"Nueva actividad\" y asígnala a uno o varios operarios.";
    reemplazarSiCambia(lista, agruparPorDia(visibles).flatMap(([fecha, delDia]) =>
        [crearEncabezadoDia(fecha, delDia.length), ...delDia.map(crearFilaActividad)]));
}

// ---------- Pestaña Proyectos ----------

function textoAvance(avance) {
    return `${duracionTexto(avance.minutos_finalizados)} de ${duracionTexto(avance.minutos_totales)} finalizadas`;
}

function crearBarraAvance(avance) {
    const barra = crearElemento("span", "avance-barra");
    barra.setAttribute("aria-hidden", "true");
    const lleno = crearElemento("span", "avance-barra-lleno");
    lleno.style.width = `${avance.porcentaje}%`;
    barra.append(lleno);
    return barra;
}

function crearFilaProyecto(proyecto) {
    const elemento = crearElemento("li");
    const fila = crearElemento("button", "fila-admin fila-proyecto");
    fila.type = "button";
    const textos = crearElemento("span", "fila-admin-textos");
    textos.append(crearElemento("strong", "fila-admin-nombre", proyecto.nombre));
    if (proyecto.descripcion) {
        textos.append(crearElemento("span", "fila-admin-datos texto-secundario", proyecto.descripcion));
    }
    const avance = crearElemento("span", "fila-proyecto-avance");
    avance.append(crearElemento("span", "cifra", `${textoAvance(proyecto.avance)}, ${proyecto.avance.porcentaje} %`),
        crearBarraAvance(proyecto.avance));
    fila.append(textos, avance,
        crearElemento("span", "cifra texto-secundario", plural(proyecto.avance.actividades, "actividad", "actividades")));
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.addEventListener("click", () => abrirEnPanel(fila, (opciones) => abrirDetalleProyecto(proyecto.id, opciones)));
    elemento.append(fila);
    return elemento;
}

function pintarProyectos() {
    const lista = document.getElementById("lista-proyectos");
    lista.hidden = proyectos.length === 0;
    document.getElementById("sin-proyectos").hidden = proyectos.length > 0;
    reemplazarSiCambia(lista, proyectos.map(crearFilaProyecto));
}

// El detalle del proyecto: su avance y sus actividades. Desde ahí se edita o se le agrega una actividad.
async function abrirDetalleProyecto(proyectoId, opciones) {
    let proyecto;
    try {
        proyecto = await pedirApi(`/proyectos/${proyectoId}`);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        opciones.alCerrar();
        return;
    }
    const contenido = [];
    if (proyecto.descripcion) {
        contenido.push(crearElemento("p", "detalle-op-descripcion", proyecto.descripcion));
    }
    const avance = crearElemento("div", "proyecto-avance");
    avance.append(crearElemento("p", "cifra", `${textoAvance(proyecto.avance)} (${proyecto.avance.porcentaje} %)`),
        crearBarraAvance(proyecto.avance));
    contenido.push(avance, crearElemento("h3", "detalle-op-subtitulo",
        plural(proyecto.avance.actividades, "actividad", "actividades")));
    const lista = crearElemento("ul", "proyecto-actividades");
    for (const actividad of ordenarActividades(proyecto.actividades || [])) {
        const fila = crearElemento("li");
        const boton = crearElemento("button", "proyecto-actividad");
        boton.type = "button";
        boton.append(crearElemento("span", "", actividad.titulo), crearEstadoComoTexto(actividad.estado));
        // Abrir una actividad reemplaza el panel del proyecto por el de la actividad.
        boton.addEventListener("click", () => formulario.abrirDetalle(actividad, { volverA: "Planeación" }));
        fila.append(boton);
        lista.append(fila);
    }
    if (!lista.children.length) {
        lista.append(crearElemento("li", "texto-secundario", "Este proyecto todavía no tiene actividades."));
    }
    contenido.push(lista);
    abrirPanelLateral({
        marca: "Proyecto", titulo: proyecto.nombre, contenido, ...opciones,
        acciones: [
            { texto: "Agregar actividad", clase: "boton", alHacer: async () => formulario.abrirNueva({ proyecto_id: proyecto.id }) },
            { texto: "Editar proyecto", clase: "boton-secundario", alHacer: async () => abrirFormularioProyecto(proyecto) },
        ],
    });
}

// Crear o editar un proyecto: nombre (obligatorio) y descripción.
function abrirFormularioProyecto(proyecto = null) {
    const nombre = crearElemento("input");
    nombre.id = "proyecto-nombre";
    nombre.maxLength = 120;
    nombre.required = true;
    nombre.value = proyecto?.nombre || "";
    const descripcion = crearElemento("textarea");
    descripcion.id = "proyecto-descripcion";
    descripcion.rows = 3;
    descripcion.value = proyecto?.descripcion || "";
    const etiquetaNombre = crearElemento("label", "", "Nombre");
    etiquetaNombre.htmlFor = nombre.id;
    const etiquetaDescripcion = crearElemento("label", "", "Descripción (opcional)");
    etiquetaDescripcion.htmlFor = descripcion.id;
    abrirDialogoAccion({
        titulo: proyecto ? "Editar proyecto" : "Nuevo proyecto",
        campos: [etiquetaNombre, nombre, etiquetaDescripcion, descripcion],
        textoConfirmar: proyecto ? "Guardar cambios" : "Crear proyecto",
        alConfirmar: async () => {
            const datos = { nombre: nombre.value, descripcion: descripcion.value };
            await (proyecto ? enviarJson(`/proyectos/${proyecto.id}`, "PUT", datos) : enviarJson("/proyectos", "POST", datos));
            await cargar();
            mostrarAviso(proyecto ? "Proyecto guardado." : "Proyecto creado.");
        },
    });
}

// ---------- Encabezado y carga ----------

function pintarResumen() {
    const porHacer = actividades.filter((a) => !terminada(a));
    const sinAsignar = porHacer.filter((a) => a.operarios.length === 0).length;
    const partes = [plural(porHacer.length, "actividad por hacer", "actividades por hacer")];
    if (sinAsignar) {
        partes.push(`${sinAsignar} sin asignar`);
    }
    document.getElementById("resumen").textContent = partes.join(", ");
}

function pintarAccionPrincipal() {
    const accion = ACCION_POR_VISTA[vista];
    const boton = document.getElementById("accion-principal");
    boton.hidden = !accion;
    if (accion) {
        boton.textContent = accion.texto;
    }
}

function pintar() {
    pintarResumen();
    pintarActividades();
    pintarProyectos();
}

async function cargar() {
    try {
        [actividades, proyectos] = await Promise.all([pedirApi("/actividades"), pedirApi("/proyectos")]);
        pintar();
    } catch (error) {
        mostrarAviso(`No se pudieron cargar las actividades: ${error.message}`, "advertencia");
    }
}

async function cargarOperarios(usuario) {
    const usuarios = await pedirApi(`/usuarios?empresa_id=${encodeURIComponent(usuario.empresa_id)}`);
    operarios = usuarios.filter((u) => u.rol === "OPERARIO" && u.activo !== false);
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(async (usuario) => {
    formulario = crearFormularioActividad({
        obtenerProyectos: () => proyectos,
        obtenerOperarios: () => operarios,
        alGuardar: cargar,
    });
    document.getElementById("accion-principal").addEventListener("click", () => ACCION_POR_VISTA[vista]?.alHacer());
    iniciarPestanas(document.querySelector(".pestanas"), (elegida) => {
        vista = elegida;
        pintarAccionPrincipal();
    });
    await Promise.all([cargar(), cargarOperarios(usuario)]);
});
