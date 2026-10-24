// Vista "Equipo" del Administrador: el tablero del turno (alcance, Secciones 6.2 y 6.5). Es la planilla
// que se pega en la pared de la planta: una fila por persona, las horas de izquierda a derecha, una
// tarjeta por actividad en su hora y la línea "Ahora". Responde cuánto trabajo tiene cada uno y cuándo.
//
// Lo ejecutado se dibuja con sus horas reales y sin los ratos en pausa. Hoy, lo pendiente se ubica con
// la programación dinámica del día de cada operario (la misma de su pantalla Hoy). Otros días, lo de
// hora fija va en su hora y lo de horario flexible en la franja "Sin hora" de la fila.

const UN_MINUTO = 60000;
const HORAS_POR_DEFECTO = [6, 18];      // Sin turnos ni actividades, el tablero muestra este rango.
const MINUTOS_MINIMOS_TARJETA = 30;     // Una tarjeta nunca se dibuja más angosta: no se podría tocar ni leer.
const MINUTOS_TARJETA_CON_ICONO = 60;   // Desde esta duración la tarjeta tiene espacio para el ícono.
const ALTO_TARJETA_REM = 3.25;          // Alto de cada sub-renglón de tarjetas (título en dos renglones), en rem.
const HORAS_VISIBLES_DIA_SIGUIENTE = 12; // Un turno de noche sigue en la mañana siguiente.

let dia = inicioDelDia(new Date());
let formulario = null;
let actividades = [];
let operarios = [];         // { id, nombre, turno, jornada, programacion }
let proyectos = [];
let capacidadPorDefecto = 0;

function inicioDelDia(fecha) {
    const copia = new Date(fecha);
    copia.setHours(0, 0, 0, 0);
    return copia;
}

const esHoy = () => fechaTexto(dia) === fechaTexto(new Date());
const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;

// Minutos desde la medianoche del día visible (pueden pasar de 1440 en un turno de noche).
function minutosDelDia(momento) {
    return (new Date(momento).getTime() - dia.getTime()) / UN_MINUTO;
}

function minutosDeHora(hora) {
    const [h, m] = hora.split(":").map(Number);
    return h * 60 + m;
}

// El turno del operario en el día visible, en minutos: [inicio, fin]. Si cruza la medianoche, el fin
// pasa de 1440.
function turnoEnMinutos(turno) {
    if (!turno) {
        return null;
    }
    const inicio = minutosDeHora(turno.hora_inicio);
    let fin = minutosDeHora(turno.hora_fin);
    if (fin <= inicio) {
        fin += 1440;
    }
    return [inicio, fin];
}

// ---------- Qué se dibuja en la fila de cada persona ----------

function dentroDelDia(inicio, fin) {
    const desde = dia.getTime();
    const hasta = desde + (24 + HORAS_VISIBLES_DIA_SIGUIENTE) * 60 * UN_MINUTO;
    return fin.getTime() > desde && inicio.getTime() < hasta;
}

// Tipo de la tarjeta de un rato trabajado, según cómo está la ejecución de esa persona.
function tipoTrabajado(ejecucion, esUltimo) {
    if (ejecucion.estado === "FINALIZADA") {
        return "hecha";
    }
    return ejecucion.estado === "EN_PROGRESO" && esUltimo ? "en-curso" : "trabajada";
}

// Los ratos trabajados del día visible: los de otros días van en su propio día.
function bloquesTrabajados(actividad, ejecucion) {
    if (!ejecucion?.fecha_inicio) {
        return [];
    }
    const segmentos = segmentosTrabajados(ejecucion);
    return segmentos
        .map(([inicio, fin], indice) => ({ actividad, inicio, fin, tipo: tipoTrabajado(ejecucion, indice === segmentos.length - 1) }))
        .filter((bloque) => dentroDelDia(bloque.inicio, bloque.fin));
}

