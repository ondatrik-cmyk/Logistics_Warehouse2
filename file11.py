# Визначити найефективніші маршрути (швидко + дешево)
#  Визначити найдорожчі та найповільніші маршрути
#  Виявити bottlenecks логістичної мережі
#  Побудувати рейтинг маршрутів за ефективністю
# Побудувати потоки:
# warehouse.city → destination_country
#
# Для кожного маршруту розрахувати:
# Середній час доставки
# Середню вартість доставки
# Кількість відправлень

import os
import sqlite3
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')
conn = sqlite3.connect(DB_PATH)

query = """
SELECT 
    w.name AS warehouse_name,
    w.city AS warehouse_city,
    c.name AS category_name,
    o.ship_country AS destination_country,
    o.order_date,
    sh.shipped_date,
    sh.cost AS shipping_cost
FROM orders o
JOIN shipments sh ON o.order_id = sh.order_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
JOIN inventory i ON p.product_id = i.product_id
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
WHERE sh.shipped_date IS NOT NULL;
"""

df = pd.read_sql_query(query, conn)
conn.close()

df['order_date'] = pd.to_datetime(df['order_date'])
df['shipped_date'] = pd.to_datetime(df['shipped_date'])
df['delivery_days'] = (df['shipped_date'] - df['order_date']).dt.days

df['month'] = df['order_date'].dt.to_period('M')

df['route'] = df['warehouse_city'] + " → " + df['destination_country']


print("РОЗПОДІЛ ЧАСУ ОБРОБКИ ПО СКЛАДАХ")
print(df.groupby('warehouse_name')['delivery_days'].mean().round(1).to_string())

print("ЗАЛЕЖНІСТЬ ЧАСУ ВІД КАТЕГОРІЇ ТОВАРУ")
print(df.groupby('category_name')['delivery_days'].mean().round(1).to_string())

print("ЗАЛЕЖНІСТЬ ЧАСУ ВІД КРАЇНИ ДОСТАВКИ")
print(df.groupby('destination_country')['delivery_days'].mean().round(1).head(10).to_string())

print("СЕЗОННІСТЬ ЧАСУ ОБРОБКИ (ПО МІСЯЦЯХ)")
print(df.groupby('month')['delivery_days'].mean().round(1).to_string())

print("РОЗРАХУНОК ПОТОКІВ ТА МАРШРУТІВ (warehouse.city → destination_country):")
routes_analysis = df.groupby('route').agg(
    avg_delivery_time=('delivery_days', 'mean'),
    avg_shipping_cost=('shipping_cost', 'mean'),
    shipments_count=('shipping_cost', 'count')
).reset_index()

routes_analysis['avg_delivery_time'] = routes_analysis['avg_delivery_time'].round(1)
routes_analysis['avg_shipping_cost'] = routes_analysis['avg_shipping_cost'].round(2)

print(routes_analysis.sort_values(by='shipments_count', ascending=False).head(15).to_string(index=False))