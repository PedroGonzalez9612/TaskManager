// Vista "Hoy" del Operario: su renglón del tablero del turno, en vertical (alcance, Secciones 6.1,
// 6.2 y 6.5; diseño en docs/disenos/operario_v3/3_hoy.png). Una línea de tiempo de solo lectura: las
// horas de arriba abajo, una fila por actividad y la línea "Ahora". El riel es sólido en lo recorrido y
// punteado en lo que viene. Toda fila abre el detalle, que es donde se inicia, se pausa y se finaliza.
// La programación la calcula el servidor (GET /programacion-del-dia). Sin la entrada marcada, o después
// de la salida, el detalle no ofrece iniciar ni reanudar (modo de lectura).

const INTERVALO_MINIMO_MIN = 5;     // Un intervalo disponible más corto que esto no se anuncia.
const RUTA_INICIO = "/static/operario/inicio.html";
const UN_MINUTO = 60000;

let actividades = [];           // Las del día, como las presenta la API (para abrir su detalle).
let programacion = null;
let cargadaEn = 0;              // Cuándo llegó la programación: el tiempo en curso se adelanta desde ahí.
let ordenando = false;          // Mientras se ordena el día no se muestra nada más (alcance, Sección 6.1).

function horaLocal(momento) {
    return horaDeMomento(momento);
}

function modoLectura() {
    return estadoDeJornada(programacion) !== "dia";
}

function abrirDetalle(actividad) {
    abrirDetalleOperario(actividad, actividades, cargar, { soloLectura: modoLectura() });
}

// ---------- Armar el día con la programación del servidor ----------
// Cada nodo dice qué es ("tipo"), en qué parte del día cae ("zona": pasado, curso, actual o futuro) y
// su momento. La zona decide el riel: sólido hasta "Ahora", punteado después.

function nodoDeTramo(tramo, actividad) {
    const momento = new Date(tramo.inicio).getTime();
    if (tramo.tipo === "FINALIZADA") {
        return { tipo: "hecha", zona: "pasado", actividad, tramo, momento };
    }
    if (tramo.tipo === "EN_CURSO") {
        return { tipo: "en-curso", zona: "curso", actividad, tramo, momento };
    }
    if (actividad.prioridad === "URGENTE") {
        return { tipo: "urgente", zona: "futuro", actividad, tramo, momento };
    }
    if (tramo.vencida) {
        return { tipo: "pendiente", zona: "pasado", actividad, tramo, momento, vencida: true };
    }
    return { tipo: "pendiente", zona: "futuro", actividad, tramo, momento, siguiente: tramo.siguiente };
}

// El turno abre y cierra la línea de tiempo. Lo que queda después del fin del turno va sobre el
// rayado de sobrecarga (alcance, Sección 6.3).
function conTurno(nodos) {
    const { turno } = programacion;
    const ahora = Date.now();
    if (!turno) {
        return [...nodos, { tipo: "fin-turno", zona: "futuro", momento: Infinity }];
    }
    const inicio = new Date(turno.inicio).getTime();
    const fin = new Date(turno.fin).getTime();
    const entrada = { tipo: "inicio-turno", zona: inicio <= ahora ? "pasado" : "futuro", momento: inicio };
    const cierre = { tipo: "fin-turno", zona: fin <= ahora ? "pasado" : "futuro", momento: fin };
    const antes = nodos.filter((nodo) => nodo.zona !== "futuro" || nodo.momento < fin);
    const despues = nodos.filter((nodo) => nodo.zona === "futuro" && nodo.momento >= fin)
        .map((nodo) => ({ ...nodo, despuesDelTurno: true }));
    // El inicio del turno va en su lugar: antes de lo que empieza después de él.
    const posicion = antes.findIndex((nodo) => nodo.momento >= inicio && nodo.zona === "futuro");
    const conEntrada = posicion === -1 ? [entrada, ...antes]
        : entrada.zona === "pasado" ? [entrada, ...antes] : [...antes.slice(0, posicion), entrada, ...antes.slice(posicion)];
    return [...conEntrada, cierre, ...despues];
}

