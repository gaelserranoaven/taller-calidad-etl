# etl/reportes.py — versión corregida (paso 5b)
import ast
import operator
import os

# Operadores permitidos en las reglas: lista blanca, nada más se evalúa.
_BINARIOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARIOS = {ast.Not: operator.not_, ast.USub: operator.neg}
_COMPARADORES = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def obtener_password():
    """La contraseña vive en la variable de entorno DB_PASSWORD, nunca en el código."""
    try:
        return os.environ["DB_PASSWORD"]
    except KeyError as exc:
        raise RuntimeError("Falta la variable de entorno DB_PASSWORD") from exc


def buscar_cliente(con, email):
    # Consulta parametrizada: el valor viaja separado del SQL (previene inyección).
    return con.execute(
        "SELECT * FROM clientes WHERE email = ?", (email,)
    ).fetchall()


def _comparar(nodo, fila):
    izquierda = _evaluar(nodo.left, fila)
    for operador, derecho in zip(nodo.ops, nodo.comparators):
        if type(operador) not in _COMPARADORES:
            raise ValueError("comparador no permitido")
        derecha = _evaluar(derecho, fila)
        if not _COMPARADORES[type(operador)](izquierda, derecha):
            return False
        izquierda = derecha
    return True


def _evaluar(nodo, fila):
    if isinstance(nodo, ast.Constant):
        return nodo.value
    if isinstance(nodo, ast.Name):
        if nodo.id not in fila:
            raise ValueError(f"campo desconocido: {nodo.id}")
        return fila[nodo.id]
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _BINARIOS:
        return _BINARIOS[type(nodo.op)](
            _evaluar(nodo.left, fila), _evaluar(nodo.right, fila))
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _UNARIOS:
        return _UNARIOS[type(nodo.op)](_evaluar(nodo.operand, fila))
    if isinstance(nodo, ast.BoolOp):
        valores = (_evaluar(v, fila) for v in nodo.values)
        return all(valores) if isinstance(nodo.op, ast.And) else any(valores)
    if isinstance(nodo, ast.Compare):
        return _comparar(nodo, fila)
    raise ValueError(f"expresión no permitida: {type(nodo).__name__}")


def evaluar_regla(expresion, fila):
    """Evalúa una regla como 'monto > 100 and id < 5' contra un dict `fila`, sin eval()."""
    try:
        arbol = ast.parse(expresion, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"regla inválida: {expresion}") from exc
    return _evaluar(arbol.body, fila)


def total(filas):
    """Suma la segunda columna de cada fila; falla con un error claro si el formato no sirve."""
    try:
        return sum(f[1] for f in filas)
    except (TypeError, IndexError) as exc:
        raise ValueError("filas con formato inválido") from exc
