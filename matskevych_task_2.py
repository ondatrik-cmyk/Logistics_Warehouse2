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

# Побудувати розподіл часу доставки по днях тижня.
def plot_delivery_distribution():
    conn = get_connection()

    query = """
    SELECT shipped_date, delivered_date 
    FROM shipments 
    WHERE shipped_date IS NOT NULL AND delivered_date IS NOT NULL;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['shipped_date'] = pd.to_datetime(df['shipped_date'])
    df['delivered_date'] = pd.to_datetime(df['delivered_date'])

    df['delivery_time'] = (df['delivered_date'] - df['shipped_date']).dt.days

    df = df[df['delivery_time'] >= 0]

    df['weekday'] = df['shipped_date'].dt.day_name()

    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    ua_days = {
        'Monday': 'Понеділок', 'Tuesday': 'Вівторок', 'Wednesday': 'Середа',
        'Thursday': 'Четвер', 'Friday': 'П\'ятниця', 'Saturday': 'Субота', 'Sunday': 'Неділя'
    }
    df['weekday'] = df['weekday'].map(ua_days)
    weekday_order_ua = [ua_days[day] for day in weekday_order]

    plt.figure(figsize=(12, 6))
    sns.boxplot(
        x='weekday',
        y='delivery_time',
        data=df,
        order=weekday_order_ua,
        palette='Set3',
        fliersize=4
    )

    plt.title('Розподіл часу доставки залежно від дня тижня відправки', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('День тижня відправки', fontsize=12)
    plt.ylabel('Час доставки (дні)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    try:
        plot_delivery_distribution()
    except Exception as e:
        print(f"Помилка при побудові графіка: {e}")