# Logistics_Warehouse2
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
    s.shipper_id,
    sh.name AS shipper_name
FROM shipments s
JOIN shippers sh ON s.shipper_id = sh.shipper_id
WHERE s.delivered_date IS NULL
  AND s.shipped_date IS NOT NULL
  AND DATE(s.shipped_date) <= DATE('now', '-7 days')
"""

df = pd.read_sql_query(query, conn)

print("Завислі доставки:")
print(df)

print("Кількість завислих доставок:")
print(len(df))

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
    s.shipper_id,
    sh.name AS shipper_name
FROM shipments s
JOIN shippers sh ON s.shipper_id = sh.shipper_id
WHERE s.delivered_date IS NULL
  AND s.shipped_date IS NOT NULL
  AND DATE(s.shipped_date) <= DATE('now', '-7 days')
"""

df = pd.read_sql_query(query, conn)

#Клієнт скаржиться, що замовив товар 2 тижні тому, а доставки досі немає
print("Завислі доставки:")
print(df)

print("Кількість завислих доставок:")
print(len(df))

if df.empty:
    print("Завислих доставок немає")
else:
    shipper_stats = df.groupby("shipper_name")["shipment_id"].count()

    print("По перевізниках:")
    print(shipper_stats)

    shipper_stats.plot(kind="bar")

    plt.title("Загублені відправлення по перевізниках")
    plt.xlabel("Перевізник")
    plt.ylabel("Кількість")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
