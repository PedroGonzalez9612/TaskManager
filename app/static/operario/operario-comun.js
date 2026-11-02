// Lo que comparten las vistas del Operario: el detalle de una actividad, que es donde la ejecuta
// (iniciar, pausar, reanudar, finalizar y devolver), y las hojas para pausar con un motivo, finalizar con
// evidencia y devolver (alcance, Secciones 5.1 y 6.1; diseño en docs/disenos/operario_v3/). En celular el
// detalle ocupa toda la pantalla, con la vuelta arriba y las acciones fijas abajo. El detalle del
// Administrador es otro (abrirDetalleActividad, en js/actividades-comun.js).

const MOTIVO_URGENTE = "Actividad urgente";
const MOTIVO_HORA_FIJA = "Actividad de hora fija";
const AVISO_HORA_FIJA_MIN = 10;     // Desde cuántos minutos antes se avisa una actividad de hora fija (alcance, 5.1).
// Una de hora fija no se pausa, salvo para detenerla por una emergencia (MOTIVOS_DETENER_HORA_FIJA en enums.py).
const MOTIVOS_DETENER_HORA_FIJA = ["Emergencia", "Falla del equipo"];

// Desde cuándo se puede iniciar una de hora fija: los mismos 10 minutos antes del aviso (alcance, 5.1).
// null si es de horario flexible o si ya se puede.
function inicioPermitidoDesde(actividad) {
    if (!actividad.hora_programada) {
        return null;
    }
    const desde = new Date(fechaDesdeTexto(actividad.fecha_programada, actividad.hora_programada).getTime()
        - AVISO_HORA_FIJA_MIN * 60000);
    return Date.now() < desde.getTime() ? desde : null;
}

// Evidencia de la ejecución (alcance, Sección 5.1).
const MAXIMO_EVIDENCIAS = 5;
const TAMANO_MAXIMO_EVIDENCIA = 5 * 1024 * 1024;
const LADO_MAXIMO_FOTO = 1600;      // Píxeles del lado mayor: la foto se lee bien y pesa unos 300 KB.
const CALIDAD_FOTO = 0.8;

function actividadEnCurso(actividades) {
    return actividades.find((actividad) => actividad.estado === "EN_EJECUCION") || null;
}

// "40" si es menos de una hora (se lee "16 min de 40 estimados"); si no, "1 h 30 min".
function estimadoCorto(minutos) {
    return minutos < 60 ? String(minutos) : duracionTexto(minutos);
}

// ---------- Las acciones según el estado (alcance, Sección 5.1) ----------

// Devuelve { acciones, aviso }. Cada acción: { texto, icono, clase, alHacer, desactivada }.
// La primera de la lista es la principal; las demás, secundarias.
function accionesDelOperario(actividad, actividades, alCambiar, soloLectura) {
    const enCurso = actividadEnCurso(actividades);
    const otraEnCurso = enCurso && enCurso.id !== actividad.id ? enCurso : null;
    const acciones = [];
    let aviso = "";
    let nota = "";          // Información que explica una acción que falta (sin color propio, 6.3).

    if (soloLectura) {
        if (["ASIGNADA", "PAUSADA"].includes(actividad.estado)) {
            aviso = "Para iniciarla o reanudarla, marca la entrada en Inicio.";
        }
        return { acciones, aviso, nota };
    }
    const esperaSuHora = actividad.estado === "ASIGNADA" ? inicioPermitidoDesde(actividad) : null;
    if (esperaSuHora) {
        // Todavía no es su hora: el botón se ve, desactivado, y la nota dice desde cuándo.
        acciones.push({ texto: "Iniciar actividad", icono: "play", desactivada: true, alHacer: () => {} });
        nota = `Es de hora fija: podrás iniciarla desde las ${horaDeMomento(esperaSuHora)}.`;
    } else if (actividad.prioridad === "URGENTE" && otraEnCurso && ["ASIGNADA", "PAUSADA"].includes(actividad.estado)) {
        // Urgente con otra en curso: una de horario flexible se pausa y la urgente empieza en el mismo
        // paso; una de hora fija no se interrumpe.
        if (otraEnCurso.hora_programada) {
            aviso = `${otraEnCurso.titulo} es de hora fija y no se interrumpe. Atiende la urgente al finalizarla.`;
        } else {
            acciones.push({ texto: "Pausar y atender", icono: "pause", alHacer: () => atenderUrgente(actividad, otraEnCurso, alCambiar) });
        }
    } else if (actividad.estado === "ASIGNADA" && actividad.hora_programada && otraEnCurso && !otraEnCurso.hora_programada) {
        // Llegó una hora fija (alcance, Sección 5.1): la que lleva se pausa con el motivo "Actividad de
        // hora fija" y la fija empieza en el mismo paso. Después se retoma la otra.
        acciones.push({
            texto: "Pausar e iniciar", icono: "pause",
            alHacer: () => pausarEIniciar(actividad, otraEnCurso, alCambiar, MOTIVO_HORA_FIJA),
        });
        nota = `${otraEnCurso.titulo} queda en pausa con el motivo "${MOTIVO_HORA_FIJA}". La retomas al terminar esta.`;
    } else if (actividad.estado === "ASIGNADA") {
        // Una sola actividad en ejecución a la vez: el botón se desactiva y se explica por qué.
        if (otraEnCurso) {
            aviso = `Ya tienes en curso ${otraEnCurso.titulo}. Páusala o finalízala antes de iniciar esta.`;
        }
        acciones.push({
            texto: "Iniciar actividad", icono: "play", desactivada: Boolean(otraEnCurso),
            alHacer: async () => {
                await pedirApi(`/actividades/${actividad.id}/iniciar`, { method: "POST" });
                await alCambiar();
                mostrarAviso(`${actividad.titulo}: en curso.`);
            },
        });
    } else if (actividad.estado === "PAUSADA") {
        if (otraEnCurso) {
            aviso = `Ya tienes en curso ${otraEnCurso.titulo}. Páusala o finalízala antes de reanudar esta.`;
        }
        acciones.push({
            texto: "Reanudar actividad", icono: "play", desactivada: Boolean(otraEnCurso),
            alHacer: async () => {
                await pedirApi(`/actividades/${actividad.id}/reanudar`, { method: "POST" });
                await alCambiar();
                mostrarAviso(`${actividad.titulo}: en curso de nuevo.`);
            },
        });
    } else if (actividad.estado === "EN_EJECUCION") {
        acciones.push({ texto: "Finalizar", icono: "check", alHacer: () => abrirFinalizar(actividad, alCambiar), abreHoja: true });
        // Una de hora fija no se pausa; solo se detiene por una emergencia, como acción de baja (alcance, 5.1).
        if (!actividad.hora_programada) {
            acciones.push({ texto: "Pausar", icono: "pause", alHacer: () => abrirPausar(actividad, alCambiar), abreHoja: true });
        } else {
            nota = "Es de hora fija: no se pausa. Al terminarla, finalízala.";
            acciones.push({ texto: "Detener por emergencia", icono: "triangle-alert", clase: "boton-terciario boton-baja",
                alHacer: () => abrirDetener(actividad, alCambiar), abreHoja: true });
        }
    }
    // Devolver: solo antes de iniciarla, con motivo. Es una acción de baja (6.2): al final, terciaria.
    if (actividad.estado === "ASIGNADA" && !actividad.ejecucion) {
        acciones.push({ texto: "Devolver actividad", icono: "undo-2", clase: "boton-terciario boton-baja",
            alHacer: () => abrirDevolver(actividad, alCambiar), abreHoja: true });
    }
    return { acciones, aviso, nota };
}

