# Перевірити, чи зберігаються популярні товари ближче до основних ринків збуту

import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')
conn = sqlite3.connect(DB_PATH)


df_sales = pd.read_sql_query("""
    SELECT product_id, COUNT(order_id) AS total_sold 
    FROM order_items 
    GROUP BY product_id;
""", conn)


df_stock = pd.read_sql_query("""
    SELECT product_id, SUM(quantity) AS total_stock 
    FROM inventory 
    GROUP BY product_id;
""", conn)

conn.close()

df_all = pd.merge(df_sales, df_stock, on='product_id', how='outer').fillna(0)

df_top10 = df_all.sort_values(by='total_sold', ascending=False).head(10)


df_top10.set_index('product_id')[['total_sold', 'total_stock']].plot(
    kind='bar',
    figsize=(12, 6),
    color=['hotpink', 'royalblue'] # Рожевий-продажів, синій-залишки
)

plt.title('ТОП-10 товарів: Продано (Рожевий) vs Залишок на складі (Синій)', fontsize=14)
plt.xlabel('ID Товару')
plt.ylabel('Кількість')
plt.legend(['Продано (Попит)', 'На складі (Запаси)'])
plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()