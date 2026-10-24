// Vista "Inicio" del Operario (alcance, Sección 6.1): la página que lo recibe después de iniciar
// sesión y responde "¿qué hago ahora?". Muestra el estado de su turno, la actividad en curso o lo que
// sigue, y una sola acción principal. Antes de la entrada, "Marcar entrada" (y pasa a Hoy) o ver el día
// en modo de lectura; con la entrada, abrir la actividad y, al final, "Marcar salida" (que solo está
// aquí); después de la salida, el balance de la jornada. Las barras del turno y de la jornada están en Hoy.

const RUTA_HOY = "/static/operario/index.html";

let programacion = null;
let nombreOperario = "";
let cargadaEn = 0;      // Cuándo llegó la programación: el tiempo en curso se adelanta desde ahí.

// "Buenos días" hasta el mediodía, "Buenas tardes" hasta las 7 de la noche y después "Buenas noches".
function saludo() {
    const hora = new Date().getHours();
    let parte = "Buenas noches";
    if (hora >= 5 && hora < 12) {
        parte = "Buenos días";
    } else if (hora >= 12 && hora < 19) {
        parte = "Buenas tardes";
    }
    return `${parte}, ${nombreOperario}`;
}

// Una frase con partes resaltadas: frase("p", "clase", "Empieza a las ", ["19:00"], ".").
// Lo que va entre corchetes se escribe en semibold con números de ancho fijo.
function frase(etiqueta, clase, ...partes) {
    const elemento = crearElemento(etiqueta, clase);
    for (const parte of partes) {
        elemento.append(Array.isArray(parte) ? crearElemento("strong", "cifra", parte[0]) : parte);
    }
    return elemento;
}

function actividadDe(tramo) {
    return programacion.actividades.find((actividad) => actividad.id === tramo.actividad_id);
}

function abrirDetalle(actividad) {
    abrirDetalleOperario(actividad, programacion.actividades, cargar,
        { soloLectura: estadoDeJornada(programacion) !== "dia" });
}

// "Operación, prioridad media. 40 min estimados." Los datos como frase, sin etiquetas (6.2).
// La urgente ya lleva su etiqueta: la frase no lo repite.
function fraseDeDatos(actividad) {
    const categoria = NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria;
    const estimado = `${duracionTexto(actividad.tiempo_estimado_min)} estimados.`;
    if (actividad.prioridad === "URGENTE") {
        return `${categoria}. ${estimado}`;
    }
    const prioridad = (NOMBRE_PRIORIDAD[actividad.prioridad] || actividad.prioridad).toLowerCase();
    return `${categoria}, prioridad ${prioridad}. ${estimado}`;
}

// "40" si es menos de una hora (se lee "16 min de 40 estimados"); si no, "1 h 30 min".
function estimadoCorto(minutos) {
    return minutos < 60 ? String(minutos) : duracionTexto(minutos);
}

// ---------- El turno, debajo del saludo ----------

function crearLineaTurno() {
    const { turno, asistencia } = programacion;
    const estado = estadoDeJornada(programacion);
    if (estado === "cierre") {
        return [frase("p", "inicio-turno-texto", "Marcaste la salida a las ", [horaDeMomento(asistencia.salida)], ".")];
    }
    if (!turno) {
        return [crearElemento("p", "inicio-turno-texto", "No tienes un turno asignado.")];
    }
    if (estado === "inicio") {
        if (programacion.retraso_entrada_min > 0) {
            // Llegada tarde (alcance, Sección 5.1): una línea con su ícono, en ámbar.
            return [crearConIcono("p", "inicio-turno-texto linea-advertencia", "clock",
                `Tu turno empezó a las ${turno.hora_inicio}, hace ${duracionTexto(programacion.retraso_entrada_min)}. Todavía no marcas la entrada.`)];
        }
        const faltan = minutosHasta(turno.inicio);
        if (faltan > 0) {
            return [frase("p", "inicio-turno-texto", "Tu turno empieza a las ", [turno.hora_inicio], `, en ${duracionTexto(faltan)}.`)];
        }
        if (minutosHasta(turno.fin) <= 0) {
            return [frase("p", "inicio-turno-texto", "Tu turno terminó a las ", [turno.hora_fin], ".")];
        }
        return [frase("p", "inicio-turno-texto", "Tu turno empezó a las ", [turno.hora_inicio], ".")];
    }
    const faltan = minutosHasta(turno.fin);
    if (faltan <= 0) {
        return [crearElemento("p", "inicio-turno-texto", `Fuera de turno desde las ${turno.hora_fin}.`)];
    }
    const enTurno = crearElemento("p", "inicio-turno-texto");
    enTurno.append(crearElemento("span", "punto-en-turno"), crearElemento("strong", "texto-en-turno", "En turno"),
        ` hasta las ${turno.hora_fin}`);
    const lineas = [enTurno];
    if (faltan <= AVISO_TURNO_MIN) {
        lineas.push(crearConIcono("p", "inicio-turno-texto linea-info", "info", `Tu turno termina en ${duracionTexto(faltan)}.`));
    }
    return lineas;
}

