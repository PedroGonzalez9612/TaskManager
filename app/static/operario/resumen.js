// Vista "Resumen" del Operario: cuánto trabajo tiene programado en la semana y cómo se reparte.

const NOMBRES_DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

let lunes = inicioDeSemana(new Date());
let grafica = null;

// Los colores y las fuentes salen de las variables de estilos.css: un solo lugar para cambiarlos.
function variableCss(nombre) {
    return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

// ---------- Indicadores ----------

function crearIndicador(titulo, valor, detalle) {
    const indicador = crearElemento("div", "indicador");
    indicador.append(
        crearElemento("p", "indicador-titulo", titulo),
        crearElemento("p", "indicador-valor cifra", valor),
        crearElemento("p", "indicador-detalle", detalle),
    );
    return indicador;
}

function pintarIndicadores(actividades, dias, capacidad) {
    const finalizadas = actividades.filter((a) => a.estado === "COMPLETADA").length;
    const totalMinutos = dias.reduce((suma, dia) => suma + dia.minutos, 0);
    const masCargado = dias.reduce((mayor, dia) => (dia.minutos > mayor.minutos ? dia : mayor), dias[0]);

    document.getElementById("indicadores").replaceChildren(
        crearIndicador("Actividades", String(actividades.length),
            actividades.length ? `${finalizadas} finalizadas` : "Nada programado"),
        crearIndicador("Tiempo programado", duracionTexto(totalMinutos),
            `Jornada de ${duracionTexto(capacidad)}`),
        crearIndicador("Día de mayor carga",
            masCargado.minutos ? `${Math.round(masCargado.minutos * 100 / capacidad)} %` : "—",
            masCargado.minutos ? masCargado.nombreLargo : "Sin actividades"),
    );
}

// ---------- Gráfica de carga por día ----------

// Dibuja la línea de capacidad de la jornada sobre las barras, con su rótulo.
const lineaCapacidad = {
    id: "lineaCapacidad",
    afterDatasetsDraw(chart, _args, opciones) {
        const y = chart.scales.y.getPixelForValue(opciones.horas);
        const { left, right } = chart.chartArea;
        const ctx = chart.ctx;
        ctx.save();
        ctx.strokeStyle = opciones.color;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(right, y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = opciones.color;
        ctx.font = `${Chart.defaults.font.weight || 400} ${Chart.defaults.font.size}px ${Chart.defaults.font.family}`;
        ctx.textAlign = "right";
        ctx.textBaseline = "bottom";
        ctx.fillText(opciones.texto, right, y - 4);
        ctx.restore();
    },
};

function pintarGrafica(dias, capacidad) {
    const horasCapacidad = capacidad / 60;
    const sobrecargado = (dia) => dia.minutos > capacidad;

    Chart.defaults.font.family = variableCss("--fuente-texto");
    Chart.defaults.font.size = 15;
    Chart.defaults.color = variableCss("--texto-secundario");

    grafica?.destroy();
    grafica = new Chart(document.getElementById("grafica-carga"), {
        type: "bar",
        data: {
            labels: dias.map((dia) => dia.nombre),
            datasets: [{
                label: "Tiempo programado",
                data: dias.map((dia) => dia.minutos / 60),
                // Una sola serie, un solo color. El rojo se reserva para los días que superan la jornada.
                backgroundColor: dias.map((dia) => variableCss(sobrecargado(dia) ? "--error" : "--principal")),
                borderRadius: 4,
                maxBarThickness: 44,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                lineaCapacidad: {
                    horas: horasCapacidad,
                    color: variableCss("--texto-secundario"),
                    texto: `Jornada: ${duracionTexto(capacidad)}`,
                },
                tooltip: {
                    callbacks: {
                        title: (items) => dias[items[0].dataIndex].nombreLargo,
                        label: (item) => {
                            const dia = dias[item.dataIndex];
                            const porcentaje = Math.round(dia.minutos * 100 / capacidad);
                            return `${duracionTexto(dia.minutos)} · ${porcentaje} % de la jornada`
                                + (sobrecargado(dia) ? " · Sobrecarga" : "");
                        },
                    },
                },
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    suggestedMax: horasCapacidad * 1.15,
                    ticks: { callback: (valor) => `${valor} h` },
                    grid: { color: variableCss("--borde") },
                    border: { display: false },
                },
            },
        },
        plugins: [lineaCapacidad],
    });

    // La misma información en una tabla, para quien no pueda leer la gráfica.
    document.querySelector("#tabla-carga tbody").replaceChildren(...dias.map((dia) => {
        const fila = crearElemento("tr");
        const porcentaje = Math.round(dia.minutos * 100 / capacidad);
        const carga = crearElemento("td", "cifra", `${porcentaje} %`);
        if (sobrecargado(dia)) {
            carga.replaceChildren(crearConIcono("span", "carga carga-sobrecarga", "triangle-alert", `${porcentaje} % · Sobrecarga`));
        }
        fila.append(
            crearElemento("td", "", dia.nombreLargo),
            crearElemento("td", "cifra", dia.minutos ? duracionTexto(dia.minutos) : "—"),
            carga,
        );
        return fila;
    }));
}

// ---------- Conteos por estado y por categoría ----------

function pintarConteos(actividades) {
    const contar = (campo) => actividades.reduce((conteo, actividad) => {
        const clave = actividad[campo];
        conteo[clave] = conteo[clave] || { cantidad: 0, minutos: 0 };
        conteo[clave].cantidad += 1;
        conteo[clave].minutos += actividad.tiempo_estimado_min || 0;
        return conteo;
    }, {});

    const pintar = (idLista, conteo, crearEtiqueta, vacio) => {
        const filas = Object.entries(conteo).map(([clave, datos]) => {
            const fila = crearElemento("li");
            fila.append(
                crearEtiqueta(clave),
                crearElemento("span", "conteo-detalle cifra",
                    `${datos.cantidad} · ${duracionTexto(datos.minutos)}`),
            );
            return fila;
        });
        document.getElementById(idLista).replaceChildren(
            ...(filas.length ? filas : [crearElemento("li", "texto-suave", vacio)]),
        );
    };

    pintar("por-estado", contar("estado"), crearEtiquetaEstado, "Sin actividades esta semana.");
    pintar("por-categoria", contar("categoria"), crearEtiquetaCategoria, "Sin actividades esta semana.");
}

// ---------- Carga de datos ----------

async function cargar() {
    const domingo = sumarDias(lunes, 6);
    const desde = fechaTexto(lunes);
    const hasta = fechaTexto(domingo);
    const formato = { day: "numeric", month: "long" };
    document.getElementById("rango-semana").textContent =
        `Del ${lunes.toLocaleDateString("es-CO", formato)} al ${domingo.toLocaleDateString("es-CO", formato)}`;

    try {
        const [actividades, carga] = await Promise.all([
            pedirApi(`/actividades?fecha_desde=${desde}&fecha_hasta=${hasta}`),
            pedirApi(`/analisis/carga?desde=${desde}&hasta=${hasta}`),
        ]);
        // El servidor ya sumó los minutos de cada jornada; aquí solo se acomodan en los 7 días.
        const jornadas = Object.fromEntries((carga.operarios[0]?.jornadas || []).map((j) => [j.fecha, j.minutos]));
        const dias = NOMBRES_DIAS.map((nombre, indice) => {
            const fecha = sumarDias(lunes, indice);
            const nombreLargo = fechaLarga(fecha);
            return {
                nombre,
                nombreLargo: nombreLargo.charAt(0).toUpperCase() + nombreLargo.slice(1),
                minutos: jornadas[fechaTexto(fecha)] || 0,
            };
        });
        pintarIndicadores(actividades, dias, carga.capacidad_min);
        pintarGrafica(dias, carga.capacidad_min);
        pintarConteos(actividades);
    } catch (error) {
        mostrarAviso(`No se pudo cargar el resumen: ${error.message}`, "advertencia");
    }
}

function moverSemana(semanas) {
    lunes = semanas === 0 ? inicioDeSemana(new Date()) : sumarDias(lunes, semanas * 7);
    cargar();
}

iniciarPaginaProtegida(["OPERARIO"]).then(async () => {
    const anterior = document.getElementById("semana-anterior");
    const siguiente = document.getElementById("semana-siguiente");
    anterior.insertAdjacentHTML("afterbegin", icono("chevron-left"));
    siguiente.insertAdjacentHTML("afterbegin", icono("chevron-right"));
    anterior.addEventListener("click", () => moverSemana(-1));
    siguiente.addEventListener("click", () => moverSemana(1));
    document.getElementById("semana-actual").addEventListener("click", () => moverSemana(0));

    // La gráfica mide el texto al dibujarse: se espera a que las fuentes estén cargadas.
    await document.fonts.ready;
    cargar();
});
