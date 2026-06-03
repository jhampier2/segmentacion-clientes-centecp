import subprocess, sys, time, json, urllib.request, socket

# Check if port 5000 is already in use
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port_busy = s.connect_ex(("127.0.0.1", 5000)) == 0
s.close()
print("Port 5000 busy before start: " + str(port_busy))

if port_busy:
    # Try to connect and see what's there
    try:
        resp = urllib.request.urlopen("http://localhost:5000/api/dashboard/resumen", timeout=3)
        data = json.loads(resp.read())
        print("Existing server responded with " + str(data.get("metricas", {}).get("total_clientes", "?")) + " clients")
    except Exception as e:
        print("Existing server error: " + str(e))

# Now try the new route on the existing server
try:
    resp = urllib.request.urlopen("http://localhost:5000/api/dashboard/clientes?cluster=0", timeout=3)
    data = json.loads(resp.read())
    print("NEW ROUTE WORKS on existing server!")
    print("total=" + str(data["total"]) + " cluster=" + str(data["cluster"]))
except urllib.error.HTTPError as e:
    print("New route returned " + str(e.code) + " on existing server")
except Exception as e:
    print("New route error: " + str(e))
