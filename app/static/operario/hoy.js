// Vista "Hoy" del Operario: su fila del tablero del turno, en vertical (alcance, Secciones 6.2 y 6.5).
// Una línea de tiempo con las horas de arriba abajo, una tarjeta por actividad en su hora, la actividad en curso
// abierta en su lugar del día y la línea "Ahora", que separa lo que ya pasó de lo que falta.
// La programación la calcula el servidor (GET /programacion-del-dia): lo terminado ocupa el tiempo
// que realmente tomó y lo pendiente se reacomoda desde que el operario queda libre.
// La pantalla tiene tres estados según la asistencia de la jornada (alcance, Sección 6.1): antes de
// marcar la entrada, el inicio de la jornada; con la entrada marcada, el día; después de la salida, el cierre.

const INTERVALO_MINIMO_MIN = 15;    // Un espacio libre más corto que esto no se anuncia.
const AVISO_TURNO_MIN = 15;         // Desde cuántos minutos antes se avisa el inicio y el fin del turno.
const MOTIVO_FIN_JORNADA = "Fin de jornada";

const hoy = new Date();
hoy.setHours(0, 0, 0, 0);
const textoHoy = fechaTexto(hoy);

let actividades = [];           // Las del día, como las presenta la API (para abrir su detalle).
let programacion = null;
let temporizador = null;
let alTic = [];                 // Lo que se actualiza cada segundo: cronómetro, avance y hora actual.

// ---------- Horas: minutos desde la medianoche ----------

