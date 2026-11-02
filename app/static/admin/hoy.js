// Hoy del Administrador (alcance, Sección 6.2): la pantalla de entrada. Tres pestañas: Pendientes (solo lo
// que pide una decisión suya, y se resuelve ahí), Personas (cómo va cada una) y Asistencia. Los estados
// de cada persona (presencia, actividad y carga) los calcula el servidor con una sola regla.

// Los grupos de Pendientes, de lo más urgente a lo menos. Un grupo vacío no se muestra.
const GRUPOS_PENDIENTES = [
    { clave: "llegada_tarde", titulo: "Llegada tarde", fila: (p) => crearFilaLlegadaTarde(p) },
    { clave: "detenidas", titulo: "Detenidas por emergencia", fila: (p) => crearFilaDetenida(p) },
    { clave: "sin_dueno", titulo: "Sin dueño", fila: (a) => crearFilaSinDueno(a) },
    { clave: "reportes", titulo: "Reportes por revisar", fila: (r) => crearFilaReporte(r) },
    { clave: "sobrecargados", titulo: "Sobrecargados", fila: (p) => crearFilaSobrecargado(p) },
];

// Necesita atención quien pide algo del Administrador; con espacio, quien puede recibir trabajo.
const PRESENCIA_QUE_PIDE_ATENCION = ["LLEGADA_TARDE", "NO_VINO", "SIN_SALIDA", "TIEMPO_ADICIONAL"];
const FILTROS_PERSONAS = [
    {
        nombre: "Necesitan atención",
        incluye: (p) => PRESENCIA_QUE_PIDE_ATENCION.includes(p.presencia.estado)
            || p.carga.estado === "SOBRECARGADO" || p.actividad.tipo === "DETENIDA",
    },
    { nombre: "Con espacio", incluye: (p) => p.carga.estado === "CON_ESPACIO" && ["EN_TURNO", "POR_LLEGAR"].includes(p.presencia.estado) },
    { nombre: "Todas", incluye: () => true },
];

let pendientes = null;
let personas = [];
let operarios = [];
let proyectos = [];
let formulario = null;
let filtroPersonas = FILTROS_PERSONAS[0];

const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;

// ---------- Piezas compartidas de esta pantalla ----------

function crearPresencia(persona) {
    const { presencia } = persona;
    return crearConIcono("span", `presencia ${TONO_PRESENCIA[presencia.estado] || ""}`,
        ICONO_PRESENCIA[presencia.estado], textoDePresencia(presencia, persona.turno));
}

function textoCarga(carga) {
    return `${duracionTexto(carga.minutos)} de ${duracionTexto(carga.capacidad_min)}`;
}

function crearCarga(carga) {
    const contenedor = crearElemento("span", "persona-carga");
    const texto = crearElemento("span", "cifra", textoCarga(carga));
    const barra = crearElemento("span", `avance-barra${carga.estado === "SOBRECARGADO" ? " avance-barra-exceso" : ""}`);
    barra.setAttribute("aria-hidden", "true");
    const lleno = crearElemento("span", "avance-barra-lleno");
    lleno.style.width = `${Math.min(100, carga.porcentaje)}%`;
    barra.append(lleno);
    contenedor.append(texto, barra);
    if (carga.estado === "SOBRECARGADO") {
        contenedor.append(crearConIcono("span", "persona-exceso", "triangle-alert", `Sobrecargado, ${carga.porcentaje} %`));
    }
    return contenedor;
}

// Qué está haciendo, como frase: lo que tiene en curso, lo detenido o nada.
function crearAhora(persona) {
    const { actividad, presencia } = persona;
    if (actividad.tipo === "EN_CURSO") {
        return crearElemento("span", "", `${actividad.titulo}, ${duracionTexto(actividad.minutos)} de ${duracionTexto(actividad.tiempo_estimado_min)}`);
    }
    if (actividad.tipo === "DETENIDA") {
        return crearConIcono("span", "persona-exceso", "triangle-alert", `Detenida: ${actividad.titulo}`);
    }
    const trabajando = ["EN_TURNO", "TIEMPO_ADICIONAL"].includes(presencia.estado);
    return trabajando
        ? crearElemento("span", "texto-secundario", "Sin actividad en curso")
        : crearElemento("span", "texto-secundario persona-sin-dato", "—");
}

