import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Box Plot delivery_time по day_of_week

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')


conn = sqlite3.connect(DB_PATH)
query = """
SELECT 
    o.order_id, 
    o.order_date, 
    s.delivered_date
FROM orders o
JOIN shipments s ON o.order_id = s.order_id
WHERE s.delivered_date IS NOT NULL;
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['order_date'] = pd.to_datetime(df['order_date'])
df['delivered_date'] = pd.to_datetime(df['delivered_date'])

df['delivery_time'] = (df['delivered_date'] - df['order_date']).dt.days
df['day_of_week'] = df['order_date'].dt.day_name()

df['month'] = df['order_date'].dt.month
df['day_of_week_num'] = df['order_date'].dt.dayofweek


plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='day_of_week', y='delivery_time', hue='day_of_week', palette='Set2', legend=False)
plt.title('Delivery time vs day_of_week')
plt.xlabel('Day of Week')
plt.ylabel('Delivery Time (days)')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.show()

# Heatmap month × day_of_week
pivot = df.pivot_table(index='month', columns='day_of_week_num', values='order_id', aggfunc='count')

plt.figure(figsize=(10, 6))
sns.heatmap(data=pivot, annot=True, cmap='Blues', fmt='.0f')
plt.title('Замовлення по місяцях та днях тижня')
plt.xlabel('День тижня (0 = Понеділок, 6 = Неділя)')
plt.ylabel('Місяць (1 = Січень, 12 = Грудень)')
plt.show()
#
# Line Chart середнього часу доставки за місяцями
monthly_delivery = df.groupby('month')['delivery_time'].mean()

plt.figure(figsize=(10, 5))

plt.plot(monthly_delivery.index, monthly_delivery.values, marker='o', color='b', linestyle='-')

plt.title('Середній час доставки за місяцями')
plt.xlabel('Місяць (1 = Січень, 12 = Грудень)')
plt.ylabel('Середній час доставки (дні)')

plt.xticks(monthly_delivery.index)

plt.grid(True, linestyle='--', alpha=0.6)
plt.show()