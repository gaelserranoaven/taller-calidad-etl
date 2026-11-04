# etl/pipeline.py
import csv
from etl.transform import normalizar_email

def ejecutar_pipeline(ruta_csv, con):
    con.execute("CREATE TABLE IF NOT EXISTS clientes "
                "(id INTEGER PRIMARY KEY, email TEXT)")
    with open(ruta_csv, encoding="utf-8") as f:
        filas = [(int(r["id"]), normalizar_email(r["email"]))
                 for r in csv.DictReader(f)]
    con.executemany(
        "INSERT OR REPLACE INTO clientes VALUES (?, ?)", filas)
    con.commit()
    return len(filas)
