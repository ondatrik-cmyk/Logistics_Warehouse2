import os
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2_contingency

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, 'online_store.db')


def get_connection():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found {DB_PATH} ")
    return sqlite3.connect(DB_PATH)

# Проаналізувати розподіл часу обробки по складах.
def analyze_warehouse_processing_time():
    conn = get_connection()

    query = """
        SELECT 
            w.name AS warehouse_name,
            o.order_id,
            (julianday(sh.shipped_date) - julianday(o.order_date)) AS processing_time
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        JOIN order_items oi ON o.order_id = oi.product_id  -- зв'язок із товарами в замовленні
        JOIN inventory inv ON oi.product_id = inv.product_id
        JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
        WHERE sh.shipped_date IS NOT NULL 
          AND o.order_date IS NOT NULL
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print(
                "Дані відсутні або дати замовлень/відправлень не заповнені."
            )
            return

        df = df[df["processing_time"] >= 0]

        stats_df = (
            df.groupby("warehouse_name")
            .agg(
                total_items=("order_id", "count"),
                avg_time=("processing_time", "mean"),
                median_time=("processing_time", "median"),
                max_time=("processing_time", "max"),
            )
            .reset_index()
        )

        print("СТАТИСТИКА ЧАСУ ОБРОБКИ ПО СКЛАДАХ (ДНІ)")
        print(
            stats_df.to_string(
                index=False,
                formatters={
                    "total_items": "{:,}".format,
                    "avg_time": "{:.2f} дн.".format,
                    "median_time": "{:.1f} дн.".format,
                    "max_time": "{:.1f} дн.".format,
                },
            )
        )

        plt.figure(figsize=(11, 6))
        sns.set_theme(style="whitegrid")

        sns.boxplot(
            data=df,
            x="warehouse_name",
            y="processing_time",
            palette="Set2",
            hue="warehouse_name",
            legend=False,
        )

        plt.title(
            "Розподіл часу обробки замовлень по складах", fontsize=14
        )
        plt.xlabel("Назва складу", fontsize=12)
        plt.ylabel("Час обробки (дні від замовлення до відправки)", fontsize=12)
        plt.xticks(rotation=30, ha="right")

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_warehouse_processing_time()

# Перевірити залежність від категорії товару.
def analyze_processing_time_by_category():
    conn = get_connection()

    query = """
        SELECT 
            c.name AS category_name,
            o.order_id,
            (julianday(sh.shipped_date) - julianday(o.order_date)) AS processing_time
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE sh.shipped_date IS NOT NULL 
          AND o.order_date IS NOT NULL
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Дані про замовлення або категорії відсутні.")
            return

        df = df[df["processing_time"] >= 0]

        stats_df = (
            df.groupby("category_name")
            .agg(
                total_items=("order_id", "count"),
                avg_time=("processing_time", "mean"),
                median_time=("processing_time", "median"),
                max_time=("processing_time", "max"),
            )
            .reset_index()
        )

        stats_df = stats_df.sort_values(by="median_time", ascending=False)

        print("СТАТИСТИКА ЧАСУ ОБРОБКИ ЗА КАТЕГОРІЯМИ (ДНІ)")
        print(
            stats_df.to_string(
                index=False,
                formatters={
                    "total_items": "{:,} од.".format,
                    "avg_time": "{:.2f} дн.".format,
                    "median_time": "{:.1f} дн.".format,
                    "max_time": "{:.1f} дн.".format,
                },
            )
        )

        plt.figure(figsize=(12, 6))
        sns.set_theme(style="whitegrid")

        ax = sns.barplot(
            data=stats_df,
            x="category_name",
            y="median_time",
            palette="viridis",
            hue="category_name",
            legend=False,
        )

        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f"{height:.1f} дн.",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                xytext=(0, 3),
                textcoords="offset points",
            )

        plt.title(
            "Медіанний час обробки замовлень у розрізі категорій товарів",
            fontsize=14,
        )
        plt.xlabel("Категорія товару", fontsize=12)
        plt.ylabel("Медіанний час обробки (дні)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, stats_df["median_time"].max() * 1.15)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_processing_time_by_category()

# Перевірити залежність від країни доставки.
def analyze_processing_time_by_country():
    conn = get_connection()

    query = """
        SELECT 
            o.ship_country AS country_name,
            o.order_id,
            (julianday(sh.shipped_date) - julianday(o.order_date)) AS processing_time
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        WHERE sh.shipped_date IS NOT NULL 
          AND o.order_date IS NOT NULL
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Дані про замовлення або країни відсутні.")
            return

        df = df[df["processing_time"] >= 0]

        stats_df = (
            df.groupby("country_name")
            .agg(
                total_orders=("order_id", "count"),
                avg_time=("processing_time", "mean"),
                median_time=("processing_time", "median"),
                max_time=("processing_time", "max"),
            )
            .reset_index()
        )

        stats_df = stats_df.sort_values(by="median_time", ascending=False)

        print("СТАТИСТИКА ЧАСУ ОБРОБКИ ЗА КРАЇНАМИ (ДНІ)")
        print(
            stats_df.to_string(
                index=False,
                formatters={
                    "total_orders": "{:,} замовл.".format,
                    "avg_time": "{:.2f} дн.".format,
                    "median_time": "{:.1f} дн.".format,
                    "max_time": "{:.1f} дн.".format,
                },
            )
        )

        plt.figure(figsize=(12, 6))
        sns.set_theme(style="whitegrid")

        ax = sns.barplot(
            data=stats_df,
            x="country_name",
            y="median_time",
            palette="viridis",
            hue="country_name",
            legend=False,
        )

        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f"{height:.1f} дн.",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                xytext=(0, 3),
                textcoords="offset points",
            )

        plt.title(
            "Медіанний час обробки замовлень залежно від країни доставки",
            fontsize=14,
        )
        plt.xlabel("Країна доставки", fontsize=12)
        plt.ylabel("Медіанний час обробки (дні)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, stats_df["median_time"].max() * 1.15)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_processing_time_by_country()

# Виявити сезонність часу обробки.
def analyze_processing_seasonality():
    conn = get_connection()

    query = """
        SELECT 
            strftime('%m', o.order_date) AS month_num,
            o.order_id,
            (julianday(sh.shipped_date) - julianday(o.order_date)) AS processing_time
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        WHERE sh.shipped_date IS NOT NULL 
          AND o.order_date IS NOT NULL
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Дані про дати замовлень або відправлень відсутні.")
            return

        df = df[df["processing_time"] >= 0]

        monthly_stats = (
            df.groupby("month_num")
            .agg(
                total_orders=("order_id", "count"),
                avg_time=("processing_time", "mean"),
                median_time=("processing_time", "median"),
            )
            .reset_index()
        )

        months_map = {
            "01": "Січень",
            "02": "Лютий",
            "03": "Березень",
            "04": "Квітень",
            "05": "Травень",
            "06": "Червень",
            "07": "Липень",
            "08": "Серпень",
            "09": "Вересень",
            "10": "Жовтень",
            "11": "Листопад",
            "12": "Грудень",
        }
        monthly_stats["month_name"] = monthly_stats["month_num"].map(months_map)

        print("СЕЗОННІСТЬ ЧАСУ ОБРОБКИ ЗА МІСЯЦЯМИ")
        print(
            monthly_stats.to_string(
                index=False,
                columns=["month_name", "total_orders", "avg_time", "median_time"],
                formatters={
                    "total_orders": "{:,} замовл.".format,
                    "avg_time": "{:.2f} дн.".format,
                    "median_time": "{:.1f} дн.".format,
                },
            )
        )

        plt.figure(figsize=(12, 6))
        sns.set_theme(style="whitegrid")

        sns.lineplot(
            data=monthly_stats,
            x="month_name",
            y="avg_time",
            marker="o",
            linewidth=2.5,
            label="Середній час",
            color="royalblue",
        )
        sns.lineplot(
            data=monthly_stats,
            x="month_name",
            y="median_time",
            marker="s",
            linewidth=2,
            linestyle="--",
            label="Медіанний час",
            color="orange",
        )

        ax2 = plt.gca().twinx()
        sns.barplot(
            data=monthly_stats,
            x="month_name",
            y="total_orders",
            alpha=0.15,
            color="gray",
            ax=ax2,
            hue="month_name",
            legend=False,
        )
        ax2.set_ylabel("Загальна кількість замовлень", color="gray", fontsize=12)
        ax2.grid(False)

        plt.title(
            "Сезонні коливання часу обробки замовлень протягом року", fontsize=14
        )
        plt.gca().set_xlabel("Місяць року", fontsize=12)
        plt.gca().set_ylabel("Час обробки (дні)", fontsize=12)
        plt.xticks(rotation=30)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_processing_seasonality()

# Знайти bottlenecks у процесі виконання замовлень.
def find_fulfillment_bottlenecks():
    conn = get_connection()

    query = """
        SELECT 
            w.name AS warehouse_name,
            s.name AS shipper_name,
            (julianday(sh.shipped_date) - julianday(o.order_date)) AS processing_days,
            (julianday(sh.delivered_date) - julianday(sh.shipped_date)) AS transit_days
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        JOIN shippers s ON sh.shipper_id = s.shipper_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN inventory inv ON oi.product_id = inv.product_id
        JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
        WHERE sh.delivered_date IS NOT NULL 
          AND sh.shipped_date IS NOT NULL 
          AND o.order_date IS NOT NULL
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Немає даних для аналізу.")
            return

        df = df[(df["processing_days"] >= 0) & (df["transit_days"] >= 0)]

        print("АНАЛІЗ ВУЗЬКИХ МІСЦЬ (BOTTLENECK ANALYSIS)")

        wh_stats = (
            df.groupby("warehouse_name")["processing_days"]
            .agg(["count", "mean", "median", "max"])
            .sort_values(by="median", ascending=False)
        )
        print("\nЕТАП 1: затримки при збиранні на складах (Processing)")
        print("-" * 60)
        print(
            wh_stats.to_string(
                formatters={
                    "count": "{:,} шт.".format,
                    "mean": "{:.2f} дн.".format,
                    "median": "{:.1f} дн.".format,
                    "max": "{:.1f} дн.".format,
                }
            )
        )

        shipper_stats = (
            df.groupby("shipper_name")["transit_days"]
            .agg(["count", "mean", "median", "max"])
            .sort_values(by="median", ascending=False)
        )
        print("\nЕТАП 2: затримки на шляху у перевізників (Transit)")
        print("-" * 60)
        print(
            shipper_stats.to_string(
                formatters={
                    "count": "{:,} шт.".format,
                    "mean": "{:.2f} дн.".format,
                    "median": "{:.1f} дн.".format,
                    "max": "{:.1f} дн.".format,
                }
            )
        )

        melted_df = df.melt(
            value_vars=["processing_days", "transit_days"],
            var_name="Logistics_Stage",
            value_name="Days",
        )
        melted_df["Logistics_Stage"] = melted_df["Logistics_Stage"].map(
            {
                "processing_days": "1. Збирання на складі",
                "transit_days": "2. Час при транспортуванні",
            }
        )

        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid")

        sns.barplot(
            data=melted_df,
            x="Logistics_Stage",
            y="Days",
            errorbar=None,
            palette="Oranges_r",
            hue="Logistics_Stage",
            legend=False,
        )

        ax = plt.gca()
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f"Середнє: {height:.2f} дн.",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
                xytext=(0, 5),
                textcoords="offset points",
            )

        plt.title(
            "Де замовлення проводять найбільше часу (Склад vs Доставка)?",
            fontsize=14,
        )
        plt.xlabel("Етап виконання замовлення", fontsize=12)
        plt.ylabel("Середня кількість днів", fontsize=12)
        plt.ylim(0, melted_df["Days"].mean() * 1.5)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час виконання аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    find_fulfillment_bottlenecks()