// ---------- Lo de ahora: la urgente, la actividad en curso o lo que sigue ----------

function crearUrgente(actividad, hayEnCurso) {
    const bloque = crearElemento("div", "inicio-urgente");
    bloque.append(
        crearConIcono("p", "inicio-urgente-etiqueta", "triangle-alert", "Urgente"),
        crearElemento("h2", "inicio-actividad-nombre", actividad.titulo),
        crearElemento("p", "", hayEnCurso
            ? "Pausa la que llevas y atiéndela antes que lo demás."
            : "Atiéndela antes que lo demás."),
    );
    return bloque;
}

// Minutos trabajados en la actividad en curso: los que dio el servidor más los que pasaron desde
// que se cargó la página (la hora la pone el servidor; aquí solo se adelanta lo que se muestra).
function minutosEnCurso(actividad) {
    const base = actividad.ejecucion?.tiempo_real_min || 0;
    return base + Math.floor((Date.now() - cargadaEn) / MINUTO_MS);
}

function crearEnCurso(actividad) {
    const bloque = crearElemento("div", "inicio-en-curso");
    const cabeza = crearElemento("div", "inicio-cabeza");
    cabeza.append(crearElemento("p", "inicio-rotulo", "Ahora"),
        crearConIcono("p", "inicio-estado-en-curso", "circle", "En curso"));

    const estimado = actividad.tiempo_estimado_min;
    const trabajado = minutosEnCurso(actividad);
    const avance = crearElemento("div", "inicio-avance");
    const restante = estimado - trabajado;
    avance.append(
        frase("p", "", [duracionTexto(trabajado)], ` de ${estimadoCorto(estimado)} estimados`),
        crearElemento("p", "texto-secundario", restante > 0
            ? `Quedan unos ${duracionTexto(restante)}`
            : `Pasó ${duracionTexto(-restante)} del estimado`),
    );
    const barra = crearElemento("div", "barra-avance");
    barra.setAttribute("role", "progressbar");
    barra.setAttribute("aria-label", "Tiempo trabajado contra lo estimado");
    barra.setAttribute("aria-valuemin", "0");
    barra.setAttribute("aria-valuemax", String(estimado));
    barra.setAttribute("aria-valuenow", String(Math.min(trabajado, estimado)));
    const relleno = crearElemento("span", "barra-avance-relleno");
    relleno.style.width = `${Math.min(100, (trabajado * 100) / estimado)}%`;
    barra.append(relleno);

    bloque.append(cabeza, crearElemento("h2", "inicio-actividad-nombre", actividad.titulo));
    if (actividad.ejecucion?.fecha_inicio) {
        bloque.append(crearElemento("p", "texto-secundario", `Desde las ${horaDeMomento(actividad.ejecucion.fecha_inicio)}`));
    }
    bloque.append(avance, barra);
    return bloque;
}

// Lo que sigue: toda la fila abre el detalle; el texto pasa a otra línea en vez de cortarse.
function crearLoQueSigue(tramo, actividad) {
    const bloque = crearElemento("div", "inicio-sigue-bloque");
    const cabeza = crearElemento("div", "inicio-cabeza");
    const hora = tramo.hora_fija ? `A las ${horaDeMomento(tramo.inicio)}` : `Hacia las ${horaDeMomento(tramo.inicio)}`;
    cabeza.append(crearElemento("p", "inicio-rotulo", "Lo que sigue"), crearElemento("p", "texto-secundario cifra", hora));

    const fila = crearElemento("button", "inicio-sigue");
    fila.type = "button";
    const textos = crearElemento("span", "inicio-sigue-textos");
    // Urgente es una de las excepciones que llevan etiqueta (6.2).
    if (actividad.prioridad === "URGENTE") {
        textos.append(crearSenalPrioridad("URGENTE"));
    }
    textos.append(crearElemento("strong", "", actividad.titulo), crearElemento("span", "texto-secundario", fraseDeDatos(actividad)));
    fila.append(textos);
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.addEventListener("click", () => abrirDetalle(actividad));
    bloque.append(cabeza, fila);
    return bloque;
}

