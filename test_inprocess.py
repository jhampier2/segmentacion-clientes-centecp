import sys, os, json
sys.path.insert(0, "backend_api")
sys.path.insert(0, os.path.join("backend_api", "src"))

# Clear caches
for r, d, f in os.walk("backend_api"):
    for dn in d:
        if dn == "__pycache__":
            import shutil
            shutil.rmtree(os.path.join(r, dn), ignore_errors=True)

from main import app

client = app.test_client()
ok = True

def test(method, path, expected_status=200, label=""):
    global ok
    if method == "GET":
        resp = client.get(path)
    else:
        resp = client.post(path, data=json.dumps({"ingresos_mensuales":5000,"linea_credito_utilizada":0.3,"dias_atraso_promedio":10}),
                          content_type="application/json")
    status_ok = resp.status_code == expected_status
    data = json.loads(resp.data)
    print(label + " -> status=" + str(resp.status_code) + " keys=" + str(list(data.keys())))
    if not status_ok:
        ok = False
    return data

# 1. New dynamic endpoint
r0 = test("GET", "/api/dashboard/clientes?cluster=0", label="cluster=0")
r1 = test("GET", "/api/dashboard/clientes?cluster=1", label="cluster=1")
r2 = test("GET", "/api/dashboard/clientes?cluster=2", label="cluster=2")

print("  cluster 0 data: total=" + str(r0["total"]) + " sample_clusters=" + str(set(c["cluster"] for c in r0["clientes"])))
print("  cluster 1 data: total=" + str(r1["total"]) + " sample_clusters=" + str(set(c["cluster"] for c in r1["clientes"])))
print("  cluster 2 data: total=" + str(r2["total"]) + " sample_clusters=" + str(set(c["cluster"] for c in r2["clientes"])))

# 2. Backward compat
rc = test("GET", "/api/dashboard/clientes-riesgo", label="clientes-riesgo")
print("  cluster=" + str(rc.get("cluster")) + " total=" + str(rc["total"]))

# 3. Resumen
rm = test("GET", "/api/dashboard/resumen", label="resumen")
print("  total_clientes=" + str(rm["metricas"]["total_clientes"]))

# 4. Segmentar
rs = test("POST", "/api/segmentar", label="segmentar")
print("  cluster=" + str(rs["cluster"]) + " sim=" + rs.get("porcentaje_similitud", "N/A"))

# 5. Frontend
html_resp = client.get("/")
html = html_resp.data.decode()
print("Frontend -> pills=" + str("cluster-pills" in html) + " filtrarCluster=" + str("filtrarCluster" in html))

print("\n" + ("ALL TESTS PASSED" if ok else "SOME TESTS FAILED"))
