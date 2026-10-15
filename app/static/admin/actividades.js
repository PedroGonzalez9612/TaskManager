// Vista "Actividades" del Administrador: filtros a la izquierda y, a la derecha, las actividades del
// filtro elegido agrupadas por día (alcance, Sección 6.2). Una actividad es independiente o de un
// proyecto; ya no hay requerimientos.

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

let actividades = [];
let operarios = [];
let proyectos = [];
let filtroElegido = FILTROS[0];
let formulario = null;

const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;

// ---------- Filtros ----------

function crearBotonFiltro(filtro) {
    const boton = crearElemento("button", "filtro");
    boton.type = "button";
    boton.setAttribute("aria-pressed", String(filtro === filtroElegido));
    boton.append(
        crearElemento("span", "", filtro.nombre),
        crearElemento("span", "filtro-cantidad cifra", String(actividades.filter((a) => filtro.incluye(a)).length)),
    );
    boton.addEventListener("click", () => {
        filtroElegido = filtro;
        pintar();
    });
    return boton;
}

function pintarFiltros() {
    document.getElementById("lista-filtros").replaceChildren(...FILTROS.map(crearBotonFiltro));
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
    const meta = crearElemento("span", "fila-meta datos-linea");
    meta.append(
        crearElemento("span", "codigo", actividad.codigo),
        crearElemento("span", "", NOMBRE_CATEGORIA[actividad.categoria]),
        crearElemento("span", "", actividad.ubicacion),
    );
    titulo.append(crearElemento("span", "fila-nombre", actividad.titulo), meta);

    const nombres = actividad.operarios.map((o) => o.nombre.split(" ")[0]);
    const operariosTexto = nombres.length ? nombres.slice(0, 2).join(", ") : "Sin asignar";

    fila.append(
        titulo,
        crearSenalPrioridad(actividad.prioridad),
        crearDatoDoble(
            actividad.hora_programada ? `Hora fija ${actividad.hora_programada}` : "Horario flexible",
            duracionTexto(actividad.tiempo_estimado_min),
        ),
        crearDatoDoble(operariosTexto, nombres.length > 2 ? `y ${nombres.length - 2} más` : ""),
        crearEstadoConInformacion(actividad),
    );
    fila.addEventListener("click", () => formulario.abrirDetalle(actividad));
    elemento.append(fila);
    return elemento;
}

// El estado y, si a una actividad por hacer le falta información, el aviso debajo.
function crearEstadoConInformacion(actividad) {
    const celda = crearElemento("span", "dato-doble");
    celda.append(crearEtiquetaEstado(actividad.estado));
    if (!actividad.lista_para_iniciar && !terminada(actividad)) {
        celda.append(crearEtiquetaFaltaInformacion(actividad));
    }
    return celda;
}

// "Hoy, miércoles 14 de octubre": el día que agrupa sus actividades (Gestalt: proximidad).
function crearEncabezadoDia(fecha, cantidad) {
    const hoy = fechaTexto(new Date());
    const texto = fechaLarga(fechaDesdeTexto(fecha));
    const encabezado = crearElemento("li", "grupo-dia");
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
    const visibles = actividades.filter((a) => filtroElegido.incluye(a));
    document.getElementById("titulo-lista").replaceChildren(
        filtroElegido.nombre,
        crearElemento("span", "cantidad cifra", visibles.length ? String(visibles.length) : ""),
    );

    const lista = document.getElementById("lista-actividades");
    lista.hidden = visibles.length === 0;
    document.getElementById("encabezado-lista").hidden = visibles.length === 0;
    document.getElementById("sin-actividades").hidden = visibles.length > 0;
    document.getElementById("sin-actividades-titulo").textContent = actividades.length
        ? `Nada en “${filtroElegido.nombre}”`
        : "Todavía no hay actividades";
    document.getElementById("sin-actividades-texto").textContent = actividades.length
        ? "Elige otro filtro para ver las demás actividades."
        : "Crea una actividad con “Nueva actividad” y asígnala a uno o varios operarios.";
    lista.replaceChildren(...agruparPorDia(visibles).flatMap(([fecha, delDia]) =>
        [crearEncabezadoDia(fecha, delDia.length), ...delDia.map(crearFilaActividad)]));
}

function pintarResumen() {
    const porHacer = actividades.filter((a) => !terminada(a));
    const sinAsignar = porHacer.filter((a) => a.operarios.length === 0).length;
    const partes = [plural(porHacer.length, "actividad por hacer", "actividades por hacer")];
    if (sinAsignar) {
        partes.push(`${sinAsignar} sin asignar`);
    }
    document.getElementById("resumen").textContent = partes.join(", ");
}

function pintar() {
    pintarResumen();
    pintarFiltros();
    pintarActividades();
}

// ---------- Carga de datos ----------

async function cargar() {
    try {
        actividades = await pedirApi("/actividades");
        pintar();
    } catch (error) {
        mostrarAviso(`No se pudieron cargar las actividades: ${error.message}`, "advertencia");
    }
}

async function cargarOperariosYProyectos(usuario) {
    const [usuarios, listaProyectos] = await Promise.all([
        pedirApi(`/usuarios?empresa_id=${encodeURIComponent(usuario.empresa_id)}`),
        pedirApi("/proyectos"),
    ]);
    operarios = usuarios.filter((u) => u.rol === "OPERARIO" && u.activo !== false);
    proyectos = listaProyectos;
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(async (usuario) => {
    formulario = crearFormularioActividad({
        obtenerProyectos: () => proyectos,
        obtenerOperarios: () => operarios,
        alGuardar: cargar,
    });
    document.getElementById("nueva-actividad").addEventListener("click", () => formulario.abrirNueva());

    await Promise.all([cargar(), cargarOperariosYProyectos(usuario)]);
});
