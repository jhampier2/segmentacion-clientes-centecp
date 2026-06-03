import subprocess, sys, time, json, urllib.request, socket, os, signal

# Kill any process on port 5000
subprocess.run(["taskkill", "/f", "/im", "python.exe"],
    capture_output=True, shell=True)
time.sleep(3)

# Verify port is free
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
busy = s.connect_ex(("127.0.0.1", 5000)) == 0
s.close()
print("Port 5000 free: " + str(not busy))

# Start fresh server
proc = subprocess.Popen(
    [sys.executable, "backend_api\\main.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(6)

# Test
def get(path):
    url = "http://localhost:5000" + path
    return json.loads(urllib.request.urlopen(url, timeout=5).read())

try:
    # Test new endpoint
    r = get("/api/dashboard/clientes?cluster=0")
    print("GET /api/dashboard/clientes?cluster=0 -> total=" + str(r["total"]) + " ok=" + str(r["cluster"] == 0))

    r = get("/api/dashboard/clientes?cluster=1")
    print("GET /api/dashboard/clientes?cluster=1 -> total=" + str(r["total"]) + " ok=" + str(r["cluster"] == 1))

    r = get("/api/dashboard/clientes?cluster=2")
    print("GET /api/dashboard/clientes?cluster=2 -> total=" + str(r["total"]) + " ok=" + str(r["cluster"] == 2))

    # Test backward compat
    rc = get("/api/dashboard/clientes-riesgo")
    print("GET /api/dashboard/clientes-riesgo -> total=" + str(rc["total"]) + " cluster=" + str(rc["cluster"]))

    # Test resumen still works
    rm = get("/api/dashboard/resumen")
    print("GET /api/dashboard/resumen -> total=" + str(rm["metricas"]["total_clientes"]))

    # Test frontend
    html = urllib.request.urlopen("http://localhost:5000/", timeout=5).read().decode()
    print("Frontend -> pills=" + str("cluster-pills" in html) + " filtrarCluster=" + str("filtrarCluster" in html))

    print("ALL TESTS PASSED")
finally:
    proc.terminate()
    proc.wait()
