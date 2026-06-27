# Порівняти розміщення товарів із географією попиту

import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')
conn = sqlite3.connect(DB_PATH)


df_demand = pd.read_sql_query("SELECT ship_country AS country, COUNT(order_id) AS orders_count FROM orders GROUP BY ship_country;", conn)

df_stock = pd.read_sql_query("SELECT w.country, SUM(i.quantity) AS stock_count FROM inventory i JOIN warehouses w ON i.warehouse_id = w.warehouse_id GROUP BY w.country;", conn)

conn.close()

comparison = pd.merge(df_demand, df_stock, on='country', how='outer').fillna(0)

comparison.set_index('country')[['orders_count', 'stock_count']].plot(
    kind='bar',
    figsize=(12, 6),
    color=['royalblue', 'lightpink']
)
plt.title('Кількість замовлень vs Товари на складах')
plt.xlabel('Країна')
plt.ylabel('Кількість')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()