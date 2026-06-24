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


stats = df.groupby(['country', 'shipper_name']).agg(
    avg_cost=('shipping_cost', 'mean'),
    avg_days=('delivery_days', 'mean')
).reset_index()

print("НАЙДЕШЕВШІ ПЕРЕВІЗНИКИ ЗА КРАЇНАМИ")
cheapest = stats.loc[stats.groupby('country')['avg_cost'].idxmin()]
print(cheapest[['country', 'shipper_name', 'avg_cost']].to_string(index=False))

print("НАЙШВИДШІ ПЕРЕВІЗНИКИ ЗА КРАЇНАМИ")
fastest = stats.loc[stats.groupby('country')['avg_days'].idxmin()]
print(fastest[['country', 'shipper_name', 'avg_days']].to_string(index=False))


# ТОП-3 країни за кількістю замовлень
top_3_countries = df['country'].value_counts().head(3).index

df_top3 = stats[stats['country'].isin(top_3_countries)]

plt.figure(figsize=(10, 6))
sns.barplot(data=df_top3, x='country', y='avg_cost', hue='shipper_name', palette='muted')

plt.title('Середня вартість доставки перевізників для ТОП-3 країн')
plt.xlabel('Країна доставки')
plt.ylabel('Середня вартість')
plt.legend(title='Перевізник')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()


print("ЧИ ЗБІГАЄТЬСЯ НАЙДЕШЕВШИЙ З НАЙШВИДШИМ?")
comparison = pd.merge(cheapest, fastest, on='country', suffixes=('_cheap', '_fast'))
comparison['is_same'] = comparison['shipper_name_cheap'] == comparison['shipper_name_fast']

print(comparison[['country', 'shipper_name_cheap', 'shipper_name_fast', 'is_same']].to_string(index=False))
print("\n💡 Компроміс: Якщо перевізники не збігаються (а так зазвичай і є), фінансистам "
      "варто запропонувати 'гібридну' модель: для стандартних товарів обирати найдешевшого, "
      "а для термінових чи преміум-замовлень — найшвидшого із доплатою клієнта.")


max_date = df['shipped_date'].max()
one_year_ago = max_date - pd.DateOffset(years=1)

df_last_year = df[df['shipped_date'] >= one_year_ago].copy()

df_last_year = df_last_year.merge(cheapest[['country', 'avg_cost']], on='country', how='left')

total_spent = df_last_year['shipping_cost'].sum()

ideal_spent = df_last_year['avg_cost'].sum()

potential_savings = total_spent - ideal_spent

print(f"РОЗРАХУНОК ЕКОНОМІЇ ЗА ОСТАННІЙ РІК (з {one_year_ago.strftime('%Y-%m-%d')} по {max_date.strftime('%Y-%m-%d')})")
print(f"Фактично витрачено на логістику: {total_spent:.2f}")
print(f"Потенційні витрати за оптимізації: {ideal_spent:.2f}")
print(f"🔥 Потенційна економія для фінансистів: {potential_savings:.2f}")