// Indicadores del Administrador (alcance, Secciones 5.2 y 6.2): cómo les fue en la semana. Tres pestañas:
// la empresa, cada persona (en orden alfabético, no es un ranking) y las actividades por categoría y por
// proyecto. Todo lo calcula el servidor; aquí solo se escribe como frases.

let lunes = inicioDeSemana(new Date());
let datos = null;
let tendencia = [];

const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;
const porcentaje = (valor) => (valor === null || valor === undefined ? "Sin datos" : `${valor} %`);

// "45 cumplidas, 3 con retraso y 2 no realizadas."
function fraseActividades(actividades) {
    if (!actividades.cumplidas && !actividades.con_retraso && !actividades.incumplidas) {
        return "Ninguna actividad evaluada todavía.";
    }
    const partes = [`${actividades.cumplidas} ${actividades.cumplidas === 1 ? "cumplida" : "cumplidas"}`];
    if (actividades.con_retraso) {
        partes.push(`${actividades.con_retraso} con retraso`);
    }
    if (actividades.incumplidas) {
        partes.push(`${actividades.incumplidas} no ${actividades.incumplidas === 1 ? "realizada" : "realizadas"}`);
    }
    const ultima = partes.pop();
    return `${partes.length ? `${partes.join(", ")} y ${ultima}` : ultima}.`;
}

function frasePrecision(actividades) {
    const valor = actividades.real_sobre_estimado;
    if (valor === null) {
        return "Todavía no hay actividades finalizadas para comparar.";
    }
    if (valor === 100) {
        return "Lo real fue exactamente lo estimado.";
    }
    return `Lo real fue un ${Math.abs(valor - 100)} % ${valor > 100 ? "más" : "menos"} que lo estimado.`;
}

// Los indicadores de un grupo (la empresa o una persona) como una lista de frases: nombre, cifra y explicación.
function crearIndicadores(jornada, actividades) {
    const lista = crearElemento("dl", "indicadores");
    const filas = [
        ["Cumplimiento de jornada", porcentaje(jornada.cumplimiento_jornada),
            `${duracionTexto(jornada.actividades_min)} en actividades de ${duracionTexto(jornada.programado_min)} programadas.`],
        ["Aprovechamiento", porcentaje(jornada.aprovechamiento),
            jornada.presente_min ? `De ${duracionTexto(jornada.presente_min)} presentes con la asistencia validada.` : "Ninguna asistencia validada todavía."],
        ["Cumplimiento de actividades", porcentaje(actividades.cumplimiento_actividades), fraseActividades(actividades)],
        ["Precisión de estimación", porcentaje(actividades.real_sobre_estimado), frasePrecision(actividades)],
        ["Tiempo adicional", jornada.adicional_min ? duracionTexto(jornada.adicional_min) : "—", "Trabajado fuera del horario del turno."],
    ];
    for (const [nombre, cifra, frase] of filas) {
        const grupo = crearElemento("div", "indicador");
        const dd = crearElemento("dd");
        dd.append(crearElemento("strong", "cifra indicador-cifra", cifra), crearElemento("span", "texto-secundario", frase));
        grupo.append(crearElemento("dt", "", nombre), dd);
        lista.append(grupo);
    }
    if (jornada.jornadas_sin_validar) {
        const aviso = crearElemento("div", "indicador");
        aviso.append(crearConIcono("dd", "linea-info", "info",
            `${plural(jornada.jornadas_sin_validar, "jornada sin validar no cuenta", "jornadas sin validar no cuentan")} en el aprovechamiento: valídalas en Hoy, Asistencia.`));
        lista.append(aviso);
    }
    return lista;
}

function porMotivo(lista) {
    return lista.map((m) => `${m.motivo} ${m.cantidad}`).join(", ");
}

// ---------- Empresa ----------

