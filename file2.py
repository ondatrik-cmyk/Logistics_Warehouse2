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


carrier_name = df_shipments['shipper_name'].iloc[0]


costs = df_shipments[df_shipments['shipper_name'] == carrier_name]['shipping_cost']

q1 = costs.quantile(0.25)
q3 = costs.quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = costs[(costs < lower_bound) | (costs > upper_bound)]


print(f"--- Аналіз для перевізника: {carrier_name} ---")
print(f"Всього доставок у базі: {len(costs)} шт.")
print(f"Нормальна ціна доставки має бути в межах: від {lower_bound:.2f} до {upper_bound:.2f}")
print(f"Кількість знайдених викидів (аномалій): {len(outliers)} шт.")

if len(outliers) > 0:
    print(f"Ось перші 5 аномальних цін для прикладу: {list(outliers.head(5))}")

plt.figure(figsize=(10, 6))

sns.boxplot(data=df_shipments, x='shipper_name', y='shipping_cost', palette='Set3')

plt.title('Розподіл вартості доставки та викиди (Аномалії)')
plt.xlabel('Перевізник')
plt.ylabel('Вартість доставки')

plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()