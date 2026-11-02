"""Datos de ejemplo: varias semanas de historia para una empresa de prueba, para que Indicadores y sus
gráficas tengan qué mostrar en una presentación.

No escribe en la base de datos por su cuenta: simula el uso real con los mismos servicios de la
aplicación y un reloj que avanza día por día por las semanas pasadas. Así todo respeta las reglas del
alcance: el Administrador crea y asigna actividades; cada operario marca su entrada (a veces tarde),
las inicia, las pausa con su motivo, las finaliza (a veces se pasa del estimado), devuelve alguna antes
de iniciarla, a veces no viene o no termina, y marca su salida; el cierre de jornada reprograma lo que
quedó; y el Administrador valida casi toda la asistencia.

Solo para la base de prueba. Los días que ya tienen marcas de asistencia se saltan. Las actividades
creadas llevan "Datos de ejemplo" en su descripción.

La conexión es la misma de la aplicación: MONGO_URI y MONGO_DB_NAME del entorno. Como la imagen de Docker
no incluye herramientas/, se copia al contenedor y se ejecuta ahí:
    docker cp herramientas/datos_de_ejemplo.py gestlab-prueba-app-1:/tmp/
    docker exec -e PYTHONPATH=/app gestlab-prueba-app-1 python /tmp/datos_de_ejemplo.py --correo laura@... [--aplicar]
"""
import argparse
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from bson import ObjectId
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config  # noqa: E402
from app.models.enums import MOTIVOS_DEVOLUCION, Rol  # noqa: E402
from app.services.composicion import construir_servicios  # noqa: E402
from app.utils.errors import ErrorApi  # noqa: E402
from app.utils.reloj import ZONA_POR_DEFECTO, momento_local  # noqa: E402

TITULOS = {
    "OPERACION": ["Tostar el lote", "Moler el lote", "Empacar café molido de 500 g", "Empacar café en grano de 1 kg",
                  "Etiquetar el lote", "Limpiar la tostadora", "Lubricar el molino", "Calibrar la selladora"],
    "REVISION": ["Revisar la báscula de despacho", "Registrar la curva de tueste", "Revisar el tamiz del molino",
                 "Revisar el extintor de la zona", "Inspeccionar los empaques recibidos"],
    "TRASLADO": ["Despachar el pedido", "Cargar el camión", "Ordenar la bodega de insumos", "Almacenar los sacos"],
    "ATENCION": ["Atender la visita del cliente", "Resolver el reclamo del pedido", "Mostrar la planta a proveedores"],
    "ADMINISTRATIVA": ["Actualizar el inventario", "Registrar las entregas del día", "Preparar el informe de producción"],
}
CATEGORIAS = list(TITULOS)
PESOS_CATEGORIA = [5, 2, 2, 1, 1]
PAUSAS = [("Actividad urgente", None), ("Otro", "Falta de material"), ("Otro", "Reunión de equipo"),
          ("Otro", "Esperando aprobación de calidad")]
TURNO_POR_DEFECTO = ("08:00", "16:00")


class Reloj:
    """La hora que los servicios creen que es. El script la mueve a cada evento."""

    def __init__(self):
        self.ahora = datetime.now(timezone.utc)

    def __call__(self):
        return self.ahora


def sesion(usuario: dict) -> dict:
    """La forma del usuario en la sesión (la que reciben los servicios como "solicitante")."""
    return {"id": str(usuario["_id"]), "nombre": usuario["nombre"], "rol": usuario["rol"],
            "empresa_id": usuario["empresa_id"]}


def dias_laborales(desde: date, hasta: date):
    dia = desde
    while dia <= hasta:
        if dia.weekday() < 5:
            yield dia
        dia += timedelta(days=1)