// ---------- Piezas del detalle ----------

// El estado como texto con su ícono (sin etiqueta) y, al lado, las excepciones con etiqueta (6.2).
function crearLineaDeEstado(actividad) {
    const linea = crearElemento("div", "detalle-op-estado");
    linea.append(crearEstadoComoTexto(actividad.estado, "detalle-op-estado-texto"));
    if (actividad.prioridad === "URGENTE") {
        linea.append(crearSenalPrioridad("URGENTE"));
    }
    if (actividad.hora_programada) {
        linea.append(crearConIcono("span", "etiqueta etiqueta-hora-fija", "lock", "Hora fija"));
    }
    if (actividad.reprogramada && actividad.estado !== "COMPLETADA") {
        const dias = actividad.dias_de_retraso;
        linea.append(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", dias === 1 ? "Retraso: 1 día" : `Retraso: ${dias} días`));
    }
    return linea;
}

function textoHora(actividad) {
    return actividad.hora_programada
        ? `A las ${actividad.hora_programada}, hora fija`
        : "Horario flexible: tú decides cuándo";
}

// Los datos en una lista de dos columnas: nombre y valor.
function crearDatosDeLaActividad(actividad) {
    const datos = crearElemento("dl", "lista-datos");
    const prioridad = crearConIcono("span", `fila-prioridad prioridad-texto-${actividad.prioridad.toLowerCase()}`,
        ICONO_PRIORIDAD[actividad.prioridad], NOMBRE_PRIORIDAD[actividad.prioridad]);
    const filas = [
        ["Hora", textoHora(actividad)],
        ["Estimado", duracionTexto(actividad.tiempo_estimado_min)],
        ["Prioridad", prioridad],
        ["Categoría", NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria],
        ["Ubicación", actividad.ubicacion],
        ["Proyecto", actividad.proyecto_nombre || "Actividad independiente"],
    ];
    if ((actividad.operarios || []).length > 1) {
        filas.push(["Con", actividad.operarios.map((o) => o.nombre).join(", ")]);
    }
    for (const [nombre, valor] of filas) {
        const dd = crearElemento("dd");
        dd.append(valor);
        datos.append(crearElemento("dt", "", nombre), dd);
    }
    return datos;
}

// El tiempo de la actividad en curso: minutos contra lo estimado, con barra (metáfora, 6.5).
function crearRegistrandoTiempo(actividad) {
    const seccion = crearElemento("section", "detalle-op-tiempo");
    const trabajado = actividad.ejecucion?.tiempo_real_min || 0;
    const estimado = actividad.tiempo_estimado_min;
    const restante = estimado - trabajado;
    const cifra = crearElemento("p", "detalle-op-cifra");
    cifra.append(crearElemento("strong", "cifra", duracionTexto(trabajado)), ` de ${estimadoCorto(estimado)} estimados`);
    const barra = crearElemento("div", "barra-avance");
    barra.setAttribute("role", "progressbar");
    barra.setAttribute("aria-label", "Tiempo trabajado contra lo estimado");
    barra.setAttribute("aria-valuemin", "0");
    barra.setAttribute("aria-valuemax", String(estimado));
    barra.setAttribute("aria-valuenow", String(Math.min(trabajado, estimado)));
    const relleno = crearElemento("span", "barra-avance-relleno");
    relleno.style.width = `${Math.min(100, (trabajado * 100) / estimado)}%`;
    barra.append(relleno);
    const resto = restante > 0 ? `Quedan unos ${duracionTexto(restante)}.` : `Pasó ${duracionTexto(-restante)} del estimado.`;
    seccion.append(
        crearConIcono("p", "detalle-op-registrando", "circle", "Registrando tiempo"),
        cifra, barra,
        crearElemento("p", "texto-secundario", `Desde las ${horaCorta(actividad.ejecucion.fecha_inicio)}. ${resto}`),
    );
    return seccion;
}

// El registro de ejecución: iniciada, cada pausa con su motivo, reanudada y finalizada (alcance, 14).
function crearRegistro(ejecucion) {
    if (!ejecucion) {
        return [];
    }
    const lista = crearElemento("ol", "detalle-op-registro");
    const evento = (hora, clase, texto, motivo) => {
        const fila = crearElemento("li", clase);
        const textos = crearElemento("span", "detalle-op-registro-texto");
        textos.append(crearElemento("strong", "", texto));
        if (motivo) {
            textos.append(crearElemento("span", "texto-secundario", `Motivo: ${motivo}`));
        }
        fila.append(crearElemento("span", "cifra", hora), crearElemento("span", "detalle-op-registro-punto"), textos);
        lista.append(fila);
    };
    evento(horaCorta(ejecucion.fecha_inicio), "registro-inicio", "Iniciada");
    for (const pausa of ejecucion.pausas || []) {
        const minutos = minutosEntre(pausa.inicio, pausa.fin || Date.now());
        evento(horaCorta(pausa.inicio), "registro-pausa", pausa.fin ? `Pausa de ${duracionTexto(minutos)}` : "En pausa", pausa.motivo);
        if (pausa.fin) {
            evento(horaCorta(pausa.fin), "registro-inicio", "Reanudada");
        }
    }
    if (ejecucion.fecha_fin) {
        evento(horaCorta(ejecucion.fecha_fin), "registro-fin", `Finalizada. Trabajaste ${duracionTexto(ejecucion.tiempo_real_min)}`);
    }
    const nodos = [crearElemento("h3", "detalle-op-subtitulo", "Registro"), lista];
    if (ejecucion.observacion) {
        nodos.push(crearElemento("h3", "detalle-op-subtitulo", "Tu observación"), crearElemento("p", "", ejecucion.observacion));
    }
    nodos.push(...crearEvidencias(ejecucion));
    return nodos;
}

// La precaución: siempre el mismo componente, fondo ámbar suave con su ícono, sin franja (6.3).
function crearPrecaucion(precauciones) {
    const texto = precauciones.map((p) => p.replace(/\.$/, "")).join(". ");
    const caja = crearElemento("div", "detalle-op-precaucion");
    caja.setAttribute("role", "note");
    caja.insertAdjacentHTML("beforeend", icono("triangle-alert"));
    const parrafo = crearElemento("p");
    parrafo.append(crearElemento("strong", "", "Precaución."), ` ${texto}.`);
    caja.append(parrafo);
    return caja;
}

// "Llamar" solo si el contacto trae un número de teléfono (siete cifras o más).
function crearContacto(contactos) {
    const lista = crearElemento("ul", "detalle-op-contactos");
    for (const contacto of contactos) {
        const fila = crearElemento("li");
        fila.append(crearElemento("span", "", contacto));
        const numero = (contacto.match(/\+?\d[\d\s-]{6,}\d/) || [])[0];
        if (numero) {
            const llamar = crearConIcono("a", "boton-secundario", "phone", "Llamar");
            llamar.href = `tel:${numero.replace(/[\s-]/g, "")}`;
            fila.append(llamar);
        }
        lista.append(fila);
    }
    return lista;
}

// La información para hacer el trabajo, por bloques (alcance, Sección 5.1).
function crearInformacionOperario(actividad, { conPrecaucionArriba = false } = {}) {
    const informacion = actividad.informacion || { bloques: [] };
    const valores = (clave) => (informacion.bloques.includes(clave) ? informacion[clave.toLowerCase()] || [] : []);
    const seccion = (titulo, ...contenido) => {
        const bloque = crearElemento("section", "detalle-op-bloque");
        bloque.append(crearElemento("h3", "detalle-op-subtitulo", titulo), ...contenido);
        return bloque;
    };
    const nodos = [];
    const precauciones = valores("PRECAUCIONES");
    if (precauciones.length && conPrecaucionArriba) {
        nodos.push(crearPrecaucion(precauciones));
    }
    if (valores("PASOS").length) {
        nodos.push(seccion("Pasos", crearListaDeBloque(BLOQUES_INFORMACION[0], valores("PASOS"))));
    }
    if (valores("HERRAMIENTAS").length) {
        nodos.push(seccion("Herramientas y materiales", crearListaDeBloque(BLOQUES_INFORMACION[1], valores("HERRAMIENTAS"))));
    }
    if (valores("EQUIPO").length) {
        nodos.push(seccion("Equipo", crearListaDeBloque(BLOQUES_INFORMACION[2], valores("EQUIPO"))));
    }
    if (precauciones.length && !conPrecaucionArriba) {
        nodos.push(crearPrecaucion(precauciones));
    }
    if (valores("CONTACTO").length) {
        nodos.push(seccion("Contacto", crearContacto(valores("CONTACTO"))));
    }
    if (informacion.bloques.includes("ADJUNTOS") && (informacion.adjuntos || []).length) {
        nodos.push(seccion("Adjuntos", ...crearArchivos(informacion.adjuntos, `/actividades/${actividad.id}/adjuntos`)));
    }
    return nodos;
}

// "Lista para iniciar" es un aviso en una línea con su ícono; no impide iniciar (alcance, Sección 5.1).
function crearListaParaIniciar(actividad) {
    if (!(actividad.informacion?.bloques || []).length) {
        return null;
    }
    return actividad.lista_para_iniciar
        ? crearConIcono("p", "linea-exito", "check", "Lista para iniciar")
        : crearConIcono("p", "linea-advertencia", "circle-alert", textoFaltaInformacion(actividad));
}

// ---------- El detalle ----------

// "actividades" es la lista completa del operario (para saber si ya tiene otra en curso) y
// "alCambiar" recarga la vista después de una acción. Con "soloLectura" (sin la entrada marcada o
// después de la salida) se ve la información, sin acciones. "volverA" es el nombre de la pantalla de
// la que vino ("Hoy", "Inicio" o "Semana").
function abrirDetalleOperario(actividad, actividades, alCambiar, { soloLectura = false, volverA = "Hoy" } = {}) {
    const dialogo = crearElemento("dialog", "dialogo detalle-op");
    dialogo.setAttribute("aria-labelledby", "detalle-op-titulo");

    const barra = crearElemento("div", "detalle-op-barra");
    const volver = crearConIcono("button", "detalle-op-volver", "chevron-left", volverA);
    volver.type = "button";
    volver.setAttribute("aria-label", `Volver a ${volverA}`);
    volver.addEventListener("click", () => dialogo.close());
    barra.append(volver, crearElemento("span", "codigo cifra texto-secundario", actividad.codigo));

    const cuerpo = crearElemento("div", "detalle-op-cuerpo");
    const titulo = crearElemento("h2", "detalle-op-titulo", actividad.titulo);
    titulo.id = "detalle-op-titulo";
    cuerpo.append(crearLineaDeEstado(actividad), titulo);

    const enCurso = actividad.estado === "EN_EJECUCION";
    if (enCurso) {
        cuerpo.append(crearElemento("p", "texto-secundario",
            `${NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria}, en ${actividad.ubicacion}`));
        cuerpo.append(crearRegistrandoTiempo(actividad), ...crearRegistro(actividad.ejecucion),
            ...crearInformacionOperario(actividad, { conPrecaucionArriba: true }));
    } else {
        if (actividad.descripcion) {
            cuerpo.append(crearElemento("p", "detalle-op-descripcion", actividad.descripcion));
        }
        cuerpo.append(crearDatosDeLaActividad(actividad));
        const lista = actividad.estado === "ASIGNADA" ? crearListaParaIniciar(actividad) : null;
        if (lista) {
            cuerpo.append(lista);
        }
        cuerpo.append(...crearRegistro(actividad.ejecucion), ...crearInformacionOperario(actividad));
    }

    const { acciones, aviso, nota } = accionesDelOperario(actividad, actividades, alCambiar, soloLectura);
    // El aviso (por qué no se puede iniciar), la nota y el error van junto a las acciones, donde se miran.
    const avisoLinea = aviso ? crearConIcono("p", "linea-advertencia", "circle-alert", aviso)
        : nota ? crearConIcono("p", "linea-info", "info", nota) : null;
    const error = crearElemento("p", "mensaje-formulario");
    error.setAttribute("role", "alert");
    error.hidden = true;

    dialogo.append(barra, cuerpo);
    if (acciones.length) {
        const pie = crearPieDeAcciones(acciones, dialogo, error);
        pie.prepend(...[avisoLinea, error].filter(Boolean));
        dialogo.append(pie);
    } else {
        cuerpo.append(...[avisoLinea, error].filter(Boolean));
    }
    dialogo.addEventListener("close", () => dialogo.remove());
    document.body.append(dialogo);
    dialogo.showModal();
    volver.focus();
    return dialogo;
}

// Las acciones, fijas abajo (al alcance del pulgar). Una sola principal; Pausar y Finalizar van lado a
// lado, como en el diseño; Devolver es terciario, debajo.
function crearPieDeAcciones(acciones, dialogo, error) {
    const pie = crearElemento("div", "detalle-op-acciones");
    const fila = crearElemento("div", "detalle-op-acciones-fila");
    acciones.forEach((accion, indice) => {
        const clase = accion.clase || (indice === 0 ? "boton" : "boton-secundario");
        const boton = crearConIcono("button", clase, accion.icono, accion.texto);
        boton.type = "button";
        boton.disabled = Boolean(accion.desactivada);
        boton.addEventListener("click", async () => {
            if (accion.abreHoja) {
                // Abre su hoja encima; el detalle se cierra cuando la acción termina.
                accion.alHacer().then((hecho) => hecho && dialogo.close());
                return;
            }
            boton.disabled = true;
            try {
                await accion.alHacer();
                dialogo.close();
            } catch (error_) {
                mostrarErrorFormulario(error, error_.message);
                boton.disabled = false;
            }
        });
        if (clase.includes("boton-terciario")) {
            pie.append(boton);
        } else {
            fila.prepend(boton);    // La principal queda a la derecha, al final de la lectura.
        }
    });
    if (fila.childElementCount) {
        pie.prepend(fila);
    }
    return pie;
}

// Pausa lo que está en curso con el motivo "Actividad urgente" e inicia (o reanuda) la urgente.
// Son dos pasos en el servidor: si el segundo falla, lo primero ya quedó en pausa y se recarga.
async function atenderUrgente(urgente, enCurso, alCambiar) {
    return pausarEIniciar(urgente, enCurso, alCambiar, MOTIVO_URGENTE);
}

// Pausa lo que está en curso con su motivo e inicia (o reanuda) la otra: la urgente o la de hora fija.
// Son dos pasos en el servidor: si el segundo falla, lo primero ya quedó en pausa y se recarga.
async function pausarEIniciar(nueva, enCurso, alCambiar, motivo) {
    try {
        await enviarJson(`/actividades/${enCurso.id}/pausar`, "POST", { motivo });
        const accion = nueva.estado === "PAUSADA" ? "reanudar" : "iniciar";
        await pedirApi(`/actividades/${nueva.id}/${accion}`, { method: "POST" });
    } catch (error) {
        alCambiar();
        throw error;
    }
    await alCambiar();
    mostrarAviso(`${enCurso.titulo} quedó en pausa. ${nueva.titulo}: en curso.`);
}

// ---------- Hojas inferiores: pausar, devolver y finalizar ----------

// Un diálogo que en celular sube desde abajo (hoja inferior, alcance 14). La acción principal va
// arriba y "Cancelar" debajo (6.2). Devuelve una promesa: true si se confirmó y salió bien.
// Con "deBaja" (devolver), el botón que confirma lleva borde y texto rojos: una acción de baja nunca es
// la principal (alcance, Sección 6.2).
function abrirHoja({ titulo, subtitulo = "", contenido = [], textoConfirmar, alConfirmar, deBaja = false }) {
    return new Promise((resolver) => {
        const hoja = crearElemento("dialog", "dialogo hoja");
        hoja.setAttribute("aria-label", titulo);
        const formulario = crearElemento("form", "hoja-formulario");
        formulario.noValidate = true;
        const asa = crearElemento("span", "hoja-asa");
        asa.setAttribute("aria-hidden", "true");
        const error = crearElemento("p", "mensaje-formulario");
        error.setAttribute("role", "alert");
        error.hidden = true;
        const confirmar = crearElemento("button",
            deBaja ? "boton-secundario boton-baja boton-principal-grande" : "boton boton-principal-grande", textoConfirmar);
        confirmar.type = "submit";
        const cancelar = crearElemento("button", "boton-secundario boton-principal-grande", "Cancelar");
        cancelar.type = "button";
        cancelar.addEventListener("click", () => hoja.close());
        const acciones = crearElemento("div", "hoja-acciones");
        acciones.append(confirmar, cancelar);
        formulario.append(asa, crearElemento("h2", "", titulo));
        if (subtitulo) {
            formulario.append(crearElemento("p", "texto-secundario hoja-subtitulo", subtitulo));
        }
        formulario.append(...contenido, error, acciones);

        let hecho = false;
        formulario.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            confirmar.disabled = true;
            try {
                await alConfirmar();
                hecho = true;
                hoja.close();
            } catch (error_) {
                mostrarErrorFormulario(error, error_.message);
                confirmar.disabled = false;
            }
        });
        hoja.append(formulario);
        hoja.addEventListener("close", () => {
            hoja.remove();
            resolver(hecho);
        });
        document.body.append(hoja);
        hoja.showModal();
        formulario.querySelector("input")?.focus();
    });
}

