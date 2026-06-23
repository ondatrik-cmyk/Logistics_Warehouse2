import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')

# Heatmap warehouse × category
conn = sqlite3.connect(DB_PATH)

query_wh_cat = """
SELECT 
    w.name AS warehouse_name,
    c.name AS category_name,
    i.quantity
FROM inventory i
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
JOIN products p ON i.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id;
"""
df_wh_cat = pd.read_sql_query(query_wh_cat, conn)
conn.close()

pivot_wh = df_wh_cat.pivot_table(index='warehouse_name', columns='category_name', values='quantity', aggfunc='sum').fillna(0)

plt.figure(figsize=(10, 6))
sns.heatmap(data=pivot_wh, annot=True, cmap='Purples', fmt='.0f', annot_kws={'size': 6})
plt.title('Heatmap warehouse × category')
plt.xlabel('Category')
plt.ylabel('Warehouse')
plt.show()

conn = sqlite3.connect(DB_PATH)

# Географічна карта складів та країн замовлень
query_geo = """
SELECT 
    w.country AS warehouse_country,
    o.ship_country AS order_country,
    o.order_id
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN inventory i ON oi.product_id = i.product_id
JOIN warehouses w ON i.warehouse_id = w.warehouse_id;
"""
df_geo = pd.read_sql_query(query_geo, conn)
conn.close()

pivot_geo = df_geo.pivot_table(index='warehouse_country', columns='order_country', values='order_id', aggfunc='count').fillna(0)

plt.figure(figsize=(10, 6))
sns.heatmap(data=pivot_geo, annot=True, cmap='Greens', fmt='.0f')
plt.title('Географічна матриця: Склади та Країни замовлень')
plt.xlabel('Країна доставки (Order Country)')
plt.ylabel('Країна складу (Warehouse Country)')
plt.show()