function pintarEmpresa() {
    const { empresa } = datos;
    document.getElementById("indicadores-empresa").replaceWith(
        Object.assign(crearIndicadores(empresa.jornada, empresa.actividades), { id: "indicadores-empresa" }));
    const pendientes = empresa.pendientes;
    const lineas = [];
    if (pendientes.reprogramadas) {
        lineas.push(`${plural(pendientes.reprogramadas, "actividad reprogramada", "actividades reprogramadas")} (la más atrasada, ${plural(pendientes.dias_de_retraso_maximo, "día", "días")}).`);
    }
    if (pendientes.no_realizadas) {
        lineas.push(`${plural(pendientes.no_realizadas, "actividad de hora fija no realizada", "actividades de hora fija no realizadas")}.`);
    }
    if (pendientes.canceladas) {
        lineas.push(`Canceladas: ${pendientes.canceladas} (${porMotivo(pendientes.canceladas_por_motivo)}).`);
    }
    if (pendientes.devoluciones) {
        lineas.push(`Devueltas: ${pendientes.devoluciones} (${porMotivo(pendientes.devoluciones_por_motivo)}).`);
    }
    document.getElementById("pendientes-empresa").replaceChildren(...(lineas.length
        ? lineas.map((linea) => crearElemento("li", "", linea))
        : [crearElemento("li", "texto-secundario", "Nada quedó pendiente esta semana.")]));
}

// ---------- Por persona ----------

function crearFilaPersona(operario) {
    const elemento = crearElemento("li");
    const fila = crearElemento("button", "fila-admin fila-indicadores");
    fila.type = "button";
    fila.dataset.foco = `indicadores-${operario.id}`;
    const celda = (texto, nombre) => {
        const valor = crearElemento("span", "cifra", texto);
        valor.dataset.nombre = nombre;      // En celular cada cifra lleva su nombre al lado.
        return valor;
    };
    fila.append(
        crearElemento("strong", "fila-admin-nombre", operario.nombre),
        celda(porcentaje(operario.jornada.cumplimiento_jornada), "Jornada"),
        celda(porcentaje(operario.jornada.aprovechamiento), "Aprovechamiento"),
        celda(porcentaje(operario.actividades.cumplimiento_actividades), "Actividades"),
        celda(porcentaje(operario.actividades.real_sobre_estimado), "Real / estimado"),
        celda(operario.jornada.adicional_min ? duracionTexto(operario.jornada.adicional_min) : "—", "Adicional"),
    );
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    fila.addEventListener("click", () => {
        document.querySelectorAll(".lista-admin [aria-current]").forEach((otra) => otra.removeAttribute("aria-current"));
        fila.setAttribute("aria-current", "true");
        abrirPersona(operario, () => fila.removeAttribute("aria-current"));
    });
    elemento.append(fila);
    return elemento;
}

function pintarPersonas() {
    const busqueda = document.getElementById("buscar-persona").value.trim().toLowerCase();
    const visibles = datos.operarios
        .filter((o) => o.nombre.toLowerCase().includes(busqueda))
        .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    reemplazarSiCambia(document.getElementById("lista-personas"), visibles.map(crearFilaPersona));
    document.getElementById("sin-personas").hidden = visibles.length > 0;
}