function crearBoton(texto, clase, alHacer, nombreIcono = null) {
    const boton = nombreIcono ? crearConIcono("button", clase, nombreIcono, texto) : crearElemento("button", clase, texto);
    boton.type = "button";
    boton.addEventListener("click", alHacer);
    return boton;
}

// Una fila de Pendientes: lo que es, una frase con el dato y sus acciones a la derecha.
function crearFilaPendiente(titulo, datos, acciones) {
    const fila = crearElemento("li", "fila-pendiente");
    const textos = crearElemento("div", "fila-admin-textos");
    textos.append(titulo, ...datos);
    const zona = crearElemento("div", "fila-pendiente-acciones");
    zona.append(...acciones);
    fila.append(textos, zona);
    return fila;
}

function crearNombre(texto, ...junto) {
    const nombre = crearElemento("span", "fila-admin-nombre");
    nombre.append(crearElemento("strong", "", texto), ...junto);
    return nombre;
}

function minutosDesde(momento) {
    return Math.max(0, Math.round((Date.now() - new Date(momento).getTime()) / 60000));
}

// ---------- Pendientes ----------

function crearFilaLlegadaTarde(persona) {
    const minutos = persona.actividades.reduce((suma, a) => suma + a.tiempo_estimado_min, 0);
    const datos = crearElemento("p", "fila-admin-datos texto-secundario");
    datos.textContent = persona.actividades.length
        ? `${plural(persona.actividades.length, "actividad", "actividades")} hoy sin iniciar, ${duracionTexto(minutos)}`
        : "No tiene actividades hoy sin iniciar";
    const acciones = persona.actividades.length
        ? [crearBoton("Reasignar su trabajo", "boton-secundario", () => abrirReasignar(persona.actividades, persona))]
        : [];
    return crearFilaPendiente(crearNombre(persona.nombre, crearPresencia(persona)), [datos], acciones);
}

async function verDetalle(actividadId) {
    try {
        formulario.abrirDetalle(await pedirApi(`/actividades/${actividadId}`), { volverA: "Hoy" });
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
    }
}

function crearFilaDetenida(persona) {
    const { actividad } = persona;
    const hora = crearConIcono("span", "etiqueta etiqueta-hora-fija", "lock", `Hora fija ${actividad.hora_programada}`);
    const datos = crearElemento("p", "fila-admin-datos texto-secundario",
        `${persona.nombre} la detuvo: ${actividad.motivo}, hace ${duracionTexto(minutosDesde(actividad.desde))}`);
    return crearFilaPendiente(crearNombre(actividad.titulo, hora), [datos],
        [crearBoton("Ver detalle", "boton-secundario", () => verDetalle(actividad.id))]);
}

function crearFilaSinDueno(actividad) {
    const nombre = crearNombre(actividad.titulo, ...crearEtiquetasDeExcepcion(actividad, { conHora: true }));
    const datos = crearElemento("p", "fila-admin-datos texto-secundario datos-linea");
    datos.append(crearElemento("span", "codigo", actividad.codigo), crearPrioridadComoTexto(actividad.prioridad),
        crearElemento("span", "cifra", duracionTexto(actividad.tiempo_estimado_min)));
    const lineas = [datos];
    const devolucion = (actividad.devoluciones || []).at(-1);
    if (actividad.estado === "DEVUELTA" && devolucion) {
        lineas.push(crearConIcono("p", "linea-info", "undo-2", `Devuelta por ${devolucion.operario_nombre}: ${devolucion.motivo}`));
    }
    return crearFilaPendiente(nombre, lineas, [crearBoton("Asignar", "boton-secundario", () => formulario.abrirEdicion(actividad), "users")]);
}

// Convertir un reporte: el formulario de actividad ya lleno con lo reportado y asignado a quien lo reportó.
function convertirReporte(reporte) {
    formulario.abrirNueva({
        titulo: reporte.titulo,
        descripcion: [`Pedido por ${reporte.pedido_por}.`, reporte.detalle].filter(Boolean).join("\n"),
        tiempo_estimado_min: reporte.tiempo_estimado_min,
        fecha_programada: fechaTexto(new Date()),
        operario_ids: [reporte.operario_id],
    }, { ruta: `/reportes/${reporte.id}/convertir`, titulo: "Convertir el reporte en actividad" });
}

