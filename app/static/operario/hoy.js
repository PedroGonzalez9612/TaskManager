// Vista "Hoy" del Operario: su fila del tablero del turno, en vertical (alcance, Secciones 6.2 y 6.5).
// Una línea de tiempo con las horas de arriba abajo, una tarjeta por actividad en su hora, la actividad en curso
// abierta en su lugar del día y la línea "Ahora", que separa lo que ya pasó de lo que falta.
// La programación la calcula el servidor (GET /programacion-del-dia): lo terminado ocupa el tiempo
// que realmente tomó y lo pendiente se reacomoda desde que el operario queda libre.
// La entrada se marca en Inicio. Sin la entrada marcada, o después de la salida, Hoy se ve en modo de
// lectura: el día completo, sin acciones para iniciar o reanudar (alcance, Sección 6.1).

const INTERVALO_MINIMO_MIN = 15;    // Un espacio libre más corto que esto no se anuncia.
// Bloques de tiempo: su alto es proporcional a la duración, con un mínimo que se puede tocar.
const PX_POR_MINUTO = 1.1;
const ALTO_MINIMO_BLOQUE = 56;
const ALTO_MAXIMO_INTERVALO = 120;
const RUTA_INICIO = "/static/operario/inicio.html";

const hoy = new Date();
hoy.setHours(0, 0, 0, 0);
const textoHoy = fechaTexto(hoy);

let actividades = [];           // Las del día, como las presenta la API (para abrir su detalle).
let programacion = null;
let temporizador = null;
let alTic = [];                 // Lo que se actualiza cada segundo: cronómetro, avance y hora actual.
let ordenando = false;          // Mientras se ordena el día no se muestra nada más (alcance, Sección 6.1).

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

function modoLectura() {
    return estadoDeJornada(programacion) !== "dia";
}

// ---------- Armar el día con la programación del servidor ----------
// Cada nodo de la línea de tiempo dice qué es ("tipo"), en qué parte del día cae ("zona": pasado,
// actual o futuro) y su hora. "aproximada" marca las horas calculadas, no fijas.

const UN_MINUTO = 60000;

function horaLocal(momento) {
    return horaDeMinutos(minutosDeFecha(new Date(momento)));
}

// La hora que se muestra junto a una actividad pendiente. Lo que caería después de la medianoche
// también dice su hora: el bloque ya avisa que pasa del turno.
function textoHoraPendiente(tramo) {
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

// El turno abre y cierra la línea de tiempo: arriba la entrada, abajo el fin del turno.
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
    if (posicion === -1) {
        return [entrada, ...nodos, fin];
    }
    // Lo que queda después del fin del turno va sobre la franja coral del desborde.
    const despues = nodos.slice(posicion).map((nodo) => ({ ...nodo, despuesDelTurno: true }));
    return [entrada, ...nodos.slice(0, posicion), fin, ...despues];
}