function horaDeMinutos(minutos) {
    const total = ((Math.round(minutos) % 1440) + 1440) % 1440;
    return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

function minutosDeFecha(fecha) {
    return fecha.getHours() * 60 + fecha.getMinutes();
}

function esDeHoy(fecha) {
    return fechaTexto(fecha) === textoHoy;
}

// ---------- Armar el día con la programación del servidor ----------
// Cada nodo de la línea de tiempo dice qué es ("tipo"), en qué parte del día cae ("zona": pasado,
// actual o futuro) y su hora. "aproximada" marca las horas calculadas, no fijas.

const UN_MINUTO = 60000;

function horaLocal(momento) {
    return horaDeMinutos(minutosDeFecha(new Date(momento)));
}

// La hora que se muestra junto a una actividad pendiente.
function textoHoraPendiente(tramo) {
    if (tramo.fuera_de_jornada) {
        return "Fuera de la jornada";
    }
    return (tramo.aproximada ? "~" : "") + horaLocal(tramo.inicio);
}

// Lo que está en curso. Si una urgente lo interrumpe, se muestra compacto, encima de "Ahora".
function nodoEnCurso(tramo, actividad, interrumpida) {
    const inicio = new Date(tramo.inicio);
    const desde = esDeHoy(inicio) ? horaLocal(inicio) : fechaCorta(inicio);
    if (interrumpida) {
        return { tipo: "compacta", zona: "pasado", actividad, tramo, hora: esDeHoy(inicio) ? desde : "", desde };
    }
    return { tipo: "en-curso", zona: "actual", actividad, tramo, desde };
}

function nodoDeTramo(tramo, actividad, interrumpida) {
    if (tramo.tipo === "FINALIZADA") {
        return { tipo: "hecha", zona: "pasado", actividad, tramo, hora: horaLocal(tramo.inicio) };
    }
    if (tramo.tipo === "EN_CURSO") {
        return nodoEnCurso(tramo, actividad, interrumpida);
    }
    if (actividad.prioridad === "URGENTE") {
        return { tipo: "urgente", zona: "futuro", actividad, tramo, hora: "" };
    }
    if (tramo.vencida) {
        return { tipo: "pendiente", zona: "pasado", actividad, tramo, hora: horaLocal(tramo.inicio), atrasada: true };
    }
    return {
        tipo: "pendiente", zona: "futuro", actividad, tramo, hora: textoHoraPendiente(tramo),
        aproximada: tramo.aproximada, siguiente: tramo.siguiente,
    };
}

// La primera urgente queda en la línea de "Ahora", salvo que haya algo en curso que no interrumpe.
function marcarAhora(nodos) {
    if (nodos.some((nodo) => nodo.zona === "actual")) {
        return nodos;
    }
    const urgente = nodos.find((nodo) => nodo.tipo === "urgente");
    if (urgente) {
        urgente.zona = "actual";
        return nodos;
    }
    // Sin nada en curso ni urgente: solo la línea, entre lo que ya pasó y lo que falta.
    const posicion = nodos.findIndex((nodo) => nodo.zona === "futuro");
    const ahora = { tipo: "ahora", zona: "actual" };
    return posicion === -1 ? [...nodos, ahora] : [...nodos.slice(0, posicion), ahora, ...nodos.slice(posicion)];
}

function momentoDeNodo(nodo) {
    if (nodo.momento) {
        return nodo.momento;
    }
    return nodo.tramo ? new Date(nodo.tramo.inicio).getTime() : Date.now();
}

// El turno abre y cierra la línea de tiempo: arriba la entrada, abajo el fin del turno y la salida.
// Sin turno asignado, la línea se cierra con el fin de la jornada.
function conTurno(nodos) {
    const { turno } = programacion;
    const ahora = Date.now();
    const inicioTurno = turno ? new Date(turno.inicio).getTime() : null;
    const finTurno = turno ? new Date(turno.fin).getTime() : null;
    const entrada = {
        tipo: "inicio-turno", zona: inicioTurno === null || inicioTurno <= ahora ? "pasado" : "futuro",
        hora: turno ? horaLocal(turno.inicio) : "",
    };
    const fin = { tipo: "fin-turno", zona: "futuro", hora: turno ? horaLocal(turno.fin) : "", momento: finTurno };
    // El fin del turno va antes de lo que quedaría después de él.
    const posicion = finTurno === null ? -1 : nodos.findIndex(
        (nodo) => nodo.zona === "futuro" && nodo.tramo && new Date(nodo.tramo.inicio).getTime() >= finTurno);
    const conFin = posicion === -1 ? [...nodos, fin] : [...nodos.slice(0, posicion), fin, ...nodos.slice(posicion)];
    return [entrada, ...conFin];
}

// Los intervalos disponibles entre una actividad y la siguiente se dicen en una sola línea.
function conIntervalos(nodos) {
    const resultado = [];
    let finAnterior = null;
    for (const nodo of nodos) {
        const inicio = momentoDeNodo(nodo);
        const ocupaHora = nodo.tipo === "pendiente" || nodo.tipo === "fin-turno";
        if (ocupaHora && nodo.zona === "futuro" && finAnterior !== null
            && inicio - finAnterior >= INTERVALO_MINIMO_MIN * UN_MINUTO) {
            resultado.push({ tipo: "intervalo", zona: "futuro", minutos: Math.round((inicio - finAnterior) / UN_MINUTO) });
        }
        resultado.push(nodo);
        if (nodo.zona !== "pasado") {
            const fin = nodo.tramo ? new Date(nodo.tramo.fin).getTime() : inicio;
            finAnterior = Math.max(finAnterior ?? 0, fin);
        }
    }
    return resultado;
}

// Devuelve los nodos de la línea de tiempo en orden: lo que pasó, "Ahora" y lo que falta.
function armarDia() {
    const porId = new Map(programacion.actividades.map((actividad) => [actividad.id, actividad]));
    const tramos = programacion.tramos.filter((tramo) => porId.has(tramo.actividad_id));
    const interrumpida = tramos.some((tramo) => tramo.interrumpe);
    const nodos = tramos.map((tramo) => nodoDeTramo(tramo, porId.get(tramo.actividad_id), interrumpida));
    return conIntervalos(conTurno(marcarAhora(nodos)));
}

// Segundos trabajados en una ejecución: del inicio a ahora, sin las pausas. No usa el estimado.
function segundosTrabajados(ejecucion) {
    const ahora = Date.now();
    const total = ahora - new Date(ejecucion.fecha_inicio).getTime();
    const pausado = (ejecucion.pausas || []).reduce(
        (suma, pausa) => suma + ((pausa.fin ? new Date(pausa.fin).getTime() : ahora) - new Date(pausa.inicio).getTime()),
        0,
    );
    return Math.max(0, Math.floor((total - pausado) / 1000));
}

// "38:12" antes de la primera hora; "1:05:20" después.
function textoCronometro(segundos) {
    const horas = Math.floor(segundos / 3600);
    const minutosYSegundos = [Math.floor((segundos % 3600) / 60), segundos % 60]
        .map((parte) => String(parte).padStart(2, "0")).join(":");
    return horas > 0 ? `${horas}:${minutosYSegundos}` : minutosYSegundos;
}

// ---------- Tarjetas ----------

// Los días de retraso los calcula el servidor, desde la fecha para la que se programó.
function textoRetraso(actividad) {
    const dias = actividad.dias_de_retraso;
    return dias === 1 ? "Retraso: 1 día" : `Retraso: ${dias} días`;
}

function abrirDetalle(actividad) {
    abrirDetalleOperario(actividad, actividades, cargar);
}

// Lo terminado dice cuánto tomó de verdad; lo pausado, cuánto le falta; lo demás, su estimado.
function textoDuracion(nodo) {
    const { actividad } = nodo;
    const estimado = duracionTexto(actividad.tiempo_estimado_min);
    if (nodo.tipo === "hecha" && actividad.ejecucion) {
        return `Tomó ${duracionTexto(actividad.ejecucion.tiempo_real_min)} de ${estimado} estimados`;
    }
    if (actividad.estado === "PAUSADA" && nodo.tramo) {
        const faltan = Math.round((new Date(nodo.tramo.fin) - new Date(nodo.tramo.inicio)) / UN_MINUTO);
        return `Faltan ${duracionTexto(faltan)} de ${estimado} estimados`;
    }
    return estimado;
}

// Tarjeta de una actividad por iniciar o finalizada: toda la tarjeta se toca para abrir el detalle.
function crearTarjeta(nodo) {
    const { actividad } = nodo;
    const tarjeta = crearElemento("button", nodo.tipo === "hecha" ? "tarjeta tarjeta-hecha" : "tarjeta");
    tarjeta.type = "button";

    const titulo = crearElemento("span", "tarjeta-titulo");
    titulo.append(crearElemento("strong", "", actividad.titulo));
    if (nodo.siguiente) {
        titulo.append(crearConIcono("span", "etiqueta etiqueta-siguiente", "chevron-right", "Siguiente"));
    }

    const datos = crearElemento("span", "tarjeta-datos");
    if (nodo.tipo === "hecha") {
        datos.append(crearEtiquetaEstado("COMPLETADA"));
    } else {
        datos.append(crearSenalPrioridad(actividad.prioridad));
    }
    if (actividad.hora_programada) {
        datos.append(crearConIcono("span", "etiqueta etiqueta-hora-fija", "lock", "Hora fija"));
    }
    if (actividad.estado === "PAUSADA") {
        datos.append(crearEtiquetaEstado("PAUSADA"));
    }
    datos.append(crearElemento("span", "cifra", textoDuracion(nodo)), crearElemento("span", "codigo", actividad.codigo));
    if (actividad.reprogramada && nodo.tipo !== "hecha") {
        datos.append(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", textoRetraso(actividad)));
    } else if (nodo.atrasada) {
        datos.append(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", "Hora vencida"));
    }

    const textos = crearElemento("span", "tarjeta-textos");
    textos.append(titulo, datos);
    tarjeta.append(textos);
    tarjeta.insertAdjacentHTML("beforeend", icono("chevron-right"));
    tarjeta.addEventListener("click", () => abrirDetalle(actividad));
    return tarjeta;
}

function crearBotonFinalizar(actividad, clase) {
    const boton = crearConIcono("button", clase, "check", "Finalizar");
    boton.type = "button";
    boton.addEventListener("click", () => abrirFinalizar(actividad, cargar));
    return boton;
}

// Una de horario flexible se pausa con un motivo; una de hora fija no tiene este botón.
function crearBotonPausar(actividad) {
    const boton = crearConIcono("button", "boton-secundario", "pause", "Pausar");
    boton.type = "button";
    boton.addEventListener("click", () => abrirPausar(actividad, cargar));
    return boton;
}

// "Ver detalle", con cuántas pausas lleva: el historial está en el detalle.
function crearEnlaceDetalle(actividad) {
    const pausas = actividad.ejecucion?.pausas?.length || 0;
    let texto = "Ver detalle";
    if (pausas === 1) {
        texto = "Ver detalle (1 pausa)";
    } else if (pausas > 1) {
        texto = `Ver detalle (${pausas} pausas)`;
    }
    const enlace = crearConIcono("button", "boton-texto tarjeta-enlace", pausas ? "pause" : "chevron-right", texto);
    enlace.type = "button";
    enlace.addEventListener("click", () => abrirDetalle(actividad));
    return enlace;
}

function crearCronometro(actividad, clase) {
    const cronometro = crearElemento("span", clase);
    cronometro.setAttribute("role", "timer");
    cronometro.setAttribute("aria-label", "Tiempo en ejecución");
    alTic.push(() => { cronometro.textContent = textoCronometro(segundosTrabajados(actividad.ejecucion)); });
    return cronometro;
}

// Mientras trabaja, lo que necesita para hacerlo sin abrir el detalle: las precauciones primero y
// después los pasos (alcance, Sección 5.1). Lo demás (herramientas, contacto, adjuntos) está en el detalle.
function crearGuiaEnCurso(actividad) {
    const informacion = actividad.informacion || { bloques: [] };
    const nodos = [];
    for (const bloque of BLOQUES_INFORMACION.filter((b) => ["PRECAUCIONES", "PASOS"].includes(b.clave))
        .reverse()) {
        const valores = informacion.bloques.includes(bloque.clave) ? informacion[bloque.campo] : [];
        if (valores.length) {
            const grupo = crearElemento("div", "tarjeta-guia");
            grupo.append(crearElemento("p", "tarjeta-guia-titulo", bloque.nombre), crearListaDeBloque(bloque, valores));
            nodos.push(grupo);
        }
    }
    return nodos;
}

// Actividad en curso, abierta en su lugar del día: cronómetro, avance contra el estimado y acciones.
function crearTarjetaEnCurso(nodo) {
    const { actividad } = nodo;
    const tarjeta = crearElemento("section", "tarjeta-en-curso");
    tarjeta.setAttribute("aria-label", "Actividad en curso");

    const cabecera = crearElemento("p", "tarjeta-cabecera");
    cabecera.append(
        crearConIcono("span", "cifra", "play", `En curso desde las ${nodo.desde}`),
        crearSenalPrioridad(actividad.prioridad),
    );

    const lugar = crearElemento("p", "tarjeta-lugar");
    lugar.append(
        crearElemento("span", "codigo", actividad.codigo),
        crearConIcono("span", "", "map-pin", actividad.ubicacion),
    );
    if (actividad.hora_programada) {
        lugar.append(crearConIcono("span", "", "lock", "Hora fija"));
    }

    const tiempo = crearElemento("p", "tarjeta-tiempo");
    tiempo.append(
        crearCronometro(actividad, "cronometro"),
        crearElemento("span", "cifra", `de ${duracionTexto(actividad.tiempo_estimado_min)}`),
    );

    const avance = crearElemento("div", "tarjeta-avance");
    avance.setAttribute("aria-hidden", "true");
    const relleno = crearElemento("div", "tarjeta-avance-relleno");
    avance.append(relleno);
    alTic.push(() => {
        const minutos = segundosTrabajados(actividad.ejecucion) / 60;
        relleno.style.width = `${Math.min(100, Math.round(minutos * 100 / actividad.tiempo_estimado_min))}%`;
    });

    const acciones = crearElemento("div", "tarjeta-acciones");
    if (!actividad.hora_programada) {
        acciones.append(crearBotonPausar(actividad));
    }
    acciones.append(crearBotonFinalizar(actividad, "boton"));

    tarjeta.append(cabecera, crearElemento("h2", "", actividad.titulo), lugar, ...crearGuiaEnCurso(actividad),
        tiempo, avance, crearEnlaceDetalle(actividad), acciones);
    return tarjeta;
}

// Con una urgente pendiente, la actividad en curso se encoge y explica qué hacer para atenderla.
function crearTarjetaCompacta(nodo) {
    const { actividad } = nodo;
    const tarjeta = crearElemento("section", "tarjeta-compacta");
    tarjeta.setAttribute("aria-label", "Actividad en curso");

    const cabecera = crearElemento("p", "tarjeta-cabecera");
    cabecera.append(crearConIcono("span", "", "play", "En curso"), crearCronometro(actividad, "cifra dato-fuerte"));

    // Puede terminarla antes de atender la urgente, o ver su detalle: no queda atrapado.
    const acciones = crearElemento("div", "tarjeta-compacta-acciones");
    acciones.append(crearEnlaceDetalle(actividad), crearBotonFinalizar(actividad, "boton-texto"));
    tarjeta.append(
        cabecera,
        crearElemento("strong", "", actividad.titulo),
        crearElemento("p", "tarjeta-nota", "Si atiendes la urgente, esta queda en pausa y no pierdes el tiempo registrado."),
        acciones,
    );
    return tarjeta;
}

// Urgente pendiente: el único bloque rojo lleno de la pantalla, con una sola acción.
function crearTarjetaUrgente(nodo) {
    const { actividad } = nodo;
    const tarjeta = crearElemento("section", "tarjeta-urgente");
    tarjeta.setAttribute("role", "alert");

    const datos = crearElemento("p", "tarjeta-lugar");
    datos.append(
        crearElemento("span", "codigo", actividad.codigo),
        crearConIcono("span", "", "map-pin", actividad.ubicacion),
        crearConIcono("span", "cifra", "clock", duracionTexto(actividad.tiempo_estimado_min)),
    );

    tarjeta.append(
        crearConIcono("p", "tarjeta-cabecera", "triangle-alert", actividad.estado === "PAUSADA" ? "Urgente en pausa" : "Urgente"),
        crearElemento("h2", "", actividad.titulo), datos, ...crearAccionesUrgente(actividad),
    );
    return tarjeta;
}

// La acción de la urgente depende de lo que el operario tenga en curso (alcance, Sección 5.1):
// una de horario flexible se pausa y la urgente empieza en el mismo paso; una de hora fija no se
// interrumpe, así que solo se puede ver la urgente; sin nada en curso, se inicia directamente.
function crearAccionesUrgente(urgente) {
    const tramo = tramoEnCurso();
    const enCurso = tramo ? actividades.find((actividad) => actividad.id === tramo.actividad_id) : null;
    const verDetalle = crearElemento("button", "boton-texto tarjeta-enlace", "Ver detalle");
    verDetalle.type = "button";
    verDetalle.addEventListener("click", () => abrirDetalle(urgente));

    if (enCurso?.hora_programada) {
        const aviso = crearElemento("p", "tarjeta-nota-urgente",
            `${enCurso.codigo} es de hora fija y no se interrumpe. Atiende la urgente al finalizarla.`);
        verDetalle.className = "boton";
        verDetalle.textContent = "Ver la urgente";
        return [aviso, verDetalle];
    }
    const retomar = urgente.estado === "PAUSADA";
    let texto = retomar ? "Reanudar la urgente" : "Iniciar la urgente";
    if (enCurso) {
        texto = "Pausar y atender";
    }
    const boton = crearConIcono("button", "boton", "play", texto);
    boton.type = "button";
    boton.addEventListener("click", () => atenderUrgente(boton, urgente, enCurso));
    return [boton, verDetalle];
}

// Pausa lo que está en curso con el motivo "Actividad urgente" e inicia (o reanuda) la urgente.
// Son dos pasos en el servidor: si el segundo falla, lo primero ya quedó en pausa y se explica.
async function atenderUrgente(boton, urgente, enCurso) {
    boton.disabled = true;
    try {
        if (enCurso) {
            await enviarJson(`/actividades/${enCurso.id}/pausar`, "POST", { motivo: MOTIVO_URGENTE });
        }
        const accion = urgente.estado === "PAUSADA" ? "reanudar" : "iniciar";
        await pedirApi(`/actividades/${urgente.id}/${accion}`, { method: "POST" });
        await cargar();
        mostrarAviso(enCurso ? `${enCurso.codigo} quedó en pausa. ${urgente.codigo} en curso.` : `${urgente.codigo} en curso.`);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
        cargar();    // Si alcanzó a pausar, la pantalla debe mostrarlo.
    }
}

// ---------- Asistencia: marca de entrada y de salida ----------

async function marcarAsistencia(boton, ruta, texto) {
    boton.disabled = true;
    try {
        await pedirApi(ruta, { method: "POST" });
        await cargar();
        mostrarAviso(texto);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
    }
}

// En la línea de tiempo la entrada y el fin del turno son solo datos: la entrada se marca en el
// inicio de la jornada y la salida, con el botón del encabezado.
function crearMarcaEntrada() {
    const marca = crearElemento("p", "linea-marca");
    marca.append("Marcaste entrada a las ", crearElemento("strong", "cifra", horaLocal(programacion.asistencia.entrada)));
    return marca;
}

function crearMarcaSalida() {
    const bloque = crearElemento("div", "linea-fin-turno");
    bloque.append(crearElemento("span", "", programacion.turno ? "Fin del turno" : "Fin de la jornada"));
    return bloque;
}

// ---------- Estados de la jornada: inicio, día y cierre ----------

function estadoJornada() {
    const { asistencia, fecha } = programacion;
    // Una asistencia de otra jornada que quedó sin salida no cuenta: hoy se marca una entrada nueva.
    if (!asistencia || asistencia.jornada !== fecha) {
        return "inicio";
    }
    return asistencia.salida ? "cierre" : "dia";
}

function tramoEnCurso() {
    return programacion.tramos.find((tramo) => tramo.tipo === "EN_CURSO") || null;
}

function crearDatos(filas) {
    const datos = crearElemento("dl", "portada-datos");
    for (const [nombre, valor] of filas) {
        datos.append(crearElemento("dt", "", nombre), crearElemento("dd", "cifra", valor));
    }
    return datos;
}

function textoTurno(turno) {
    return turno ? `${turno.nombre}, ${turno.hora_inicio} a ${turno.hora_fin}` : "Sin turno asignado";
}

// Antes de marcar la entrada: lo que tiene programado y una sola acción principal.
function crearInicioJornada() {
    const { tramos, resumen, turno, asistencia } = programacion;
    const porId = new Map(actividades.map((actividad) => [actividad.id, actividad]));
    const porHacer = tramos.filter((tramo) => tramo.tipo !== "FINALIZADA" && porId.has(tramo.actividad_id));
    const urgentes = porHacer.filter((tramo) => porId.get(tramo.actividad_id).prioridad === "URGENTE").length;
    const contenido = [crearDatos([["Turno", textoTurno(turno)]])];

    if (porHacer.length) {
        contenido.push(
            crearElemento("h2", "", "Lo que tienes programado"),
            crearDatos([
                ["Actividades", String(porHacer.length)],
                ["Tiempo estimado", duracionTexto(resumen.pendiente_min)],
            ]),
        );
        if (urgentes) {
            const aviso = crearElemento("p", "portada-urgentes");
            aviso.append(crearSenalPrioridad("URGENTE"), crearElemento("span", "",
                urgentes === 1 ? "1 actividad urgente te espera." : `${urgentes} actividades urgentes te esperan.`));
            contenido.push(aviso);
        }
    } else {
        contenido.push(crearElemento("p", "texto-suave", "No tienes actividades programadas para hoy."));
    }
    if (asistencia) {
        contenido.push(crearElemento("p", "texto-suave",
            "Tu jornada anterior quedó sin marca de salida. Tu Administrador la corrige."));
    }

    const boton = crearConIcono("button", "boton boton-bloque", "log-in", "Marcar entrada");
    boton.type = "button";
    boton.addEventListener("click", () => marcarAsistencia(boton, "/asistencia/entrada", "Entrada registrada."));
    contenido.push(boton);
    return contenido;
}

// Después de marcar la salida: las marcas, el tiempo trabajado y lo que quedó sin finalizar.
function crearCierreJornada() {
    const { tramos, resumen, asistencia } = programacion;
    const finalizadas = tramos.filter((tramo) => tramo.tipo === "FINALIZADA").length;
    const sinFinalizar = tramos.length - finalizadas;
    const contenido = [crearDatos([
        ["Entrada", horaLocal(asistencia.entrada)],
        ["Salida", horaLocal(asistencia.salida)],
        ["Tiempo presente", duracionTexto(asistencia.minutos_presente)],
        ["Tiempo en actividades", duracionTexto(resumen.trabajado_min)],
        ["Actividades finalizadas", `${finalizadas} de ${tramos.length}`],
    ])];
    if (sinFinalizar) {
        const cuantas = sinFinalizar === 1
            ? "Quedó 1 actividad sin finalizar."
            : `Quedaron ${sinFinalizar} actividades sin finalizar.`;
        contenido.push(crearConIcono("p", "aviso aviso-info", "info",
            `${cuantas} Las de horario flexible pasan a tu siguiente jornada.`));
    }
    contenido.push(crearElemento("p", "texto-suave",
        "Si marcaste la salida por error, pide a tu Administrador que la corrija."));
    return contenido;
}

// Muestra el estado que corresponde y oculta lo de los otros dos.
function pintarJornada() {
    const estado = estadoJornada();
    const esDia = estado === "dia";
    const portada = document.getElementById("portada-jornada");
    document.getElementById("saludo").textContent = {
        inicio: `Hola, ${nombreOperario}`, dia: `Tu turno, ${nombreOperario}`, cierre: "Jornada terminada",
    }[estado];
    document.getElementById("turno-resumen").hidden = !esDia;
    document.getElementById("turno-acciones").hidden = !esDia;
    portada.hidden = esDia;

    if (esDia) {
        pintarResumen(programacion.resumen);
        pintarLineaDeTiempo();
        return;
    }
    clearInterval(temporizador);
    for (const id of ["mensaje", "linea-tiempo", "ordenador", "turno-sobrecarga"]) {
        document.getElementById(id).hidden = true;
    }
    portada.replaceChildren(...(estado === "inicio" ? crearInicioJornada() : crearCierreJornada()));
}

// Aviso de 15 minutos: antes de la entrada, cuánto falta para que inicie el turno; durante el día,
// cuánto falta para que termine. Es informativo: el turno no limita la entrada ni la salida.
function pintarAvisoTurno() {
    const aviso = document.getElementById("aviso-turno");
    const turno = programacion?.turno;
    const estado = turno ? estadoJornada() : "";
    const momento = { inicio: turno?.inicio, dia: turno?.fin }[estado];
    const faltan = momento ? Math.ceil((new Date(momento).getTime() - Date.now()) / UN_MINUTO) : 0;
    aviso.hidden = faltan <= 0 || faltan > AVISO_TURNO_MIN;
    if (!aviso.hidden) {
        const texto = estado === "inicio" ? "Tu turno inicia en" : "Tu turno termina en";
        aviso.replaceChildren(...crearConIcono("span", "", "info", `${texto} ${duracionTexto(faltan)}.`).childNodes);
    }
}

// ---------- Marcar salida ----------

// Con una actividad en curso no se marca la salida: la de horario flexible se pausa con el motivo
// "Fin de jornada" y la de hora fija, que no se pausa, se finaliza. Todo en el mismo paso.
function abrirSalida() {
    const tramo = tramoEnCurso();
    const enCurso = tramo ? actividades.find((actividad) => actividad.id === tramo.actividad_id) : null;
    const esFija = Boolean(enCurso?.hora_programada);
    const dialogo = crearElemento("dialog", "dialogo");

    const encabezado = crearElemento("div", "dialogo-encabezado");
    const cerrar = crearElemento("button", "boton-cerrar", "×");
    cerrar.type = "button";
    cerrar.setAttribute("aria-label", "Cerrar");
    cerrar.addEventListener("click", () => dialogo.close());
    encabezado.append(crearElemento("h2", "", "Marcar salida"), cerrar);

    const cuerpo = crearElemento("div", "detalle-cuerpo");
    if (enCurso) {
        cuerpo.append(crearConIcono("p", "aviso aviso-advertencia aviso-bloque", "circle-alert", esFija
            ? `Tienes ${enCurso.codigo} en curso. Es de hora fija y no se pausa: se finaliza antes de marcar la salida.`
            : `Tienes ${enCurso.codigo} en curso. Se pausa con el motivo "${MOTIVO_FIN_JORNADA}" y la retomas en tu siguiente jornada.`));
    }
    cuerpo.append(crearElemento("p", "portada-nota",
        "Después de marcar la salida no podrás iniciar ni reanudar actividades en esta jornada."));
    const error = crearElemento("p", "mensaje-formulario");
    error.setAttribute("role", "alert");
    error.hidden = true;

    let textoConfirmar = "Marcar salida";
    if (enCurso) {
        textoConfirmar = esFija ? "Finalizar y marcar salida" : "Pausar y marcar salida";
    }
    const confirmar = crearConIcono("button", "boton", "log-out", textoConfirmar);
    confirmar.type = "button";
    confirmar.addEventListener("click", async () => {
        confirmar.disabled = true;
        try {
            if (enCurso && esFija) {
                await pedirApi(`/actividades/${enCurso.id}/finalizar`, { method: "POST" });
            } else if (enCurso) {
                await enviarJson(`/actividades/${enCurso.id}/pausar`, "POST", { motivo: MOTIVO_FIN_JORNADA });
            }
            await pedirApi("/asistencia/salida", { method: "POST" });
            dialogo.close();
            await cargar();
            mostrarAviso("Salida registrada.");
        } catch (error_) {
            mostrarErrorFormulario(error, error_.message);
            confirmar.disabled = false;
            cargar();    // Si alcanzó a pausar o finalizar, la pantalla debe mostrarlo.
        }
    });
    const cancelar = crearElemento("button", "boton-secundario", "Cancelar");
    cancelar.type = "button";
    cancelar.addEventListener("click", () => dialogo.close());
    const acciones = crearElemento("div", "dialogo-acciones");
    acciones.append(cancelar, confirmar);

    cuerpo.append(error, acciones);
    dialogo.append(encabezado, cuerpo);
    dialogo.addEventListener("close", () => dialogo.remove());
    document.body.append(dialogo);
    dialogo.showModal();
}

// ---------- Línea de tiempo ----------

function crearNodo(nodo) {
    const elemento = crearElemento("li", `linea-nodo ${nodo.zona}`);

    if (nodo.tipo === "intervalo") {
        elemento.classList.add("linea-nodo-intervalo");
        elemento.append(crearElemento("p", "linea-intervalo cifra", `${duracionTexto(nodo.minutos)} disponibles`));
        return elemento;
    }

    const hora = crearElemento("span", "linea-hora cifra", nodo.hora || "");
    if (nodo.aproximada) {
        hora.classList.add("linea-hora-aproximada");
        hora.title = "Hora aproximada: esta actividad no tiene hora fija";
    }
    if (nodo.zona === "actual") {
        // La hora de "Ahora" se actualiza sola.
        hora.classList.add("linea-hora-ahora");
        const reloj = crearElemento("span");
        alTic.push(() => { reloj.textContent = horaDeMinutos(minutosDeFecha(new Date())); });
        hora.replaceChildren(reloj, crearElemento("span", "", "Ahora"));
    }

    const punto = crearElemento("span", "linea-punto");
    punto.setAttribute("aria-hidden", "true");
    if (nodo.tipo === "urgente") {
        punto.classList.add("linea-punto-urgente");
    } else if (nodo.atrasada) {
        punto.classList.add("linea-punto-pendiente");
    }

    const contenido = {
        "inicio-turno": crearMarcaEntrada,
        "fin-turno": crearMarcaSalida,
        "ahora": () => crearElemento("p", "linea-ahora", "Sin actividad en curso. Selecciona una para iniciarla."),
        "en-curso": crearTarjetaEnCurso,
        "compacta": crearTarjetaCompacta,
        "urgente": crearTarjetaUrgente,
    }[nodo.tipo] || crearTarjeta;

    elemento.append(hora, punto, contenido(nodo));
    return elemento;
}

function pintarLineaDeTiempo() {
    const linea = document.getElementById("linea-tiempo");
    const mensaje = document.getElementById("mensaje");
    clearInterval(temporizador);
    alTic = [];

    const nodos = armarDia();
    const hayActividades = nodos.some((nodo) => nodo.actividad);
    mensaje.hidden = hayActividades;
    mensaje.classList.remove("mensaje-error");
    mensaje.textContent = "No tienes actividades para hoy.";
    linea.hidden = false;
    linea.replaceChildren(...nodos.map(crearNodo));
    pintarBotonOrdenar();

    const tic = () => alTic.forEach((actualizar) => actualizar());
    tic();
    temporizador = setInterval(tic, 1000);
}

// ---------- Ordenar el día: solo las actividades de horario flexible ----------

// Las que el Operario puede mover: pendientes, de horario flexible y no urgentes, en su orden actual.
function actividadesQueSeOrdenan() {
    const porId = new Map(programacion.actividades.map((actividad) => [actividad.id, actividad]));
    return programacion.tramos
        .filter((tramo) => tramo.tipo === "PENDIENTE" && !tramo.hora_fija && !tramo.vencida)
        .map((tramo) => porId.get(tramo.actividad_id))
        .filter((actividad) => actividad && actividad.prioridad !== "URGENTE");
}

function pintarBotonOrdenar() {
    const boton = document.getElementById("ordenar-dia");
    boton.hidden = actividadesQueSeOrdenan().length < 2;
}

function crearFilaOrden(actividad, indice, total, mover) {
    const fila = crearElemento("li", "orden-fila");
    const textos = crearElemento("span", "orden-textos");
    textos.append(
        crearElemento("strong", "", actividad.titulo),
        crearElemento("span", "orden-datos cifra", `${NOMBRE_PRIORIDAD[actividad.prioridad]}, ${duracionTexto(actividad.tiempo_estimado_min)}`),
    );
    const subir = crearConIcono("button", "boton-icono", "arrow-up", "");
    subir.type = "button";
    subir.disabled = indice === 0;
    subir.setAttribute("aria-label", `Subir ${actividad.titulo}`);
    subir.addEventListener("click", () => mover(indice, -1));
    const bajar = crearConIcono("button", "boton-icono", "arrow-down", "");
    bajar.type = "button";
    bajar.disabled = indice === total - 1;
    bajar.setAttribute("aria-label", `Bajar ${actividad.titulo}`);
    bajar.addEventListener("click", () => mover(indice, 1));
    fila.append(crearElemento("span", "orden-posicion cifra", String(indice + 1)), textos, subir, bajar);
    return fila;
}

async function guardarOrden(boton, opciones, texto) {
    boton.disabled = true;
    try {
        await pedirApi("/orden-del-dia", opciones);
        cerrarOrdenador();
        await cargar();
        mostrarAviso(texto);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
    }
}

function cerrarOrdenador() {
    document.getElementById("ordenador").hidden = true;
    document.getElementById("linea-tiempo").hidden = false;
    document.getElementById("ordenar-dia").hidden = false;
}

function abrirOrdenador() {
    const ordenador = document.getElementById("ordenador");
    let orden = actividadesQueSeOrdenan();
    const lista = crearElemento("ol", "orden-lista");
    const pintar = () => lista.replaceChildren(...orden.map((actividad, indice) => crearFilaOrden(actividad, indice, orden.length, mover)));
    function mover(indice, paso) {
        const copia = [...orden];
        [copia[indice], copia[indice + paso]] = [copia[indice + paso], copia[indice]];
        orden = copia;
        pintar();
        lista.querySelectorAll("button")[Math.max(0, (indice + paso) * 2 + (paso > 0 ? 1 : 0))]?.focus();
    }
    pintar();

    const listo = crearElemento("button", "boton", "Listo");
    listo.type = "button";
    listo.addEventListener("click", () => guardarOrden(listo, enviarCuerpo(orden), "Orden del día guardado."));
    const sugerido = crearConIcono("button", "boton-secundario", "rotate-ccw", "Volver al orden sugerido");
    sugerido.type = "button";
    sugerido.addEventListener("click", () => guardarOrden(sugerido, { method: "DELETE" }, "Se restableció el orden sugerido."));
    const cancelar = crearElemento("button", "boton-texto", "Cancelar");
    cancelar.type = "button";
    cancelar.addEventListener("click", cerrarOrdenador);
    const acciones = crearElemento("div", "orden-acciones");
    acciones.append(listo, sugerido, cancelar);

    const encabezado = crearElemento("div", "panel-encabezado");
    encabezado.append(crearElemento("h2", "", "Ordenar mi día"));
    encabezado.id = "titulo-ordenador";
    const nota = crearElemento("p", "orden-nota",
        "Mueve las actividades de horario flexible. Las de hora fija y las urgentes no se mueven.");
    const cuerpo = crearElemento("div", "panel-cuerpo");
    cuerpo.append(nota, lista, acciones);
    ordenador.replaceChildren(encabezado, cuerpo);

    document.getElementById("linea-tiempo").hidden = true;
    document.getElementById("ordenar-dia").hidden = true;
    ordenador.hidden = false;
    listo.focus();
}

function enviarCuerpo(orden) {
    return { method: "PUT", body: JSON.stringify({ actividad_ids: orden.map((actividad) => actividad.id) }) };
}

// ---------- Encabezado: lo trabajado (real), lo que falta y lo disponible ----------

// "En turno" o "Fuera de turno", con su horario. Color, ícono (punto) y texto (alcance, Sección 6.3).
function pintarEstadoTurno() {
    const estado = document.getElementById("turno-estado");
    const { turno } = programacion;
    estado.hidden = !turno;
    if (!turno) {
        return;
    }
    const horario = `${turno.nombre}, ${turno.hora_inicio} a ${turno.hora_fin}`;
    // Con la salida marcada ya no está "En turno", aunque el horario del turno no haya terminado.
    const salio = estadoJornada() === "cierre";
    const enTurno = Boolean(programacion.en_turno) && !salio;
    estado.classList.toggle("en-turno", enTurno);
    if (salio) {
        estado.textContent = `Salida marcada (turno ${horario})`;
    } else {
        estado.textContent = `${enTurno ? "En turno" : "Fuera de turno"} (${horario})`;
    }
}

function pintarResumen(resumen) {
    document.getElementById("turno-resumen").replaceChildren(
        crearElemento("strong", "", duracionTexto(resumen.trabajado_min)),
        ` trabajados, ${duracionTexto(resumen.pendiente_min)} por hacer y `
        + `${duracionTexto(resumen.disponible_min)} disponibles`,
    );
    const superaLaJornada = resumen.trabajado_min + resumen.pendiente_min > resumen.capacidad_min;
    document.getElementById("turno-sobrecarga").hidden = !superaLaJornada;
}

// ---------- Carga de datos ----------

// La pantalla se ubica en "Ahora" solo la primera vez que muestra el día; después el operario se
// desplaza por su cuenta.
let vistaUbicada = false;
let nombreOperario = "";

async function cargar() {
    try {
        programacion = await pedirApi("/programacion-del-dia");
        actividades = programacion.actividades;
        pintarEstadoTurno();
        pintarJornada();
        pintarAvisoTurno();
        if (!vistaUbicada && estadoJornada() === "dia") {
            document.querySelector(".linea-nodo.actual")?.scrollIntoView({ block: "center" });
            vistaUbicada = true;
        }
    } catch {
        const mensaje = document.getElementById("mensaje");
        mensaje.hidden = false;
        mensaje.textContent = "No pudimos cargar tus actividades. Revisa tu conexión e inténtalo de nuevo.";
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then((usuario) => {
    nombreOperario = usuario.nombre.split(" ")[0];
    const fecha = fechaLarga(hoy);
    document.getElementById("fecha-hoy").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    document.getElementById("turno-sobrecarga").insertAdjacentHTML("afterbegin", icono("triangle-alert"));
    const ordenar = document.getElementById("ordenar-dia");
    ordenar.append(...crearConIcono("span", "", "arrow-up-down", "Ordenar mi día").childNodes);
    ordenar.addEventListener("click", abrirOrdenador);
    const salida = document.getElementById("marcar-salida");
    salida.append(...crearConIcono("span", "", "log-out", "Marcar salida").childNodes);
    salida.addEventListener("click", abrirSalida);
    // El aviso del turno depende de la hora: se revisa cada medio minuto.
    setInterval(pintarAvisoTurno, 30000);
    cargar();
});
