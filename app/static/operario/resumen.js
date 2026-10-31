// Vista "Resumen" del Operario (alcance, Secciones 5.2 y 6.1): cómo le fue en la semana. Los
// indicadores van como frases, sin una tarjeta por número y sin rankings (6.2). Debajo, su asistencia
// día por día, lo real frente a lo estimado de cada actividad finalizada, sus pausas por motivo y lo
// que viene. Los datos son de GET /analisis/indicadores, que a un Operario solo le da los suyos.

let lunes = inicioDeSemana(new Date());
// Pasarse del estimado hasta un 10 % es normal: solo se marca en ámbar lo que se pasa más.
const MARGEN_ESTIMADO = 0.1;

// ---------- Utilidades ----------

function hora(momento) {
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

// "lunes 19"
function diaCorto(textoFecha) {
    const fecha = fechaDesdeTexto(textoFecha);
    return `${fecha.toLocaleDateString("es-CO", { weekday: "long" })} ${fecha.getDate()}`;
}

// Una frase con partes resaltadas: lo que va entre corchetes se escribe en semibold.
function frase(...partes) {
    const parrafo = crearElemento("p");
    for (const parte of partes) {
        parrafo.append(Array.isArray(parte) ? crearElemento("strong", "cifra", parte[0]) : parte);
    }
    return parrafo;
}

function seccion(id, titulo, ...contenido) {
    const elemento = document.getElementById(id);
    const encabezado = crearElemento("h2", "", titulo);
    encabezado.id = `titulo-${id.replace("resumen-", "")}`;
    elemento.replaceChildren(encabezado, ...contenido);
    elemento.hidden = false;
}

function actividadesTexto(cantidad) {
    return cantidad === 1 ? "1 actividad" : `${cantidad} actividades`;
}

// ---------- Cómo te fue: frases (alcance, Sección 6.2) ----------

function pintarFrases(yo) {
    const { jornada, actividades } = yo;
    const evaluadas = actividades.cumplidas + actividades.incumplidas + actividades.con_retraso;
    const frases = [];

    if (jornada.jornadas) {
        frases.push(frase("Pasaste el ", [`${jornada.cumplimiento_jornada} %`], " de tu tiempo programado en actividades: ",
            [duracionTexto(jornada.actividades_min)], ` de ${duracionTexto(jornada.programado_min)}.`));
    } else {
        frases.push(frase("Todavía no hay jornadas terminadas en esta semana."));
    }
    if (evaluadas) {
        const partes = ["Finalizaste a tiempo ", [`${actividades.cumplidas} de ${evaluadas}`], " actividades"];
        if (actividades.con_retraso) {
            partes.push(`; ${actividadesTexto(actividades.con_retraso)} se ${actividades.con_retraso === 1 ? "pasó" : "pasaron"} de su día`);
        }
        if (actividades.incumplidas) {
            partes.push(`; ${actividades.incumplidas === 1 ? "1 no se hizo" : `${actividades.incumplidas} no se hicieron`}`);
        }
        frases.push(frase(...partes, "."));
    }
    if (actividades.pendientes) {
        frases.push(frase("Tienes ", [actividadesTexto(actividades.pendientes)], " por hacer en jornadas que no han terminado."));
    }
    if (actividades.estimado_min) {
        frases.push(frase("Lo real fue el ", [`${actividades.real_sobre_estimado} %`], " de lo estimado."));
    }
    if (jornada.adicional_min) {
        frases.push(frase("Trabajaste ", [duracionTexto(jornada.adicional_min)], " fuera de tu turno."));
    }
    if (jornada.aprovechamiento !== null) {
        frases.push(frase("Aprovechaste el ", [`${jornada.aprovechamiento} %`], " del tiempo que estuviste presente."));
    }
    if (jornada.jornadas_sin_validar) {
        const cuantas = jornada.jornadas_sin_validar === 1 ? "1 jornada espera" : `${jornada.jornadas_sin_validar} jornadas esperan`;
        frases.push(crearConIcono("p", "linea-info", "info", `${cuantas} la validación de tu Administrador.`));
    }
    const contenedor = document.getElementById("resumen-frases");
    contenedor.replaceChildren(...frases);
    contenedor.hidden = false;
}

// ---------- Tu carga por día: una franja simple, sin librería (alcance, Sección 6.2) ----------
// Cada día con su carga frente a su capacidad. La barra es lo programado; si pasa de la capacidad,
// lo que sobra se ve rayado en rojo (sobrecarga, 6.3) y el texto lo dice.

function pintarCarga(carga) {
    const jornadas = Object.fromEntries((carga.operarios[0]?.jornadas || []).map((j) => [j.fecha, j]));
    const lista = crearElemento("ul", "resumen-carga-lista");
    for (let dia = 0; dia < 7; dia += 1) {
        const fecha = fechaTexto(sumarDias(lunes, dia));
        const jornada = jornadas[fecha];
        const fila = crearElemento("li");
        const texto = jornada
            ? `${duracionTexto(jornada.minutos)} de ${duracionTexto(jornada.capacidad_min)}${jornada.sobrecarga ? ", sobrecarga" : ""}`
            : "Sin trabajo programado";
        const barra = crearElemento("div", "barra-avance");
        barra.setAttribute("aria-hidden", "true");
        if (jornada) {
            const total = Math.max(jornada.minutos, jornada.capacidad_min);
            const lleno = crearElemento("span", "barra-avance-relleno");
            lleno.style.width = `${(Math.min(jornada.minutos, jornada.capacidad_min) * 100) / total}%`;
            barra.append(lleno);
            if (jornada.sobrecarga) {
                const exceso = crearElemento("span", "barra-avance-sobrecarga");
                exceso.style.width = `${((jornada.minutos - jornada.capacidad_min) * 100) / total}%`;
                barra.append(exceso);
            }
        }
        fila.append(
            crearElemento("span", "resumen-dia", diaCorto(fecha)),
            barra,
            jornada?.sobrecarga
                ? crearConIcono("span", "resumen-carga-texto semana-carga-exceso", "triangle-alert", texto)
                : crearElemento("span", "resumen-carga-texto cifra texto-secundario", texto),
        );
        lista.append(fila);
    }
    seccion("resumen-carga", "Tu carga por día", lista);
}

// ---------- Tu asistencia ----------

const ESTADO_ASISTENCIA = {
    VALIDADA: ["check", "estado-op-completada", "Validada"],
    CORREGIDA: ["pencil", "estado-op-completada", "Corregida"],
    REGISTRADA: ["circle", "texto-secundario", "Por validar"],
};

function pintarAsistencia(asistencias) {
    if (!asistencias.length) {
        seccion("resumen-asistencia", "Tu asistencia", crearElemento("p", "texto-secundario", "No marcaste asistencia esta semana."));
        return;
    }
    const lista = crearElemento("ul", "resumen-filas");
    for (const asistencia of asistencias) {
        const [icono_, clase, texto] = ESTADO_ASISTENCIA[asistencia.estado] || ESTADO_ASISTENCIA.REGISTRADA;
        const fila = crearElemento("li");
        fila.append(
            crearElemento("span", "resumen-dia", diaCorto(asistencia.jornada)),
            crearElemento("span", "cifra", asistencia.salida
                ? `${hora(asistencia.entrada)} a ${hora(asistencia.salida)}` : `${hora(asistencia.entrada)}, sin salida`),
            crearConIcono("span", `resumen-estado ${clase}`, icono_, texto),
        );
        lista.append(fila);
    }
    seccion("resumen-asistencia", "Tu asistencia", lista);
}

// ---------- Lo real frente a lo estimado ----------

function pintarTiempos(finalizadas) {
    if (!finalizadas.length) {
        seccion("resumen-tiempos", "Lo real frente a lo estimado",
            crearElemento("p", "texto-secundario", "Todavía no finalizas actividades de esta semana."));
        return;
    }
    const lista = crearElemento("ul", "resumen-tiempos-lista");
    for (const actividad of finalizadas) {
        const diferencia = actividad.real_min - actividad.estimado_min;
        const fila = crearElemento("li");
        const textos = crearElemento("div", "resumen-tiempo-textos");
        let detalle = "justo lo estimado";
        if (diferencia > 0) {
            detalle = `${duracionTexto(diferencia)} más`;
        } else if (diferencia < 0) {
            detalle = `${duracionTexto(-diferencia)} menos`;
        }
        textos.append(
            crearElemento("strong", "", actividad.titulo),
            crearElemento("span", "texto-secundario cifra",
                `Tomó ${duracionTexto(actividad.real_min)} de ${duracionTexto(actividad.estimado_min)}, ${detalle}`),
        );
        // La barra compara con lo estimado: llena es lo estimado; si se pasa, la marca pasa del borde.
        const barra = crearElemento("div", "barra-avance");
        barra.setAttribute("aria-hidden", "true");
        const relleno = crearElemento("span", "barra-avance-relleno");
        relleno.style.width = `${Math.min(100, (actividad.real_min * 100) / Math.max(1, actividad.estimado_min))}%`;
        barra.append(relleno);
        if (diferencia > actividad.estimado_min * MARGEN_ESTIMADO) {
            barra.classList.add("barra-avance-excedida");
        }
        fila.append(textos, barra);
        lista.append(fila);
    }
    seccion("resumen-tiempos", "Lo real frente a lo estimado", lista);
}

// ---------- Tus pausas ----------

function pintarPausas(pausas) {
    if (!pausas.length) {
        seccion("resumen-pausas", "Tus pausas", crearElemento("p", "texto-secundario", "No hiciste pausas esta semana."));
        return;
    }
    const lista = crearElemento("ul", "resumen-filas");
    for (const pausa of pausas) {
        const fila = crearElemento("li");
        fila.append(
            crearElemento("span", "", pausa.motivo),
            crearElemento("span", "cifra texto-secundario",
                `${pausa.cantidad === 1 ? "1 vez" : `${pausa.cantidad} veces`}, ${duracionTexto(pausa.minutos)}`),
        );
        lista.append(fila);
    }
    seccion("resumen-pausas", "Tus pausas", lista);
}

// ---------- Lo que viene ----------

function pintarLoQueViene(yo, siguiente) {
    const frases = [];
    const { reprogramadas, dias_de_retraso_maximo: dias } = yo.pendientes;
    if (reprogramadas) {
        frases.push(frase([actividadesTexto(reprogramadas)], ` ${reprogramadas === 1 ? "pasó" : "pasaron"} a otra jornada`,
            dias ? `, con hasta ${dias === 1 ? "1 día" : `${dias} días`} de retraso.` : "."));
    }
    if (siguiente !== null) {
        frases.push(siguiente
            ? frase("La semana siguiente tienes ", [duracionTexto(siguiente)], " de trabajo programado.")
            : frase("Para la semana siguiente todavía no tienes trabajo programado."));
    }
    if (frases.length) {
        seccion("resumen-viene", "Lo que viene", ...frases);
    } else {
        document.getElementById("resumen-viene").hidden = true;
    }
}

// ---------- Carga de datos ----------

async function cargar() {
    const domingo = sumarDias(lunes, 6);
    const desde = fechaTexto(lunes);
    const hasta = fechaTexto(domingo);
    const formato = { day: "numeric", month: "long" };
    document.getElementById("rango-semana").textContent =
        `Del ${lunes.toLocaleDateString("es-CO", formato)} al ${domingo.toLocaleDateString("es-CO", formato)}`;
    const mensaje = document.getElementById("mensaje");

    // La carga de la semana siguiente solo se pregunta cuando se mira la semana en curso.
    const esEstaSemana = desde === fechaTexto(inicioDeSemana(new Date()));
    const lunesSiguiente = sumarDias(lunes, 7);
    try {
        const [indicadores, cargaDeLaSemana, carga] = await Promise.all([
            pedirApi(`/analisis/indicadores?desde=${desde}&hasta=${hasta}`),
            pedirApi(`/analisis/carga?desde=${desde}&hasta=${hasta}`),
            esEstaSemana
                ? pedirApi(`/analisis/carga?desde=${fechaTexto(lunesSiguiente)}&hasta=${fechaTexto(sumarDias(lunesSiguiente, 6))}`)
                : Promise.resolve(null),
        ]);
        const yo = indicadores.operarios[0];
        const siguiente = carga
            ? (carga.operarios[0]?.jornadas || []).reduce((suma, jornada) => suma + jornada.minutos, 0)
            : null;
        mensaje.hidden = true;
        pintarFrases(yo);
        pintarCarga(cargaDeLaSemana);
        pintarAsistencia(yo.detalle.asistencias);
        pintarTiempos(yo.detalle.finalizadas);
        pintarPausas(yo.detalle.pausas_por_motivo);
        pintarLoQueViene(yo, siguiente);
    } catch (error) {
        mensaje.hidden = false;
        mensaje.textContent = `No pudimos cargar tu semana: ${error.message}`;
        mensaje.classList.add("mensaje-error");
    }
}

function moverSemana(semanas) {
    lunes = semanas === 0 ? inicioDeSemana(new Date()) : sumarDias(lunes, semanas * 7);
    cargar();
}

iniciarPaginaProtegida(["OPERARIO"]).then(() => {
    const anterior = document.getElementById("semana-anterior");
    const siguiente = document.getElementById("semana-siguiente");
    anterior.insertAdjacentHTML("afterbegin", icono("chevron-left"));
    siguiente.insertAdjacentHTML("afterbegin", icono("chevron-right"));
    anterior.addEventListener("click", () => moverSemana(-1));
    siguiente.addEventListener("click", () => moverSemana(1));
    document.getElementById("semana-actual").addEventListener("click", () => moverSemana(0));
    cargar();
});
