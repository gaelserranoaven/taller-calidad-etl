# etl/transform.py
import re
PATRON = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")

def normalizar_email(email):
    if not isinstance(email, str) or not email.strip():
        raise ValueError("email vacío")
    limpio = email.strip().lower()
    if not PATRON.match(limpio):
        raise ValueError(f"email inválido: {email}")
    return limpio

def calcular_total(precio, cantidad, descuento=0.0):
    if precio < 0 or cantidad < 0 or not 0 <= descuento <= 1:
        raise ValueError("parámetros fuera de rango")
    return round(precio * cantidad * (1 - descuento), 2)
