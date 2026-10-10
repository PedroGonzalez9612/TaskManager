"""Pruebas de los proyectos y de las actividades independientes (alcance, Sección 5.1)."""
import pytest

from app.utils.errors import NotFoundError, ValidationError

DATOS_ACTIVIDAD = {
    "titulo": "Montar la banda", "ubicacion": "Línea 1", "categoria": "PRODUCCION",
    "tiempo_estimado_min": 60, "fecha_programada": "2026-10-10",
}


def crear_proyecto(servicios, empresa, nombre="Montaje de la línea 3", **campos):
    return servicios.proyectos.crear_proyecto({"nombre": nombre, **campos}, empresa.admin)


def crear_en(servicios, empresa, proyecto=None, **campos):
    """Crea una actividad sin requerimiento: de ese proyecto, o independiente si no se indica."""
    datos = {**DATOS_ACTIVIDAD, **campos}
    if proyecto:
        datos["proyecto_id"] = proyecto["id"]
    return servicios.actividades.crear_actividad(datos, empresa.admin)


# ---------- Proyectos ----------

def test_crear_un_proyecto_exige_nombre(servicios, empresa):
    for nombre in (None, "", "   "):
        with pytest.raises(ValidationError):
            servicios.proyectos.crear_proyecto({"nombre": nombre}, empresa.admin)
    assert servicios.proyectos.listar_proyectos(empresa.admin) == []


def test_el_servidor_pone_el_autor_y_la_fecha(servicios, empresa, reloj):
    datos = {"nombre": "  Montaje  ", "creado_por_id": "otro", "fecha_creacion": "2000-01-01", "empresa_id": "x"}
    proyecto = servicios.proyectos.crear_proyecto(datos, empresa.admin)

    assert proyecto["nombre"] == "Montaje"
    assert proyecto["descripcion"] == ""
    assert proyecto["empresa_id"] == empresa.id
    assert proyecto["creado_por_id"] == empresa.admin["id"]
    assert proyecto["fecha_creacion"] == reloj.ahora.replace(tzinfo=None)    # Mongo guarda las fechas sin zona.
    assert proyecto["avance"] == {"minutos_finalizados": 0, "minutos_totales": 0, "porcentaje": 0, "actividades": 0}
    assert proyecto["actividades"] == []


def test_editar_un_proyecto(servicios, empresa):
    proyecto = crear_proyecto(servicios, empresa, descripcion="Primera versión")

    editado = servicios.proyectos.actualizar_proyecto(proyecto["id"], {"nombre": "Montaje línea 4"}, empresa.admin)
    assert (editado["nombre"], editado["descripcion"]) == ("Montaje línea 4", "Primera versión")

    with pytest.raises(ValidationError):
        servicios.proyectos.actualizar_proyecto(proyecto["id"], {"nombre": " "}, empresa.admin)
    with pytest.raises(ValidationError):
        servicios.proyectos.actualizar_proyecto(proyecto["id"], {}, empresa.admin)


def test_un_proyecto_de_otra_empresa_no_existe(servicios, empresa, otra_empresa):
    proyecto = crear_proyecto(servicios, empresa)

    with pytest.raises(NotFoundError):
        servicios.proyectos.obtener_proyecto(proyecto["id"], otra_empresa.admin)
    with pytest.raises(NotFoundError):
        servicios.proyectos.actualizar_proyecto(proyecto["id"], {"nombre": "Ajeno"}, otra_empresa.admin)
    with pytest.raises(NotFoundError):
        servicios.proyectos.obtener_proyecto("no-es-un-id", empresa.admin)
    assert servicios.proyectos.listar_proyectos(otra_empresa.admin) == []