function horaCorta_(momento) {
    if (!momento) {
        return "—";
    }
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

// El detalle de una persona: sus indicadores, su asistencia, lo que finalizó y sus pausas.
function abrirPersona(operario, alCerrar) {
    const { detalle } = operario;
    const contenido = [crearIndicadores(operario.jornada, operario.actividades)];

    const asistencia = crearElemento("ul", "indicadores-detalle");
    for (const dia of detalle.asistencias) {
        const fila = crearElemento("li");
        const fecha = fechaLarga(fechaDesdeTexto(dia.jornada));
        fila.append(crearElemento("span", "", fecha.charAt(0).toUpperCase() + fecha.slice(1)),
            crearElemento("span", "cifra texto-secundario", `Entrada ${horaCorta_(dia.entrada)}, salida ${horaCorta_(dia.salida)}`));
        if (dia.salida_anticipada_min > 0) {
            fila.append(crearConIcono("span", "linea-info", "clock", `Salida anticipada de ${duracionTexto(dia.salida_anticipada_min)}`));
        }
        asistencia.append(fila);
    }
    contenido.push(crearElemento("h3", "detalle-op-subtitulo", "Asistencia"),
        detalle.asistencias.length ? asistencia : crearElemento("p", "texto-secundario", "No marcó asistencia esta semana."));

    const finalizadas = crearElemento("ul", "indicadores-detalle");
    for (const actividad of detalle.finalizadas) {
        const fila = crearElemento("li");
        fila.append(crearElemento("span", "", actividad.titulo),
            crearElemento("span", "cifra texto-secundario",
                `Real ${duracionTexto(actividad.real_min)} de ${duracionTexto(actividad.estimado_min)} estimados`));
        finalizadas.append(fila);
    }
    contenido.push(crearElemento("h3", "detalle-op-subtitulo", "Lo que finalizó"),
        detalle.finalizadas.length ? finalizadas : crearElemento("p", "texto-secundario", "No finalizó actividades esta semana."));

    if (detalle.pausas_por_motivo.length) {
        const pausas = crearElemento("ul", "indicadores-detalle");
        for (const motivo of detalle.pausas_por_motivo) {
            const fila = crearElemento("li");
            fila.append(crearElemento("span", "", motivo.motivo),
                crearElemento("span", "cifra texto-secundario", `${plural(motivo.cantidad, "pausa", "pausas")}, ${duracionTexto(motivo.minutos)}`));
            pausas.append(fila);
        }
        contenido.push(crearElemento("h3", "detalle-op-subtitulo", "Pausas por motivo"), pausas);
    }
    abrirPanelLateral({ marca: document.getElementById("rango-semana").textContent, titulo: operario.nombre,
        contenido, volverA: "Indicadores", alCerrar });
}

// ---------- Por actividad ----------

function crearFilaGrupo(nombre, actividades) {
    const fila = crearElemento("li", "fila-pendiente");
    const textos = crearElemento("div", "fila-admin-textos");
    textos.append(crearElemento("strong", "fila-admin-nombre", nombre),
        crearElemento("p", "fila-admin-datos texto-secundario", `${fraseActividades(actividades)} ${frasePrecision(actividades)}`));
    fila.append(textos, crearElemento("strong", "cifra indicador-cifra", porcentaje(actividades.cumplimiento_actividades)));
    return fila;
}

function pintarActividad() {
    document.getElementById("por-categoria").replaceChildren(...datos.categorias.map((c) =>
        crearFilaGrupo(NOMBRE_CATEGORIA[c.categoria] || c.categoria, c.actividades)));
    document.getElementById("por-proyecto").replaceChildren(...datos.proyectos.map((p) => crearFilaGrupo(p.nombre, p.actividades)));
    document.getElementById("sin-proyectos").hidden = datos.proyectos.length > 0;
}

// ---------- Gráficas (alcance, Sección 7: Chart.js). Cada una lleva también su tabla ----------

const formatoPorcentaje = (valor) => (valor === null || valor === undefined ? "Sin datos" : `${Math.round(valor)} %`);
const formatoTiempo = (valor) => duracionTexto(Math.round(valor || 0));
const etiquetaSemana = (fecha) => fechaDesdeTexto(fecha).toLocaleDateString("es-CO", { day: "numeric", month: "short" });

// ¿Vamos mejorando? Tres indicadores en las últimas 8 semanas (una sola escala: todos son porcentajes).
function pintarTendencia() {
    const contenedor = document.getElementById("grafica-tendencia");
    const titulo = "Tendencia de las últimas 8 semanas (cada punto es una semana, desde su lunes)";
    if (!tendencia.some((s) => s.cumplimiento_jornada !== null || s.cumplimiento_actividades !== null || s.aprovechamiento !== null)) {
        pintarSinDatos(contenedor, titulo, "Todavía no hay semanas con jornadas terminadas para comparar.");
        return;
    }
    const ultima = tendencia.at(-1);
    pintarGrafica(contenedor, {
        id: "lienzo-tendencia", titulo, tipo: "linea", formato: formatoPorcentaje,
        etiquetas: tendencia.map((s) => etiquetaSemana(s.desde)),
        series: [
            { nombre: "Cumplimiento de jornada", valores: tendencia.map((s) => s.cumplimiento_jornada) },
            { nombre: "Cumplimiento de actividades", valores: tendencia.map((s) => s.cumplimiento_actividades) },
            { nombre: "Aprovechamiento", valores: tendencia.map((s) => s.aprovechamiento) },
        ],
        descripcion: `Tendencia de 8 semanas. La última: cumplimiento de jornada ${formatoPorcentaje(ultima.cumplimiento_jornada)}, `
            + `de actividades ${formatoPorcentaje(ultima.cumplimiento_actividades)} y aprovechamiento ${formatoPorcentaje(ultima.aprovechamiento)}.`,
    });
}

// ¿Qué nos frena? El tiempo en pausa por motivo, de todos, y las devoluciones por motivo.
function pintarMotivos() {
    const minutos = new Map();
    for (const operario of datos.operarios) {
        for (const motivo of operario.detalle.pausas_por_motivo) {
            minutos.set(motivo.motivo, (minutos.get(motivo.motivo) || 0) + motivo.minutos);
        }
    }
    const pausas = [...minutos].sort((a, b) => b[1] - a[1]);
    const contenedorPausas = document.getElementById("grafica-pausas");
    if (pausas.length) {
        pintarGrafica(contenedorPausas, {
            id: "lienzo-pausas", titulo: "Tiempo en pausa por motivo", tipo: "barras", horizontal: true, formato: formatoTiempo,
            etiquetas: pausas.map(([motivo]) => motivo),
            series: [{ nombre: "Tiempo en pausa", valores: pausas.map(([, valor]) => valor) }],
            eje: ejeEnHoras([{ valores: pausas.map(([, valor]) => valor) }]),
            descripcion: `El motivo con más tiempo en pausa es ${pausas[0][0]}, con ${formatoTiempo(pausas[0][1])}.`,
        });
    } else {
        pintarSinDatos(contenedorPausas, "Tiempo en pausa por motivo", "Nadie pausó actividades esta semana.");
    }
    const devoluciones = datos.empresa.pendientes.devoluciones_por_motivo;
    const contenedorDevoluciones = document.getElementById("grafica-devoluciones");
    if (devoluciones.length) {
        pintarGrafica(contenedorDevoluciones, {
            id: "lienzo-devoluciones", titulo: "Devoluciones por motivo", tipo: "barras", horizontal: true,
            formato: (valor) => String(Math.round(valor)), eje: ejeEnCantidades,
            etiquetas: devoluciones.map((d) => d.motivo),
            series: [{ nombre: "Devoluciones", valores: devoluciones.map((d) => d.cantidad) }],
            descripcion: `El motivo más frecuente de devolución es ${devoluciones[0].motivo}, con ${devoluciones[0].cantidad}.`,
        });
    } else {
        pintarSinDatos(contenedorDevoluciones, "Devoluciones por motivo", "Nadie devolvió actividades esta semana.");
    }
}

// ¿Quién tiene la carga desbalanceada? Horas en actividades frente a horas programadas, en orden alfabético.
function pintarGraficaPersonas() {
    const contenedor = document.getElementById("grafica-personas");
    const titulo = "Horas en actividades frente a las programadas";
    const personas = [...datos.operarios].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    if (!personas.some((o) => o.jornada.programado_min)) {
        pintarSinDatos(contenedor, titulo, "Ninguna jornada terminó esta semana.");
        return;
    }
    pintarGrafica(contenedor, {
        id: "lienzo-personas", titulo, tipo: "barras", horizontal: true, formato: formatoTiempo,
        etiquetas: personas.map((o) => o.nombre),
        series: [
            { nombre: "En actividades", valores: personas.map((o) => o.jornada.actividades_min) },
            { nombre: "Programado", valores: personas.map((o) => o.jornada.programado_min) },
        ],
        descripcion: "Por persona, en orden alfabético: las horas en actividades frente a las horas programadas de la semana.",
        eje: ejeEnHoras([{ valores: personas.flatMap((o) => [o.jornada.actividades_min, o.jornada.programado_min]) }]),
    });
}

// ¿En qué tipo de trabajo estimamos mal? Lo estimado frente a lo real de lo finalizado, por categoría.
function pintarGraficaCategorias() {
    const contenedor = document.getElementById("grafica-categorias");
    const titulo = "Lo estimado frente a lo real, por categoría";
    const categorias = datos.categorias.filter((c) => c.actividades.estimado_min);
    if (!categorias.length) {
        pintarSinDatos(contenedor, titulo, "Todavía no hay actividades finalizadas esta semana.");
        return;
    }
    pintarGrafica(contenedor, {
        id: "lienzo-categorias", titulo, tipo: "barras", formato: formatoTiempo,
        etiquetas: categorias.map((c) => NOMBRE_CATEGORIA[c.categoria] || c.categoria),
        series: [
            { nombre: "Estimado", valores: categorias.map((c) => c.actividades.estimado_min) },
            { nombre: "Real", valores: categorias.map((c) => c.actividades.real_min) },
        ],
        descripcion: "Por categoría, el tiempo estimado frente al tiempo real de las actividades finalizadas.",
        eje: ejeEnHoras([{ valores: categorias.flatMap((c) => [c.actividades.estimado_min, c.actividades.real_min]) }]),
    });
}

// ---------- Carga ----------

async function cargar() {
    const formato = { day: "numeric", month: "long" };
    const domingo = sumarDias(lunes, 6);
    document.getElementById("rango-semana").textContent =
        `Semana del ${lunes.toLocaleDateString("es-CO", formato)} al ${domingo.toLocaleDateString("es-CO", formato)}`;
    const mensaje = document.getElementById("mensaje");
    try {
        [datos, tendencia] = await Promise.all([
            pedirApi(`/analisis/indicadores?desde=${fechaTexto(lunes)}&hasta=${fechaTexto(domingo)}`),
            pedirApi(`/analisis/indicadores/tendencia?hasta=${fechaTexto(domingo)}&semanas=8`),
        ]);
        mensaje.hidden = true;
        pintarEmpresa();
        pintarPersonas();
        pintarActividad();
        pintarTendencia();
        pintarMotivos();
        pintarGraficaPersonas();
        pintarGraficaCategorias();
    } catch (error) {
        mensaje.hidden = false;
        mensaje.textContent = `No se pudieron calcular los indicadores: ${error.message}`;
    }
}

function moverSemana(semanas) {
    lunes = semanas === 0 ? inicioDeSemana(new Date()) : sumarDias(lunes, semanas * 7);
    cargar();
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(() => {
    const anterior = document.getElementById("semana-anterior");
    const siguiente = document.getElementById("semana-siguiente");
    anterior.insertAdjacentHTML("afterbegin", icono("chevron-left"));
    siguiente.insertAdjacentHTML("afterbegin", icono("chevron-right"));
    anterior.addEventListener("click", () => moverSemana(-1));
    siguiente.addEventListener("click", () => moverSemana(1));
    document.getElementById("semana-actual").addEventListener("click", () => moverSemana(0));
    document.getElementById("buscar-persona").addEventListener("input", pintarPersonas);
    iniciarPestanas(document.querySelector(".pestanas"));
    cargar();
});
