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
    o.order_id,
    o.ship_country AS country,
    s.name AS shipper_name,
    sh.cost AS shipping_cost,
    o.order_date,
    sh.shipped_date
FROM orders o
JOIN shipments sh ON o.order_id = sh.order_id
JOIN shippers s ON sh.shipper_id = s.shipper_id
WHERE sh.shipped_date IS NOT NULL;
"""

df = pd.read_sql_query(query, conn)
conn.close()


df['order_date'] = pd.to_datetime(df['order_date'])
df['shipped_date'] = pd.to_datetime(df['shipped_date'])

df['delivery_days'] = (df['shipped_date'] - df['order_date']).dt.days



# Scatter Plot (avg_cost × avg_delivery_time)

scatter_data = df.groupby(['country', 'shipper_name']).agg(
    avg_cost=('shipping_cost', 'mean'),
    avg_delivery_time=('delivery_days', 'mean'),
    shipments_count=('order_id', 'count')
).reset_index()

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=scatter_data,
    x='avg_delivery_time',
    y='avg_cost',
    hue='shipper_name',
    size='shipments_count',
    sizes=(40, 400),
    alpha=0.7
)

plt.title('Середня ціна vs Час доставки')
plt.xlabel('Середній час доставки (дні)')
plt.ylabel('Середня вартість доставки')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()



# Bar Chart ТОП-10 маршрутів

top_routes = df['country'].value_counts().head(10).reset_index()
top_routes.columns = ['country', 'shipments_count']

plt.figure(figsize=(10, 6))
sns.barplot(
    data=top_routes,
    x='shipments_count',
    y='country',
    hue='country',
    palette='viridis',
    legend=False
)

plt.title('ТОП-10 маршрутів (країн) за кількістю відправлень')
plt.xlabel('Кількість відправлень')
plt.ylabel('Країна доставки')
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()


# Карта логістичних потоків (Матриця зв'язків)

pivot_flows = df.pivot_table(
    index='shipper_name',
    columns='country',
    values='order_id',
    aggfunc='count'
).fillna(0)

plt.figure(figsize=(12, 6))
sns.heatmap(
    data=pivot_flows,
    annot=True,
    cmap='YlGnBu',
    fmt='.0f',
    linewidths=0.5,
    annot_kws={'size': 9}
)

plt.title('Кількість замовлень за напрямками')
plt.xlabel('Країна доставки')
plt.ylabel('Перевізник')
plt.tight_layout()
plt.show()