import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.db_config import get_connection
import pandas as pd
from datetime import datetime

QUERY_VARIABLES = """
SELECT
    c.idCG AS id_cliente,
    CONCAT(c.ap, ' ', c.am, ' ', c.nom) AS nombre_completo,
    c.dni,
    COALESCE(c.ingresos_mensuales, 0) AS ingresos_mensuales,
    COALESCE(ROUND(act.saldo_total / act.monto_aprobado, 4), 0) AS linea_credito_utilizada,
    COALESCE(act.dias_atraso_promedio, 0) AS dias_atraso_promedio
FROM tclie_general c
LEFT JOIN (
    SELECT
        p.idCG,
        MAX(p.montoAprovado) AS monto_aprobado,
        COALESCE(SUM(d.saldo), 0) AS saldo_total,
        COALESCE(AVG(d.dias_atraso), 0) AS dias_atraso_promedio
    FROM tprestamo p
    LEFT JOIN (
        SELECT
            idP,
            saldo,
            DATEDIFF(COALESCE(fechaPago, NOW()), expiration_at) AS dias_atraso
        FROM tpresta_detalle
    ) d ON p.idP = d.idP
    GROUP BY p.idCG
) act ON c.idCG = act.idCG
WHERE c.status = 'ACTIVE'
ORDER BY c.idCG
"""

def extraer_variables():
    conn = get_connection()
    df = pd.read_sql(QUERY_VARIABLES, conn)
    conn.close()
    return df