// La siguiente de hora fija, en una línea: no se mueve, así que conviene tenerla presente.
function crearSiguienteFija(excluir) {
    const tramo = programacion.tramos.find((t) => t.tipo === "PENDIENTE" && t.hora_fija && !t.vencida
        && t.actividad_id !== excluir);
    if (!tramo) {
        return null;
    }
    const linea = crearElemento("p", "inicio-fija");
    linea.insertAdjacentHTML("beforeend", icono("lock"));
    linea.append(frase("span", "", "Sigue a las ", [horaDeMomento(tramo.inicio)], `: ${actividadDe(tramo).titulo}`));
    return linea;
}

// Arma lo de ahora y devuelve también la actividad que abre la acción principal.
function crearAhora() {
    const pendientes = programacion.tramos.filter((t) => t.tipo === "PENDIENTE");
    const tramoUrgente = pendientes.find((t) => actividadDe(t)?.prioridad === "URGENTE");
    const tramoEnCurso = programacion.tramos.find((t) => t.tipo === "EN_CURSO");
    const tramoSigue = pendientes.find((t) => t.siguiente) || pendientes.find((t) => !t.vencida);
    const contenido = [];
    let principal = null;

    if (tramoUrgente) {
        const urgente = actividadDe(tramoUrgente);
        contenido.push(crearUrgente(urgente, Boolean(tramoEnCurso)));
        principal = { texto: "Atender la urgente", actividad: urgente };
    }
    if (tramoEnCurso) {
        const enCurso = actividadDe(tramoEnCurso);
        contenido.push(crearEnCurso(enCurso));
        principal ||= { texto: "Abrir actividad", actividad: enCurso };
    } else if (tramoSigue && tramoSigue !== tramoUrgente) {
        const sigue = actividadDe(tramoSigue);
        contenido.push(crearLoQueSigue(tramoSigue, sigue));
        principal ||= { texto: "Abrir actividad", actividad: sigue };
    }

    const fija = crearSiguienteFija(principal?.actividad.id);
    if (fija) {
        contenido.push(fija);
    }
    if (!contenido.length) {
        contenido.push(crearElemento("p", "texto-secundario", "No tienes más actividades por hacer hoy."));
    }
    return { contenido, principal };
}

// Antes de la entrada: lo que sigue y cuánto trabajo hay en el día.
function crearAntesDeLaEntrada() {
    const pendientes = programacion.tramos.filter((t) => t.tipo !== "FINALIZADA");
    const tramoSigue = pendientes.find((t) => t.siguiente) || pendientes[0];
    const contenido = [];
    if (tramoSigue) {
        contenido.push(crearLoQueSigue(tramoSigue, actividadDe(tramoSigue)));
    }
    const cuantas = pendientes.length;
    contenido.push(crearElemento("p", "texto-secundario", cuantas
        ? `Tienes ${cuantas === 1 ? "1 actividad" : `${cuantas} actividades`} hoy, ${duracionTexto(programacion.resumen.pendiente_min)} en total.`
        : "No tienes actividades programadas para hoy."));
    return contenido;
}

// Después de la salida: el balance de la jornada, en frases (sin una tarjeta por número).
function crearBalance() {
    const { tramos, resumen, asistencia } = programacion;
    const finalizadas = tramos.filter((tramo) => tramo.tipo === "FINALIZADA").length;
    const sinFinalizar = tramos.length - finalizadas;
    const contenido = [
        crearElemento("h2", "inicio-rotulo", "Balance de la jornada"),
        frase("p", "", "Entraste a las ", [horaDeMomento(asistencia.entrada)], " y saliste a las ",
            [horaDeMomento(asistencia.salida)], `: ${duracionTexto(asistencia.minutos_presente)} presente.`),
        frase("p", "", "Trabajaste ", [duracionTexto(resumen.trabajado_min)], " en actividades."),
        frase("p", "", "Finalizaste ", [`${finalizadas} de ${tramos.length}`], " actividades."),
    ];
    if (sinFinalizar) {
        const cuantas = sinFinalizar === 1 ? "Quedó 1 actividad sin finalizar." : `Quedaron ${sinFinalizar} actividades sin finalizar.`;
        contenido.push(crearConIcono("p", "linea-info", "info", `${cuantas} Las de horario flexible pasan a tu siguiente jornada.`));
    }
    contenido.push(crearElemento("p", "texto-secundario", "Si marcaste la salida por error, pide a tu Administrador que la corrija."));
    return contenido;
}

