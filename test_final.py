import subprocess, sys, time, json, urllib.request, signal

proc = subprocess.Popen(
    [sys.executable, "backend_api\\main.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(5)

def get(path):
    url = "http://localhost:5000" + path
    return json.loads(urllib.request.urlopen(url, timeout=5).read())

try:
    r0 = get("/api/dashboard/clientes?cluster=0")
    r1 = get("/api/dashboard/clientes?cluster=1")
    r2 = get("/api/dashboard/clientes?cluster=2")

    print("cluster=0 -> total=" + str(r0["total"]) + " sample_clusters=" + str(set(c["cluster"] for c in r0["clientes"])))
    print("cluster=1 -> total=" + str(r1["total"]) + " sample_clusters=" + str(set(c["cluster"] for c in r1["clientes"])))
    print("cluster=2 -> total=" + str(r2["total"]) + " sample_clusters=" + str(set(c["cluster"] for c in r2["clientes"])))

    rc = get("/api/dashboard/clientes-riesgo")
    print("clientes-riesgo -> total=" + str(rc["total"]) + " cluster=" + str(rc["cluster"]))

    html = urllib.request.urlopen("http://localhost:5000/", timeout=5).read().decode()
    print("Frontend pills=" + str("cluster-pills" in html) + " filtrarCluster=" + str("filtrarCluster" in html))

finally:
    proc.terminate()
    proc.wait()