// Los motivos como opciones de radio de 52 px; con "Otro" se escribe cuál (alcance, Sección 5.1).
function crearOpcionesDeMotivo(motivos, nombre) {
    const grupo = crearElemento("fieldset", "hoja-opciones");
    grupo.append(crearElemento("legend", "solo-lectores", "Motivo"));
    const otroTexto = crearElemento("input", "hoja-otro");
    otroTexto.type = "text";
    otroTexto.maxLength = 120;
    otroTexto.placeholder = "Escribe el motivo";
    otroTexto.setAttribute("aria-label", "¿Cuál es el motivo?");
    otroTexto.hidden = true;
    motivos.forEach((motivo) => {
        const etiqueta = crearElemento("label", "hoja-opcion");
        const radio = crearElemento("input");
        radio.type = "radio";
        radio.name = nombre;
        radio.value = motivo;
        radio.addEventListener("change", () => {
            otroTexto.hidden = motivo !== OPCION_OTRO;
            if (!otroTexto.hidden) {
                otroTexto.focus();
            }
        });
        etiqueta.append(radio, crearElemento("span", "", motivo === OPCION_OTRO ? "Otro motivo" : motivo));
        grupo.append(etiqueta);
    });
    grupo.append(otroTexto);
    const leer = () => {
        const elegido = grupo.querySelector("input[type=radio]:checked");
        if (!elegido) {
            throw new Error("Elige el motivo.");
        }
        return { motivo: elegido.value, detalle: otroTexto.value };
    };
    return { grupo, leer };
}