// La línea "Ahora" separa lo que ya pasó (y lo que está en curso) de lo que falta.
function conAhora(nodos) {
    const ahora = { tipo: "ahora", zona: "actual", momento: Date.now() };
    const posicion = nodos.findIndex((nodo) => nodo.zona === "futuro");
    return posicion === -1 ? [...nodos, ahora] : [...nodos.slice(0, posicion), ahora, ...nodos.slice(posicion)];
}

// "Ordenar mi día" va justo después de la línea "Ahora" (alcance, Sección 6.1). Solo con la entrada
// marcada y con al menos dos actividades que se puedan mover.
function conOrdenar(nodos) {
    if (modoLectura() || actividadesQueSeOrdenan().length < 2) {
        return nodos;
    }
    const posicion = nodos.findIndex((nodo) => nodo.tipo === "ahora") + 1;
    return [...nodos.slice(0, posicion), { tipo: "ordenar", zona: "futuro" }, ...nodos.slice(posicion)];
}

// Los intervalos disponibles entre una actividad y la siguiente se dicen en una línea de texto.
function conIntervalos(nodos) {
    const resultado = [];
    let finAnterior = null;
    for (const nodo of nodos) {
        const ocupaHora = ["pendiente", "urgente", "fin-turno"].includes(nodo.tipo);
        if (ocupaHora && nodo.zona === "futuro" && finAnterior !== null && Number.isFinite(nodo.momento)
            && nodo.momento - finAnterior >= INTERVALO_MINIMO_MIN * UN_MINUTO) {
            resultado.push({ tipo: "intervalo", zona: "futuro", momento: finAnterior,
                minutos: Math.round((nodo.momento - finAnterior) / UN_MINUTO), despuesDelTurno: nodo.despuesDelTurno });
        }
        resultado.push(nodo);
        // Desde dónde se cuenta lo libre: el fin de lo que está en curso o viene, "Ahora" o el inicio del turno.
        if (nodo.tramo && nodo.zona !== "pasado") {
            finAnterior = Math.max(finAnterior ?? 0, new Date(nodo.tramo.fin).getTime());
        } else if (nodo.tipo === "ahora" || (nodo.tipo === "inicio-turno" && nodo.zona === "futuro")) {
            finAnterior = Math.max(finAnterior ?? 0, nodo.momento);
        }
    }
    return resultado;
}

function armarDia() {
    const porId = new Map(programacion.actividades.map((actividad) => [actividad.id, actividad]));
    const nodos = programacion.tramos.filter((tramo) => porId.has(tramo.actividad_id))
        .map((tramo) => nodoDeTramo(tramo, porId.get(tramo.actividad_id)));
    return conIntervalos(conOrdenar(conAhora(conTurno(nodos))));
}

// ---------- Filas ----------

// Minutos trabajados en la actividad en curso: los del servidor más los que pasaron desde que se cargó.
function minutosEnCurso(actividad) {
    return (actividad.ejecucion?.tiempo_real_min || 0) + Math.floor((Date.now() - cargadaEn) / UN_MINUTO);
}

// "40" si es menos de una hora ("16 min de 40"); si no, "1 h 30 min".
function estimadoCorto(minutos) {
    return minutos < 60 ? String(minutos) : duracionTexto(minutos);
}

function textoRetraso(actividad) {
    const dias = actividad.dias_de_retraso;
    return dias === 1 ? "Retraso: 1 día" : `Retraso: ${dias} días`;
}

