"""Repositorios del segundo bloque de la Etapa 4: proyectos, catálogos, y lo que cancelar y
devolver necesitan de actividades, asignaciones y ejecuciones. Usa la base en memoria de conftest."""
from app.models.proyecto import Proyecto
from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.catalogo_repository import CatalogoRepository, clave_de
from app.repositories.ejecucion_repository import EjecucionRepository
from app.repositories.proyecto_repository import ProyectoRepository

EMPRESA = "empresa-1"
OTRA_EMPRESA = "empresa-2"
PAUSA = "MOTIVO_PAUSA"
CANCELACION = "MOTIVO_CANCELACION"


def _actividad(repo, titulo, empresa_id=EMPRESA, **campos):
    documento = {
        "titulo": titulo, "empresa_id": empresa_id, "estado": "PENDIENTE",
        "tiempo_estimado_min": 60, "fecha_programada": "2026-10-10", **campos,
    }
    return repo.insert(documento)


def _titulos(documentos):
    return sorted(doc["titulo"] for doc in documentos)


# ---------- Proyectos ----------

def test_proyectos_de_la_empresa_ordenados_por_nombre(db):
    repo = ProyectoRepository(db)
    repo.insert(Proyecto("Montaje línea 3", EMPRESA).to_dict())
    repo.insert(Proyecto("Auditoría", EMPRESA).to_dict())
    repo.insert(Proyecto("De otra empresa", OTRA_EMPRESA).to_dict())

    assert [doc["nombre"] for doc in repo.find_by_empresa(EMPRESA)] == ["Auditoría", "Montaje línea 3"]


def test_proyecto_se_lee_y_se_actualiza_por_id(db):
    repo = ProyectoRepository(db)
    proyecto_id = repo.insert(Proyecto("Montaje", EMPRESA, descripcion="Fase 1").to_dict())

    assert repo.update(proyecto_id, {"nombre": "Montaje línea 3"})
    assert Proyecto.from_doc(repo.find_by_id(proyecto_id))["nombre"] == "Montaje línea 3"


# ---------- Catálogos ----------

def test_la_clave_ignora_espacios_sobrantes_y_mayusculas():
    assert clave_de("  Falta   Repuesto ") == "falta repuesto"


def test_catalogo_lista_en_orden_alfabetico(db):
    repo = CatalogoRepository(db)
    for valor in ("Zona bloqueada", "falta repuesto", "Árbol caído", "Cambio de plan"):
        repo.registrar(EMPRESA, PAUSA, valor)

    assert repo.listar(EMPRESA, PAUSA) == ["Árbol caído", "Cambio de plan", "falta repuesto", "Zona bloqueada"]


def test_catalogo_no_repite_un_valor_que_ya_existe(db):
    repo = CatalogoRepository(db)
    repo.registrar(EMPRESA, PAUSA, "Falta repuesto")
    repo.registrar(EMPRESA, PAUSA, "  falta   REPUESTO ")

    assert repo.listar(EMPRESA, PAUSA) == ["Falta repuesto"]    # Queda como se escribió primero.


def test_catalogo_separa_por_empresa_y_por_tipo(db):
    repo = CatalogoRepository(db)
    repo.registrar(EMPRESA, PAUSA, "Falta repuesto")
    repo.registrar(EMPRESA, CANCELACION, "Falta repuesto")
    repo.registrar(OTRA_EMPRESA, PAUSA, "Corte de luz")

    assert repo.listar(EMPRESA, PAUSA) == ["Falta repuesto"]
    assert repo.listar(EMPRESA, CANCELACION) == ["Falta repuesto"]
    assert repo.listar(OTRA_EMPRESA, PAUSA) == ["Corte de luz"]
    assert repo.listar(OTRA_EMPRESA, CANCELACION) == []


def test_catalogo_no_guarda_un_valor_vacio(db):
    repo = CatalogoRepository(db)
    repo.registrar(EMPRESA, PAUSA, "   ")
    repo.registrar(EMPRESA, PAUSA, None)

    assert repo.listar(EMPRESA, PAUSA) == []


def test_el_indice_unico_del_catalogo_existe(db):
    indice = db["catalogos"].index_information()["valor_unico"]

    assert indice["unique"] is True
    assert [campo for campo, _ in indice["key"]] == ["empresa_id", "tipo", "clave"]


# ---------- Actividades ----------

def test_buscar_por_proyecto_y_independientes(db):
    repo = ActividadRepository(db)
    _actividad(repo, "Del proyecto A", proyecto_id="A")
    _actividad(repo, "Del proyecto B", proyecto_id="B")
    _actividad(repo, "Independiente con None", proyecto_id=None)
    _actividad(repo, "Independiente sin el campo")
    _actividad(repo, "De otra empresa", empresa_id=OTRA_EMPRESA, proyecto_id="A")

    assert _titulos(repo.buscar(EMPRESA, proyecto_id="A")) == ["Del proyecto A"]
    assert _titulos(repo.buscar(EMPRESA, independientes=True)) == ["Independiente con None", "Independiente sin el campo"]
    assert len(repo.buscar(EMPRESA)) == 4


def test_buscar_conserva_los_filtros_anteriores(db):
    repo = ActividadRepository(db)
    _actividad(repo, "Con requerimiento", requerimiento_id="R1", proyecto_id="A")
    _actividad(repo, "Otra", requerimiento_id="R2", proyecto_id="A", estado="COMPLETADA")

    assert _titulos(repo.buscar(EMPRESA, "R1")) == ["Con requerimiento"]
    assert _titulos(repo.buscar(EMPRESA, proyecto_id="A", estados=["COMPLETADA"])) == ["Otra"]


