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

# Визначити найкраще співвідношення ціна/швидкість.
def analyze_shipping_value():
    conn = get_connection()

    query = """
        SELECT 
            s.name AS shipper_name,
            AVG(sh.cost) AS avg_cost,
            AVG(julianday(sh.delivered_date) - julianday(sh.shipped_date)) AS avg_delivery_days
        FROM shipments sh
        JOIN shippers s ON sh.shipper_id = s.shipper_id
        WHERE sh.delivered_date IS NOT NULL AND sh.shipped_date IS NOT NULL AND sh.cost > 0
        GROUP BY s.shipper_id
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Недостатньо даних про доставку для аналіза.")
            return

        df = df[df['avg_delivery_days'] > 0]

        df['cost_per_day'] = df['avg_cost'] / df['avg_delivery_days']

        df_sorted = df.sort_values(by='cost_per_day', ascending=True)

        print("АНАЛІЗ СЛУЖБ ДОСТАВКИ (ЦІНА / ШВИДКІСТЬ)")
        print(df_sorted.to_string(index=False, formatters={
            'avg_cost': '{:.2f}'.format,
            'avg_delivery_days': '{:.1f}'.format,
            'cost_per_day': '{:.2f}'.format
        }))

        best = df_sorted.iloc[0]
        print(f"\nНайкращій перевізник: {best['shipper_name']}")
        print(f"Середня швидкість: {best['avg_delivery_days']:.1f} дн. | Середня ціна: {best['avg_cost']:.2f}")

    except Exception as e:
        print(f"Помилка аналіза: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_shipping_value()