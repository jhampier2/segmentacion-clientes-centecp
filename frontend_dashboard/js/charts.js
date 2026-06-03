let chartInstance = null;

export function renderDonutChart(canvasId, distribucion) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstance) chartInstance.destroy();

    const labels = distribucion.map(d => d.nivel_riesgo);
    const data = distribucion.map(d => d.cantidad);
    const colors = ["#00c853", "#ffc107", "#f44336"];

    chartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors,
                borderColor: "#0a0a0a",
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#ccc", padding: 16, font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.parsed / total) * 100).toFixed(1);
                            return `${ctx.label}: ${ctx.parsed} clientes (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

export function renderBarChart(canvasId, distribucion) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: distribucion.map(d => d.nivel_riesgo),
            datasets: [{
                label: "Clientes",
                data: distribucion.map(d => d.cantidad),
                backgroundColor: ["rgba(0,200,83,0.7)", "rgba(255,193,7,0.7)", "rgba(244,67,54,0.7)"],
                borderColor: ["#00c853", "#ffc107", "#f44336"],
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: "#888" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                x: {
                    ticks: { color: "#ccc" },
                    grid: { display: false }
                }
            }
        }
    });
}