class Simulacion:
    def __init__(self, db, admin, operarios, zona, azar):
        self.reloj = Reloj()
        self.servicios = construir_servicios(db, reloj=self.reloj)
        self.admin, self.operarios, self.zona, self.azar = admin, operarios, zona, azar
        self.cuenta = {"actividades": 0, "finalizadas": 0, "pausas": 0, "devueltas": 0, "reasignadas": 0, "canceladas": 0,
                       "ausencias": 0, "asistencias": 0, "validadas": 0, "errores": 0}

    def a_las(self, fecha: str, hora: str, minutos: int = 0):
        return momento_local(fecha, hora, self.zona) + timedelta(minutes=minutos)

    def turno(self, operario, fecha: str) -> tuple:
        turno = self.servicios.turnos.turno_de(operario["id"], fecha)
        return (turno.hora_inicio, turno.hora_fin) if turno else TURNO_POR_DEFECTO

    def intentar(self, accion, *argumentos):
        """Un paso de la simulación. Si una regla lo impide (por ejemplo, ya había marcas ese día), se cuenta y sigue."""
        try:
            return accion(*argumentos)
        except ErrorApi:
            self.cuenta["errores"] += 1
            return None

    # ---------- Lo que hace el Administrador ----------

    def planear(self, fecha: str):
        self.reloj.ahora = self.a_las(fecha, "05:00")
        # Lo que devolvieron ayer se le pasa a otra persona para hoy (Hoy, Pendientes, "Sin dueño").
        sin_dueno = self.intentar(self.servicios.actividades.listar_actividades,
                                  {"sin_asignar": True, "fecha_hasta": fecha}, self.admin) or []
        for actividad in sin_dueno:
            if "Datos de ejemplo" in (actividad.get("descripcion") or ""):
                if self.intentar(self.servicios.actividades.actualizar_actividad, actividad["id"],
                                 {"operario_ids": [self.azar.choice(self.operarios)["id"]], "fecha_programada": fecha},
                                 self.admin):
                    self.cuenta["reasignadas"] += 1
        for operario in self.operarios:
            # Como haría un Administrador cuidadoso: entre el 65 % y el 95 % de la capacidad de su turno,
            # contando lo que ya trae (lo reprogramado de días anteriores).
            capacidad = self.servicios.turnos.capacidad_de(operario["id"], fecha)
            meta = capacidad * self.azar.uniform(0.65, 0.95)
            carga = self.servicios.carga.carga_por_jornada(self.admin["empresa_id"], fecha, fecha, [operario["id"]])
            asignado = sum(j["minutos"] for o in carga["operarios"] for j in o["jornadas"])
            while asignado < meta:
                categoria = self.azar.choices(CATEGORIAS, PESOS_CATEGORIA)[0]
                datos = {
                    "titulo": f"{self.azar.choice(TITULOS[categoria])} {self.azar.randint(100, 199)}"
                    if categoria == "OPERACION" else self.azar.choice(TITULOS[categoria]),
                    "descripcion": "Datos de ejemplo.",
                    "categoria": categoria,
                    "ubicacion": self.azar.choice(["Línea 1", "Línea 2", "Bodega", "Laboratorio", "Muelle de carga"]),
                    "prioridad": self.azar.choices(["BAJA", "MEDIA", "ALTA", "URGENTE"], [2, 5, 3, 0.4])[0],
                    "tiempo_estimado_min": self.azar.choice([30, 45, 60, 90, 120]),
                    "fecha_programada": fecha,
                    "operario_ids": [operario["id"]],
                }
                asignado += datos["tiempo_estimado_min"]
                actividad = self.intentar(self.servicios.actividades.crear_actividad, datos, self.admin)
                if actividad:
                    self.cuenta["actividades"] += 1
                    if self.azar.random() < 0.02:      # El trabajo ya no hace falta: se cancela con su motivo.
                        if self.intentar(self.servicios.actividades.cancelar, actividad["id"], self.admin,
                                         "Otro", "El pedido se anuló"):
                            self.cuenta["canceladas"] += 1

    def validar(self, asistencia_id: str, fecha: str):
        self.reloj.ahora = self.a_las(fecha, "23:59", 10 * 60)      # A la mañana siguiente.
        if self.intentar(self.servicios.asistencia.validar, self.admin, asistencia_id):
            self.cuenta["validadas"] += 1

    # ---------- La jornada de un operario ----------

    def jornada(self, operario, fecha: str):
        inicio, fin = self.turno(operario, fecha)
        if self.azar.random() < 0.05:                   # No vino: el cierre de jornada reprograma su trabajo.
            self.cuenta["ausencias"] += 1
            return
        self.reloj.ahora = self.a_las(fecha, inicio, self.azar.choice([-10, -5, 0, 3, 8, 25]))
        if not self.intentar(self.servicios.asistencia.marcar_entrada, operario):
            return
        self.cuenta["asistencias"] += 1
        fin_turno = self.a_las(fecha, fin) if fin > inicio else self.a_las(fecha, fin, 24 * 60)
        suyas = self.intentar(self.servicios.actividades.listar_actividades,
                              {"fecha_desde": fecha, "fecha_hasta": fecha}, operario) or []
        por_hacer = [a for a in suyas if a["estado"] in ("ASIGNADA", "PAUSADA")]
        por_hacer.sort(key=lambda a: -a["peso_prioridad"])
        for actividad in por_hacer:
            if self.reloj.ahora >= fin_turno - timedelta(minutes=20):
                break
            if actividad["estado"] == "ASIGNADA" and self.azar.random() < 0.03:
                if self.intentar(self.servicios.ejecucion.devolver, actividad["id"], operario,
                                 self.azar.choice(MOTIVOS_DEVOLUCION)):
                    self.cuenta["devueltas"] += 1
                continue
            self.ejecutar(operario, actividad, fin_turno)
        self.reloj.ahora = max(self.reloj.ahora + timedelta(minutes=5),
                               fin_turno + timedelta(minutes=self.azar.choice([-45, 0, 0, 5, 10, 30])))
        salida = self.intentar(self.servicios.asistencia.marcar_salida, operario)
        if salida and self.azar.random() < 0.85:
            self.validar(salida["id"], fecha)

    def ejecutar(self, operario, actividad, fin_turno):
        accion = self.servicios.ejecucion.reanudar if actividad["estado"] == "PAUSADA" else self.servicios.ejecucion.iniciar
        if not self.intentar(accion, actividad["id"], operario):
            return
        trabajo = round(actividad["tiempo_estimado_min"] * self.azar.uniform(0.7, 1.4))
        if self.azar.random() < 0.25:                   # Una pausa con su motivo en medio.
            self.reloj.ahora += timedelta(minutes=trabajo // 2)
            motivo, detalle = self.azar.choice(PAUSAS)
            if self.intentar(self.servicios.ejecucion.pausar, actividad["id"], operario, motivo, detalle):
                self.cuenta["pausas"] += 1
                self.reloj.ahora += timedelta(minutes=self.azar.randint(10, 40))
                self.intentar(self.servicios.ejecucion.reanudar, actividad["id"], operario)
            trabajo -= trabajo // 2
        if self.reloj.ahora + timedelta(minutes=trabajo) > fin_turno:
            # No alcanza a terminarla: la pausa con "Fin de jornada" y el cierre la reprograma.
            self.reloj.ahora = fin_turno - timedelta(minutes=5)
            self.intentar(self.servicios.ejecucion.pausar, actividad["id"], operario, "Fin de jornada")
            return
        self.reloj.ahora += timedelta(minutes=trabajo)
        if self.intentar(self.servicios.ejecucion.finalizar, actividad["id"], operario, None):
            self.cuenta["finalizadas"] += 1
        self.reloj.ahora += timedelta(minutes=self.azar.randint(3, 15))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--correo", required=True, help="Correo del Administrador de la empresa de prueba.")
    parser.add_argument("--semanas", type=int, default=8, help="Semanas de historia antes de la actual (por defecto 8).")
    parser.add_argument("--semilla", type=int, default=2026, help="Semilla del azar: la misma da los mismos datos.")
    parser.add_argument("--aplicar", action="store_true", help="Escribir. Sin esto solo muestra lo que haría.")
    argumentos = parser.parse_args()

    db = MongoClient(Config.MONGO_URI)[Config.MONGO_DB_NAME]
    admin = db.usuarios.find_one({"correo": argumentos.correo, "rol": Rol.ADMINISTRADOR.value})
    if not admin:
        sys.exit(f"No hay un Administrador con el correo {argumentos.correo}.")
    empresa = db.empresas.find_one({"_id": ObjectId(admin["empresa_id"])}) or {}
    operarios = [sesion(o) for o in db.usuarios.find(
        {"empresa_id": admin["empresa_id"], "rol": Rol.OPERARIO.value, "activo": {"$ne": False}}).sort("nombre", 1)]
    hoy = datetime.now(timezone.utc).date()
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    desde = lunes_actual - timedelta(weeks=argumentos.semanas)
    hasta = lunes_actual - timedelta(days=1)
    dias = list(dias_laborales(desde, hasta))
    print(f"Empresa: {empresa.get('nombre')}. Administrador: {admin['nombre']}. Operarios: {len(operarios)}.")
    print(f"Historia: {len(dias)} días laborales, del {desde} al {hasta} (unas {len(dias) * len(operarios) * 3} actividades).")
    if not argumentos.aplicar:
        print("Solo se mostró lo que haría. Para escribir, agrega --aplicar.")
        return

    simulacion = Simulacion(db, sesion(admin), operarios, empresa.get("zona_horaria") or ZONA_POR_DEFECTO,
                            random.Random(argumentos.semilla))
    for numero, dia in enumerate(dias, start=1):
        fecha = dia.isoformat()
        simulacion.planear(fecha)
        for operario in operarios:
            simulacion.jornada(operario, fecha)
        if numero % 5 == 0:
            print(f"  Hasta el {fecha}: {simulacion.cuenta}")
    # Un último paso con la hora real cierra las jornadas que quedaron abiertas.
    simulacion.reloj.ahora = datetime.now(timezone.utc)
    simulacion.servicios.cierre_jornada.cerrar_pendientes(admin["empresa_id"])
    print(f"Listo: {simulacion.cuenta}")


if __name__ == "__main__":
    main()