function descartarReporte(reporte) {
    const motivo = crearElemento("textarea");
    motivo.id = "descartar-motivo";
    motivo.rows = 3;
    motivo.maxLength = 1000;
    const etiqueta = crearElemento("label", "", "Motivo");
    etiqueta.htmlFor = motivo.id;
    abrirDialogoAccion({
        titulo: "Descartar el reporte",
        subtitulo: `${reporte.titulo} (reporte de ${reporte.operario_nombre})`,
        campos: [etiqueta, motivo, crearElemento("p", "ayuda-campo", "No se borra: el operario ve que se descartó y el motivo.")],
        textoConfirmar: "Descartar reporte",
        iconoConfirmar: "minus",
        textoCerrar: "Volver",
        alConfirmar: async () => {
            await enviarJson(`/reportes/${reporte.id}/descartar`, "POST", { motivo: motivo.value });
            await cargar();
            mostrarAviso("Reporte descartado.");
        },
    });
}

function crearFilaReporte(reporte) {
    const datos = crearElemento("p", "fila-admin-datos texto-secundario datos-linea");
    datos.append(crearElemento("span", "", `Reporte de ${reporte.operario_nombre}`),
        crearElemento("span", "", `Pedido por ${reporte.pedido_por}`));
    if (reporte.tiempo_estimado_min) {
        datos.append(crearElemento("span", "cifra", duracionTexto(reporte.tiempo_estimado_min)));
    }
    const lineas = [datos];
    if (reporte.detalle) {
        lineas.push(crearElemento("p", "fila-admin-datos", reporte.detalle));
    }
    return crearFilaPendiente(crearNombre(reporte.titulo), lineas, [
        crearBoton("Convertir en actividad", "boton-secundario", () => convertirReporte(reporte), "plus"),
        crearBoton("Descartar", "boton-terciario boton-baja", () => descartarReporte(reporte)),
    ]);
}

function crearFilaSobrecargado(persona) {
    const datos = crearElemento("p", "fila-admin-datos texto-secundario cifra",
        `${textoCarga(persona.carga)} (${persona.carga.porcentaje} %)`);
    return crearFilaPendiente(crearNombre(persona.nombre), [datos],
        [crearBoton("Ver su día", "boton-secundario", () => abrirPersona(persona))]);
}

function pintarPendientes() {
    const contenedor = document.getElementById("grupos-pendientes");
    const grupos = GRUPOS_PENDIENTES.filter((grupo) => pendientes[grupo.clave].length).map((grupo) => {
        const seccion = crearElemento("section", "grupo-pendiente");
        const titulo = crearElemento("h2", "titulo-con-cantidad", grupo.titulo);
        titulo.append(crearElemento("span", "cantidad cifra", String(pendientes[grupo.clave].length)));
        const lista = crearElemento("ul", "lista-admin");
        lista.append(...pendientes[grupo.clave].map(grupo.fila));
        seccion.append(titulo, lista);
        return seccion;
    });
    contenedor.replaceChildren(...grupos);
    document.getElementById("sin-pendientes").hidden = pendientes.total > 0;
    document.getElementById("cantidad-pendientes").textContent = pendientes.total ? String(pendientes.total) : "";
    pintarCantidadDelMenu(pendientes.total);
}

// ---------- Reasignar (alcance, Sección 5.1: solo lo que nadie ha iniciado) ----------

// Quién puede recibir el trabajo: los demás operarios, primero los que tienen espacio.
function candidatosPara(persona) {
    const orden = { CON_ESPACIO: 0, NORMAL: 1, SOBRECARGADO: 2 };
    return personas
        .filter((p) => p.id !== persona.id && !["NO_VINO", "LLEGADA_TARDE"].includes(p.presencia.estado))
        .sort((a, b) => orden[a.carga.estado] - orden[b.carga.estado] || a.carga.minutos - b.carga.minutos);
}

