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

// ---------- Información para el operario (alcance, Sección 5.1) ----------

const TAMANO_MAXIMO_ADJUNTO = 5 * 1024 * 1024;
const MAXIMO_ADJUNTOS = 5;

// Lista de valores de un bloque (herramientas, equipo, precauciones, contacto): un campo que sugiere
// lo que la empresa ya registró y, debajo, lo agregado, cada uno con su botón para quitarlo.
function crearListaDeValores(bloque) {
    const contenedor = crearElemento("div", "lista-valores");
    const sugerencias = crearElemento("datalist");
    sugerencias.id = `sugerencias-${bloque.campo}`;
    const entrada = crearEntrada(`info-${bloque.campo}`, "", "text", { maxLength: 200 });
    entrada.setAttribute("list", sugerencias.id);
    entrada.placeholder = `Por ejemplo: ${bloque.ejemplo}`;
    const agregar = crearConIcono("button", "boton-secundario", "plus", "Agregar");
    agregar.type = "button";
    const elegidos = crearElemento("ul", "valores-elegidos");
    let valores = [];

    function pintar() {
        elegidos.replaceChildren(...valores.map((valor, indice) => {
            const fila = crearElemento("li", "", valor);
            const quitar = crearElemento("button", "boton-cerrar", "×");
            quitar.type = "button";
            quitar.setAttribute("aria-label", `Quitar ${valor}`);
            quitar.addEventListener("click", () => {
                valores.splice(indice, 1);
                pintar();
            });
            fila.append(quitar);
            return fila;
        }));
    }

    function agregarEscrito() {
        const texto = entrada.value.trim().replace(/\s+/g, " ");
        if (texto && !valores.some((valor) => valor.toLowerCase() === texto.toLowerCase())) {
            valores.push(texto);
            pintar();
        }
        entrada.value = "";
        entrada.focus();
    }
    agregar.addEventListener("click", agregarEscrito);
    // Enter agrega el valor en lugar de enviar el formulario.
    entrada.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            evento.preventDefault();
            agregarEscrito();
        }
    });

    const fila = crearElemento("div", "lista-valores-entrada");
    fila.append(entrada, agregar);
    contenedor.append(crearElemento("label", "", bloque.nombre), fila, sugerencias, elegidos);
    contenedor.querySelector("label").htmlFor = entrada.id;
    return {
        elemento: contenedor,
        cargar(lista, opciones) {
            valores = [...lista];
            entrada.value = "";
            sugerencias.replaceChildren(...opciones.map((opcion) => {
                const elemento = crearElemento("option");
                elemento.value = opcion;
                return elemento;
            }));
            pintar();
        },
        // Lo que quedó escrito sin pulsar "Agregar" también se guarda.
        leer: () => {
            const pendiente = entrada.value.trim();
            return pendiente ? [...valores, pendiente] : [...valores];
        },
    };
}

