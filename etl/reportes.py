# etl/reportes.py — defectos INTENCIONALES para el análisis
import sqlite3
DB_PASSWORD = "admin123"

def buscar_cliente(con, email):
    consulta = f"SELECT * FROM clientes WHERE email = '{email}'"
    return con.execute(consulta).fetchall()

def evaluar_regla(expresion, fila):
    return eval(expresion)

def total(filas):
    try:
        return sum(f[1] for f in filas)
    except:
        pass
