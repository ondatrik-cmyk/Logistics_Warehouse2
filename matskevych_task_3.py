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

# Аномалії вартості доставки.
# Scatter Plot (shipping_cost vs delivery_time) з кольором по shipper.
# Box Plot shipping_cost по shipper.
# Bar Chart середнього cost_per_day.
def analyze_shipping_cost_anomalies():
    conn = get_connection()

    query = """
    SELECT 
        s.cost AS shipping_cost,
        s.shipped_date,
        s.delivered_date,
        sh.name AS shipper_name
    FROM shipments s
    JOIN shippers sh ON s.shipper_id = sh.shipper_id
    WHERE s.shipped_date IS NOT NULL 
      AND s.delivered_date IS NOT NULL 
      AND s.cost IS NOT NULL;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Перевірте зв'язки між таблицями.")
        return

    df['shipped_date'] = pd.to_datetime(df['shipped_date'])
    df['delivered_date'] = pd.to_datetime(df['delivered_date'])
    df['delivery_time'] = (df['delivered_date'] - df['shipped_date']).dt.days

    df = df[df['delivery_time'] >= 0]

    df['delivery_time_calc'] = df['delivery_time'].replace(0, 0.5)
    df['cost_per_day'] = df['shipping_cost'] / df['delivery_time_calc']

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle('Аналіз аномалій вартості доставки', fontsize=16, fontweight='bold', y=1.02)

    sns.scatterplot(
        ax=axes[0],
        x='delivery_time',
        y='shipping_cost',
        hue='shipper_name',
        data=df,
        alpha=0.7,
        palette='tab10'
    )
    axes[0].set_title('Вартість vs Час доставки')
    axes[0].set_xlabel('Час доставки (дні)')
    axes[0].set_ylabel('Вартість доставки (у.о.)')
    axes[0].grid(True, linestyle='--', alpha=0.5)

    sns.boxplot(
        ax=axes[1],
        x='shipper_name',
        y='shipping_cost',
        data=df,
        palette='Set2'
    )
    axes[1].set_title('Розподіл вартості по перевізниках')
    axes[1].set_xlabel('Перевізник')
    axes[1].set_ylabel('Вартість доставки (у.о.)')
    axes[1].tick_params(axis='x', rotation=30)
    axes[1].grid(axis='y', linestyle='--', alpha=0.5)

    avg_cost_per_day = df.groupby('shipper_name')['cost_per_day'].mean().reset_index()

    sns.barplot(
        ax=axes[2],
        x='shipper_name',
        y='cost_per_day',
        data=avg_cost_per_day,
        palette='coolwarm'
    )
    axes[2].set_title('Середня вартість доставки за 1 день')
    axes[2].set_xlabel('Перевізник')
    axes[2].set_ylabel('Вартість за день в дорозі (у.о./день)')
    axes[2].tick_params(axis='x', rotation=30)
    axes[2].grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    analyze_shipping_cost_anomalies()