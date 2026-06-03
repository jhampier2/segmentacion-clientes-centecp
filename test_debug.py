import subprocess, sys, time, json, urllib.request, socket

# Check port
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port_busy = sock.connect_ex(("127.0.0.1", 5000)) == 0
sock.close()
print(f"Port 5000 busy: {port_busy}")

# Kill if busy
if port_busy:
    subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
    time.sleep(3)

port_busy2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
busy2 = port_busy2.connect_ex(("127.0.0.1", 5000)) == 0
port_busy2.close()
print(f"Port 5000 busy after kill: {busy2}")

# Start fresh
proc = subprocess.Popen([sys.executable, "backend_api\\main.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

# Test
req = urllib.request.Request("http://localhost:5000/api/segmentar",
    data=json.dumps({"ingresos_mensuales": 15000, "linea_credito_utilizada": 0.1, "dias_atraso_promedio": 0}).encode(),
    headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
print(f"Response keys: {list(resp.keys())}")
print(json.dumps(resp, indent=2, ensure_ascii=False))

# Test frontend
html = urllib.request.urlopen("http://localhost:5000/", timeout=5).read().decode()
print(f"Frontend OK: {len(html)} bytes, modal={'modal-overlay' in html}")

proc.terminate()
proc.wait()
print("Done")