// Lo que le falta: hoy, donde lo pone la programación del día; otro día, en su hora fija. Devuelve un
// bloque (de tipo "sin-hora" si es de horario flexible de otro día) o null si no hay nada que dibujar.
function bloquePorHacer(actividad, ejecucion, tramo) {
    if (tramo?.tipo === "EN_CURSO") {
        return { actividad, inicio: new Date(), fin: new Date(tramo.fin), tipo: "proyeccion" };
    }
    if (tramo?.tipo === "PENDIENTE") {
        return { actividad, inicio: new Date(tramo.inicio), fin: new Date(tramo.fin), tipo: "pendiente", aproximada: tramo.aproximada };
    }
    if (esHoy() || actividad.estado === "NO_REALIZADA") {
        return null;
    }
    if (actividad.hora_programada) {
        const inicio = fechaDesdeTexto(actividad.fecha_programada, actividad.hora_programada);
        const falta = Math.max(0, actividad.tiempo_estimado_min - (ejecucion?.tiempo_real_min || 0));
        return { actividad, inicio, fin: new Date(inicio.getTime() + falta * UN_MINUTO), tipo: "pendiente" };
    }
    return ejecucion?.fecha_inicio ? null : { actividad, tipo: "sin-hora" };
}

function bloquesDe(operario) {
    const bloques = [];
    const sinHora = [];
    const tramos = new Map((operario.programacion?.tramos || []).map((tramo) => [tramo.actividad_id, tramo]));
    const delOperario = actividades.filter((a) => a.operarios.some((asignado) => asignado.id === operario.id));

    for (const actividad of delOperario) {
        const ejecucion = (actividad.ejecuciones || []).find((propia) => propia.usuario_id === operario.id);
        bloques.push(...bloquesTrabajados(actividad, ejecucion));
        if (["FINALIZADA", "CERRADA"].includes(ejecucion?.estado)) {
            continue;
        }
        const porHacer = bloquePorHacer(actividad, ejecucion, tramos.get(actividad.id));
        if (porHacer?.tipo === "sin-hora") {
            sinHora.push(actividad);
        } else if (porHacer) {
            bloques.push(porHacer);
        }
    }
    return { bloques, sinHora };
}

// ---------- Rango de horas: del turno más temprano al más tardío ----------

function rangoDeHoras(filas) {
    let desde = Infinity;
    let hasta = -Infinity;
    for (const { operario, bloques } of filas) {
        const turno = turnoEnMinutos(operario.turno);
        if (turno) {
            desde = Math.min(desde, turno[0]);
            hasta = Math.max(hasta, turno[1]);
        }
        for (const bloque of bloques) {
            desde = Math.min(desde, Math.max(0, minutosDelDia(bloque.inicio)));
            hasta = Math.max(hasta, Math.min(2880, minutosDelDia(bloque.fin)));
        }
    }
    if (desde === Infinity) {
        [desde, hasta] = HORAS_POR_DEFECTO.map((hora) => hora * 60);
    }
    return [Math.floor(desde / 60), Math.max(Math.ceil(hasta / 60), Math.floor(desde / 60) + 4)];
}

// ---------- Dibujo ----------

function porcentaje(minutos, rango) {
    const [desde, hasta] = rango;
    return ((minutos - desde * 60) * 100) / ((hasta - desde) * 60);
}

function ubicar(elemento, desdeMin, hastaMin, rango) {
    const izquierda = Math.max(0, porcentaje(desdeMin, rango));
    const derecha = Math.min(100, porcentaje(hastaMin, rango));
    elemento.style.left = `${izquierda}%`;
    elemento.style.width = `${Math.max(0, derecha - izquierda)}%`;
}

function horaTexto(momento) {
    return horaCorta(momento);
}

const NOMBRE_TIPO = {
    "hecha": "Finalizada", "en-curso": "En curso", "trabajada": "Trabajada, ahora en pausa",
    "proyeccion": "Lo que le falta", "pendiente": "Por hacer",
};

// Reparte las tarjetas en sub-renglones para que ninguna tape a otra. Devuelve cuántos hacen falta.
function repartirEnRenglones(bloques) {
    const finales = [];
    const ordenados = [...bloques].sort((a, b) => a.inicio - b.inicio);
    for (const bloque of ordenados) {
        const desde = minutosDelDia(bloque.inicio);
        let renglon = finales.findIndex((fin) => fin <= desde);
        if (renglon === -1) {
            renglon = finales.length;
            finales.push(0);
        }
        bloque.renglon = renglon;
        finales[renglon] = Math.max(desde + MINUTOS_MINIMOS_TARJETA, minutosDelDia(bloque.fin));
    }
    return Math.max(1, finales.length);
}