// ---------- Acciones: una sola principal, abajo, al alcance del pulgar (6.2) ----------

function crearBoton(clase, iconoNombre, texto, alHacer) {
    const boton = iconoNombre ? crearConIcono("button", clase, iconoNombre, texto) : crearElemento("button", clase, texto);
    boton.type = "button";
    boton.addEventListener("click", alHacer);
    return boton;
}

function crearAcciones(estado, principal) {
    const acciones = [];
    if (estado === "inicio") {
        const entrada = crearBoton("boton boton-principal-grande", "log-in", "Marcar entrada",
            () => marcarAsistencia(entrada, "/asistencia/entrada", "Entrada registrada.",
                async () => { window.location.href = RUTA_HOY; }));
        const verDia = crearElemento("a", "enlace-grande", "Ver mi día sin marcar la entrada");
        verDia.href = RUTA_HOY;
        acciones.push(entrada, verDia);
        if (programacion.asistencia && programacion.asistencia.jornada !== programacion.fecha) {
            acciones.push(crearElemento("p", "texto-secundario", "Tu jornada anterior quedó sin marca de salida. Tu Administrador la corrige."));
        }
    } else if (estado === "dia") {
        if (principal) {
            acciones.push(crearBoton("boton boton-principal-grande", "", principal.texto, () => abrirDetalle(principal.actividad)));
        }
        // "Marcar salida" solo está en Inicio. Con una actividad en curso se desactiva y se dice por qué.
        const enCurso = programacion.tramos.some((t) => t.tipo === "EN_CURSO");
        const salida = crearBoton("boton-secundario boton-principal-grande", "log-out", "Marcar salida",
            () => abrirSalida(programacion, cargar));
        salida.disabled = enCurso;
        acciones.push(salida);
        if (enCurso) {
            const motivo = crearElemento("p", "texto-secundario inicio-motivo", "Para marcar la salida, pausa o finaliza la actividad en curso.");
            motivo.id = "motivo-salida";
            salida.setAttribute("aria-describedby", motivo.id);
            acciones.push(motivo);
        }
    } else {
        const verDia = crearElemento("a", "enlace-grande", "Ver mi día");
        verDia.href = RUTA_HOY;
        acciones.push(verDia);
    }
    return acciones;
}

// ---------- Pintar ----------

function pintarFecha() {
    const fecha = fechaLarga(new Date());
    const conMayuscula = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    // En turno se agrega la hora; antes de la entrada basta con la fecha.
    const conHora = programacion && estadoDeJornada(programacion) === "dia";
    document.getElementById("fecha-inicio").textContent = conHora ? `${conMayuscula}, ${horaDeMomento(Date.now())}` : conMayuscula;
}

function pintar() {
    const estado = estadoDeJornada(programacion);
    document.getElementById("saludo").textContent = saludo();
    pintarFecha();
    document.getElementById("inicio-turno").replaceChildren(...crearLineaTurno());

    let contenido;
    let principal = null;
    if (estado === "inicio") {
        contenido = crearAntesDeLaEntrada();
    } else if (estado === "dia") {
        ({ contenido, principal } = crearAhora());
    } else {
        contenido = crearBalance();
    }
    const ahora = document.getElementById("inicio-ahora");
    ahora.replaceChildren(...contenido);
    ahora.hidden = false;

    const acciones = document.getElementById("inicio-acciones");
    acciones.replaceChildren(...crearAcciones(estado, principal));
    acciones.hidden = false;
}

async function cargar() {
    const mensaje = document.getElementById("mensaje");
    try {
        programacion = await pedirApi("/programacion-del-dia");
        cargadaEn = Date.now();
        mensaje.hidden = true;
        pintar();
    } catch {
        mensaje.hidden = false;
        mensaje.textContent = "No pudimos cargar tu jornada. Revisa tu conexión e inténtalo de nuevo.";
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then((usuario) => {
    nombreOperario = usuario.nombre.split(" ")[0];
    // El tiempo se muestra en minutos: basta con repintar cada medio minuto (sin segundos corriendo).
    setInterval(() => programacion && !document.querySelector("dialog[open]") && pintar(), 30000);
    cargar();
});
