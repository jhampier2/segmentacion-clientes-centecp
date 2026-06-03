import subprocess, sys, time, json, urllib.request

proc = subprocess.Popen([sys.executable, "backend_api\\main.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

ok = True

def test_post(path, data, expected_keys):
    global ok
    req = urllib.request.Request(f"http://localhost:5000{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
    keys = list(resp.keys())
    has = all(k in resp for k in expected_keys)
    print(f"  {path} -> keys={keys} | has_all={has}")
    if not has:
        ok = False
    return resp

def test_get(path, expected_contains=None):
    global ok
    resp = urllib.request.urlopen(f"http://localhost:5000{path}", timeout=5)
    body = resp.read().decode()
    print(f"  GET {path} -> status={resp.status} size={len(body)}", end="")
    if expected_contains:
        found = expected_contains in body
        print(f" contains='{expected_contains}'={found}", end="")
        if not found:
            ok = False
    print()

print("=== 1. Nuevo endpoint /api/segmentar (bajo riesgo) ===")
r1 = test_post("/api/segmentar",
    {"ingresos_mensuales": 20000, "linea_credito_utilizada": 0.05, "dias_atraso_promedio": 0},
    ["cluster", "nivel_riesgo", "porcentaje_similitud", "recomendacion_accion"])
print(f"   > cluster={r1['cluster']} riesgo={r1['nivel_riesgo']} sim={r1['porcentaje_similitud']}")
print(f"   > recomendacion: {r1['recomendacion_accion']}")

print("\n=== 2. Nuevo endpoint /api/segmentar (alto riesgo) ===")
r2 = test_post("/api/segmentar",
    {"ingresos_mensuales": 800, "linea_credito_utilizada": 0.99, "dias_atraso_promedio": 150},
    ["cluster", "nivel_riesgo", "porcentaje_similitud", "recomendacion_accion"])
print(f"   > cluster={r2['cluster']} riesgo={r2['nivel_riesgo']} sim={r2['porcentaje_similitud']}")

print("\n=== 3. GET /api/dashboard/resumen ===")
r3 = json.loads(urllib.request.urlopen("http://localhost:5000/api/dashboard/resumen", timeout=5).read())
print(f"   > total={r3['metricas']['total_clientes']} dist={[d['cantidad'] for d in r3['distribucion']]}")

print("\n=== 4. GET / frontend ===")
test_get("/", "modal-overlay")

print("\n=== 5. GET /css/dashboard.css ===")
test_get("/css/dashboard.css", "modal-overlay")

print("\n=== 6. GET /js/api_client.js ===")
test_get("/js/api_client.js", "fetchResumen")

proc.terminate()
proc.wait()
print(f"\n{'='*40}")
print("RESULTADO: " + ("TODAS LAS PRUEBAS PASARON" if ok else "ALGUNAS PRUEBAS FALLARON"))