// Las excepciones llevan etiqueta (Urgente, Hora fija, Retraso); "Siguiente" es texto (6.2).
function crearExcepciones(nodo) {
    const { actividad } = nodo;
    const excepciones = [];
    if (actividad.hora_programada && nodo.tipo !== "hecha") {
        excepciones.push(crearConIcono("span", "etiqueta etiqueta-hora-fija", "lock", "Hora fija"));
    }
    if (nodo.vencida) {
        excepciones.push(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", "Hora vencida"));
    } else if (actividad.reprogramada && nodo.tipo !== "hecha") {
        excepciones.push(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", textoRetraso(actividad)));
    }
    if (nodo.siguiente) {
        excepciones.push(crearElemento("span", "fila-siguiente", "Siguiente"));
    }
    if (!excepciones.length) {
        return null;
    }
    const linea = crearElemento("span", "fila-excepciones");
    linea.append(...excepciones);
    return linea;
}

// Los datos como frase: "Operación, 30 min, prioridad media". El estado va como texto con su ícono.
function crearDatos(nodo) {
    const { actividad, tramo } = nodo;
    const datos = crearElemento("span", "fila-datos");
    const categoria = NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria;
    if (nodo.tipo === "en-curso") {
        datos.classList.add("fila-datos-en-curso");
        datos.textContent = `En curso, ${duracionTexto(minutosEnCurso(actividad))} de ${estimadoCorto(actividad.tiempo_estimado_min)}`;
        return datos;
    }
    if (nodo.tipo === "hecha") {
        const real = actividad.ejecucion?.tiempo_real_min;
        datos.append(...crearConIcono("span", "fila-estado estado-finalizada", "check",
            real ? `Finalizada, tomó ${duracionTexto(real)}` : "Finalizada").childNodes);
        return datos;
    }
    if (actividad.estado === "PAUSADA") {
        const faltan = Math.round((new Date(tramo.fin) - new Date(tramo.inicio)) / UN_MINUTO);
        const pausada = crearConIcono("span", "fila-estado estado-pausada", "pause",
            faltan > 0 ? `Pausada, faltan ${duracionTexto(faltan)}` : "Pausada");
        datos.append(pausada, `. ${categoria}`);
        return datos;
    }
    datos.append(`${categoria}, ${duracionTexto(actividad.tiempo_estimado_min)}`);
    if (["ALTA", "MEDIA", "BAJA"].includes(actividad.prioridad)) {
        datos.append(", ");
        datos.append(crearConIcono("span", `fila-prioridad prioridad-texto-${actividad.prioridad.toLowerCase()}`,
            ICONO_PRIORIDAD[actividad.prioridad], `prioridad ${NOMBRE_PRIORIDAD[actividad.prioridad].toLowerCase()}`));
    }
    return datos;
}

function crearFila(nodo) {
    const { actividad } = nodo;
    const fila = crearElemento("button", `fila fila-${nodo.tipo}`);
    fila.type = "button";
    const textos = crearElemento("span", "fila-textos");
    const excepciones = crearExcepciones(nodo);
    if (excepciones) {
        textos.append(excepciones);
    }
    textos.append(crearElemento("strong", "fila-nombre", actividad.titulo), crearDatos(nodo));
    fila.append(textos);
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.setAttribute("aria-label", `${actividad.titulo}. Ver detalle`);
    fila.addEventListener("click", () => abrirDetalle(actividad));
    return fila;
}

// Urgente pendiente: el único bloque rojo lleno de la pantalla. Se atiende desde su detalle.
function crearUrgente(nodo) {
    const { actividad } = nodo;
    const bloque = crearElemento("section", "dia-urgente");
    bloque.setAttribute("role", "alert");
    const hayEnCurso = programacion.tramos.some((tramo) => tramo.tipo === "EN_CURSO");
    const abrir = crearElemento("button", "boton-sobre-urgente", "Abrir la urgente");
    abrir.type = "button";
    abrir.addEventListener("click", () => abrirDetalle(actividad));
    bloque.append(
        crearConIcono("p", "dia-urgente-etiqueta", "triangle-alert", actividad.estado === "PAUSADA" ? "Urgente en pausa" : "Urgente"),
        crearElemento("h2", "", actividad.titulo),
        crearElemento("p", "", `${NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria}, ${duracionTexto(actividad.tiempo_estimado_min)}. `
            + (hayEnCurso ? "Pausa la que llevas y atiéndela." : "Atiéndela antes que lo demás.")),
        abrir,
    );
    return bloque;
}

// ---------- Marcas del turno y de "Ahora" ----------

function crearMarcaEntrada() {
    const marca = crearElemento("p", "dia-marca");
    const { asistencia, fecha } = programacion;
    if (asistencia && asistencia.jornada === fecha) {
        marca.append("Inicio del turno, entrada a las ", crearElemento("span", "cifra", horaLocal(asistencia.entrada)));
    } else {
        marca.textContent = "Inicio del turno. Todavía no marcas la entrada";
    }
    return marca;
}

// El fin del turno suma lo que queda después de él: cuánto tendría que quedarse (alcance, Sección 5.1).
function crearMarcaFinTurno() {
    const marca = crearElemento("div", "dia-marca");
    marca.append(crearElemento("p", "", programacion.turno ? "Fin del turno" : "Fin de la jornada"));
    const fuera = programacion.tramos.filter((tramo) => tramo.fuera_del_turno_min > 0);
    if (fuera.length) {
        const cuantas = fuera.length === 1 ? "1 actividad pasa" : `${fuera.length} actividades pasan`;
        marca.append(crearConIcono("p", "linea-advertencia", "clock",
            `${cuantas} de tu turno: ${duracionTexto(programacion.resumen.fuera_del_turno_min)} más`));
    }
    return marca;
}

function crearBotonOrdenar() {
    const boton = crearConIcono("button", "boton-secundario dia-ordenar", "arrow-up-down", "Ordenar mi día");
    boton.type = "button";
    boton.addEventListener("click", abrirOrdenador);
    return boton;
}

// La hora a la izquierda: exacta y en semibold si es de hora fija; con "~" y en gris si es calculada.
function crearHora(nodo) {
    const hora = crearElemento("span", "dia-hora cifra");
    if (nodo.tipo === "ahora") {
        hora.classList.add("dia-hora-ahora");
        hora.textContent = horaLocal(Date.now());
        return hora;
    }
    if (["ordenar"].includes(nodo.tipo) || !Number.isFinite(nodo.momento)) {
        return hora;
    }
    const aproximada = nodo.tipo === "intervalo" || (nodo.tramo && nodo.tramo.aproximada && nodo.zona === "futuro");
    hora.textContent = (aproximada ? "~" : "") + horaLocal(nodo.momento);
    hora.classList.add(aproximada ? "dia-hora-aproximada" : "dia-hora-exacta");
    return hora;
}

// El nodo del riel: lleno en lo hecho, anillo grueso en lo que está en curso, abierto en lo que viene.
function crearPunto(nodo) {
    const punto = crearElemento("span", "dia-punto");
    punto.setAttribute("aria-hidden", "true");
    if (nodo.tipo === "fin-turno") {
        punto.classList.add("dia-punto-fin");
    } else if (nodo.tipo === "en-curso") {
        punto.classList.add("dia-punto-curso");
    } else if (nodo.tipo === "ahora" || nodo.zona === "pasado") {
        punto.classList.add("dia-punto-lleno");
    } else if (["intervalo", "ordenar"].includes(nodo.tipo)) {
        punto.classList.add("dia-punto-ninguno");
    }
    return punto;
}

function crearNodo(nodo) {
    const elemento = crearElemento("li", `dia-nodo dia-${nodo.zona} dia-nodo-${nodo.tipo}`);
    if (nodo.despuesDelTurno) {
        elemento.classList.add("dia-desborde");
    }
    const contenido = {
        "inicio-turno": crearMarcaEntrada,
        "fin-turno": crearMarcaFinTurno,
        "ahora": () => crearElemento("span", "dia-ahora", "Ahora"),
        "ordenar": crearBotonOrdenar,
        "intervalo": (n) => crearElemento("p", "dia-intervalo", `Disponible, ${duracionTexto(n.minutos)}`),
        "urgente": crearUrgente,
    }[nodo.tipo] || crearFila;
    elemento.append(crearHora(nodo), crearPunto(nodo), contenido(nodo));
    return elemento;
}

function pintarLineaDeTiempo() {
    const linea = document.getElementById("linea-tiempo");
    const mensaje = document.getElementById("mensaje");
    const nodos = armarDia();
    const hayActividades = nodos.some((nodo) => nodo.actividad);
    mensaje.hidden = hayActividades;
    mensaje.classList.remove("mensaje-error");
    mensaje.textContent = "No tienes actividades para hoy.";
    linea.hidden = ordenando;
    linea.replaceChildren(...nodos.map(crearNodo));
}

// ---------- Encabezado: la carga y el tiempo disponible (alcance, Sección 6.1) ----------

// La barra: el trabajo en el color principal y lo disponible en blanco con borde. Si el trabajo no
// cabe, lo que pasa se raya en rojo (sobrecarga). Lo mismo está escrito en la frase de encima.
function crearBarraCarga(trabajo, capacidad) {
    const total = Math.max(trabajo, capacidad, 1);
    const barra = crearElemento("div", "dia-barra");
    barra.setAttribute("aria-hidden", "true");
    const ocupado = crearElemento("span", "dia-barra-trabajo");
    ocupado.style.width = `${(Math.min(trabajo, capacidad) * 100) / total}%`;
    barra.append(ocupado);
    if (trabajo > capacidad) {
        const exceso = crearElemento("span", "dia-barra-exceso");
        exceso.style.width = `${((trabajo - capacidad) * 100) / total}%`;
        barra.append(exceso);
    }
    return barra;
}

function pintarEncabezado() {
    const { resumen, turno } = programacion;
    const trabajo = resumen.trabajado_min + resumen.pendiente_min;
    const capacidad = resumen.capacidad_min;
    const frase = crearElemento("p", "dia-frase");
    frase.append(crearElemento("strong", "cifra", duracionTexto(trabajo)), " de trabajo");
    if (trabajo > capacidad) {
        frase.append(", ", crearElemento("strong", "cifra", duracionTexto(trabajo - capacidad)), " más de lo que cabe en tu jornada");
    } else {
        frase.append(" y ", crearElemento("strong", "cifra", duracionTexto(capacidad - trabajo)), " disponibles");
    }
    const horario = crearElemento("p", "dia-horario cifra",
        turno ? `Turno de ${turno.hora_inicio} a ${turno.hora_fin}` : "Sin turno asignado");
    document.getElementById("dia-carga").replaceChildren(frase, crearBarraCarga(trabajo, capacidad), horario);

    // Avisos del turno y del modo de lectura, como líneas con su ícono (sin caja).
    const avisos = [];
    const aviso = avisoDelTurno(programacion);
    if (aviso) {
        const [tipo, texto] = aviso;
        avisos.push(crearConIcono("p", tipo === "info" ? "linea-info" : "linea-advertencia", tipo === "info" ? "info" : "clock", texto));
    }
    const estado = estadoDeJornada(programacion);
    if (estado !== "dia") {
        const lectura = crearConIcono("p", "linea-info", "info", estado === "inicio"
            ? "Estás viendo tu día. Para iniciar actividades, marca la entrada en Inicio."
            : "Ya marcaste la salida: tu día queda en modo de lectura.");
        const enlace = crearElemento("a", "", "Ir a Inicio");
        enlace.href = RUTA_INICIO;
        lectura.querySelector("span").append(" ", enlace);
        avisos.push(lectura);
    }
    document.getElementById("dia-avisos").replaceChildren(...avisos);
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

// Cada fila dice a qué hora quedaría la actividad con el orden que se está armando.
function crearFilaOrden(actividad, indice, total, mover, tramo) {
    const fila = crearElemento("li", "orden-fila");
    const textos = crearElemento("span", "orden-textos");
    const datos = [NOMBRE_PRIORIDAD[actividad.prioridad], duracionTexto(actividad.tiempo_estimado_min)].join(", ");
    textos.append(crearElemento("strong", "", actividad.titulo), crearElemento("span", "orden-datos cifra", datos));
    if (tramo) {
        const horario = crearElemento("span", "orden-horario cifra", `~${horaLocal(tramo.inicio)} a ${horaLocal(tramo.fin)}`);
        if (tramo.fuera_del_turno_min > 0) {
            horario.append(crearConIcono("span", "etiqueta etiqueta-fuera-turno", "clock",
                `${duracionTexto(tramo.fuera_del_turno_min)} después de tu turno`));
        }
        textos.append(horario);
    }
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
    ordenando = false;
    document.getElementById("ordenador").hidden = true;
    document.getElementById("linea-tiempo").hidden = false;
}

// Mientras se ordena, la pantalla muestra solo la lista y sus acciones (alcance, Sección 6.1). El
// servidor calcula la hora de cada actividad con el orden nuevo, sin guardarlo (vista previa).
function abrirOrdenador() {
    ordenando = true;
    const ordenador = document.getElementById("ordenador");
    let orden = actividadesQueSeOrdenan();
    let tramos = new Map();
    const lista = crearElemento("ol", "orden-lista");
    lista.setAttribute("aria-live", "polite");
    const pintar = () => lista.replaceChildren(...orden.map((actividad, indice) =>
        crearFilaOrden(actividad, indice, orden.length, mover, tramos.get(actividad.id))));

    async function calcularHoras() {
        try {
            const previa = await enviarJson("/orden-del-dia/vista-previa", "POST", { actividad_ids: orden.map((a) => a.id) });
            tramos = new Map(previa.tramos.map((tramo) => [tramo.actividad_id, tramo]));
        } catch {
            tramos = new Map();     // Sin las horas, el orden se puede seguir armando.
        }
        pintar();
    }

    function mover(indice, paso) {
        const copia = [...orden];
        [copia[indice], copia[indice + paso]] = [copia[indice + paso], copia[indice]];
        orden = copia;
        pintar();
        lista.querySelectorAll("button")[Math.max(0, (indice + paso) * 2 + (paso > 0 ? 1 : 0))]?.focus();
        calcularHoras();
    }
    tramos = new Map(programacion.tramos.map((tramo) => [tramo.actividad_id, tramo]));
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
        "Mueve las actividades de horario flexible. Cada una dice a qué hora quedaría. Las de hora fija y las urgentes no se mueven.");
    const cuerpo = crearElemento("div", "panel-cuerpo");
    cuerpo.append(nota, lista, acciones);
    ordenador.replaceChildren(encabezado, cuerpo);

    document.getElementById("linea-tiempo").hidden = true;
    ordenador.hidden = false;
    ordenador.scrollIntoView({ block: "start" });
    listo.focus();
}

function enviarCuerpo(orden) {
    return { method: "PUT", body: JSON.stringify({ actividad_ids: orden.map((actividad) => actividad.id) }) };
}

// ---------- Carga de datos ----------

// La pantalla se ubica en "Ahora" solo la primera vez que muestra el día; después el operario se
// desplaza por su cuenta.
let vistaUbicada = false;

function pintar() {
    pintarEncabezado();
    pintarLineaDeTiempo();
}

async function cargar() {
    try {
        programacion = await pedirApi("/programacion-del-dia");
        actividades = programacion.actividades;
        cargadaEn = Date.now();
        pintar();
        if (!vistaUbicada) {
            document.querySelector(".dia-nodo-ahora")?.scrollIntoView({ block: "center" });
            vistaUbicada = true;
        }
    } catch {
        const mensaje = document.getElementById("mensaje");
        mensaje.hidden = false;
        mensaje.textContent = "No pudimos cargar tus actividades. Revisa tu conexión e inténtalo de nuevo.";
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then(() => {
    const fecha = fechaLarga(new Date());
    document.getElementById("fecha-hoy").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    // El tiempo va en minutos: basta con repintar cada medio minuto (sin segundos corriendo).
    setInterval(() => programacion && !ordenando && !document.querySelector("dialog[open]") && pintar(), 30000);
    cargar();
});