function abrirReasignar(actividades, persona) {
    const candidatos = candidatosPara(persona);
    const selectores = actividades.map((actividad, indice) => {
        const selector = crearElemento("select");
        selector.id = `reasignar-${indice}`;
        selector.append(new Option("Dejar en su día", ""));
        for (const candidato of candidatos) {
            const libre = Math.max(0, candidato.carga.capacidad_min - candidato.carga.minutos);
            selector.append(new Option(`${candidato.nombre}: ${textoDePresencia(candidato.presencia, candidato.turno).toLowerCase()}, ${duracionTexto(libre)} libres`, candidato.id));
        }
        const etiqueta = crearElemento("label", "", `${actividad.titulo} (${duracionTexto(actividad.tiempo_estimado_min)})`);
        etiqueta.htmlFor = selector.id;
        return { actividad, etiqueta, selector };
    });
    abrirDialogoAccion({
        titulo: `Reasignar el trabajo de ${persona.nombre}`,
        subtitulo: "Elige a quién pasarle cada actividad. Primero aparece quien tiene más espacio.",
        campos: selectores.flatMap(({ etiqueta, selector }) => [etiqueta, selector]),
        textoConfirmar: "Reasignar",
        iconoConfirmar: "users",
        alConfirmar: async () => {
            const cambios = selectores.filter(({ selector }) => selector.value);
            for (const { actividad, selector } of cambios) {
                const otros = actividad.operarios.map((o) => o.id).filter((id) => id !== persona.id);
                await enviarJson(`/actividades/${actividad.id}`, "PUT", { operario_ids: [...otros, selector.value] });
            }
            await cargar();
            mostrarAviso(cambios.length ? `${plural(cambios.length, "actividad reasignada", "actividades reasignadas")}.` : "Nada cambió.");
        },
    });
}

// ---------- Personas ----------

function crearFilaPersona(persona) {
    const elemento = crearElemento("li");
    const fila = crearElemento("button", "fila-admin fila-persona");
    fila.type = "button";
    fila.dataset.foco = `persona-${persona.id}`;
    const nombre = crearElemento("span", "fila-admin-textos");
    nombre.append(crearElemento("strong", "fila-admin-nombre", persona.nombre));
    if (persona.turno) {
        nombre.append(crearElemento("span", "fila-admin-datos texto-secundario cifra",
            `Turno de ${persona.turno.hora_inicio} a ${persona.turno.hora_fin}`));
    }
    fila.append(nombre, crearPresencia(persona), crearAhora(persona), crearCarga(persona.carga));
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.addEventListener("click", () => {
        document.querySelectorAll(".lista-admin [aria-current]").forEach((otra) => otra.removeAttribute("aria-current"));
        fila.setAttribute("aria-current", "true");
        abrirPersona(persona, () => fila.removeAttribute("aria-current"));
    });
    elemento.append(fila);
    return elemento;
}

function pintarPersonas() {
    document.getElementById("filtros-personas").replaceChildren(...FILTROS_PERSONAS.map((filtro) => {
        const boton = crearElemento("button", "filtro-linea");
        boton.type = "button";
        boton.setAttribute("aria-pressed", String(filtro === filtroPersonas));
        boton.append(crearElemento("span", "", filtro.nombre),
            crearElemento("span", "filtro-cantidad cifra", String(personas.filter(filtro.incluye).length)));
        boton.addEventListener("click", () => {
            filtroPersonas = filtro;
            pintarPersonas();
        });
        return boton;
    }));
    const busqueda = document.getElementById("buscar-persona").value.trim().toLowerCase();
    const visibles = personas.filter((p) => filtroPersonas.incluye(p) && p.nombre.toLowerCase().includes(busqueda));
    reemplazarSiCambia(document.getElementById("lista-personas"), visibles.map(crearFilaPersona));
    document.getElementById("sin-personas").hidden = visibles.length > 0;
}

