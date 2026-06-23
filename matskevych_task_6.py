import os
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')


def get_connection():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found {DB_PATH} ")
    return sqlite3.connect(DB_PATH)

# Створити метрику cost_per_day = shipping_cost / delivery_time.
def calculate_cost_per_day():
    conn = get_connection()

    query = """
    SELECT 
        order_id,
        shipper_id,
        cost,
        shipped_date,
        delivered_date
    FROM shipments
    WHERE shipped_date IS NOT NULL 
      AND delivered_date IS NOT NULL 
      AND cost IS NOT NULL;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Немає даних для розрахунку. Перевірте таблицю shipments.")
        return None

    df['shipped_date'] = pd.to_datetime(df['shipped_date'])
    df['delivered_date'] = pd.to_datetime(df['delivered_date'])

    df['delivery_time'] = (df['delivered_date'] - df['shipped_date']).dt.days

    df = df[df['delivery_time'] >= 0].copy()

    df['delivery_time_calc'] = df['delivery_time'].replace(0, 0.5)
    df['cost_per_day'] = df['cost'] / df['delivery_time_calc']

    df['cost_per_day'] = df['cost_per_day'].round(2)

    df = df.drop(columns=['delivery_time_calc'])

    return df


if __name__ == "__main__":
    result_df = calculate_cost_per_day()
    if result_df is not None:
        print("Результати розрахунку метрики cost_per_day (топ-10 рядків): ")
        print(result_df[['order_id', 'cost', 'delivery_time', 'cost_per_day']].head(10).to_string(index=False))