"""Temporary check for the chart builder. Delete after Step 9."""

from app.agent.charts import build_chart

SQL = """
SELECT cu.region, ROUND(AVG(t.total)) AS avg_order_value
FROM (
    SELECT o.order_id, o.customer_id,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY 1, 2
) t
JOIN customers cu ON cu.customer_id = t.customer_id
GROUP BY 1
ORDER BY 2 DESC
"""

chart = build_chart(SQL, "bar", "Average order value by region")

print("chart type:", chart["data"][0]["type"])
print("x labels  :", chart["data"][0]["x"])

import plotly.graph_objects as go
go.Figure(chart).write_html("chart.html")
print("saved chart.html - double-click it to view")