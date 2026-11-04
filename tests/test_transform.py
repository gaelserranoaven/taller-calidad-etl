# tests/test_transform.py
import pytest
from etl.transform import normalizar_email, calcular_total


# ---------- normalizar_email ----------

@pytest.mark.parametrize("entrada, esperado", [
    ("  Ana@Mail.COM ", "ana@mail.com"),                       # espacios + mayúsculas
    ("luis.p+datos@uni.edu.co", "luis.p+datos@uni.edu.co"),    # punto y plus
    ("ANA@MAIL.COM", "ana@mail.com"),                          # solo mayúsculas
    ("\tpedro@mail.com\n", "pedro@mail.com"),                  # tab y salto de línea
    ("a_b-c@sub-dom.mail.com", "a_b-c@sub-dom.mail.com"),      # guiones y subdominio
])
def test_normalizar_email_valido(entrada, esperado):
    assert normalizar_email(entrada) == esperado


@pytest.mark.parametrize("entrada", [
    "", "   ", "sin-arroba", None, 123,
    "@mail.com", "ana@", "ana@mail", "ana mail@x.com", "ana@@mail.com",
])
def test_normalizar_email_invalido(entrada):
    with pytest.raises(ValueError):
        normalizar_email(entrada)


@pytest.mark.parametrize("entrada", ["", "   ", None, 42])
def test_normalizar_email_vacio_mensaje(entrada):
    with pytest.raises(ValueError, match="email vacío"):
        normalizar_email(entrada)


def test_normalizar_email_invalido_mensaje_incluye_original():
    with pytest.raises(ValueError, match="email inválido: sin-arroba"):
        normalizar_email("sin-arroba")


# ---------- calcular_total ----------

def test_calcular_total_sin_descuento():
    assert calcular_total(10.0, 3) == 30.0


def test_calcular_total_con_descuento():
    assert calcular_total(100, 2, 0.1) == 180.0


@pytest.mark.parametrize("descuento, esperado", [(0, 200.0), (1, 0.0)])
def test_calcular_total_descuento_limites(descuento, esperado):
    assert calcular_total(100, 2, descuento) == esperado


@pytest.mark.parametrize("precio, cantidad", [(0, 5), (50, 0), (0, 0)])
def test_calcular_total_cero(precio, cantidad):
    assert calcular_total(precio, cantidad) == 0.0


@pytest.mark.parametrize("precio, cantidad", [(-1, 1), (1, -1), (-5, -5)])
def test_calcular_total_negativos(precio, cantidad):
    with pytest.raises(ValueError):
        calcular_total(precio, cantidad)


@pytest.mark.parametrize("descuento", [-0.01, 1.01, 2, -1])
def test_calcular_total_descuento_fuera_de_rango(descuento):
    with pytest.raises(ValueError, match="parámetros fuera de rango"):
        calcular_total(100, 1, descuento)


@pytest.mark.parametrize("precio, cantidad, descuento, esperado", [
    (19.99, 3, 0.1, 53.97),   # 53.973 -> 53.97
    (0.1, 3, 0.0, 0.3),       # 0.30000000000000004 -> 0.3
    (9.99, 1, 0.5, 5.0),      # 4.995 en float cae en 5.0; se documenta el redondeo
])
def test_calcular_total_redondeo_a_dos_decimales(precio, cantidad, descuento, esperado):
    assert calcular_total(precio, cantidad, descuento) == esperado