async function abrirConMotivos(ruta, nombre, armar) {
    let motivos;
    try {
        motivos = await pedirApi(ruta);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        return false;
    }
    return armar(crearOpcionesDeMotivo(motivos, nombre));
}

// Pausar: los motivos de la empresa; lo escrito en "Otro" queda en la lista (alcance, Sección 5.1).
function abrirPausar(actividad, alCambiar) {
    return abrirConMotivos("/catalogos/motivos-pausa", "motivo-pausa", ({ grupo, leer }) => abrirHoja({
        titulo: "Pausar actividad",
        subtitulo: `¿Por qué pausas ${actividad.titulo}? Queda en el registro.`,
        contenido: [grupo],
        textoConfirmar: "Pausar actividad",
        alConfirmar: async () => {
            await enviarJson(`/actividades/${actividad.id}/pausar`, "POST", leer());
            await alCambiar();
            mostrarAviso(`${actividad.titulo} quedó en pausa. La retomas con "Reanudar actividad".`);
        },
    }));
}

// Detener una de hora fija: solo por una emergencia, con uno de dos motivos y sin "Otro". Queda
// pausada, el Administrador la ve en "Por atender" y se puede reanudar (alcance, Sección 5.1).
function abrirDetener(actividad, alCambiar) {
    const { grupo, leer } = crearOpcionesDeMotivo(MOTIVOS_DETENER_HORA_FIJA, "motivo-detener");
    return abrirHoja({
        titulo: "Detener por emergencia",
        subtitulo: `${actividad.titulo} es de hora fija: solo se detiene si pasa algo grave. Tu Administrador lo verá.`,
        contenido: [grupo],
        textoConfirmar: "Detener actividad",
        deBaja: true,
        alConfirmar: async () => {
            await enviarJson(`/actividades/${actividad.id}/pausar`, "POST", leer());
            await alCambiar();
            mostrarAviso(`${actividad.titulo} quedó detenida. Avisamos a tu Administrador.`);
        },
    });
}

