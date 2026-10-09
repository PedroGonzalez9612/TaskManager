// Diálogo para crear o editar una actividad (Administrador). Lo usan las vistas "Equipo" y "Actividades".
// Mientras se elige la fecha muestra la carga de cada operario en esa jornada, para ver la
// sobrecarga antes de asignar (alcance, Sección 5.2).

function crearCampo(textoEtiqueta, control, ayuda = "") {
    const campo = crearElemento("div", "campo-formulario");
    const etiqueta = crearElemento("label", "", textoEtiqueta);
    etiqueta.htmlFor = control.id;
    campo.append(etiqueta, control);
    if (ayuda) {
        campo.append(crearElemento("p", "ayuda-campo", ayuda));
    }
    return campo;
}

function crearEntrada(id, nombre, tipo = "text", atributos = {}) {
    const entrada = crearElemento(tipo === "textarea" ? "textarea" : "input");
    entrada.id = id;
    entrada.name = nombre;
    if (tipo !== "textarea") {
        entrada.type = tipo;
    }
    Object.assign(entrada, atributos);
    return entrada;
}

function crearSelector(id, nombre, opciones) {
    const selector = crearElemento("select");
    selector.id = id;
    selector.name = nombre;
    for (const [valor, texto] of opciones) {
        const opcion = crearElemento("option", "", texto);
        opcion.value = valor;
        selector.append(opcion);
    }
    return selector;
}

