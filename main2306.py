
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect("online_store.db")

query = """
SELECT
    s.shipment_id,
    s.order_id,
    s.shipped_date,
    s.delivered_date,
    sh.name AS shipper_name
FROM shipments s
JOIN shippers sh ON s.shipper_id = sh.shipper_id
WHERE s.delivered_date IS NOT NULL
"""

df = pd.read_sql_query(query, conn)
#Клієнт скаржиться, що замовив товар 2 тижні тому, а доставки досі немає
print("Завислі доставки:")
print(df)

print("Кількість завислих доставок:")
print(len(df))

if len(df) == 0:
    print("У базі немає завислих доставок без дати доставки.")
else:
    shipper_stats = df.groupby("shipper_name")["shipment_id"].count()

    print("Загублені доставки по перевізниках:")
    print(shipper_stats)

    plt.figure(figsize=(8, 5))
    shipper_stats.plot(kind="bar")
    plt.title("Кількість загублених відправлень по перевізниках")
    plt.xlabel("Перевізник")
    plt.ylabel("Кількість")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()



#- Перевірити наявність weekend effect (відправлення у п'ятницю або вихідні)
print("\n--- Weekend effect ---")

query_weekend = """
SELECT
    shipped_date,
    delivered_date
FROM shipments
WHERE shipped_date IS NOT NULL
AND delivered_date IS NOT NULL
"""

df_weekend = pd.read_sql_query(query_weekend, conn)

df_weekend["shipped_date"] = pd.to_datetime(df_weekend["shipped_date"])
df_weekend["delivered_date"] = pd.to_datetime(df_weekend["delivered_date"])

df_weekend["delivery_days"] = (
    df_weekend["delivered_date"] - df_weekend["shipped_date"]
).dt.days

df_weekend["day_of_week"] = df_weekend["shipped_date"].dt.day_name()

weekend_result = df_weekend.groupby("day_of_week")["delivery_days"].mean()

print("Середній час доставки по днях тижня:")
print(weekend_result)

weekend_result.plot(kind="bar")

plt.title("Weekend effect: середній час доставки по днях тижня")
plt.xlabel("День тижня відправлення")
plt.ylabel("Середній час доставки, дні")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()