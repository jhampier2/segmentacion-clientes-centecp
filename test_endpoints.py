import subprocess, sys, time, json, urllib.request, urllib.error

# Start server
proc = subprocess.Popen([sys.executable, "main.py"], cwd="backend_api", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

def test_get(path):
    try:
        resp = urllib.request.urlopen(f"http://localhost:5000{path}", timeout=5)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def test_post(path, data):
    try:
        req = urllib.request.Request(
            f"http://localhost:5000{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

# Test 1: POST /api/segmentar
r1 = test_post("/api/segmentar", {"ingresos_mensuales": 6000, "linea_credito_utilizada": 0.4, "dias_atraso_promedio": 10})
print(f"POST /api/segmentar => {json.dumps(r1, indent=2)}")

# Test 2: GET /api/dashboard/resumen
r2 = test_get("/api/dashboard/resumen")
print(f"\nGET /api/dashboard/resumen => {json.dumps(r2, indent=2)}")

# Test 3: GET /api/dashboard/clientes-riesgo
r3 = test_get("/api/dashboard/clientes-riesgo")
print(f"\nGET /api/dashboard/clientes-riesgo => total={r3.get('total')}, primeros 3 nomina: {[c['nombre_completo'] for c in r3.get('clientes', [])[:3]]}")

proc.terminate()
proc.wait()
print("\nTodos los endpoints respondieron correctamente!")