function crearTarjetaTablero(bloque, rango) {
    const { actividad } = bloque;
    const urgente = actividad.prioridad === "URGENTE" && bloque.tipo === "pendiente";
    const clases = ["tarjeta-tablero", `tablero-${bloque.tipo}`];
    if (urgente) {
        clases.push("tablero-urgente");
    }
    if (bloque.aproximada) {
        clases.push("tablero-aproximada");
    }
    const tarjeta = crearElemento("button", clases.join(" "));
    tarjeta.type = "button";
    const icono_ = { hecha: "check", "en-curso": "play", trabajada: "pause" }[bloque.tipo] || ICONO_PRIORIDAD[actividad.prioridad];
    tarjeta.append(...crearConIcono("span", "", icono_, actividad.titulo).childNodes);
    const descripcion = `${actividad.titulo}, ${NOMBRE_TIPO[bloque.tipo]}, ${bloque.aproximada ? "~" : ""}${horaTexto(bloque.inicio)} a ${horaTexto(bloque.fin)}`;
    tarjeta.title = descripcion;
    tarjeta.setAttribute("aria-label", descripcion);
    const desde = minutosDelDia(bloque.inicio);
    const hasta = Math.max(minutosDelDia(bloque.fin), desde + MINUTOS_MINIMOS_TARJETA);
    // En una tarjeta angosta el ícono le quitaría el espacio al nombre: el estado lo dice el color.
    tarjeta.classList.toggle("tarjeta-angosta", hasta - desde < MINUTOS_TARJETA_CON_ICONO);
    ubicar(tarjeta, desde, hasta, rango);
    tarjeta.style.top = `calc(var(--e2) + ${bloque.renglon * ALTO_TARJETA_REM}rem)`;
    tarjeta.addEventListener("click", (evento) => {
        evento.stopPropagation();
        formulario.abrirDetalle(actividad);
    });
    return tarjeta;
}

// Lo que no es turno se raya en gris; lo programado después del fin del turno, en rojo (sobrecarga).
function crearZonas(operario, bloques, rango) {
    const zonas = [];
    const turno = turnoEnMinutos(operario.turno);
    const [desde, hasta] = rango.map((hora) => hora * 60);
    if (!turno) {
        return zonas;
    }
    for (const [inicio, fin] of [[desde, turno[0]], [turno[1], hasta]]) {
        if (fin > inicio) {
            const zona = crearElemento("span", "tablero-fuera-turno");
            ubicar(zona, inicio, fin, rango);
            zonas.push(zona);
        }
    }
    for (const bloque of bloques) {
        const fin = minutosDelDia(bloque.fin);
        if (["pendiente", "proyeccion"].includes(bloque.tipo) && fin > turno[1]) {
            const exceso = crearElemento("span", "tablero-sobrecarga");
            ubicar(exceso, Math.max(turno[1], minutosDelDia(bloque.inicio)), fin, rango);
            zonas.push(exceso);
        }
    }
    return zonas;
}

function crearLineasDeHora(rango) {
    const lineas = [];
    for (let hora = rango[0] + 1; hora < rango[1]; hora++) {
        const linea = crearElemento("span", "tablero-linea-hora");
        linea.style.left = `${porcentaje(hora * 60, rango)}%`;
        lineas.push(linea);
    }
    return lineas;
}

function crearLineaAhora(rango) {
    const ahora = minutosDelDia(new Date());
    if (!esHoy() || ahora < rango[0] * 60 || ahora > rango[1] * 60) {
        return [];
    }
    const linea = crearElemento("span", "tablero-ahora");
    linea.style.left = `${porcentaje(ahora, rango)}%`;
    return [linea];
}

