import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')
conn = sqlite3.connect(DB_PATH)

query_iqr = """
SELECT 
    s.name AS shipper_name,
    sh.cost AS shipping_cost
FROM shipments sh
JOIN shippers s ON sh.shipper_id = s.shipper_id;
"""

df_shipments = pd.read_sql_query(query_iqr, conn)
conn.close()

g = sns.FacetGrid(df_shipments, col="shipper_name", height=4, aspect=1.5)
g.map(sns.histplot, "shipping_cost", kde=True, color="orange")

g.set_axis_labels("Вартість доставки", "Кількість замовлень")
plt.show()