// Crea el diálogo una sola vez por página. "obtenerRequerimientos" y "obtenerOperarios" devuelven las
// listas vigentes; "alGuardar" se llama después de crear, editar o eliminar, para recargar la vista.
function crearFormularioActividad({ obtenerRequerimientos, obtenerOperarios, alGuardar }) {
    const dialogo = crearElemento("dialog", "dialogo dialogo-ancho");
    let actividadEnEdicion = null;

    const encabezado = crearElemento("div", "dialogo-encabezado");
    const titulo = crearElemento("h2", "", "Nueva actividad");
    const cerrar = crearElemento("button", "boton-cerrar", "×");
    cerrar.type = "button";
    cerrar.dataset.cerrar = "";
    cerrar.setAttribute("aria-label", "Cerrar");
    encabezado.append(titulo, cerrar);

    const formulario = crearElemento("form", "formulario");
    formulario.noValidate = true;

    const requerimiento = crearSelector("act-requerimiento", "requerimiento_id", []);
    const tituloActividad = crearEntrada("act-titulo", "titulo", "text", { required: true, maxLength: 120 });
    const descripcion = crearEntrada("act-descripcion", "descripcion", "textarea", { rows: 3 });
    const categoria = crearSelector("act-categoria", "categoria", Object.entries(NOMBRE_CATEGORIA));
    const prioridad = crearSelector("act-prioridad", "prioridad",
        Object.keys(PESO_PRIORIDAD).reverse().map((clave) => [clave, NOMBRE_PRIORIDAD[clave]]));
    const ubicacion = crearEntrada("act-ubicacion", "ubicacion", "text", { required: true, maxLength: 80 });
    const fecha = crearEntrada("act-fecha", "fecha_programada", "date", { required: true });
    const hora = crearEntrada("act-hora", "hora_programada", "time");
    const horas = crearEntrada("act-horas", "horas", "number", { min: 0, max: 24, step: 1 });
    const minutos = crearEntrada("act-minutos", "minutos", "number", { min: 0, max: 59, step: 5 });

    const fila = (...campos) => {
        const contenedor = crearElemento("div", "fila-campos");
        contenedor.append(...campos);
        return contenedor;
    };

    const grupoOperarios = crearElemento("fieldset", "grupo-campos");
    grupoOperarios.append(crearElemento("legend", "", "Operarios asignados"));
    const listaOperarios = crearElemento("div", "lista-opciones");
    grupoOperarios.append(listaOperarios);

    const mensaje = crearElemento("p", "mensaje-formulario");
    mensaje.setAttribute("role", "alert");
    mensaje.hidden = true;

    const acciones = crearElemento("div", "dialogo-acciones");
    const eliminar = crearElemento("button", "boton-peligro", "Eliminar");
    eliminar.type = "button";
    const cancelar = crearElemento("button", "boton-secundario", "Cancelar");
    cancelar.type = "button";
    cancelar.dataset.cerrar = "";
    const guardar = crearElemento("button", "boton", "Guardar actividad");
    guardar.type = "submit";
    acciones.append(eliminar, cancelar, guardar);

    formulario.append(
        crearCampo("Requerimiento", requerimiento),
        crearCampo("Título", tituloActividad),
        crearCampo("Qué hay que hacer", descripcion),
        fila(crearCampo("Categoría", categoria), crearCampo("Prioridad", prioridad)),
        crearCampo("Ubicación", ubicacion, "Línea, máquina o área donde se hace el trabajo."),
        fila(crearCampo("Fecha", fecha), crearCampo("Hora (opcional)", hora)),
        fila(crearCampo("Estimado: horas", horas), crearCampo("Minutos", minutos)),
        grupoOperarios, mensaje, acciones,
    );
    dialogo.append(encabezado, formulario);
    document.body.append(dialogo);
    configurarDialogo([], dialogo);

    // Lista de operarios con la carga que ya tienen en la fecha elegida.
    async function pintarOperarios(seleccionados) {
        const operarios = obtenerOperarios();
        if (operarios.length === 0) {
            listaOperarios.replaceChildren(
                crearElemento("p", "texto-suave", "Tu empresa todavía no tiene operarios. Créalos en Usuarios."));
            return;
        }

        let cargas = {};
        let capacidad = 0;
        if (fecha.value) {
            try {
                const carga = await pedirApi(`/analisis/carga?desde=${fecha.value}&hasta=${fecha.value}`);
                capacidad = carga.capacidad_min;
                cargas = Object.fromEntries(carga.operarios.map((o) => [o.id, o.jornadas[0]?.minutos || 0]));
            } catch (error) {
                // Sin la carga el formulario sigue sirviendo; solo no se muestra el porcentaje.
            }
        }

        listaOperarios.replaceChildren(...operarios.map((operario) => {
            const opcion = crearElemento("label", "opcion");
            const casilla = crearElemento("input");
            casilla.type = "checkbox";
            casilla.value = operario.id;
            casilla.checked = seleccionados.includes(operario.id);
            opcion.append(casilla, crearElemento("span", "opcion-texto", operario.nombre));

            if (capacidad) {
                const porcentaje = Math.round((cargas[operario.id] || 0) * 100 / capacidad);
                const sobrecargado = porcentaje > 100;
                const carga = sobrecargado
                    ? crearConIcono("span", "carga cifra carga-sobrecarga", "triangle-alert", `${porcentaje} %`)
                    : crearElemento("span", "carga cifra", `${porcentaje} %`);
                carga.title = "Carga del operario en esa jornada, sin contar esta actividad nueva";
                opcion.append(carga);
            }
            return opcion;
        }));
    }

    const operariosMarcados = () =>
        [...listaOperarios.querySelectorAll("input:checked")].map((casilla) => casilla.value);

    fecha.addEventListener("change", () => pintarOperarios(operariosMarcados()));

    function abrir(actividad, valores = {}) {
        actividadEnEdicion = actividad;
        titulo.textContent = actividad ? `Editar ${actividad.codigo}` : "Nueva actividad";
        guardar.textContent = actividad ? "Guardar cambios" : "Guardar actividad";
        eliminar.hidden = !actividad;

        requerimiento.replaceChildren(...obtenerRequerimientos().map((r) => {
            const opcion = crearElemento("option", "", r.titulo);
            opcion.value = r.id;
            return opcion;
        }));

        dialogo.showModal();    // Primero se abre: al cerrarse el diálogo anterior el formulario quedó en blanco.
        const origen = actividad || valores;
        requerimiento.value = origen.requerimiento_id || requerimiento.options[0]?.value || "";
        tituloActividad.value = origen.titulo || "";
        descripcion.value = origen.descripcion || "";
        categoria.value = origen.categoria || "PRODUCCION";
        prioridad.value = origen.prioridad || "MEDIA";
        ubicacion.value = origen.ubicacion || "";
        fecha.value = origen.fecha_programada || fechaTexto(new Date());
        hora.value = origen.hora_programada || "";
        const estimado = origen.tiempo_estimado_min || 60;
        horas.value = Math.floor(estimado / 60);
        minutos.value = estimado % 60;
        pintarOperarios(actividad ? actividad.operarios.map((o) => o.id) : (valores.operario_ids || []));
        tituloActividad.focus();
    }

    function validar(datos) {
        if (!datos.requerimiento_id) {
            return "Primero crea un requerimiento: toda actividad pertenece a uno.";
        }
        if (!datos.titulo.trim() || !datos.ubicacion.trim() || !datos.fecha_programada) {
            return "Completa título, ubicación y fecha.";
        }
        if ((Number(datos.horas) || 0) * 60 + (Number(datos.minutos) || 0) < 1) {
            return "Indica el tiempo estimado.";
        }
        return null;
    }

    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(dialogo, validar, async (datos) => {
            const cuerpo = {
                requerimiento_id: datos.requerimiento_id,
                titulo: datos.titulo,
                descripcion: datos.descripcion,
                categoria: datos.categoria,
                prioridad: datos.prioridad,
                ubicacion: datos.ubicacion,
                fecha_programada: datos.fecha_programada,
                hora_programada: datos.hora_programada || null,
                tiempo_estimado_min: (Number(datos.horas) || 0) * 60 + (Number(datos.minutos) || 0),
                operario_ids: operariosMarcados(),
            };
            const guardada = actividadEnEdicion
                ? await enviarJson(`/actividades/${actividadEnEdicion.id}`, "PUT", cuerpo)
                : await enviarJson("/actividades", "POST", cuerpo);
            await alGuardar();

            // Alerta de sobrecarga: la actividad se guarda, pero se avisa quién supera su jornada.
            if (guardada.sobrecargas.length) {
                const detalle = guardada.sobrecargas.map((s) => `${s.operario} (${s.porcentaje} %)`).join(", ");
                return {
                    tipo: "advertencia",
                    texto: `${guardada.codigo} guardada. Supera el 100 % de la jornada: ${detalle}.`,
                };
            }
            return `${guardada.codigo} guardada.`;
        });
    });

    // Eliminar pide una segunda confirmación en el mismo botón, para evitar borrados por error.
    eliminar.addEventListener("click", async () => {
        if (eliminar.dataset.confirmar !== "si") {
            eliminar.dataset.confirmar = "si";
            eliminar.textContent = "¿Eliminar? Toca de nuevo";
            return;
        }
        try {
            await pedirApi(`/actividades/${actividadEnEdicion.id}`, { method: "DELETE" });
            const codigo = actividadEnEdicion.codigo;
            dialogo.close();
            await alGuardar();
            mostrarAviso(`${codigo} eliminada.`);
        } catch (error) {
            mostrarErrorFormulario(mensaje, error.message);
        }
    });
    dialogo.addEventListener("close", () => {
        delete eliminar.dataset.confirmar;
        eliminar.textContent = "Eliminar";
    });

    return {
        abrirNueva: (valores) => abrir(null, valores),
        abrirEdicion: (actividad) => abrir(actividad),
    };
}
