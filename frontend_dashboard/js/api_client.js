const API_BASE = "";

export async function fetchResumen() {
    const resp = await fetch(`${API_BASE}/api/dashboard/resumen`);
    if (!resp.ok) throw new Error(`Error ${resp.status}`);
    return resp.json();
}

export async function fetchClientes(cluster = null) {
    const params = cluster !== null ? `?cluster=${cluster}` : "";
    const resp = await fetch(`${API_BASE}/api/dashboard/clientes${params}`);
    if (!resp.ok) throw new Error(`Error ${resp.status}`);
    return resp.json();
}

export async function fetchClientesRiesgo() {
    return fetchClientes(2);
}