def test_rutas_de_proyectos_solo_para_el_administrador(cliente_de, empresa, otra_empresa):
    admin = cliente_de(empresa.admin)
    creado = admin.post("/proyectos", json={"nombre": "Montaje", "descripcion": "Línea 3"})
    assert creado.status_code == 201
    ruta = f"/proyectos/{creado.get_json()['id']}"

    assert admin.post("/proyectos", json={}).status_code == 400
    assert [p["nombre"] for p in admin.get("/proyectos").get_json()] == ["Montaje"]
    assert admin.get(ruta).get_json()["avance"]["minutos_totales"] == 0
    assert admin.put(ruta, json={"nombre": "Montaje 2"}).get_json()["nombre"] == "Montaje 2"

    assert cliente_de().get("/proyectos").status_code == 401
    operario = cliente_de(empresa.ana)
    assert operario.post("/proyectos", json={"nombre": "No puedo"}).status_code == 403
    assert operario.get("/proyectos").status_code == 403
    assert operario.get(ruta).status_code == 403
    assert operario.put(ruta, json={"nombre": "No puedo"}).status_code == 403
    assert cliente_de(otra_empresa.admin).get(ruta).status_code == 404
    assert cliente_de(otra_empresa.admin).put(ruta, json={"nombre": "Ajeno"}).status_code == 404


# ---------- Actividades independientes y de proyecto ----------

def test_una_actividad_sin_proyecto_ni_requerimiento_es_independiente(servicios, empresa):
    independiente = crear_en(servicios, empresa)

    assert independiente["proyecto_id"] is None
    assert independiente["requerimiento_id"] is None
    assert independiente["fecha_original"] == independiente["fecha_programada"] == "2026-10-10"
    assert independiente["reprogramada"] is False


def test_crear_una_actividad_de_proyecto_y_cambiarla_de_proyecto(servicios, empresa):
    proyecto = crear_proyecto(servicios, empresa)
    actividad = crear_en(servicios, empresa, proyecto)
    assert actividad["proyecto_id"] == proyecto["id"]

    editar = servicios.actividades.actualizar_actividad
    assert editar(actividad["id"], {"proyecto_id": None}, empresa.admin)["proyecto_id"] is None
    assert editar(actividad["id"], {"proyecto_id": proyecto["id"]}, empresa.admin)["proyecto_id"] == proyecto["id"]
    # Editar otro campo no la saca del proyecto.
    assert editar(actividad["id"], {"titulo": "Otro título"}, empresa.admin)["proyecto_id"] == proyecto["id"]


def test_el_requerimiento_sigue_funcionando_y_convive_con_el_proyecto(servicios, empresa, crear_actividad):
    """La interfaz actual sigue creando actividades con requerimiento_id."""
    proyecto = crear_proyecto(servicios, empresa)
    assert crear_actividad([])["requerimiento_id"] == empresa.requerimiento_id

    con_los_dos = crear_actividad([], proyecto_id=proyecto["id"])
    assert con_los_dos["requerimiento_id"] == empresa.requerimiento_id
    assert con_los_dos["proyecto_id"] == proyecto["id"]


def test_no_se_acepta_el_proyecto_de_otra_empresa(servicios, repos, empresa, otra_empresa):
    ajeno = crear_proyecto(servicios, otra_empresa, "Proyecto ajeno")
    propia = crear_en(servicios, empresa)

    with pytest.raises(ValidationError):
        crear_en(servicios, empresa, ajeno)
    with pytest.raises(ValidationError):
        crear_en(servicios, empresa, {"id": "no-es-un-id"})
    with pytest.raises(ValidationError):
        servicios.actividades.actualizar_actividad(propia["id"], {"proyecto_id": ajeno["id"]}, empresa.admin)

    assert repos.actividades.find_by_id(propia["id"])["proyecto_id"] is None
    assert len(servicios.actividades.listar_actividades({}, empresa.admin)) == 1


