# tests/test_integracion.py
import sqlite3
import pytest
from etl.pipeline import ejecutar_pipeline


@pytest.fixture
def conexion():
    con = sqlite3.connect(":memory:")
    yield con
    con.close()


def _contar(con):
    return con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]


def test_pipeline_carga_clientes(conexion, tmp_path):
    csv = tmp_path / "clientes.csv"
    csv.write_text("id,email\n1, Ana@Mail.com\n2,luis@mail.com\n")
    ejecutar_pipeline(csv, conexion)
    filas = conexion.execute(
        "SELECT email FROM clientes ORDER BY id").fetchall()
    assert filas == [("ana@mail.com",), ("luis@mail.com",)]


def test_pipeline_devuelve_cantidad_de_filas_procesadas(conexion, tmp_path):
    csv = tmp_path / "clientes.csv"
    csv.write_text("id,email\n1,ana@mail.com\n2,luis@mail.com\n")
    assert ejecutar_pipeline(csv, conexion) == 2


def test_pipeline_es_idempotente(conexion, tmp_path):
    csv = tmp_path / "clientes.csv"
    csv.write_text("id,email\n1,ana@mail.com\n2,luis@mail.com\n")
    ejecutar_pipeline(csv, conexion)
    ejecutar_pipeline(csv, conexion)
    assert _contar(conexion) == 2          # dos filas, no cuatro


def test_pipeline_reemplaza_el_email_si_el_id_ya_existe(conexion, tmp_path):
    primero = tmp_path / "a.csv"
    primero.write_text("id,email\n1,viejo@mail.com\n")
    segundo = tmp_path / "b.csv"
    segundo.write_text("id,email\n1,nuevo@mail.com\n")
    ejecutar_pipeline(primero, conexion)
    ejecutar_pipeline(segundo, conexion)
    assert conexion.execute("SELECT email FROM clientes").fetchall() == [("nuevo@mail.com",)]


def test_pipeline_con_email_invalido_es_atomico(conexion, tmp_path):
    """Decisión de diseño: un email inválido rechaza TODO el archivo y no carga nada."""
    csv = tmp_path / "clientes.csv"
    csv.write_text("id,email\n1,ana@mail.com\n2,esto-no-es-un-email\n3,luis@mail.com\n")
    with pytest.raises(ValueError, match="email inválido"):
        ejecutar_pipeline(csv, conexion)
    assert _contar(conexion) == 0


def test_pipeline_con_email_vacio_lanza_error(conexion, tmp_path):
    csv = tmp_path / "clientes.csv"
    csv.write_text("id,email\n1,\n")
    with pytest.raises(ValueError, match="email vacío"):
        ejecutar_pipeline(csv, conexion)


def test_pipeline_csv_inexistente(conexion, tmp_path):
    with pytest.raises(FileNotFoundError):
        ejecutar_pipeline(tmp_path / "no_existe.csv", conexion)


def test_pipeline_id_no_numerico_lanza_error(conexion, tmp_path):
    csv = tmp_path / "clientes.csv"
    csv.write_text("id,email\nabc,ana@mail.com\n")
    with pytest.raises(ValueError):
        ejecutar_pipeline(csv, conexion)
