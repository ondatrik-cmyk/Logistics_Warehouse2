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

# Швидкість обробки замовлення (Order Processing Time).
# Box Plot processing_time по складах.
# Box Plot processing_time по категоріях.
# Box Plot processing_time по країнах.
# Line Chart середнього processing_time за місяцями.
def analyze_order_processing_time():
    conn = get_connection()

    query = """
    SELECT 
        o.order_date,
        s.shipped_date,
        w.name AS warehouse_name,
        c.name AS category_name,
        o.ship_country
    FROM shipments s
    JOIN orders o ON s.order_id = o.order_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN categories c ON p.category_id = c.category_id
    JOIN inventory i ON p.product_id = i.product_id
    JOIN warehouses w ON i.warehouse_id = w.warehouse_id
    WHERE o.order_date IS NOT NULL 
      AND s.shipped_date IS NOT NULL;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Дані не знайдені. Перевірте зв'язки між таблицями orders, shipments та inventory.")
        return

    df['order_date'] = pd.to_datetime(df['order_date'])
    df['shipped_date'] = pd.to_datetime(df['shipped_date'])

    df['processing_time'] = (df['shipped_date'] - df['order_date']).dt.days
    df = df[df['processing_time'] >= 0]

    df['year_month'] = df['order_date'].dt.to_period('M').astype(str)

    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.suptitle('Аналіз швидкості обробки замовлень (Order Processing Time)', fontsize=18, fontweight='bold', y=0.98)

    sns.boxplot(
        ax=axes[0, 0],
        x='warehouse_name',
        y='processing_time',
        data=df,
        palette='Set2'
    )
    axes[0, 0].set_title('Розподіл часу обробки по складах', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Назва складу')
    axes[0, 0].set_ylabel('Час обробки (дні)')
    axes[0, 0].tick_params(axis='x', rotation=25)
    axes[0, 0].grid(axis='y', linestyle='--', alpha=0.5)

    sns.boxplot(
        ax=axes[0, 1],
        x='category_name',
        y='processing_time',
        data=df,
        palette='Pastel1'
    )
    axes[0, 1].set_title('Розподіл часу обробки по категоріях товарів', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Категорія')
    axes[0, 1].set_ylabel('Час обробки (дні)')
    axes[0, 1].tick_params(axis='x', rotation=25)
    axes[0, 1].grid(axis='y', linestyle='--', alpha=0.5)

    top_countries = df['ship_country'].value_counts().nlargest(10).index
    df_top_countries = df[df['ship_country'].isin(top_countries)]

    sns.boxplot(
        ax=axes[1, 0],
        x='ship_country',
        y='processing_time',
        data=df_top_countries,
        order=top_countries,
        palette='Accent'
    )
    axes[1, 0].set_title('Розподіл часу обробки по країнах доставки (Топ-10)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Країна')
    axes[1, 0].set_ylabel('Час обробки (дні)')
    axes[1, 0].tick_params(axis='x', rotation=25)
    axes[1, 0].grid(axis='y', linestyle='--', alpha=0.5)

    monthly_avg = df.groupby('year_month')['processing_time'].mean().reset_index()
    monthly_avg = monthly_avg.sort_values('year_month')

    sns.lineplot(
        ax=axes[1, 1],
        x='year_month',
        y='processing_time',
        data=monthly_avg,
        marker='o',
        color='#e74c3c',
        linewidth=2.5
    )
    axes[1, 1].set_title('Динаміка середнього часу обробки за місяцями', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Період (Місяць)')
    axes[1, 1].set_ylabel('Середній час (дні)')
    axes[1, 1].tick_params(axis='x', rotation=35)
    axes[1, 1].grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    try:
        analyze_order_processing_time()
    except Exception as e:
        print(f"Сталася помилка: {e}")
        print("Перевірте назви колонок країн в orders (o.shipping_country) та логіку зв'язку замовлень із складами.")