// El editor de la información: primero se eligen los bloques; cada bloque elegido muestra su campo.
function crearEditorInformacion() {
    const grupo = crearElemento("fieldset", "grupo-campos editor-informacion");
    grupo.append(crearElemento("legend", "", "Información para el operario"),
        crearElemento("p", "ayuda-campo",
            "Elige qué necesita saber para hacer el trabajo. La actividad queda lista para iniciar cuando cada bloque elegido tiene contenido."));

    const selector = crearElemento("div", "selector-bloques");
    const editores = {};
    const campos = crearElemento("div", "campos-informacion");

    const pasos = crearEntrada("info-pasos", "", "textarea", { rows: 4 });
    pasos.placeholder = "Un paso por renglón, en orden";
    editores.PASOS = { elemento: crearCampo("Pasos", pasos), cargar: (lista) => { pasos.value = lista.join("\n"); },
        leer: () => pasos.value.split("\n") };

    // Adjuntos: los que ya tiene la actividad y los que se van a subir al guardar.
    const archivo = crearEntrada("info-adjuntos", "", "file", { multiple: true, accept: "application/pdf,image/jpeg,image/png,image/webp" });
    const etiquetaArchivo = crearConIcono("label", "etiqueta-archivos", "paperclip", "Elegir manuales, planos o fotos");
    etiquetaArchivo.htmlFor = archivo.id;
    const existentes = crearElemento("ul", "evidencia-adjuntos");
    const nuevos = crearElemento("ul", "evidencia-elegida");
    let pendientes = [];
    archivo.addEventListener("change", () => {
        pendientes = [...pendientes, ...archivo.files];
        archivo.value = "";
        nuevos.replaceChildren(...pendientes.map((elegido) => crearConIcono("li", "", "paperclip", elegido.name)));
    });
    const campoAdjuntos = crearElemento("div", "campo-formulario");
    campoAdjuntos.append(crearElemento("p", "etiqueta-campo", "Adjuntos"), etiquetaArchivo, archivo, existentes, nuevos,
        crearElemento("p", "ayuda-campo", "PDF o imagen, hasta 5 MB cada uno y 5 por actividad. Se suben al guardar y no se borran."));
    editores.ADJUNTOS = {
        elemento: campoAdjuntos,
        cargar: (lista) => {
            pendientes = [];
            nuevos.replaceChildren();
            existentes.replaceChildren(...lista.map((adjunto) => crearConIcono("li", "", "paperclip", adjunto.nombre)));
        },
    };

    for (const bloque of BLOQUES_INFORMACION.filter((b) => b.sugerencias)) {
        editores[bloque.clave] = crearListaDeValores(bloque);
    }

    const casillas = BLOQUES_INFORMACION.map((bloque) => {
        const opcion = crearElemento("label", "opcion-bloque");
        const casilla = crearElemento("input");
        casilla.type = "checkbox";
        casilla.value = bloque.clave;
        casilla.addEventListener("change", () => { editores[bloque.clave].elemento.hidden = !casilla.checked; });
        opcion.append(casilla, crearElemento("span", "", bloque.nombre));
        selector.append(opcion);
        campos.append(editores[bloque.clave].elemento);
        return casilla;
    });
    grupo.append(selector, campos);

    return {
        elemento: grupo,
        async cargar(actividad) {
            const informacion = actividad?.informacion || { bloques: [], adjuntos: [] };
            let sugerencias = {};
            try {
                const listas = await Promise.all(BLOQUES_INFORMACION.filter((b) => b.sugerencias)
                    .map((b) => pedirApi(`/catalogos/informacion/${b.sugerencias}`)));
                sugerencias = Object.fromEntries(BLOQUES_INFORMACION.filter((b) => b.sugerencias)
                    .map((b, indice) => [b.clave, listas[indice]]));
            } catch (error) {
                // Sin sugerencias el formulario sigue sirviendo: se escribe cada valor.
            }
            for (const [indice, bloque] of BLOQUES_INFORMACION.entries()) {
                casillas[indice].checked = informacion.bloques.includes(bloque.clave);
                editores[bloque.clave].elemento.hidden = !casillas[indice].checked;
                editores[bloque.clave].cargar(bloque.campo ? informacion[bloque.campo] || [] : informacion.adjuntos || [],
                    sugerencias[bloque.clave] || []);
            }
        },
        leer() {
            const informacion = { bloques: casillas.filter((c) => c.checked).map((c) => c.value) };
            for (const bloque of BLOQUES_INFORMACION.filter((b) => b.campo)) {
                informacion[bloque.campo] = informacion.bloques.includes(bloque.clave) ? editores[bloque.clave].leer() : [];
            }
            return informacion;
        },
        // Los archivos se suben después de guardar, porque necesitan el id de la actividad.
        archivosPorSubir: () => (casillas.at(-1).checked ? [...pendientes] : []),
        // Lo que ya subió sale de la lista: si otro archivo falla, al reintentar no se repite.
        quitarPendiente(subido) {
            pendientes = pendientes.filter((elegido) => elegido !== subido);
            nuevos.replaceChildren(...pendientes.map((elegido) => crearConIcono("li", "", "paperclip", elegido.name)));
        },
        validar(actividad) {
            const total = (actividad?.informacion?.adjuntos?.length || 0) + this.archivosPorSubir().length;
            if (total > MAXIMO_ADJUNTOS) {
                return `Una actividad puede tener como máximo ${MAXIMO_ADJUNTOS} adjuntos.`;
            }
            const pesado = this.archivosPorSubir().find((elegido) => elegido.size > TAMANO_MAXIMO_ADJUNTO);
            return pesado ? `"${pesado.name}" pesa más de 5 MB.` : null;
        },
    };
}