function crearEncabezadoHoras(rango) {
    const fila = crearElemento("li", "tablero-fila tablero-horas");
    fila.setAttribute("aria-hidden", "true");
    const carril = crearElemento("div", "tablero-carril");
    const ahora = minutosDelDia(new Date());
    const conAhora = esHoy() && ahora >= rango[0] * 60 && ahora <= rango[1] * 60;
    for (let hora = rango[0]; hora < rango[1]; hora++) {
        if (conAhora && Math.abs(hora * 60 - ahora) < 50) {
            continue;
        }
        const etiqueta = crearElemento("span", "tablero-hora cifra", `${String(hora % 24).padStart(2, "0")}:00`);
        etiqueta.style.left = `${porcentaje(hora * 60, rango)}%`;
        carril.append(etiqueta);
    }
    if (conAhora) {
        const etiqueta = crearElemento("span", "tablero-ahora-etiqueta cifra", `Ahora, ${horaCorta(new Date())}`);
        etiqueta.style.left = `${porcentaje(ahora, rango)}%`;
        carril.append(etiqueta);
    }
    fila.append(crearElemento("div", "tablero-persona"), carril);
    return fila;
}

// Nombre, horas y medidor de carga. La sobrecarga se dice con ícono y texto (alcance, Sección 6.3).
function crearPersona(operario) {
    const persona = crearElemento("div", "tablero-persona");
    const jornada = operario.jornada || { minutos: 0, porcentaje: 0, sobrecarga: false };
    const capacidad = jornada.capacidad_min || capacidadPorDefecto;
    persona.append(crearElemento("strong", "tablero-nombre", operario.nombre));
    const horas = `${duracionTexto(jornada.minutos)} de ${duracionTexto(capacidad)}`;
    persona.append(jornada.sobrecarga
        ? crearConIcono("span", "tablero-horas-persona cifra tablero-persona-sobrecarga", "triangle-alert", `Sobrecarga: ${horas}`)
        : crearElemento("span", "tablero-horas-persona cifra", horas));
    const barra = crearElemento("span", "tablero-barra");
    const relleno = crearElemento("span", jornada.sobrecarga ? "tablero-barra-relleno sobrecarga" : "tablero-barra-relleno");
    relleno.style.width = `${Math.min(100, jornada.porcentaje)}%`;
    barra.append(relleno);
    barra.setAttribute("aria-hidden", "true");
    persona.append(barra);
    return persona;
}

function crearFila({ operario, bloques, sinHora }, rango) {
    const fila = crearElemento("li", "tablero-fila");
    fila.setAttribute("aria-label", `Fila de ${operario.nombre}`);
    const carril = crearElemento("div", "tablero-carril");
    const renglones = repartirEnRenglones(bloques);
    carril.style.minHeight = `calc(var(--e4) + ${renglones * ALTO_TARJETA_REM}rem)`;
    carril.title = "Toca un espacio libre para crear una actividad a esa hora";
    carril.append(...crearZonas(operario, bloques, rango), ...crearLineasDeHora(rango),
        ...bloques.map((bloque) => crearTarjetaTablero(bloque, rango)), ...crearLineaAhora(rango));
    // Clic en un espacio libre: nueva actividad para esa persona, a esa hora (redondeada a 15 min).
    carril.addEventListener("click", (evento) => {
        const caja = carril.getBoundingClientRect();
        const minutos = rango[0] * 60 + ((evento.clientX - caja.left) / caja.width) * (rango[1] - rango[0]) * 60;
        const redondeado = Math.round(minutos / 15) * 15 % 1440;
        formulario.abrirNueva({
            fecha_programada: fechaTexto(dia),
            hora_programada: `${String(Math.floor(redondeado / 60)).padStart(2, "0")}:${String(redondeado % 60).padStart(2, "0")}`,
            operario_ids: [operario.id],
        });
    });
    fila.append(crearPersona(operario), carril);
    if (sinHora.length) {
        const franja = crearElemento("div", "tablero-sin-hora");
        franja.append(crearElemento("span", "tablero-sin-hora-titulo", "Sin hora"));
        for (const actividad of sinHora) {
            const ficha = crearConIcono("button", "tarjeta-tablero tablero-pendiente tablero-ficha-sin-hora",
                ICONO_PRIORIDAD[actividad.prioridad], actividad.titulo);
            ficha.type = "button";
            ficha.addEventListener("click", () => formulario.abrirDetalle(actividad));
            franja.append(ficha);
        }
        fila.append(franja);
    }
    return fila;
}