def test_find_by_proyectos_trae_solo_los_campos_del_avance(db):
    repo = ActividadRepository(db)
    _actividad(repo, "Hecha", proyecto_id="A", estado="COMPLETADA", tiempo_estimado_min=120)
    _actividad(repo, "Por hacer", proyecto_id="A", tiempo_estimado_min=60)
    _actividad(repo, "Cancelada", proyecto_id="A", estado="CANCELADA", tiempo_estimado_min=30)
    _actividad(repo, "De B", proyecto_id="B")
    _actividad(repo, "De C", proyecto_id="C")
    _actividad(repo, "Independiente")
    _actividad(repo, "De otra empresa", empresa_id=OTRA_EMPRESA, proyecto_id="A")

    documentos = repo.find_by_proyectos(EMPRESA, ["A", "B"])

    assert len(documentos) == 4
    assert all(set(doc) == {"_id", "proyecto_id", "estado", "tiempo_estimado_min"} for doc in documentos)
    avance = Proyecto.calcular_avance([doc for doc in documentos if doc["proyecto_id"] == "A"])
    assert avance == {"minutos_finalizados": 120, "minutos_totales": 180, "porcentaje": 67, "actividades": 2}
    assert repo.find_by_proyectos(EMPRESA, []) == []


def test_guardar_actividad_solo_si_sigue_en_el_estado_esperado(db):
    repo = ActividadRepository(db)
    actividad_id = _actividad(repo, "Calibrar", estado="PAUSADA")
    cancelada = {"estado": "CANCELADA", "cancelacion": {"motivo": "Ya no se necesita"}}

    assert repo.guardar(actividad_id, cancelada, estado_esperado="ASIGNADA") is False
    assert repo.find_by_id(actividad_id)["estado"] == "PAUSADA"

    assert repo.guardar(actividad_id, cancelada, estado_esperado="PAUSADA") is True
    guardada = repo.find_by_id(actividad_id)
    assert guardada["estado"] == "CANCELADA"
    assert guardada["cancelacion"] == {"motivo": "Ya no se necesita"}
    assert guardada["titulo"] == "Calibrar"

    assert repo.guardar(actividad_id, {"titulo": "Sin condición"}) is True
    assert repo.guardar("no-es-un-id", cancelada) is False


def test_el_indice_por_proyecto_existe(db):
    indice = db["actividades"].index_information()["empresa_proyecto"]

    assert [campo for campo, _ in indice["key"]] == ["empresa_id", "proyecto_id"]


# ---------- Asignaciones ----------

def _asignacion(actividad_id, usuario_id, estado="ACTIVA", **campos):
    return {"actividad_id": actividad_id, "usuario_id": usuario_id, "estado": estado, **campos}


def test_insertar_activa_rechaza_la_repetida(db):
    repo = AsignacionRepository(db)

    assert repo.insertar_activa(_asignacion("act-1", "ana")) is not None
    assert repo.insertar_activa(_asignacion("act-1", "ana")) is None
    assert repo.insertar_activa(_asignacion("act-1", "luis")) is not None
    assert repo.contar_activas("act-1") == 2


def test_se_puede_volver_a_asignar_despues_de_una_devolucion(db):
    repo = AsignacionRepository(db)
    devolucion = {"motivo": "Falta información", "fecha": "2026-10-10T08:00:00"}
    repo.insert(_asignacion("act-1", "ana", estado="DEVUELTA", devolucion=devolucion))

    assert repo.insertar_activa(_asignacion("act-1", "ana")) is not None


def test_el_historial_trae_las_cerradas_con_su_devolucion(db):
    repo = AsignacionRepository(db)
    devolucion = {"motivo": "Falta información", "fecha": "2026-10-10T08:00:00"}
    repo.insert(_asignacion("act-1", "ana", estado="DEVUELTA", devolucion=devolucion, fecha_fin="f"))
    repo.insert(_asignacion("act-1", "luis", estado="RETIRADA", retirada_por_id="marta"))
    repo.insert(_asignacion("act-1", "sara"))
    repo.insert(_asignacion("act-2", "ana"))

    historial = {doc["usuario_id"]: doc for doc in repo.find_by_actividad("act-1", incluir_historial=True)}

    assert set(historial) == {"ana", "luis", "sara"}
    assert historial["ana"]["devolucion"] == devolucion
    assert historial["ana"]["fecha_fin"] == "f"
    assert historial["luis"]["retirada_por_id"] == "marta"
    assert [doc["usuario_id"] for doc in repo.find_by_actividad("act-1")] == ["sara"]


def test_contar_activas_no_cuenta_las_cerradas(db):
    repo = AsignacionRepository(db)
    repo.insert(_asignacion("act-1", "ana", estado="DEVUELTA"))
    repo.insert(_asignacion("act-1", "luis"))
    repo.insert({"actividad_id": "act-1", "usuario_id": "sara"})    # Anterior a la regla: sin estado.
    repo.insert(_asignacion("act-2", "ana"))

    assert repo.contar_activas("act-1") == 2
    assert repo.contar_activas("act-sin-nadie") == 0


# ---------- Ejecuciones ----------

def test_abiertas_de_actividad_son_las_en_curso_y_las_pausadas(db):
    repo = EjecucionRepository(db)
    for numero, (usuario, estado, actividad) in enumerate([
        ("ana", "PAUSADA", "act-1"), ("luis", "EN_PROGRESO", "act-1"),
        ("sara", "FINALIZADA", "act-1"), ("juan", "CERRADA", "act-1"), ("eva", "PAUSADA", "act-2"),
    ]):
        repo.insert({
            "actividad_id": actividad, "usuario_id": usuario, "estado": estado,
            "asignacion_id": f"asig-{numero}",
        })

    abiertas = repo.find_abiertas_de_actividad("act-1")

    assert sorted(doc["usuario_id"] for doc in abiertas) == ["ana", "luis"]