async function subirAdjuntos(actividadId, archivos, alSubir) {
    for (const archivo of archivos) {
        const datos = new FormData();
        datos.append("archivo", archivo, archivo.name);
        await pedirApi(`/actividades/${actividadId}/adjuntos`, { method: "POST", body: datos });
        alSubir(archivo);
    }
}

// Crea el diálogo una sola vez por página. "obtenerProyectos" y "obtenerOperarios" devuelven las
// listas vigentes; "alGuardar" se llama después de crear, editar o eliminar, para recargar la vista.
// Revisa en el navegador lo mínimo antes de enviar (el servidor vuelve a validar todo).
function validarDatosActividad(datos) {
    if (!datos.titulo.trim() || !datos.ubicacion.trim() || !datos.fecha_programada) {
        return "Completa título, ubicación y fecha.";
    }
    if ((Number(datos.horas) || 0) * 60 + (Number(datos.minutos) || 0) < 1) {
        return "Indica el tiempo estimado.";
    }
    return null;
}

function crearFormularioActividad({ obtenerProyectos, obtenerOperarios, alGuardar }) {
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

    const proyecto = crearSelector("act-proyecto", "proyecto_id", []);
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

    const editorInformacion = crearEditorInformacion();

    const grupoOperarios = crearElemento("fieldset", "grupo-campos");
    grupoOperarios.append(crearElemento("legend", "", "Operarios asignados"));
    const listaOperarios = crearElemento("div", "lista-opciones");
    grupoOperarios.append(listaOperarios);

    const mensaje = crearElemento("p", "mensaje-formulario");
    mensaje.setAttribute("role", "alert");
    mensaje.hidden = true;

    const acciones = crearElemento("div", "dialogo-acciones");
    const cancelar = crearElemento("button", "boton-secundario", "Cancelar");
    cancelar.type = "button";
    cancelar.dataset.cerrar = "";
    const guardar = crearElemento("button", "boton", "Guardar actividad");
    guardar.type = "submit";
    acciones.append(cancelar, guardar);

    formulario.append(
        crearCampo("Título", tituloActividad),
        crearCampo("Descripción de la actividad", descripcion),
        editorInformacion.elemento,
        fila(crearCampo("Categoría", categoria), crearCampo("Prioridad", prioridad)),
        crearCampo("Ubicación", ubicacion, "Línea, máquina o área donde se hace el trabajo."),
        fila(crearCampo("Fecha", fecha), crearCampo("Hora fija (opcional)", hora)),
        crearElemento("p", "ayuda-campo",
            "Sin hora, es de horario flexible: el operario decide cuándo hacerla. Con hora, se hace a esa hora y no se mueve."),
        fila(crearCampo("Estimado: horas", horas), crearCampo("Minutos", minutos)),
        crearCampo("Proyecto (opcional)", proyecto, "Sin proyecto, es una actividad independiente."),
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

        const ninguno = crearElemento("option", "", "Ninguno");
        ninguno.value = "";
        proyecto.replaceChildren(ninguno, ...obtenerProyectos().map((p) => {
            const opcion = crearElemento("option", "", p.nombre);
            opcion.value = p.id;
            return opcion;
        }));

        dialogo.showModal();    // Primero se abre: al cerrarse el diálogo anterior el formulario quedó en blanco.
        const origen = actividad || valores;
        proyecto.value = origen.proyecto_id || "";
        tituloActividad.value = origen.titulo || "";
        descripcion.value = origen.descripcion || "";
        categoria.value = origen.categoria || "OPERACION";
        prioridad.value = origen.prioridad || "MEDIA";
        ubicacion.value = origen.ubicacion || "";
        fecha.value = origen.fecha_programada || fechaTexto(new Date());
        hora.value = origen.hora_programada || "";
        const estimado = origen.tiempo_estimado_min || 60;
        horas.value = Math.floor(estimado / 60);
        minutos.value = estimado % 60;
        pintarOperarios(actividad ? actividad.operarios.map((o) => o.id) : (valores.operario_ids || []));
        editorInformacion.cargar(actividad);
        tituloActividad.focus();
    }

    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const validar = (datos) => validarDatosActividad(datos) || editorInformacion.validar(actividadEnEdicion);
        enviarFormularioDialogo(dialogo, validar, async (datos) => {
            const cuerpo = {
                proyecto_id: datos.proyecto_id || null,
                titulo: datos.titulo,
                descripcion: datos.descripcion,
                categoria: datos.categoria,
                prioridad: datos.prioridad,
                ubicacion: datos.ubicacion,
                fecha_programada: datos.fecha_programada,
                hora_programada: datos.hora_programada || null,
                tiempo_estimado_min: (Number(datos.horas) || 0) * 60 + (Number(datos.minutos) || 0),
                operario_ids: operariosMarcados(),
                informacion: editorInformacion.leer(),
            };
            const guardada = actividadEnEdicion
                ? await enviarJson(`/actividades/${actividadEnEdicion.id}`, "PUT", cuerpo)
                : await enviarJson("/actividades", "POST", cuerpo);
            // La actividad ya quedó guardada: si un archivo falla, se avisa y se puede subir al editarla.
            actividadEnEdicion = guardada;
            await subirAdjuntos(guardada.id, editorInformacion.archivosPorSubir(),
                (subido) => editorInformacion.quitarPendiente(subido));
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

    // Cancelar con motivo: la actividad no se borra, queda en el historial (alcance, Sección 5.1).
    async function abrirCancelar(actividad) {
        let motivo;
        try {
            motivo = await crearSelectorMotivo("/catalogos/motivos-cancelacion", "cancelar");
        } catch (error) {
            mostrarAviso(error.message, "advertencia");
            return;
        }
        abrirDialogoAccion({
            titulo: "Cancelar actividad",
            subtitulo: `${actividad.titulo} (${actividad.codigo})`,
            campos: [...motivo.campos, crearElemento("p", "ayuda-campo",
                "No se borra: sale del día de sus operarios y queda en el historial con su motivo.")],
            textoConfirmar: "Cancelar actividad",
            iconoConfirmar: "minus",
            textoCerrar: "Volver",
            alConfirmar: async () => {
                await enviarJson(`/actividades/${actividad.id}/cancelar`, "POST", motivo.leer());
                await alGuardar();
                mostrarAviso(`${actividad.codigo} cancelada.`);
            },
        });
    }

    // Primero la información (alcance, Sección 6.2): el detalle con el registro de cada operario. Las
    // acciones dependen del estado (alcance, Sección 5.1, reglas de estado de la actividad).
    function abrirDetalle(actividad) {
        const acciones = [];
        if (actividad.editable) {
            acciones.push({ texto: "Editar", clase: "boton-secundario", alHacer: async () => abrir(actividad) });
        }
        if (actividad.cancelable) {
            acciones.push({ texto: "Cancelar actividad", clase: "boton-secundario peligro", alHacer: () => abrirCancelar(actividad) });
        }
        let aviso = "";
        if (!actividad.editable && actividad.cancelable) {
            aviso = "Alguien ya inició esta actividad: no se edita ni se reasigna. Si el trabajo cambió, cancélala y crea una nueva.";
        } else if (!actividad.editable && actividad.estado_general === "EN_EJECUCION") {
            aviso = "Alguien la tiene en curso: mientras tanto no se edita, no se reasigna ni se cancela.";
        }
        abrirDetalleActividad(actividad, { acciones, aviso, extra: crearRegistrosDelEquipo(actividad) });
    }

    return {
        abrirNueva: (valores) => abrir(null, valores),
        abrirEdicion: (actividad) => abrir(actividad),
        abrirDetalle,
    };
}
