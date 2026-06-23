
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

weekend_result = weekend_result.reindex(
    ["Friday", "Saturday", "Sunday"]
)

weekend_result.plot(kind="bar")

plt.title("Weekend Effect")
plt.xlabel("День відправлення")
plt.ylabel("Середній час доставки (дні)")
plt.show()


#- Проаналізувати тренд часу доставки за 2022–2026 роки

query_trend = """
SELECT
    shipped_date,
    delivered_date
FROM shipments
WHERE shipped_date IS NOT NULL
AND delivered_date IS NOT NULL
"""

df_trend = pd.read_sql_query(query_trend, conn)

df_trend["shipped_date"] = pd.to_datetime(df_trend["shipped_date"])
df_trend["delivered_date"] = pd.to_datetime(df_trend["delivered_date"])

df_trend["delivery_days"] = (df_trend["delivered_date"] - df_trend["shipped_date"]).dt.days

df_trend["year"] = df_trend["shipped_date"].dt.year

trend_result = df_trend.groupby("year")["delivery_days"].mean()

print(trend_result)

trend_result.plot(kind="line", marker="o")

plt.title("Тренд часу доставки 2022-2026")
plt.xlabel("Рік")
plt.ylabel("Середній час доставки (дні)")
plt.grid(True)

plt.show()