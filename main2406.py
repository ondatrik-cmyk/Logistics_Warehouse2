
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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
#1Клієнт скаржиться, що замовив товар 2 тижні тому, а доставки досі немає
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



#2- Перевірити наявність weekend effect (відправлення у п'ятницю або вихідні)
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


#-3 Проаналізувати тренд часу доставки за 2022–2026 роки

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

#-4 Heatmap warehouse × category- Географічна карта складів та країн замовлень

print("\n--- Heatmap warehouse x category ---")

import seaborn as sns

query_heatmap = """
SELECT
    w.name AS warehouse_name,
    c.name AS category_name,
    COUNT(o.order_id) AS orders_count
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
JOIN inventory i ON p.product_id = i.product_id
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
GROUP BY w.name, c.name
"""

df_heatmap = pd.read_sql_query(query_heatmap, conn)

print(df_heatmap)

pivot = df_heatmap.pivot_table(
    values="orders_count",
    index="warehouse_name",
    columns="category_name",
    aggfunc="sum",
    fill_value=0
)

plt.figure(figsize=(10, 6))
sns.heatmap(pivot, annot=True, fmt=".0f")
plt.title("Heatmap: склад × категорія")
plt.xlabel("Категорія")
plt.ylabel("Склад")
plt.tight_layout()
plt.show()


#- 5Побудувати Heatmap (month × day_of_week) середнього часу доставки
print("\n--- Heatmap month x day_of_week ---")

query_heatmap = """
SELECT
    shipped_date,
    delivered_date
FROM shipments
WHERE shipped_date IS NOT NULL
AND delivered_date IS NOT NULL
"""

df_heatmap = pd.read_sql_query(query_heatmap, conn)

df_heatmap["shipped_date"] = pd.to_datetime(df_heatmap["shipped_date"])
df_heatmap["delivered_date"] = pd.to_datetime(df_heatmap["delivered_date"])

df_heatmap["delivery_days"] = (df_heatmap["delivered_date"] -df_heatmap["shipped_date"]).dt.days

df_heatmap["month"] = df_heatmap["shipped_date"].dt.month
df_heatmap["day_of_week"] = df_heatmap["shipped_date"].dt.day_name()

print(df_heatmap.head())
print(df_heatmap.columns)

pivot = pd.pivot_table(
    df_heatmap,
    values="delivery_days",
    index="month",
    columns="day_of_week",
    aggfunc="mean")

plt.figure(figsize=(12, 6))
sns.heatmap(pivot, annot=True, fmt=".1f")
plt.title("Heatmap Month × Day of Week)")
plt.xlabel("День тижня")
plt.ylabel("Місяць")
plt.tight_layout()
plt.show()


#6 Прогнозування обсягу відвантажень

query = """
SELECT
    DATE(shipped_date) as ship_date,
    COUNT(*) as shipments_count
FROM shipments
WHERE shipped_date IS NOT NULL
GROUP BY DATE(shipped_date)
ORDER BY ship_date
"""

df = pd.read_sql_query(query, conn)

df["ship_date"] = pd.to_datetime(df["ship_date"])

forecast = df["shipments_count"].mean()
# Forecast vs Actual
plt.figure(figsize=(10,5))
plt.plot(df["ship_date"], df["shipments_count"], label="Actual")
plt.axhline(forecast, linestyle="--", label="Forecast")
plt.title("Forecast vs Actual")
plt.legend()
plt.show()

# Residual Plot
df["residual"] = df["shipments_count"] - forecast

plt.figure(figsize=(10,5))
plt.scatter(df["ship_date"], df["residual"])
plt.axhline(0, linestyle="--")
plt.title("Residual Plot")
plt.show()

# Seasonal Plot по місяцях
df["month"] = df["ship_date"].dt.month

seasonal = df.groupby("month")["shipments_count"].mean()

plt.figure(figsize=(8,5))
seasonal.plot(kind="bar")
plt.title("Seasonal Decomposition Plot")
plt.xlabel("Month")
plt.ylabel("Average Shipments")
plt.show()

#-7 Перевірити залежність між вартістю та швидкістю доставки
print("\n--- Вартість vs швидкість доставки ---")

query_cost = """
SELECT
    s.cost,
    s.shipped_date,
    s.delivered_date
FROM shipments s
WHERE s.shipped_date IS NOT NULL
AND s.delivered_date IS NOT NULL
AND s.cost IS NOT NULL
"""

df_cost = pd.read_sql_query(query_cost, conn)

df_cost["shipped_date"] = pd.to_datetime(df_cost["shipped_date"])
df_cost["delivered_date"] = pd.to_datetime(df_cost["delivered_date"])

df_cost["delivery_days"] = (df_cost["delivered_date"] - df_cost["shipped_date"]).dt.days

df_cost["cost_group"] = pd.cut(df_cost["cost"], bins=5)

cost_result = df_cost.groupby("cost_group")["delivery_days"].mean()

cost_result.plot(
    kind="line",
    marker="o")
plt.title("Вартість vs швидкість доставки")
plt.xlabel("Група вартості")
plt.ylabel("Середній час доставки (дні)")
plt.grid(True)
plt.ylim(0,5)
plt.show()