function pintarLeyenda() {
    const elementos = [
        ["tablero-en-curso", "En curso"], ["tablero-pendiente", "Por hacer"], ["tablero-trabajada", "Trabajada, en pausa"],
        ["tablero-hecha", "Finalizada"], ["tablero-fuera-turno", "Fuera del turno"], ["tablero-sobrecarga", "Pasa del turno"],
    ];
    document.getElementById("leyenda-tablero").replaceChildren(...elementos.map(([clase, texto]) => {
        const item = crearElemento("span", "leyenda-tablero-item");
        item.append(crearElemento("span", `leyenda-muestra ${clase}`), texto);
        return item;
    }));
}

function pintarTablero() {
    const filas = operarios.map((operario) => ({ operario, ...bloquesDe(operario) }));
    const rango = rangoDeHoras(filas);
    const tablero = document.getElementById("tablero");
    tablero.style.setProperty("--horas-tablero", String(rango[1] - rango[0]));
    tablero.replaceChildren(crearEncabezadoHoras(rango), ...filas.map((fila) => crearFila(fila, rango)));
    document.getElementById("sin-operarios").hidden = operarios.length > 0;
    document.getElementById("tablero-desplazable").hidden = operarios.length === 0;

    // Cuando no cabe, el tablero se desplaza de lado: hoy se abre en "Ahora"; otro día, en el inicio
    // del turno más temprano. La franja "Sin hora" mide lo que se ve, para quedarse fija a la izquierda.
    const desplazable = document.getElementById("tablero-desplazable");
    tablero.style.setProperty("--ancho-visible", `${desplazable.clientWidth}px`);
    const ahora = tablero.querySelector(".tablero-ahora");
    const carril = tablero.querySelector(".tablero-horas .tablero-carril");
    if (ahora) {
        desplazable.scrollLeft = carril.offsetLeft + ahora.offsetLeft - desplazable.clientWidth / 2;
    } else {
        const inicios = filas.map(({ operario }) => turnoEnMinutos(operario.turno)?.[0]).filter((m) => m !== undefined);
        const primero = inicios.length ? Math.min(...inicios) : rango[0] * 60;
        desplazable.scrollLeft = (carril.offsetWidth * porcentaje(primero, rango)) / 100 - 24;
    }
}

// Lo que necesita al Administrador: actividades del día sin nadie (nunca asignadas o devueltas).
function pintarPorAtender() {
    const pendientes = actividades.filter((a) => a.operarios.length === 0 && !["COMPLETADA", "NO_REALIZADA"].includes(a.estado));
    document.getElementById("titulo-por-atender").replaceChildren("Por atender",
        crearElemento("span", "cantidad cifra", pendientes.length ? String(pendientes.length) : ""));
    document.getElementById("nada-por-atender").hidden = pendientes.length > 0;
    document.getElementById("por-atender").replaceChildren(...pendientes.map((actividad) => {
        const fila = crearElemento("li", "fila-por-atender");
        const textos = crearElemento("div");
        const meta = crearElemento("p", "fila-meta datos-linea");
        meta.append(crearElemento("span", "codigo", actividad.codigo),
            crearElemento("span", "cifra", duracionTexto(actividad.tiempo_estimado_min)));
        if (!actividad.lista_para_iniciar) {
            meta.append(crearEtiquetaFaltaInformacion(actividad));
        }
        textos.append(crearSenalPrioridad(actividad.prioridad), crearElemento("p", "fila-nombre", actividad.titulo), meta);
        const devolucion = (actividad.devoluciones || []).at(-1);
        if (actividad.estado === "DEVUELTA" && devolucion) {
            textos.append(crearConIcono("p", "aviso aviso-advertencia", "rotate-ccw",
                `Devuelta por ${devolucion.operario_nombre}: ${devolucion.motivo}`));
        }
        const asignar = crearConIcono("button", "boton-secundario", "users", "Asignar");
        asignar.type = "button";
        asignar.addEventListener("click", () => formulario.abrirEdicion(actividad));
        fila.append(textos, asignar);
        return fila;
    }));
}