// Devolver: antes de iniciarla, con su motivo. Vuelve al Administrador (alcance, Sección 5.1).
function abrirDevolver(actividad, alCambiar) {
    return abrirConMotivos("/catalogos/motivos-devolucion", "motivo-devolucion", ({ grupo, leer }) => abrirHoja({
        titulo: "Devolver actividad",
        subtitulo: `${actividad.titulo} sale de tu día y vuelve a quien la asignó, con el motivo que elijas.`,
        contenido: [grupo],
        textoConfirmar: "Devolver actividad",
        deBaja: true,
        alConfirmar: async () => {
            await enviarJson(`/actividades/${actividad.id}/devolver`, "POST", leer());
            await alCambiar();
            mostrarAviso(`Devolviste ${actividad.titulo}.`);
        },
    }));
}

// Reduce una foto en el celular antes de subirla, para no gastar datos. Devuelve un JPG.
async function reducirFoto(archivo) {
    let imagen;
    try {
        imagen = await createImageBitmap(archivo);
    } catch (error) {
        throw new Error(`No se pudo leer la foto "${archivo.name}". Usa una foto JPG o PNG.`);
    }
    const escala = Math.min(1, LADO_MAXIMO_FOTO / Math.max(imagen.width, imagen.height));
    const lienzo = document.createElement("canvas");
    lienzo.width = Math.round(imagen.width * escala);
    lienzo.height = Math.round(imagen.height * escala);
    lienzo.getContext("2d").drawImage(imagen, 0, 0, lienzo.width, lienzo.height);
    const reducida = await new Promise((resolver) => lienzo.toBlob(resolver, "image/jpeg", CALIDAD_FOTO));
    return { contenido: reducida, nombre: archivo.name.replace(/\.[^.]+$/, "") + ".jpg" };
}