#8Наближається Black Friday. Відділ закупівель хоче знати — чи **вистачить місця на складах** для додаткових запасів?
#8.1Порахувати ** поточну заповненість кожного складу ** (сума quantity у inventory)

print("\n--- Заповненість складів ---")

query_storage = """
SELECT
    w.name AS warehouse_name,
    SUM(i.quantity) AS total_quantity
FROM inventory i
JOIN warehouses w
ON i.warehouse_id = w.warehouse_id
GROUP BY w.name
"""

df_storage = pd.read_sql_query(query_storage, conn)
print(df_storage)

#8.2. Якщо припустити, що кожен склад може вмістити на 30% більше — скільки ще товарів можна дозавантажити?
df_storage["max_capacity"] = df_storage["total_quantity"] * 1.3
df_storage["free_space"] = (df_storage["max_capacity"]- df_storage["total_quantity"])

print(df_storage[["warehouse_name", "total_quantity", "free_space"]])

#8.3 Які **категорії товарів** займають найбільше місця на кожному складі?

print("\n--- Категорії на складах ---")
query_category = """
SELECT
    w.name AS warehouse_name,
    c.name AS category_name,
    SUM(i.quantity) AS total_quantity
FROM inventory i
JOIN warehouses w
ON i.warehouse_id = w.warehouse_id
JOIN products p
ON i.product_id = p.product_id
JOIN categories c
ON p.category_id = c.category_id
GROUP BY w.name, c.name
ORDER BY total_quantity DESC
"""

df_category = pd.read_sql_query(query_category, conn)

print(df_category)

#8.4. Побудувати **bar chart** — заповненість складів з лінією 70% (резерв)
plt.figure(figsize=(10,5))
plt.bar(df_storage["warehouse_name"],df_storage["total_quantity"])
reserve_line = (df_storage["max_capacity"] * 0.7).mean()

plt.axhline(
    reserve_line,
    color="red",
    linestyle="--",
    label="70% резерв")

plt.title("Заповненість складів")
plt.xlabel("Склад")
plt.ylabel("Кількість товару")

plt.legend()
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

#8.5. Визначити склади, які працюють на **понад 80% ємності** — там можливий дефіцит місця
df_storage["load_percent"] = (df_storage["total_quantity"]/ df_storage["max_capacity"]) * 100

risk_storage = df_storage[df_storage["load_percent"] > 80]

print("\nСклади понад 80% завантаження:")

print(risk_storage[
          ["warehouse_name",
           "load_percent"]])

#9.- Агрегувати shipments по місяцях
# - Виконати декомпозицію:
# - Trend   - Seasonality   - Residuals - Визначити пікові місяці та сезонні коливання
# - Побудувати прогноз на 6 місяців:   - Moving Average   - Exponential Smoothing
# - Лінійна регресія по тренду - Порівняти фактичні та прогнозні значення

query_forecast = """
SELECT
    DATE(shipped_date, 'start of month') AS month,
    COUNT(*) AS shipments
FROM shipments
WHERE shipped_date IS NOT NULL
GROUP BY month
ORDER BY month
"""

df_forecast = pd.read_sql_query(query_forecast, conn)
df_forecast["month"] = pd.to_datetime(df_forecast["month"])

df_forecast["moving_average"] = df_forecast["shipments"].rolling(window=3).mean()

alpha = 0.3
df_forecast["exp_smoothing"] = df_forecast["shipments"].copy()

for i in range(1, len(df_forecast)):
    df_forecast.loc[i, "exp_smoothing"] = (
        alpha * df_forecast.loc[i, "shipments"] +
        (1 - alpha) * df_forecast.loc[i - 1, "exp_smoothing"])

last = df_forecast.tail(12).copy()

x = np.arange(len(last))
y = last["shipments"]
m, b = np.polyfit(x, y, 1)
last["linear_regression"] = m * x + b

future_x = np.arange(len(last), len(last) + 6)
future_forecast = m * future_x + b

future_months = pd.date_range(
    last["month"].iloc[-1] + pd.DateOffset(months=1),
    periods=6,
    freq="MS")

df_future = pd.DataFrame({
    "month": future_months,
    "forecast": future_forecast})

print("Прогноз на 6 місяців:")
print(df_future)

plt.figure(figsize=(12, 6))

plt.plot(
    df_forecast["month"],
    df_forecast["shipments"],
    marker="o",
    label="Actual")

plt.plot(
    df_forecast["month"],
    df_forecast["moving_average"],
    marker="o",
    label="Moving Average")

plt.plot(
    df_forecast["month"],
    df_forecast["exp_smoothing"],
    marker="o",
    label="Exponential Smoothing")

plt.plot(
    last["month"],
    last["linear_regression"],
    color="red",
    linewidth=3,
    label="Linear Regression")

plt.plot(
    df_future["month"],
    df_future["forecast"],
    "r--",
    linewidth=3,
    label="Forecast 6 months")

plt.title("Прогнозування обсягу відвантажень")
plt.xlabel("Місяць")
plt.ylabel("Кількість відвантажень")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()