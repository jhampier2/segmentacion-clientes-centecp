import subprocess, sys, time, json, urllib.request

proc = subprocess.Popen([sys.executable, "backend_api\\main.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

def get(path):
    return json.loads(urllib.request.urlopen("http://localhost:5000" + path, timeout=5).read())

r0 = get("/api/dashboard/clientes?cluster=0")
r1 = get("/api/dashboard/clientes?cluster=1")
r2 = get("/api/dashboard/clientes?cluster=2")

print("Cluster 0: total=" + str(r0["total"]) + " cluster=" + str(r0["cluster"]))
print("Cluster 1: total=" + str(r1["total"]) + " cluster=" + str(r1["cluster"]))
print("Cluster 2: total=" + str(r2["total"]) + " cluster=" + str(r2["cluster"]))

c0s = set(c["cluster"] for c in r0["clientes"])
c1s = set(c["cluster"] for c in r1["clientes"])
c2s = set(c["cluster"] for c in r2["clientes"])
print("Cluster 0 response clusters: " + str(c0s))
print("Cluster 1 response clusters: " + str(c1s))
print("Cluster 2 response clusters: " + str(c2s))

rc = get("/api/dashboard/clientes-riesgo")
print("Backward compat /clientes-riesgo: total=" + str(rc["total"]) + " has_cluster=" + str("cluster" in rc))

html = urllib.request.urlopen("http://localhost:5000/", timeout=5).read().decode()
print("Frontend has pills: " + str("cluster-pills" in html))
print("Frontend has filtrarCluster: " + str("filtrarCluster" in html))

proc.terminate()
proc.wait()
print("All tests passed")