def test_listar_las_independientes_y_las_de_un_proyecto(servicios, cliente_de, empresa, crear_actividad):
    proyecto = crear_proyecto(servicios, empresa)
    otro = crear_proyecto(servicios, empresa, "Otro proyecto")
    crear_en(servicios, empresa, proyecto, titulo="Del proyecto")
    crear_en(servicios, empresa, otro, titulo="Del otro proyecto")
    crear_en(servicios, empresa, titulo="Independiente")
    crear_actividad([], titulo="Con requerimiento")    # Lo que antes era un requerimiento es una independiente.

    def titulos(filtros):
        return sorted(a["titulo"] for a in servicios.actividades.listar_actividades(filtros, empresa.admin))

    assert titulos({"proyecto_id": proyecto["id"]}) == ["Del proyecto"]
    assert titulos({"independientes": True}) == ["Con requerimiento", "Independiente"]
    assert len(titulos({})) == 4

    admin = cliente_de(empresa.admin)
    assert [a["titulo"] for a in admin.get(f"/actividades?proyecto_id={proyecto['id']}").get_json()] == ["Del proyecto"]
    assert sorted(a["titulo"] for a in admin.get("/actividades?independientes=1").get_json()) == ["Con requerimiento", "Independiente"]
    assert len(admin.get("/actividades").get_json()) == 4


# ---------- Avance ----------

def test_el_avance_se_mide_en_horas_sin_las_canceladas_y_con_las_no_realizadas(
        servicios, repos, empresa):
    proyecto = crear_proyecto(servicios, empresa)
    vacio = crear_proyecto(servicios, empresa, "Sin actividades")
    hecha = crear_en(servicios, empresa, proyecto, titulo="Hecha", tiempo_estimado_min=120, operario_ids=[empresa.ana["id"]])
    crear_en(servicios, empresa, proyecto, titulo="Por hacer", tiempo_estimado_min=60)
    cancelada = crear_en(servicios, empresa, proyecto, titulo="Cancelada", tiempo_estimado_min=300)
    no_realizada = crear_en(servicios, empresa, proyecto, titulo="No realizada", tiempo_estimado_min=60,
                            hora_programada="09:00")
    crear_en(servicios, empresa, titulo="Independiente", tiempo_estimado_min=500)    # No es del proyecto.

    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)
    servicios.actividades.cancelar(cancelada["id"], empresa.admin, "Otro", "Ya no hace falta")
    # "No realizada" se construye en un paso posterior: aquí el estado se pone directamente.
    repos.actividades.update(no_realizada["id"], {"estado": "NO_REALIZADA"})

    # 120 finalizados de 240 (120 + 60 + 60): la cancelada (300) sale del total.
    esperado = {"minutos_finalizados": 120, "minutos_totales": 240, "porcentaje": 50, "actividades": 3}
    detalle = servicios.proyectos.obtener_proyecto(proyecto["id"], empresa.admin)
    assert detalle["avance"] == esperado
    # El detalle sí muestra la cancelada: no se borra, solo deja de contar.
    assert sorted(a["titulo"] for a in detalle["actividades"]) == ["Cancelada", "Hecha", "No realizada", "Por hacer"]
    assert "operarios" in detalle["actividades"][0]    # La misma forma de GET /actividades.

    avances = {p["nombre"]: p["avance"] for p in servicios.proyectos.listar_proyectos(empresa.admin)}
    assert avances[proyecto["nombre"]] == esperado
    assert avances[vacio["nombre"]] == {
        "minutos_finalizados": 0, "minutos_totales": 0, "porcentaje": 0, "actividades": 0,
    }


def test_listar_proyectos_trae_las_actividades_en_una_sola_consulta(servicios, repos, empresa, monkeypatch):
    for nombre in ("Uno", "Dos", "Tres"):
        crear_en(servicios, empresa, crear_proyecto(servicios, empresa, nombre))

    llamadas = []
    original = repos.actividades.find_by_proyectos.__func__

    def contar(self, empresa_id, proyecto_ids):
        llamadas.append(proyecto_ids)
        return original(self, empresa_id, proyecto_ids)

    monkeypatch.setattr(type(repos.actividades), "find_by_proyectos", contar)
    proyectos = servicios.proyectos.listar_proyectos(empresa.admin)

    assert len(llamadas) == 1
    assert len(llamadas[0]) == 3
    assert [p["avance"]["minutos_totales"] for p in proyectos] == [60, 60, 60]
