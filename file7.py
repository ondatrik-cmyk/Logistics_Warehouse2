# Побудувати матрицю warehouse × category за кількістю одиниць на складі

import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')

conn = sqlite3.connect(DB_PATH)

query = """
SELECT 
    w.name AS warehouse,
    c.name AS category,
    i.quantity AS quantity_products
FROM inventory i
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
JOIN products p ON i.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
WHERE i.quantity IS NOT NULL;
"""

df = pd.read_sql_query(query, conn)
conn.close()

pivot_matrix = df.pivot_table(
    index='warehouse',
    columns='category',
    values='quantity_products',
    aggfunc='sum'
).fillna(0)


plt.figure(figsize=(12, 7))

sns.heatmap(
    data=pivot_matrix,
    annot=True,
    cmap='RdYlGn',
    fmt='.0f',
    linewidths=0.5,
    annot_kws={'size': 8}
)

plt.title('Склади × Категорії (кількість одиниць)')
plt.xlabel('Категорія товару')
plt.ylabel('Склад')

plt.tight_layout()
plt.show()



