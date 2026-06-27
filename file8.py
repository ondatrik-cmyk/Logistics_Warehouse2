# Визначити спеціалізовані склади
import os
import sqlite3
import pandas as pd

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
JOIN categories c ON p.category_id = c.category_id;
"""
df = pd.read_sql_query(query, conn)
conn.close()

pivot_matrix = df.pivot_table(
    index='warehouse',
    columns='category',
    values='quantity_products',
    aggfunc='sum'
).fillna(0)


for warehouse_name in pivot_matrix.index:
    warehouse_stocks = pivot_matrix.loc[warehouse_name]


    total_products = warehouse_stocks.sum()

    if total_products == 0:
        print(f"Склад порожній: {warehouse_name}")
        continue

    main_category = warehouse_stocks.idxmax()
    main_category_qty = warehouse_stocks.max()

    percentage = (main_category_qty / total_products) * 100

    print(f"Склад: {warehouse_name}")
    print(f"Всього товарів на складі: {total_products:.0f}")
    print(f"Основна категорія: {main_category} ({main_category_qty:.0f})")
    print(f"% основної категорії: {percentage:.1f}")

    if percentage >= 50:
        print(f"Спеціалізований склад, категорії '{main_category}'.")
    else:
        print(f"Універсальний склад, різні категорії.")