// El día de una persona, en el panel lateral: lo que la programación del día le tiene, en orden. Lo
// que nadie ha iniciado se puede reasignar desde aquí.
async function abrirPersona(persona, alCerrar = null) {
    let programacion;
    try {
        programacion = await pedirApi(`/programacion-del-dia?operario_id=${encodeURIComponent(persona.id)}`);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        alCerrar?.();
        return;
    }
    const porId = new Map(programacion.actividades.map((a) => [a.id, a]));
    const datos = crearElemento("dl", "lista-datos");
    for (const [nombre, valor] of [["Ahora", crearAhora(persona)], ["Carga", crearCarga(persona.carga)]]) {
        const dd = crearElemento("dd");
        dd.append(valor);
        datos.append(crearElemento("dt", "", nombre), dd);
    }
    const lista = crearElemento("ol", "dia-persona");
    for (const tramo of programacion.tramos) {
        const actividad = porId.get(tramo.actividad_id);
        if (!actividad) {
            continue;
        }
        const fila = crearElemento("li", "dia-persona-fila");
        const hora = `${tramo.aproximada ? "~" : ""}${horaDeMomento(tramo.inicio)}`;
        const textos = crearElemento("div", "fila-admin-textos");
        textos.append(crearNombre(actividad.titulo, ...crearEtiquetasDeExcepcion(actividad)),
            crearEstadoComoTexto(actividad.estado));
        fila.append(crearElemento("span", "cifra dia-persona-hora", hora), textos);
        if (actividad.estado === "ASIGNADA" && !tramo.parte) {
            fila.append(crearBoton("Reasignar", "boton-texto", () => abrirReasignar([actividad], persona)));
        }
        lista.append(fila);
    }
    if (!lista.children.length) {
        lista.append(crearElemento("li", "texto-secundario", "No tiene actividades en esta jornada."));
    }
    abrirPanelLateral({
        marca: persona.turno ? `Turno de ${persona.turno.hora_inicio} a ${persona.turno.hora_fin}` : "Sin turno",
        titulo: persona.nombre,
        antesDelTitulo: [crearPresencia(persona)],
        contenido: [datos, crearElemento("h3", "detalle-op-subtitulo", "Su día"), lista],
        volverA: "Hoy",
        alCerrar,
    });
}

// ---------- Encabezado y carga ----------

function pintarResumen() {
    const conTurno = personas.filter((p) => p.presencia.estado !== "SIN_TURNO");
    const cuenta = new Map();
    for (const persona of conTurno) {
        cuenta.set(persona.presencia.estado, (cuenta.get(persona.presencia.estado) || 0) + 1);
    }
    const partes = [...cuenta].map(([estado, cantidad]) => `${cantidad} ${NOMBRE_PRESENCIA[estado].toLowerCase()}`);
    const trabajo = personas.reduce((suma, p) => suma + p.carga.minutos, 0);
    const capacidad = conTurno.reduce((suma, p) => suma + p.carga.capacidad_min, 0);
    document.getElementById("resumen").textContent = conTurno.length
        ? `${plural(conTurno.length, "persona con turno", "personas con turno")}: ${partes.join(", ")}. ${duracionTexto(trabajo)} de trabajo para ${duracionTexto(capacidad)} de capacidad.`
        : "Nadie tiene turno hoy.";
}

async function cargar() {
    try {
        [pendientes, personas] = await Promise.all([pedirApi("/hoy/pendientes"), pedirApi("/hoy/personas")]);
        pintarResumen();
        pintarPendientes();
        pintarPersonas();
        await cargarAsistencia();
    } catch (error) {
        mostrarAviso(`No se pudo cargar el día: ${error.message}`, "advertencia");
    }
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(async (usuario) => {
    const fecha = fechaLarga(new Date());
    document.getElementById("fecha-hoy").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    formulario = crearFormularioActividad({
        obtenerProyectos: () => proyectos,
        obtenerOperarios: () => operarios,
        alGuardar: cargar,
    });
    document.getElementById("nueva-actividad").addEventListener("click", () => formulario.abrirNueva());
    document.getElementById("buscar-persona").addEventListener("input", pintarPersonas);
    iniciarPestanas(document.querySelector(".pestanas"));
    configurarAsistencia();
    const [usuarios, listaProyectos] = await Promise.all([
        pedirApi(`/usuarios?empresa_id=${encodeURIComponent(usuario.empresa_id)}`),
        pedirApi("/proyectos"),
        cargar(),
    ]);
    operarios = usuarios.filter((u) => u.rol === "OPERARIO" && u.activo !== false);
    proyectos = listaProyectos;
    // Lo que cambia con el reloj (presencia, minutos en curso) se vuelve a pedir cada minuto.
    setInterval(() => !document.querySelector("dialog[open]") && cargar(), 60000);
});