async function subirEvidencia(actividad, archivo) {
    const { contenido, nombre } = archivo.type.startsWith("image/")
        ? await reducirFoto(archivo)
        : { contenido: archivo, nombre: archivo.name };
    if (contenido.size > TAMANO_MAXIMO_EVIDENCIA) {
        throw new Error(`"${archivo.name}" pesa más de 5 MB.`);
    }
    const datos = new FormData();
    datos.append("archivo", contenido, nombre);
    await pedirApi(`/actividades/${actividad.id}/evidencias`, { method: "POST", body: datos });
}

// Finalizar: cuánto trabajó, una observación y la evidencia opcional (alcance, Sección 5.1).
// Primero se suben los archivos y después se finaliza: la evidencia se agrega con la actividad en curso.
function abrirFinalizar(actividad, alCambiar) {
    const pausas = actividad.ejecucion?.pausas?.length || 0;
    const resumen = crearElemento("dl", "hoja-resumen");
    for (const [valor, nombre] of [
        [duracionTexto(actividad.ejecucion?.tiempo_real_min || 0), "trabajados"],
        [duracionTexto(actividad.tiempo_estimado_min), "estimados"],
        [String(pausas), pausas === 1 ? "pausa" : "pausas"],
    ]) {
        const grupo = crearElemento("div");
        grupo.append(crearElemento("dd", "cifra", valor), crearElemento("dt", "", nombre));
        resumen.append(grupo);
    }

    const etiqueta = crearElemento("label", "hoja-etiqueta");
    etiqueta.htmlFor = "finalizar-observacion";
    etiqueta.append(crearElemento("strong", "", "Observación"), crearElemento("span", "texto-secundario", " (opcional)"));
    const observacion = crearElemento("textarea");
    observacion.id = "finalizar-observacion";
    observacion.rows = 3;
    observacion.maxLength = 500;
    observacion.placeholder = "Qué hiciste, qué encontraste o qué quedó pendiente";

    const entrada = crearElemento("input", "solo-lectores");
    entrada.id = "finalizar-archivos";
    entrada.type = "file";
    entrada.accept = "image/*,application/pdf";
    entrada.multiple = true;
    const agregar = crearConIcono("label", "hoja-agregar", "camera", "Agregar fotos o archivos");
    agregar.htmlFor = entrada.id;
    const elegidos = crearElemento("ul", "evidencia-elegida");
    elegidos.setAttribute("aria-live", "polite");
    entrada.addEventListener("change", () => elegidos.replaceChildren(...[...entrada.files].map((archivo) =>
        crearConIcono("li", "", archivo.type.startsWith("image/") ? "camera" : "paperclip", archivo.name))));

    return abrirHoja({
        titulo: "Finalizar actividad",
        subtitulo: actividad.titulo,
        contenido: [resumen, etiqueta, observacion, entrada, agregar, elegidos,
            crearElemento("p", "texto-secundario", `Hasta ${MAXIMO_EVIDENCIAS} archivos de 5 MB cada uno.`)],
        textoConfirmar: "Finalizar actividad",
        alConfirmar: async () => {
            const lista = [...entrada.files];
            if (lista.length > MAXIMO_EVIDENCIAS) {
                throw new Error(`Elige como máximo ${MAXIMO_EVIDENCIAS} archivos.`);
            }
            for (const archivo of lista) {
                await subirEvidencia(actividad, archivo);
            }
            await enviarJson(`/actividades/${actividad.id}/finalizar`, "POST", { observacion: observacion.value });
            await alCambiar();
            mostrarAviso(lista.length ? `${actividad.titulo}: finalizada, con ${lista.length} de evidencia.` : `${actividad.titulo}: finalizada.`);
        },
    });
}

