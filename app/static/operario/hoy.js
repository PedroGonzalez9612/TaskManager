// Vista "Hoy" del Operario: la actividad en curso con su cronómetro, la carga del día
// y la agenda de los próximos días agrupada por fecha.

const DIAS_HACIA_ATRAS = 14;    // Para encontrar actividades atrasadas.
const DIAS_HACIA_ADELANTE = 7;

const hoy = new Date();
hoy.setHours(0, 0, 0, 0);
const textoHoy = fechaTexto(hoy);

let actividades = [];
let temporizador = null;

// ---------- Resumen del día ----------

function pintarResumen(carga) {
    const seccion = document.getElementById("resumen-dia");
    const delDia = actividades.filter((a) => a.fecha_programada === textoHoy);
    const jornada = carga.operarios[0]?.jornadas[0] || { minutos: 0, porcentaje: 0, sobrecarga: false };

    const texto = crearElemento("p", "resumen-texto");
    texto.append(
        crearElemento("strong", "", delDia.length === 1 ? "1 actividad hoy" : `${delDia.length} actividades hoy`),
        crearElemento("span", "cifra", `${duracionTexto(jornada.minutos)} de ${duracionTexto(carga.capacidad_min)}`),
    );

    // Barra de avance de la jornada: el único uso del coral de marca además del logo y el avatar.
    const barra = crearElemento("div", "barra-jornada");
    barra.setAttribute("role", "img");
    barra.setAttribute("aria-label", `Carga del día: ${jornada.porcentaje} % de la jornada`);
    const relleno = crearElemento("div", "barra-jornada-relleno");
    relleno.style.width = `${Math.min(jornada.porcentaje, 100)}%`;
    barra.append(relleno);

    const pie = crearElemento("p", "resumen-pie");
    pie.append(crearElemento("span", "", "Carga de tu jornada"), crearElemento("span", "cifra", `${jornada.porcentaje} %`));

    seccion.replaceChildren(texto, barra, pie);
    if (jornada.sobrecarga) {
        seccion.append(crearConIcono("p", "aviso aviso-advertencia", "circle-alert",
            "Tienes más trabajo programado del que cabe en la jornada. Coméntalo con tu administrador."));
    }
    seccion.hidden = false;
}

// ---------- Urgente pendiente ----------

function pintarAvisoUrgente() {
    const aviso = document.getElementById("aviso-urgente");
    const urgentes = actividades.filter((a) => a.prioridad === "URGENTE" && a.estado === "ASIGNADA");
    aviso.hidden = urgentes.length === 0;
    if (urgentes.length === 0) {
        return;
    }

    const texto = urgentes.length === 1
        ? `Actividad urgente: ${urgentes[0].titulo}`
        : `Tienes ${urgentes.length} actividades urgentes pendientes`;
    const boton = crearElemento("button", "boton-claro", "Ver");
    boton.type = "button";
    boton.addEventListener("click", () => abrirDetalleOperario(urgentes[0], actividades, cargar));
    aviso.replaceChildren(crearConIcono("span", "aviso-urgente-texto", "triangle-alert", texto), boton);
}

// ---------- Actividad en curso ----------

function pintarAhora() {
    const seccion = document.getElementById("ahora");
    const enCurso = actividadEnCurso(actividades);
    clearInterval(temporizador);
    seccion.hidden = !enCurso;
    if (!enCurso) {
        return;
    }

    const cabecera = crearElemento("div", "ahora-cabecera");
    cabecera.append(crearElemento("span", "ahora-rotulo", "Ahora"), crearElemento("span", "codigo cifra", enCurso.codigo));

    const cronometro = crearElemento("p", "cronometro");
    cronometro.setAttribute("aria-label", "Tiempo en ejecución");
    const actualizar = () => { cronometro.textContent = tiempoTranscurrido(enCurso.ejecucion.fecha_inicio); };
    actualizar();
    temporizador = setInterval(actualizar, 1000);

    const lugar = crearConIcono("p", "ahora-lugar", "map-pin", enCurso.ubicacion);
    const estimado = crearConIcono("p", "ahora-lugar", "clock", `Estimado ${duracionTexto(enCurso.tiempo_estimado_min)}`);

    const acciones = crearElemento("div", "ahora-acciones");
    const detalle = crearElemento("button", "boton-secundario", "Ver detalle");
    detalle.type = "button";
    detalle.addEventListener("click", () => abrirDetalleOperario(enCurso, actividades, cargar));
    const finalizar = crearConIcono("button", "boton", "check", "Finalizar");
    finalizar.type = "button";
    finalizar.addEventListener("click", async () => {
        finalizar.disabled = true;
        try {
            await pedirApi(`/actividades/${enCurso.id}/finalizar`, { method: "POST" });
            await cargar();
            mostrarAviso(`${enCurso.codigo} finalizada.`);
        } catch (error) {
            mostrarAviso(error.message, "advertencia");
            finalizar.disabled = false;
        }
    });
    acciones.append(detalle, finalizar);

    seccion.replaceChildren(
        cabecera, crearElemento("h2", "ahora-titulo", enCurso.titulo), cronometro, lugar, estimado, acciones,
    );
}