function pintarResumen() {
    const fecha = fechaLarga(dia);
    document.getElementById("fecha-equipo").textContent = `${esHoy() ? "Hoy, " : ""}${fecha}`;
    const programado = operarios.reduce((suma, o) => suma + (o.jornada?.minutos || 0), 0);
    const capacidad = operarios.reduce((suma, o) => suma + (o.jornada?.capacidad_min || capacidadPorDefecto), 0);
    document.getElementById("resumen").textContent = [
        plural(operarios.length, "operario", "operarios"),
        `${duracionTexto(programado)} de trabajo para ${duracionTexto(capacidad)} de capacidad`,
    ].join(", ");

    const sobrecargados = operarios.filter((o) => o.jornada?.sobrecarga);
    const aviso = document.getElementById("aviso-sobrecarga");
    aviso.hidden = sobrecargados.length === 0;
    if (sobrecargados.length) {
        const nombres = sobrecargados.map((o) => `${o.nombre} (${o.jornada.porcentaje} %)`).join(", ");
        aviso.replaceChildren(crearConIcono("span", "", "triangle-alert",
            `Superan la capacidad de su jornada: ${nombres}. Reasígnales actividades por hacer a quien tenga espacio.`));
    }
}

// ---------- Carga de datos ----------

async function cargar() {
    const fecha = fechaTexto(dia);
    try {
        const [lista, carga, listaProyectos] = await Promise.all([
            pedirApi(`/actividades?fecha_desde=${fecha}&fecha_hasta=${fecha}`),
            pedirApi(`/analisis/carga?desde=${fecha}&hasta=${fecha}`),
            pedirApi("/proyectos"),
        ]);
        actividades = actividadesDelHorario(lista);     // Las canceladas no se dibujan.
        proyectos = listaProyectos;
        capacidadPorDefecto = carga.capacidad_min;
        // El turno de ESE día: un cambio de turno rige desde su fecha.
        operarios = carga.operarios.map((o) => ({
            id: o.id, nombre: o.nombre, turno: o.turnos?.[fecha] || null, jornada: o.jornadas[0] || null,
        }));
        if (esHoy()) {
            // Hoy: lo pendiente va donde lo pone la programación del día de cada persona.
            await Promise.all(operarios.map(async (operario) => {
                try {
                    operario.programacion = await pedirApi(`/programacion-del-dia?operario_id=${encodeURIComponent(operario.id)}`);
                } catch (error) {
                    operario.programacion = null;
                }
            }));
        }
        pintarResumen();
        pintarTablero();
        pintarPorAtender();
    } catch (error) {
        mostrarAviso(`No se pudo cargar el equipo: ${error.message}`, "advertencia");
    }
}

function moverDia(dias) {
    dia = dias === 0 ? inicioDelDia(new Date()) : inicioDelDia(sumarDias(dia, dias));
    cargar();
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(() => {
    formulario = crearFormularioActividad({
        obtenerProyectos: () => proyectos,
        obtenerOperarios: () => operarios,
        alGuardar: cargar,
    });
    pintarLeyenda();
    const anterior = document.getElementById("dia-anterior");
    const siguiente = document.getElementById("dia-siguiente");
    anterior.insertAdjacentHTML("afterbegin", icono("chevron-left"));
    siguiente.insertAdjacentHTML("afterbegin", icono("chevron-right"));
    anterior.addEventListener("click", () => moverDia(-1));
    siguiente.addEventListener("click", () => moverDia(1));
    document.getElementById("dia-hoy").addEventListener("click", () => moverDia(0));
    document.getElementById("nueva-actividad").addEventListener("click", () =>
        formulario.abrirNueva({ fecha_programada: fechaTexto(dia) }));
    cargar();
    // La línea "Ahora" y lo que está en curso se mueven con la hora.
    setInterval(() => {
        if (esHoy() && !document.querySelector("dialog[open]")) {
            pintarTablero();
        }
    }, 60000);
});