// "Ordenar mi día" va en la línea de tiempo, justo antes de la primera actividad por hacer
// (alcance, Sección 6.1). Solo con la entrada marcada y con al menos dos actividades que se puedan mover.
function conOrdenar(nodos) {
    if (modoLectura() || actividadesQueSeOrdenan().length < 2) {
        return nodos;
    }
    const posicion = nodos.findIndex((nodo) => nodo.tipo === "pendiente" && nodo.zona === "futuro");
    return posicion === -1 ? nodos : [...nodos.slice(0, posicion), { tipo: "ordenar", zona: "futuro" }, ...nodos.slice(posicion)];
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
        if (nodo.zona !== "pasado" && nodo.tipo !== "ordenar") {
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
    return conIntervalos(conTurno(conOrdenar(marcarAhora(nodos))));
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
    abrirDetalleOperario(actividad, actividades, cargar, { soloLectura: modoLectura() });
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

// Terminada: visto. Vencida (hora fija que pasó sin iniciarse): reloj. Lo demás: su categoría.
function iconoDelBloque(nodo) {
    if (nodo.tipo === "hecha") {
        return "check";
    }
    return nodo.atrasada ? "clock" : ICONO_CATEGORIA[nodo.actividad.categoria];
}

function minutosDelTramo(tramo) {
    return Math.max(0, Math.round((new Date(tramo.fin) - new Date(tramo.inicio)) / UN_MINUTO));
}

// Bloque de tiempo de una actividad por iniciar o finalizada (dirección visual: la jornada como
// capacidad). El color es el de su categoría; el alto, proporcional a su duración. Lo proyectado
// (hora aproximada) va rayado; lo de hora fija y lo terminado, sólido. Se toca para abrir el detalle.
function crearTarjeta(nodo) {
    const { actividad, tramo } = nodo;
    const hecha = nodo.tipo === "hecha";
    const clases = ["bloque-dia", `bloque-cat-${String(actividad.categoria).toLowerCase()}`];
    if (hecha) {
        clases.push("bloque-hecho");
    } else if (nodo.aproximada) {
        clases.push("bloque-proyectado");
    }
    if (nodo.atrasada) {
        clases.push("bloque-vencido");
    }
    const bloque = crearElemento("button", clases.join(" "));
    bloque.type = "button";
    const minutos = hecha && actividad.ejecucion ? actividad.ejecucion.tiempo_real_min : minutosDelTramo(tramo);
    bloque.style.minHeight = `${Math.max(ALTO_MINIMO_BLOQUE, Math.round(minutos * PX_POR_MINUTO))}px`;

    const cabeza = crearElemento("span", "bloque-cabeza");
    cabeza.append(
        crearConIcono("strong", "bloque-nombre", iconoDelBloque(nodo), actividad.titulo),
        crearElemento("span", "bloque-duracion cifra", duracionTexto(minutos)),
    );

    const datos = crearElemento("span", "bloque-datos");
    if (nodo.siguiente) {
        datos.append(crearConIcono("span", "etiqueta etiqueta-siguiente", "chevron-right", "Siguiente"));
    }
    if (hecha) {
        datos.append(crearElemento("span", "cifra", `Estimado ${duracionTexto(actividad.tiempo_estimado_min)}`));
    } else {
        datos.append(crearSenalPrioridad(actividad.prioridad));
    }
    if (actividad.hora_programada) {
        datos.append(crearConIcono("span", "etiqueta etiqueta-hora-fija", "lock", "Hora fija"));
    }
    if (actividad.estado === "PAUSADA") {
        datos.append(crearEtiquetaEstado("PAUSADA"));
    }
    if (actividad.reprogramada && !hecha) {
        datos.append(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", textoRetraso(actividad)));
    } else if (nodo.atrasada) {
        datos.append(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", "Hora vencida"));
    }

    bloque.append(cabeza, datos);
    bloque.setAttribute("aria-label", `${actividad.titulo}, ${duracionTexto(minutos)}. Ver detalle`);
    bloque.addEventListener("click", () => abrirDetalle(actividad));
    return bloque;
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

// Mientras trabaja, sin abrir el detalle (alcance, Sección 5.1): las precauciones en una sola línea,
// porque son de seguridad, y los pasos plegados, para que la tarjeta no ocupe toda la pantalla.
// Lo demás (herramientas, contacto, adjuntos) está en el detalle.
function crearGuiaEnCurso(actividad) {
    const informacion = actividad.informacion || { bloques: [] };
    const valoresDe = (clave) => (informacion.bloques.includes(clave) ? informacion[clave.toLowerCase()] || [] : []);
    const nodos = [];
    const precauciones = valoresDe("PRECAUCIONES");
    if (precauciones.length) {
        const texto = precauciones.map((precaucion) => precaucion.replace(/\.$/, "")).join(". ");
        nodos.push(crearConIcono("p", "tarjeta-precauciones", "triangle-alert", `${texto}.`));
    }
    const pasos = valoresDe("PASOS");
    if (pasos.length) {
        const plegable = crearElemento("details", "tarjeta-pasos");
        plegable.append(
            crearConIcono("summary", "", "list-checks", pasos.length === 1 ? "Ver el paso" : `Ver los ${pasos.length} pasos`),
            crearListaDeBloque(BLOQUES_INFORMACION[0], pasos),
        );
        nodos.push(plegable);
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

    tarjeta.append(cabecera, crearElemento("h2", "", actividad.titulo), lugar, ...crearGuiaEnCurso(actividad),
        tiempo, avance, crearEnlaceDetalle(actividad));
    if (!modoLectura()) {
        const acciones = crearElemento("div", "tarjeta-acciones");
        if (!actividad.hora_programada) {
            acciones.append(crearBotonPausar(actividad));
        }
        acciones.append(crearBotonFinalizar(actividad, "boton"));
        tarjeta.append(acciones);
    }
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
    acciones.append(crearEnlaceDetalle(actividad));
    if (!modoLectura()) {
        acciones.append(crearBotonFinalizar(actividad, "boton-texto"));
    }
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

    if (modoLectura()) {
        verDetalle.className = "boton";
        verDetalle.textContent = "Ver la urgente";
        return [verDetalle];
    }
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

function tramoEnCurso() {
    return programacion.tramos.find((tramo) => tramo.tipo === "EN_CURSO") || null;
}

// ---------- Inicio y fin del turno en la línea de tiempo ----------

function crearMarcaEntrada() {
    const marca = crearElemento("p", "linea-marca");
    const { asistencia, fecha } = programacion;
    if (asistencia && asistencia.jornada === fecha) {
        marca.append("Marcaste entrada a las ", crearElemento("strong", "cifra", horaLocal(asistencia.entrada)));
    } else {
        marca.append(programacion.turno ? "Inicio del turno. Todavía no marcas la entrada" : "Todavía no marcas la entrada");
    }
    return marca;
}

// El fin del turno suma lo que queda después de él: cuánto tendría que quedarse (alcance, Sección 5.1).
function crearMarcaFinTurno() {
    const bloque = crearElemento("div", "linea-fin-turno");
    bloque.append(crearElemento("span", "", programacion.turno ? "Fin del turno" : "Fin de la jornada"));
    const fuera = programacion.tramos.filter((tramo) => tramo.fuera_del_turno_min > 0);
    if (fuera.length) {
        const cuantas = fuera.length === 1 ? "1 actividad pasa" : `${fuera.length} actividades pasan`;
        bloque.append(crearConIcono("span", "linea-fin-turno-extra", "clock",
            `${cuantas} de tu turno: ${duracionTexto(programacion.resumen.fuera_del_turno_min)} más`));
    }
    return bloque;
}

function crearNodoOrdenar() {
    const boton = crearConIcono("button", "boton-texto linea-ordenar", "arrow-up-down", "Ordenar mi día");
    boton.type = "button";
    boton.addEventListener("click", abrirOrdenador);
    return boton;
}

// ---------- Línea de tiempo ----------

function crearNodo(nodo) {
    const elemento = crearElemento("li", `linea-nodo ${nodo.zona}`);
    if (nodo.despuesDelTurno) {
        elemento.classList.add("linea-nodo-desborde");
    }

    if (nodo.tipo === "intervalo") {
        // El tiempo libre ocupa espacio, como en la planilla: más libre, más hueco (con un tope).
        elemento.classList.add("linea-nodo-intervalo");
        elemento.style.minHeight = `${Math.min(ALTO_MAXIMO_INTERVALO, Math.round(nodo.minutos * PX_POR_MINUTO))}px`;
        elemento.append(crearElemento("p", "linea-intervalo cifra", `${duracionTexto(nodo.minutos)} disponibles`));
        return elemento;
    }
    if (nodo.tipo === "ordenar") {
        elemento.classList.add("linea-nodo-ordenar");
        elemento.append(crearElemento("span", "linea-hora"), crearNodoOrdenar());
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

    const textoAhora = modoLectura() ? "Sin actividad en curso." : "Sin actividad en curso. Selecciona una para iniciarla.";
    const contenido = {
        "inicio-turno": crearMarcaEntrada,
        "fin-turno": crearMarcaFinTurno,
        "ahora": () => crearElemento("p", "linea-ahora", textoAhora),
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

    const nodos = armarDia();
    const hayActividades = nodos.some((nodo) => nodo.actividad);
    mensaje.hidden = hayActividades;
    mensaje.classList.remove("mensaje-error");
    mensaje.textContent = "No tienes actividades para hoy.";
    linea.hidden = ordenando;
    linea.replaceChildren(...nodos.map(crearNodo));
}

// ---------- Encabezado: la hora, el turno y la jornada en barras (alcance, Sección 6.1) ----------

function pintarEncabezado() {
    const cinta = crearCintaDelDia(programacion);
    alTic.push(cinta.actualizar);
    document.getElementById("cinta-dia").replaceChildren(cinta.elemento);
    pintarAvisoDelTurno(document.getElementById("aviso-turno"), programacion);

    // Modo de lectura: sin la entrada marcada, o después de la salida.
    const aviso = document.getElementById("aviso-lectura");
    const estado = estadoDeJornada(programacion);
    aviso.hidden = estado === "dia";
    if (!aviso.hidden) {
        const texto = estado === "inicio"
            ? "Estás viendo tu día. Para iniciar actividades, marca la entrada en Inicio."
            : "Ya marcaste la salida: tu día queda en modo de lectura.";
        const enlace = crearElemento("a", "boton-texto", "Ir a Inicio");
        enlace.href = RUTA_INICIO;
        aviso.replaceChildren(crearConIcono("span", "aviso-lectura-texto", "info", texto), enlace);
    }

    // "Marcar salida" va al final del día y no se muestra mientras se ordena (alcance, Sección 6.1).
    document.getElementById("fin-del-dia").hidden = estado !== "dia" || ordenando;
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
    pintarEncabezado();
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
    document.getElementById("fin-del-dia").hidden = true;
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

async function cargar() {
    try {
        programacion = await pedirApi("/programacion-del-dia");
        actividades = programacion.actividades;
        clearInterval(temporizador);
        alTic = [];
        pintarEncabezado();
        pintarLineaDeTiempo();
        const tic = () => alTic.forEach((actualizar) => actualizar());
        tic();
        temporizador = setInterval(tic, 1000);
        if (!vistaUbicada) {
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

iniciarPaginaProtegida(["OPERARIO"]).then(() => {
    const fecha = fechaLarga(hoy);
    document.getElementById("fecha-hoy").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    const salida = document.getElementById("marcar-salida");
    salida.append(...crearConIcono("span", "", "log-out", "Marcar salida").childNodes);
    salida.addEventListener("click", () => abrirSalida(programacion, cargar));
    // Los avisos del turno dependen de la hora: se revisan cada medio minuto.
    setInterval(() => programacion && pintarAvisoDelTurno(document.getElementById("aviso-turno"), programacion), 30000);
    cargar();
});