// ---------- Agenda ----------

function crearFila(actividad) {
    const fila = crearElemento("button", `fila-actividad prioridad-${actividad.prioridad.toLowerCase()}`);
    fila.type = "button";
    if (actividad.estado === "COMPLETADA") {
        fila.classList.add("fila-finalizada");
    }

    const hora = crearElemento("span", "fila-hora cifra", actividad.hora_programada || "Sin hora");

    const contenido = crearElemento("span", "fila-contenido");
    contenido.append(
        crearElemento("strong", "fila-titulo", actividad.titulo),
        crearElemento("span", "fila-detalle", `${actividad.ubicacion} · ${duracionTexto(actividad.tiempo_estimado_min)}`),
    );

    const senales = crearElemento("span", "senales");
    senales.append(crearSenalPrioridad(actividad.prioridad), crearEtiquetaEstado(actividad.estado));

    fila.append(hora, contenido, senales);
    fila.addEventListener("click", () => abrirDetalleOperario(actividad, actividades, cargar));
    return fila;
}

function tituloDeGrupo(fecha) {
    if (fecha === textoHoy) {
        return "Hoy";
    }
    if (fecha === fechaTexto(sumarDias(hoy, 1))) {
        return "Mañana";
    }
    const texto = fechaLarga(fechaDesdeTexto(fecha));
    return texto.charAt(0).toUpperCase() + texto.slice(1);
}

function pintarAgenda() {
    const agenda = document.getElementById("agenda");
    const mensaje = document.getElementById("mensaje");

    const atrasadas = actividades.filter((a) => a.fecha_programada < textoHoy && a.estado !== "COMPLETADA");
    const vigentes = actividades.filter((a) => a.fecha_programada >= textoHoy);
    const grupos = new Map();
    if (atrasadas.length) {
        grupos.set("Atrasadas", atrasadas);
    }
    for (const actividad of vigentes) {
        const titulo = tituloDeGrupo(actividad.fecha_programada);
        grupos.set(titulo, [...(grupos.get(titulo) || []), actividad]);
    }

    mensaje.hidden = grupos.size > 0;
    mensaje.textContent = "No tienes actividades programadas para los próximos días.";

    agenda.replaceChildren(...[...grupos].map(([titulo, lista]) => {
        const seccion = crearElemento("section", "grupo-dia");
        const encabezado = crearElemento("h2", "grupo-dia-titulo", titulo);
        encabezado.append(crearElemento("span", "grupo-dia-cantidad cifra", String(lista.length)));
        const filas = crearElemento("div", "lista-agenda");
        filas.append(...lista.map(crearFila));
        seccion.append(encabezado, filas);
        return seccion;
    }));
}

// ---------- Carga de datos ----------

async function cargar() {
    const desde = fechaTexto(sumarDias(hoy, -DIAS_HACIA_ATRAS));
    const hasta = fechaTexto(sumarDias(hoy, DIAS_HACIA_ADELANTE));
    try {
        const [lista, carga] = await Promise.all([
            pedirApi(`/actividades?fecha_desde=${desde}&fecha_hasta=${hasta}`),
            pedirApi(`/analisis/carga?desde=${textoHoy}&hasta=${textoHoy}`),
        ]);
        actividades = ordenarActividades(lista);
        pintarResumen(carga);
        pintarAvisoUrgente();
        pintarAhora();
        pintarAgenda();
    } catch (error) {
        const mensaje = document.getElementById("mensaje");
        mensaje.hidden = false;
        mensaje.textContent = `No se pudieron cargar las actividades: ${error.message}`;
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then((usuario) => {
    document.getElementById("saludo").textContent = `Hola, ${usuario.nombre.split(" ")[0]}`;
    const fecha = fechaLarga(hoy);
    document.getElementById("fecha-hoy").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    cargar();
});