// ---------- La fila de una actividad: la comparten Hoy y Semana (alcance, Sección 6.2) ----------
// "nodo" trae la actividad, su tramo y cómo se ve: tipo ("hecha", "en-curso" o "pendiente"), vencida,
// siguiente y, en Semana, urgenteComoEtiqueta (en Hoy la urgente es un bloque rojo aparte).

// Las excepciones llevan etiqueta (Urgente, Hora fija, Retraso u Hora vencida); "Siguiente" es texto (6.2).
function crearExcepciones(nodo) {
    const { actividad } = nodo;
    const excepciones = [];
    if (nodo.urgenteComoEtiqueta && actividad.prioridad === "URGENTE" && nodo.tipo !== "hecha") {
        excepciones.push(crearSenalPrioridad("URGENTE"));
    }
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
// "cargadaEn" es cuándo llegó la programación: el tiempo en curso se adelanta desde ahí.
function crearDatosDeFila(nodo, cargadaEn) {
    const { actividad, tramo } = nodo;
    const datos = crearElemento("span", "fila-datos");
    const categoria = NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria;
    if (nodo.tipo === "en-curso") {
        const minutos = (actividad.ejecucion?.tiempo_real_min || 0) + Math.floor((Date.now() - cargadaEn) / 60000);
        datos.classList.add("fila-datos-en-curso");
        // Partida por una hora fija (alcance, Sección 6.2): las dos filas se leen como una sola actividad.
        const parte = tramo?.parte ? "Parte 1, en curso" : "En curso";
        datos.textContent = `${parte}, ${duracionTexto(minutos)} de ${estimadoCorto(actividad.tiempo_estimado_min)}`;
        return datos;
    }
    if (tramo?.parte === 2) {
        const falta = Math.round((new Date(tramo.fin) - new Date(tramo.inicio)) / 60000);
        datos.textContent = `Parte 2: lo que falta, ${duracionTexto(falta)}`;
        return datos;
    }
    if (nodo.tipo === "hecha") {
        const real = actividad.ejecucion?.tiempo_real_min;
        datos.append(...crearConIcono("span", "fila-estado estado-finalizada", "check",
            real ? `Finalizada, tomó ${duracionTexto(real)}` : "Finalizada").childNodes);
        return datos;
    }
    if (actividad.estado === "PAUSADA") {
        const faltan = Math.round((new Date(tramo.fin) - new Date(tramo.inicio)) / 60000);
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

// La fila completa: toda ella abre el detalle. Su nombre accesible es su texto visible (etiquetas,
// nombre y datos); "data-foco" permite devolverle el foco si la pantalla se repinta.
function crearFilaDeActividad(nodo, cargadaEn, alAbrir) {
    const { actividad } = nodo;
    const fila = crearElemento("button", `fila fila-${nodo.tipo}`);
    fila.type = "button";
    fila.dataset.foco = `fila-${actividad.id}${nodo.tramo?.parte ? `-${nodo.tramo.parte}` : ""}`;
    const textos = crearElemento("span", "fila-textos");
    const excepciones = crearExcepciones(nodo);
    if (excepciones) {
        textos.append(excepciones);
    }
    textos.append(crearElemento("strong", "fila-nombre", actividad.titulo), crearDatosDeFila(nodo, cargadaEn));
    fila.append(textos);
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.addEventListener("click", () => alAbrir(actividad));
    return fila;
}

// ---------- La jornada: lo que comparten Inicio y Hoy (alcance, Secciones 5.1 y 6.1) ----------

const MOTIVO_FIN_JORNADA = "Fin de jornada";
const AVISO_TURNO_MIN = 15;     // Desde cuántos minutos antes se avisa el inicio y el fin del turno.
const MINUTO_MS = 60000;

// "inicio" antes de marcar la entrada, "dia" con la entrada marcada y "cierre" después de la salida.
// Una asistencia de otra jornada que quedó sin salida no cuenta: hoy se marca una entrada nueva.
function estadoDeJornada(programacion) {
    const { asistencia, fecha } = programacion;
    if (!asistencia || asistencia.jornada !== fecha) {
        return "inicio";
    }
    return asistencia.salida ? "cierre" : "dia";
}

function horaDeMomento(momento) {
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

function minutosHasta(momento) {
    return Math.ceil((new Date(momento).getTime() - Date.now()) / MINUTO_MS);
}

// Avisos del turno: la llegada tarde (alcance, Sección 5.1) y los 15 minutos antes del inicio y del
// fin. Devuelve [tipo, texto] o null.
function avisoDelTurno(programacion) {
    const { turno } = programacion;
    const estado = estadoDeJornada(programacion);
    if (!turno || estado === "cierre") {
        return null;
    }
    if (estado === "inicio" && programacion.retraso_entrada_min > 0) {
        return ["advertencia", `Tu turno empezó hace ${duracionTexto(programacion.retraso_entrada_min)} y no has marcado la entrada.`];
    }
    const faltan = minutosHasta(estado === "inicio" ? turno.inicio : turno.fin);
    if (faltan > 0 && faltan <= AVISO_TURNO_MIN) {
        return ["info", `${estado === "inicio" ? "Tu turno inicia en" : "Tu turno termina en"} ${duracionTexto(faltan)}.`];
    }
    return null;
}

// ---------- Aviso de hora fija (alcance, Sección 5.1) ----------
// Desde 10 minutos antes de una actividad de hora fija, y mientras no se haya iniciado en su tiempo,
// Inicio y Hoy lo avisan con una línea y la acción de abrirla. Solo con la entrada marcada.

function horaFijaProxima(programacion) {
    if (estadoDeJornada(programacion) !== "dia") {
        return null;
    }
    const tramo = programacion.tramos.find((t) => t.tipo === "PENDIENTE" && t.hora_fija
        && minutosHasta(t.inicio) <= AVISO_HORA_FIJA_MIN && minutosHasta(t.fin) > 0);
    const actividad = tramo && programacion.actividades.find((a) => a.id === tramo.actividad_id);
    return actividad ? { tramo, actividad, minutos: minutosHasta(tramo.inicio) } : null;
}

function crearAvisoHoraFija(programacion, alAbrir) {
    const proxima = horaFijaProxima(programacion);
    if (!proxima) {
        return null;
    }
    const { tramo, actividad, minutos } = proxima;
    const hayEnCurso = programacion.tramos.some((t) => t.tipo === "EN_CURSO");
    let texto = minutos > 0
        ? `En ${duracionTexto(minutos)}, a las ${horaDeMomento(tramo.inicio)}, empieza ${actividad.titulo}. Es de hora fija.`
        : `Ya es la hora de ${actividad.titulo}, que es de hora fija.`;
    if (hayEnCurso) {
        texto += minutos > 0 ? " A esa hora pausa la que llevas." : " Pausa la que llevas e iníciala.";
    }
    const aviso = crearElemento("div", "aviso-hora-fija");
    const abrir = crearElemento("button", "boton-texto", "Abrir");
    abrir.type = "button";
    abrir.dataset.foco = `hora-fija-${actividad.id}`;
    abrir.setAttribute("aria-label", `Abrir ${actividad.titulo}`);
    abrir.addEventListener("click", () => alAbrir(actividad));
    aviso.append(crearConIcono("p", "linea-advertencia", "lock", texto), abrir);
    return aviso;
}

async function marcarAsistencia(boton, ruta, texto, alCambiar) {
    boton.disabled = true;
    try {
        await pedirApi(ruta, { method: "POST" });
        mostrarAviso(texto);
        await alCambiar();
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
    }
}

// Marcar salida (alcance, Sección 5.1): con una actividad en curso no se marca la salida; la de horario
// flexible se pausa con el motivo "Fin de jornada" y la de hora fija, que no se pausa, se finaliza.
// Todo en el mismo paso.
function abrirSalida(programacion, alCambiar) {
    const tramo = programacion.tramos.find((t) => t.tipo === "EN_CURSO");
    const enCurso = tramo ? programacion.actividades.find((a) => a.id === tramo.actividad_id) : null;
    const esFija = Boolean(enCurso?.hora_programada);

    const campos = [];
    if (enCurso) {
        campos.push(crearConIcono("p", "aviso aviso-advertencia aviso-bloque", "circle-alert", esFija
            ? `Tienes ${enCurso.codigo} en curso. Es de hora fija y no se pausa: se finaliza antes de marcar la salida.`
            : `Tienes ${enCurso.codigo} en curso. Se pausa con el motivo "${MOTIVO_FIN_JORNADA}" y la retomas en tu siguiente jornada.`));
    }
    // Salida anticipada (alcance, Sección 5.1): se permite, y se avisa antes de confirmar.
    const faltanDelTurno = programacion.turno ? minutosHasta(programacion.turno.fin) : 0;
    if (faltanDelTurno > 0) {
        campos.push(crearConIcono("p", "linea-info", "clock",
            `Tu turno termina a las ${horaDeMomento(programacion.turno.fin)}. Si sales ahora, quedará como salida anticipada (${duracionTexto(faltanDelTurno)} antes).`));
    }
    campos.push(crearElemento("p", "texto-secundario",
        "Después de marcar la salida no podrás iniciar ni reanudar actividades en esta jornada."));

    let textoConfirmar = "Marcar salida";
    if (enCurso) {
        textoConfirmar = esFija ? "Finalizar y marcar salida" : "Pausar y marcar salida";
    }
    abrirDialogoAccion({
        titulo: "Marcar salida",
        campos,
        textoConfirmar,
        iconoConfirmar: "log-out",
        alConfirmar: async () => {
            try {
                if (enCurso && esFija) {
                    await pedirApi(`/actividades/${enCurso.id}/finalizar`, { method: "POST" });
                } else if (enCurso) {
                    await enviarJson(`/actividades/${enCurso.id}/pausar`, "POST", { motivo: MOTIVO_FIN_JORNADA });
                }
                await pedirApi("/asistencia/salida", { method: "POST" });
            } catch (error) {
                alCambiar();    // Si alcanzó a pausar o finalizar, la pantalla debe mostrarlo.
                throw error;
            }
            await alCambiar();
            mostrarAviso("Salida registrada.");
        },
    });
}
