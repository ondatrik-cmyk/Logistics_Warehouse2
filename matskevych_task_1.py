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

# Дослідити вплив дня тижня відправки на швидкість доставки.
def analyze_delivery_by_weekday():
    conn = get_connection()

    query = """
    SELECT 
        s.shipped_date,
        s.delivered_date,
        sh.name
    FROM shipments s
    JOIN orders o ON s.order_id = o.order_id
    JOIN shippers sh ON s.shipper_id = sh.shipper_id
    WHERE s.shipped_date IS NOT NULL AND s.delivered_date IS NOT NULL;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df['shipped_date'] = pd.to_datetime(df['shipped_date'])
    df['delivered_date'] = pd.to_datetime(df['delivered_date'])

    df['delivery_time_days'] = (df['delivered_date'] - df['shipped_date']).dt.days

    df = df[df['delivery_time_days'] >= 0]

    df['shipment_weekday_num'] = df['shipped_date'].dt.weekday
    df['shipment_weekday'] = df['shipped_date'].dt.day_name()

    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    summary = df.groupby('shipment_weekday')['delivery_time_days'].agg(['mean', 'median', 'count']).reindex(
        weekday_order)
    print("Зведена статистика по днях тижня: ")
    print(summary)

    plt.figure(figsize=(10, 5))
    sns.barplot(
        x='shipment_weekday',
        y='delivery_time_days',
        data=df,
        order=weekday_order,
        errorbar=None,
        palette='viridis'
    )
    plt.title('Середня швидкість доставки в залежності від дня відправки')
    plt.xlabel('День тижня відправки')
    plt.ylabel('Середня кількість днів')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10, 5))
    sns.boxplot(
        x='shipment_weekday',
        y='delivery_time_days',
        data=df,
        order=weekday_order,
        palette='pastel'
    )
    plt.title('Розподіл часу доставки по днях відправки')
    plt.xlabel('День тижня відправки')
    plt.ylabel('Днів у дорозі')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        analyze_delivery_by_weekday()
    except Exception as e:
        print(f"Помилка при аналізі: {e}")
        print("Перевірте точні назви стовпців.")

# Розрахувати delivery_time = delivered_date - shipped_date.
def calculate_delivery_time():
    conn = get_connection()

    query = """
    SELECT 
        order_id,
        shipped_date,
        delivered_date,
        (julianday(delivered_date) - julianday(shipped_date)) AS delivery_time
    FROM shipments
    WHERE shipped_date IS NOT NULL AND delivered_date IS NOT NULL;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df['delivery_time'] = df['delivery_time'].round(2)

    df = df[df['delivery_time'] >= 0]

    return df


if __name__ == "__main__":
    try:
        delivery_df = calculate_delivery_time()
        print("Результати розрахунку delivery_time (перші 10 строк): ")
        print(delivery_df.head(10).to_string(index=False))
    except Exception as e:
        print(f"Виникла помилка: {e}")
        print("Перевірте, що колонки shipped_date и delivered_date знаходяться в таблиці shipments.")
