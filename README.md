# Taller: calidad en un mini-pipeline ETL

Pipeline que lee clientes desde un CSV, los limpia (`etl/transform.py`) y los carga en SQLite
(`etl/pipeline.py`). Calidad verificada con **pytest + pytest-cov** y **SonarQube**, todo en Docker Desktop.

```
taller-calidad/
├── etl/            transform.py · pipeline.py · reportes.py (paso 5)
├── tests/          test_transform.py · test_integracion.py · test_reportes.py (paso 5)
├── docker-compose.yml   SonarQube + contenedor de pruebas + scanner
├── sonar.ps1            atajos de PowerShell
├── sonar-project.properties · .coveragerc · requirements.txt
```

## Historial de Git = evidencia (antes / después)

| Tag | Qué contiene | Para qué captura |
|---|---|---|
| `paso4-baseline` | Código limpio: transform + pipeline + pruebas | Análisis **inicial** de SonarQube |
| `paso5-defectos` | Se agrega `reportes.py` con defectos intencionales (sin pruebas) | Hallazgos de SonarQube (Quality Gate **fallido**) |
| `paso5-corregido` (= `main`) | Defectos corregidos + `test_reportes.py` | Quality Gate **aprobado** |

## Ejecución en PowerShell (Docker Desktop abierto)

Si PowerShell bloquea el script por la política de ejecución, no la cambies: lanza cada comando así,
`powershell -ExecutionPolicy Bypass -File .\sonar.ps1 <accion>`.

1. **Levantar SonarQube**: `.\sonar.ps1 levantar` y abre <http://localhost:9000>.
   Ingreso `admin` / `admin`; te pedirá cambiar la clave.
2. **Crear el proyecto**: *Create a local project* → *Project key* = `taller-calidad` → rama `main` →
   *Use the global setting* → *Locally*. Luego **My Account > Security > Generate Token**.
3. **Token solo en la sesión** (nunca lo subas a Git):
   `$env:SONAR_TOKEN = "squ_xxxxxxxx"`
4. **Pruebas locales sin Sonar**: `.\sonar.ps1 pruebas` (pytest -v + cobertura dentro de Docker).
5. **Tres análisis, uno por tag**:
   ```powershell
   git checkout paso4-baseline ; .\sonar.ps1 analizar     # captura A
   git checkout paso5-defectos ; .\sonar.ps1 analizar     # captura B
   git checkout paso5-corregido; .\sonar.ps1 analizar     # captura C
   git checkout main                                      # volver al final
   ```
6. Al terminar: `.\sonar.ps1 bajar` (conserva datos) o `.\sonar.ps1 limpiar` (borra todo).

El scanner corre en la red de Compose y llega a SonarQube por `http://sonarqube:9000`,
por eso **no hace falta** `--network host` (que en Docker Desktop no funciona igual que en Linux).

## Checklist de capturas (revisar una por una)

- [ ] **1. pytest -v**: todas las pruebas en verde (`.\sonar.ps1 pruebas`).
- [ ] **2. Cobertura**: tabla `term-missing`; `transform.py` ≥ 90 % y paquete `etl` ≥ 80 %.
- [ ] **3. SonarQube baseline** (`paso4-baseline`): panel general con Quality Gate y cobertura **distinta de 0 %**.
      Si sale 0 %, revisa que `coverage.xml` exista y que `.coveragerc` tenga `relative_files = True`.
- [ ] **4. Hallazgos** (`paso5-defectos`): lista de *Issues* y *Security Hotspots*, con el tipo de cada uno
      (hotspot, vulnerabilidad, bug o code smell) tal como lo muestra SonarQube.
- [ ] **5. Quality Gate aprobado** (`paso5-corregido`): estado *Passed* en el panel.
- [ ] **6. Hotspots**: si SonarQube deja alguno abierto, ábrelo, léelo y márcalo *Safe* o *Fixed* con justificación;
      el Quality Gate "Sonar way" exige 100 % de hotspots revisados.

## Notas de diseño (para el informe)

- **Pipeline atómico**: si una fila trae un email inválido, `ejecutar_pipeline` lanza `ValueError` y **no carga ninguna fila**.
  Alternativa escalable: cuarentena (cargar las válidas y reportar las rechazadas).
- **Idempotencia**: `INSERT OR REPLACE` sobre `id` hace que ejecutar dos veces deje el mismo resultado.
- **Límites conocidos** (candidatos a mejora): el regex acepta dominios como `a@b..`; `calcular_total` usa `float`
  para dinero (`Decimal` sería lo correcto); un CSV con BOM (exportado de Excel) rompería la lectura de `id`
  (solución: `encoding="utf-8-sig"`).
- La identidad de Git de los commits es de ejemplo; cámbiala con `git config user.name/user.email`
  antes de subir el repo a tu GitHub.
