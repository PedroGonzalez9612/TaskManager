// Vista "Hoy" del Operario: su fila del tablero del turno, en vertical (alcance, Secciones 6.2 y 6.5).
// Una línea de tiempo con las horas de arriba abajo, una tarjeta por actividad en su hora, la actividad en curso
// abierta en su lugar del día y la línea "Ahora", que separa lo que ya pasó de lo que falta.
// La programación la calcula el servidor (GET /programacion-del-dia): lo terminado ocupa el tiempo
// que realmente tomó y lo pendiente se reacomoda desde que el operario queda libre.

const INTERVALO_MINIMO_MIN = 15;    // Un espacio libre más corto que esto no se anuncia.

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
        return `Tomó ${duracionTexto(actividad.ejecucion.tiempo_real_min)} · estimado ${estimado}`;
    }
    if (actividad.estado === "PAUSADA" && nodo.tramo) {
        const faltan = Math.round((new Date(nodo.tramo.fin) - new Date(nodo.tramo.inicio)) / UN_MINUTO);
        return `Faltan ${duracionTexto(faltan)} · estimado ${estimado}`;
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
    if (actividad.reprogramada) {
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
    boton.addEventListener("click", async () => {
        boton.disabled = true;
        try {
            await pedirApi(`/actividades/${actividad.id}/finalizar`, { method: "POST" });
            await cargar();
            mostrarAviso(`${actividad.codigo} finalizada.`);
        } catch (error) {
            mostrarAviso(error.message, "advertencia");
            boton.disabled = false;
        }
    });
    return boton;
}

function crearCronometro(actividad, clase) {
    const cronometro = crearElemento("span", clase);
    cronometro.setAttribute("role", "timer");
    cronometro.setAttribute("aria-label", "Tiempo en ejecución");
    alTic.push(() => { cronometro.textContent = textoCronometro(segundosTrabajados(actividad.ejecucion)); });
    return cronometro;
}

// Actividad en curso, abierta en su lugar del día: cronómetro, avance contra el estimado y acciones.
function crearTarjetaEnCurso(nodo) {
    const { actividad } = nodo;
    const tarjeta = crearElemento("section", "tarjeta-en-curso");
    tarjeta.setAttribute("aria-label", "Actividad en curso");

    const cabecera = crearElemento("p", "tarjeta-cabecera");
    cabecera.append(
        crearConIcono("span", "cifra", "play", `En curso · desde ${nodo.desde}`),
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
    const detalle = crearElemento("button", "boton-secundario", "Ver detalle");
    detalle.type = "button";
    detalle.addEventListener("click", () => abrirDetalle(actividad));
    acciones.append(detalle, crearBotonFinalizar(actividad, "boton"));

    tarjeta.append(cabecera, crearElemento("h2", "", actividad.titulo), lugar, tiempo, avance, acciones);
    return tarjeta;
}

// Con una urgente pendiente, la actividad en curso se encoge y explica qué hacer para atenderla.
function crearTarjetaCompacta(nodo) {
    const { actividad } = nodo;
    const tarjeta = crearElemento("section", "tarjeta-compacta");
    tarjeta.setAttribute("aria-label", "Actividad en curso");

    const cabecera = crearElemento("p", "tarjeta-cabecera");
    cabecera.append(crearConIcono("span", "", "play", "En curso"), crearCronometro(actividad, "cifra dato-fuerte"));

    tarjeta.append(
        cabecera,
        crearElemento("strong", "", actividad.titulo),
        crearElemento("p", "tarjeta-nota", "Para atender la urgente, finaliza primero esta actividad."),
        crearBotonFinalizar(actividad, "boton-secundario"),
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

    const boton = crearElemento("button", "boton", "Ver y atender la actividad");
    boton.type = "button";
    boton.addEventListener("click", () => abrirDetalle(actividad));

    tarjeta.append(
        crearConIcono("p", "tarjeta-cabecera", "triangle-alert", "Urgente"),
        crearElemento("h2", "", actividad.titulo), datos, boton,
    );
    return tarjeta;
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

function crearMarcaEntrada() {
    const { asistencia } = programacion;
    if (asistencia) {
        const marca = crearElemento("p", "linea-marca");
        marca.append("Marcaste entrada a las ", crearElemento("strong", "cifra", horaLocal(asistencia.entrada)));
        return marca;
    }
    // Una sola acción principal por pantalla: si ya hay algo en curso, la principal es "Finalizar".
    const hayEnCurso = programacion.tramos.some((tramo) => tramo.tipo === "EN_CURSO");
    const boton = crearConIcono("button", hayEnCurso ? "boton-secundario" : "boton", "log-in", "Marcar entrada");
    boton.type = "button";
    boton.addEventListener("click", () => marcarAsistencia(boton, "/asistencia/entrada", "Entrada registrada."));
    return boton;
}

function crearMarcaSalida() {
    const { asistencia, turno } = programacion;
    const bloque = crearElemento("div", "linea-fin-turno");
    bloque.append(crearElemento("span", "", turno ? "Fin del turno" : "Fin de la jornada"));
    if (asistencia?.salida) {
        const marca = crearElemento("span", "linea-marca");
        marca.append("Saliste a las ", crearElemento("strong", "cifra", horaLocal(asistencia.salida)));
        bloque.append(marca);
    } else if (asistencia) {
        const boton = crearConIcono("button", "boton-secundario", "log-out", "Marcar salida");
        boton.type = "button";
        boton.addEventListener("click", () => marcarAsistencia(boton, "/asistencia/salida", "Salida registrada."));
        bloque.append(boton);
    }
    return bloque;
}

// ---------- Línea de tiempo ----------

function crearNodo(nodo) {
    const elemento = crearElemento("li", `linea-nodo ${nodo.zona}`);

    if (nodo.tipo === "intervalo") {
        elemento.classList.add("linea-nodo-intervalo");
        elemento.append(crearElemento("p", "linea-intervalo cifra", `Disponible · ${duracionTexto(nodo.minutos)}`));
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
        crearElemento("span", "orden-datos cifra", `${NOMBRE_PRIORIDAD[actividad.prioridad]} · ${duracionTexto(actividad.tiempo_estimado_min)}`),
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
    estado.classList.toggle("en-turno", Boolean(programacion.en_turno));
    estado.textContent = programacion.en_turno ? `En turno · ${horario}` : `Fuera de turno · ${horario}`;
}

function pintarResumen(resumen) {
    document.getElementById("turno-resumen").replaceChildren(
        crearElemento("strong", "", duracionTexto(resumen.trabajado_min)),
        ` trabajados · ${duracionTexto(resumen.pendiente_min)} por hacer · `
        + `${duracionTexto(resumen.disponible_min)} disponibles`,
    );
    const superaLaJornada = resumen.trabajado_min + resumen.pendiente_min > resumen.capacidad_min;
    document.getElementById("turno-sobrecarga").hidden = !superaLaJornada;
}

// ---------- Carga de datos ----------

async function cargar() {
    try {
        programacion = await pedirApi("/programacion-del-dia");
        actividades = programacion.actividades;
        pintarResumen(programacion.resumen);
        pintarEstadoTurno();
        pintarLineaDeTiempo();
    } catch {
        const mensaje = document.getElementById("mensaje");
        mensaje.hidden = false;
        mensaje.textContent = "No pudimos cargar tus actividades. Revisa tu conexión e inténtalo de nuevo.";
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then((usuario) => {
    document.getElementById("saludo").textContent = `Tu turno, ${usuario.nombre.split(" ")[0]}`;
    const fecha = fechaLarga(hoy);
    document.getElementById("fecha-hoy").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    document.getElementById("turno-sobrecarga").insertAdjacentHTML("afterbegin", icono("triangle-alert"));
    const ordenar = document.getElementById("ordenar-dia");
    ordenar.append(...crearConIcono("span", "", "arrow-up-down", "Ordenar mi día").childNodes);
    ordenar.addEventListener("click", abrirOrdenador);
    cargar();
});
