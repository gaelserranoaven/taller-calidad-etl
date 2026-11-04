# tests/test_reportes.py
import sqlite3
import pytest
from etl.reportes import buscar_cliente, evaluar_regla, obtener_password, total


@pytest.fixture
def conexion():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, email TEXT)")
    con.executemany("INSERT INTO clientes VALUES (?, ?)",
                    [(1, "ana@mail.com"), (2, "luis@mail.com")])
    con.commit()
    yield con
    con.close()


# ---------- contraseña por variable de entorno ----------

def test_obtener_password_lee_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "valor-de-prueba")
    assert obtener_password() == "valor-de-prueba"


def test_obtener_password_sin_variable_falla_con_mensaje_claro(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="DB_PASSWORD"):
        obtener_password()


# ---------- buscar_cliente (SQL parametrizado) ----------

def test_buscar_cliente_encuentra_coincidencia_exacta(conexion):
    assert buscar_cliente(conexion, "ana@mail.com") == [(1, "ana@mail.com")]


def test_buscar_cliente_sin_coincidencias(conexion):
    assert buscar_cliente(conexion, "nadie@mail.com") == []


@pytest.mark.parametrize("ataque", [
    "' OR '1'='1",
    "x' OR 1=1 --",
    "'; DROP TABLE clientes; --",
])
def test_buscar_cliente_resiste_inyeccion_sql(conexion, ataque):
    assert buscar_cliente(conexion, ataque) == []
    # La tabla sigue intacta tras el intento de ataque.
    assert conexion.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 2


# ---------- evaluar_regla (sin eval) ----------

@pytest.mark.parametrize("regla, fila, esperado", [
    ("monto > 100", {"monto": 150}, True),
    ("monto > 100", {"monto": 50}, False),
    ("monto >= 100 and id < 5", {"monto": 100, "id": 3}, True),
    ("monto >= 100 and id < 5", {"monto": 100, "id": 9}, False),
    ("monto < 10 or id == 1", {"monto": 500, "id": 1}, True),
    ("not (monto > 10)", {"monto": 5}, True),
    ("0 < monto <= 100", {"monto": 50}, True),
    ("0 < monto <= 100", {"monto": 500}, False),
    ("monto * 2 - 1 == 9", {"monto": 5}, True),
    ("-monto < 0", {"monto": 3}, True),
    ("monto / 2 == 2.5", {"monto": 5}, True),
    ("estado == 'activo'", {"estado": "activo"}, True),
    ("estado != 'activo'", {"estado": "activo"}, False),
])
def test_evaluar_regla_validas(regla, fila, esperado):
    assert evaluar_regla(regla, fila) is esperado


@pytest.mark.parametrize("regla", [
    "__import__('os').system('echo hack')",   # llamada a función
    "monto.real > 1",                         # acceso a atributos
    "[x for x in range(3)]",                  # comprensión
    "monto ** 2 > 1",                         # operador no permitido
    "monto in (1, 2)",                        # comparador no permitido
    "lambda: 1",                              # lambda
])
def test_evaluar_regla_rechaza_construcciones_peligrosas(regla):
    with pytest.raises(ValueError):
        evaluar_regla(regla, {"monto": 1})


def test_evaluar_regla_campo_desconocido():
    with pytest.raises(ValueError, match="campo desconocido: precio"):
        evaluar_regla("precio > 1", {"monto": 1})


def test_evaluar_regla_sintaxis_invalida():
    with pytest.raises(ValueError, match="regla inválida"):
        evaluar_regla("monto >", {"monto": 1})


# ---------- total (excepción específica) ----------

def test_total_suma_la_segunda_columna():
    assert total([(1, 10), (2, 5.5)]) == 15.5


def test_total_de_lista_vacia_es_cero():
    assert total([]) == 0


@pytest.mark.parametrize("filas", [
    [(1, "texto")],      # TypeError al sumar
    [(1,)],              # IndexError: falta la columna
    None,                # TypeError: no iterable
])
def test_total_con_formato_invalido_lanza_value_error(filas):
    with pytest.raises(ValueError, match="formato inválido"):
        total(filas)
