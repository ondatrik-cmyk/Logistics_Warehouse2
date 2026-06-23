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

# Stacked Bar Chart повернення/не повернення по shipper
# Grouped Bar Chart причина повернення × shipper
# Bar Chart return_rate по delivery_bucket
def analyze_returns_and_delivery():
    conn = get_connection()

    query = """
    SELECT 
        s.order_id,
        s.shipped_date,
        s.delivered_date,
        sh.name AS shipper_name,
        r.reason AS return_reason,
        CASE WHEN r.return_id IS NOT NULL THEN 'Returned' ELSE 'Not Returned' END AS return_status
    FROM shipments s
    JOIN shippers sh ON s.shipper_id = sh.shipper_id
    LEFT JOIN returns r ON s.order_id = r.order_id
    WHERE s.shipped_date IS NOT NULL AND s.delivered_date IS NOT NULL;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Дані для аналізу відсутні. Перевірте заповненість таблиць.")
        return

    df['shipped_date'] = pd.to_datetime(df['shipped_date'])
    df['delivered_date'] = pd.to_datetime(df['delivered_date'])
    df['delivery_time'] = (df['delivered_date'] - df['shipped_date']).dt.days
    df = df[df['delivery_time'] >= 0]

    bins = [-1, 2, 5, 10, 20, float('inf')]
    labels = ['0-2 дні', '3-5 днів', '6-10 днів', '11-20 днів', '20+ днів']
    df['delivery_bucket'] = pd.cut(df['delivery_time'], bins=bins, labels=labels)

    fig, axes = plt.subplots(1, 3, figsize=(22, 6))
    fig.suptitle('Аналіз повернень товарів у розрізі перевізників та термінів доставки', fontsize=16, fontweight='bold',
                 y=1.02)

    shipper_returns = pd.crosstab(df['shipper_name'], df['return_status'])
    shipper_returns.plot(
        kind='bar',
        stacked=True,
        ax=axes[0],
        color=['#2ecc71', '#e74c3c'],
        alpha=0.85
    )
    axes[0].set_title('Загальна кількість замовлень та повернень')
    axes[0].set_xlabel('Перевізник')
    axes[0].set_ylabel('Кількість замовлень')
    axes[0].tick_params(axis='x', rotation=30)
    axes[0].legend(title='Статус замовлення')
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)

    df_returned = df[df['return_status'] == 'Returned'].copy()

    if not df_returned.empty and df_returned['return_reason'].notna().any():
        sns.countplot(
            ax=axes[1],
            x='return_reason',
            hue='shipper_name',
            data=df_returned,
            palette='Set2'
        )
        axes[1].set_title('Причини повернення в розрізі перевізників')
        axes[1].set_xlabel('Причина повернення')
        axes[1].set_ylabel('Кількість повернень')
        axes[1].tick_params(axis='x', rotation=30)
        axes[1].legend(title='Перевізник')
        axes[1].grid(axis='y', linestyle='--', alpha=0.5)
    else:
        axes[1].text(0.5, 0.5, 'Немає даних про\nпричини повернень', ha='center', va='center', fontsize=12)
        axes[1].set_title('Причини повернення в розрізі перевізників')

    df['is_returned'] = df['return_status'].apply(lambda x: 1 if x == 'Returned' else 0)

    bucket_return_rate = df.groupby('delivery_bucket', observed=False)['is_returned'].mean().reset_index()
    bucket_return_rate['return_rate_pct'] = bucket_return_rate['is_returned'] * 100

    sns.barplot(
        ax=axes[2],
        x='delivery_bucket',
        y='return_rate_pct',
        data=bucket_return_rate,
        palette='YlOrRd'
    )
    axes[2].set_title('Рівень повернень (Return Rate) відносно терміну доставки')
    axes[2].set_xlabel('Тривалість доставки')
    axes[2].set_ylabel('% повернень від загальної кількості')
    axes[2].grid(axis='y', linestyle='--', alpha=0.5)

    for p in axes[2].patches:
        axes[2].annotate(f"{p.get_height():.1f}%",
                         (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='center',
                         xytext=(0, 5),
                         textcoords='offset points',
                         fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    analyze_returns_and_delivery()