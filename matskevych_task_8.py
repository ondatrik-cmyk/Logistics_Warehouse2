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

# Перевірити кореляцію між delivery_time та return_rate.
def analyze_delivery_vs_returns():
    conn = get_connection()

    query = """
        SELECT 
            o.order_id,
            o.ship_country,
            (julianday(sh.delivered_date) - julianday(sh.shipped_date)) AS delivery_time,
            CASE WHEN r.return_id IS NOT NULL THEN 1 ELSE 0 END AS is_returned
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        LEFT JOIN returns r ON o.order_id = r.order_id
        WHERE sh.delivered_date IS NOT NULL 
          AND sh.shipped_date IS NOT NULL
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Немає даних для аналізу. Перевірте заповненість таблиць.")
            return

        df = df[df["delivery_time"] >= 0]

        country_stats = (
            df.groupby("ship_country")
            .agg(
                avg_delivery_time=("delivery_time", "mean"),
                return_rate=("is_returned", "mean"),
                total_orders=("order_id", "count"),
            )
            .reset_index()
        )

        country_stats = country_stats[country_stats["total_orders"] >= 5]

        if len(country_stats) < 2:
            print(
                "Недостатньо груп (країн) із замовленнями для розрахунку кореляції."
            )
            print("Загальна статистика по замовленнях:")
            print(country_stats)
            return

        correlation = country_stats["avg_delivery_time"].corr(
            country_stats["return_rate"]
        )

        print("СТАТИСТИКА ПО КРАЇНАХ")
        print(
            country_stats.to_string(
                index=False,
                formatters={
                    "avg_delivery_time": "{:.1f} дн.".format,
                    "return_rate": "{:.2%}".format,
                },
            )
        )

        print("\nРЕЗУЛЬТАТ АНАЛІЗУ КОРЕЛЯЦІЇ")
        print(f"Коефіцієнт кореляції Пірсона: {correlation:.4f}")

        if abs(correlation) < 0.1:
            print("Висновок: Лінійна кореляція відсутня.")
        elif abs(correlation) < 0.3:
            print("Висновок: Слабкий зв'язок.")
        elif abs(correlation) < 0.5:
            print("Висновок: Помірна кореляція.")
        else:
            print(
                f"Висновок: Сильна {'пряма' if correlation > 0 else 'зворотна'} кореляція."
            )
            if correlation > 0:
                print("Чим довша доставка, тим частіше клієнти повертають товар.")

        plt.figure(figsize=(10, 6))
        sns.regplot(
            data=country_stats,
            x="avg_delivery_time",
            y="return_rate",
            scatter_kws={"s": 100, "alpha": 0.7},
            line_kws={"color": "red", "linewidth": 2},
        )

        for i, row in country_stats.iterrows():
            plt.text(
                row["avg_delivery_time"] + 0.1,
                row["return_rate"],
                row["ship_country"],
                fontsize=9,
            )

        plt.title(
            f"Залежність повернень від часу доставки (Кореляція: {correlation:.2f})",
            fontsize=14,
        )
        plt.xlabel("Середній час доставки (дні)", fontsize=12)
        plt.ylabel("Частка повернень (Return Rate)", fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_delivery_vs_returns()

# Розподілити доставки за групами: 1–2 дні, 3–5 днів, 6+ днів.
def analyze_delivery_groups():
    conn = get_connection()

    query = """
        SELECT 
            CASE 
                WHEN (julianday(delivered_date) - julianday(shipped_date)) <= 2 THEN '1–2 дні'
                WHEN (julianday(delivered_date) - julianday(shipped_date)) <= 5 THEN '3–5 днів'
                ELSE '6+ днів'
            END AS delivery_group,
            COUNT(shipment_id) AS total_shipments,
            ROUND(AVG(cost), 2) AS avg_cost
        FROM shipments
        WHERE delivered_date IS NOT NULL 
          AND shipped_date IS NOT NULL
          AND (julianday(delivered_date) - julianday(shipped_date)) >= 0
        GROUP BY delivery_group
        ORDER BY 
            CASE delivery_group
                WHEN '1–2 дні' THEN 1
                WHEN '3–5 днів' THEN 2
                ELSE 3
            END
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("У таблиці shipments немає завершених доставок.")
            return

        total_all = df["total_shipments"].sum()
        df["percentage"] = (df["total_shipments"] / total_all) * 100

        print("РОЗПОДІЛ ДОСТАВОК ЗА ГРУПАМИ")
        print(
            df.to_string(
                index=False,
                formatters={
                    "total_shipments": "{:,} замовл.".format,
                    "avg_cost": "{:.2f} у.о.".format,
                    "percentage": "{:.1f}%".format,
                },
            )
        )

        plt.figure(figsize=(9, 5))
        sns.set_theme(style="whitegrid")

        ax = sns.barplot(
            data=df,
            x="delivery_group",
            y="total_shipments",
            palette="Blues_d",
            hue="delivery_group",
            legend=False,
        )

        for p in ax.patches:
            height = p.get_height()
            pct = (height / total_all) * 100
            ax.annotate(
                f"{int(height):,}\n({pct:.1f}%)",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                xytext=(0, 5),
                textcoords="offset points",
            )

        plt.title("Розподіл замовлень за термінами доставки", fontsize=14)
        plt.xlabel("Інтервал доставки", fontsize=12)
        plt.ylabel("Кількість доставок", fontsize=12)

        plt.ylim(0, df["total_shipments"].max() * 1.15)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_delivery_groups()

# Розрахувати частку повернень для кожної групи.
def analyze_returns_by_delivery_groups():
    conn = get_connection()

    query = """
        SELECT 
            CASE 
                WHEN (julianday(sh.delivered_date) - julianday(sh.shipped_date)) <= 2 THEN '1–2 дні'
                WHEN (julianday(sh.delivered_date) - julianday(sh.shipped_date)) <= 5 THEN '3–5 днів'
                ELSE '6+ днів'
            END AS delivery_group,
            COUNT(o.order_id) AS total_orders,
            SUM(CASE WHEN r.return_id IS NOT NULL THEN 1 ELSE 0 END) AS total_returns
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        LEFT JOIN returns r ON o.order_id = r.order_id
        WHERE sh.delivered_date IS NOT NULL 
          AND sh.shipped_date IS NOT NULL
          AND (julianday(sh.delivered_date) - julianday(sh.shipped_date)) >= 0
        GROUP BY delivery_group
        ORDER BY 
            CASE delivery_group
                WHEN '1–2 дні' THEN 1
                WHEN '3–5 днів' THEN 2
                ELSE 3
            END
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Дані про доставки або замовлення відсутні.")
            return

        df["return_rate"] = (df["total_returns"] / df["total_orders"]) * 100

        print("ЧАСТКА ПОВЕРНЕНЬ ЗА ГРУПАМИ ДОСТАВКИ")
        print(
            df.to_string(
                index=False,
                formatters={
                    "total_orders": "{:,} замовл.".format,
                    "total_returns": "{:,} поверн.".format,
                    "return_rate": "{:.2f}%".format,
                },
            )
        )

        plt.figure(figsize=(8, 5))
        sns.set_theme(style="whitegrid")

        ax = sns.barplot(
            data=df,
            x="delivery_group",
            y="return_rate",
            palette="Reds_d",
            hue="delivery_group",
            legend=False,
        )

        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f"{height:.2f}%",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
                xytext=(0, 5),
                textcoords="offset points",
            )

        plt.title("Частка повернень залежно від термінів доставки", fontsize=14)
        plt.xlabel("Інтервал доставки", fontsize=12)
        plt.ylabel("Частка повернень (Return Rate, %)", fontsize=12)

        plt.ylim(0, df["return_rate"].max() * 1.15)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час розрахунку: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_returns_by_delivery_groups()

# Перевірити вплив перевізника на ймовірність повернення.
def analyze_shipper_influence():
    conn = get_connection()

    query = """
        SELECT 
            s.name AS shipper_name,
            COUNT(o.order_id) AS total_orders,
            SUM(CASE WHEN r.return_id IS NOT NULL THEN 1 ELSE 0 END) AS total_returns,
            AVG(julianday(sh.delivered_date) - julianday(sh.shipped_date)) AS avg_delivery_time
        FROM orders o
        JOIN shipments sh ON o.order_id = sh.order_id
        JOIN shippers s ON sh.shipper_id = s.shipper_id
        LEFT JOIN returns r ON o.order_id = r.order_id
        WHERE sh.delivered_date IS NOT NULL AND sh.shipped_date IS NOT NULL
        GROUP BY s.shipper_id
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Дані про перевезення або повернення відсутні.")
            return

        df["return_rate"] = (df["total_returns"] / df["total_orders"]) * 100
        df["successful_orders"] = df["total_orders"] - df["total_returns"]

        df_sorted = df.sort_values(by="return_rate", ascending=False)

        print("АНАЛІЗ ПОВЕРНЕНЬ ПО ПЕРЕВІЗНИКАМ")
        print(
            df_sorted.to_string(
                index=False,
                columns=[
                    "shipper_name",
                    "total_orders",
                    "total_returns",
                    "return_rate",
                    "avg_delivery_time",
                ],
                formatters={
                    "total_orders": "{:,} зак.".format,
                    "total_returns": "{:,} возвр.".format,
                    "return_rate": "{:.2f}%".format,
                    "avg_delivery_time": "{:.1f} дн.".format,
                },
            )
        )

        contingency_table = df[["total_returns", "successful_orders"]].values

        if len(df) >= 2:
            chi2, p_value, dof, expected = chi2_contingency(contingency_table)
            print("\nРЕЗУЛЬТАТ СТАТИСТИЧНОГО ТЕСТУ")
            print(f"p-value: {p_value:.4f}")
            if p_value < 0.05:
                print(
                    "Висновок: перевізник суттєво впливає на вірогідність повернення. Відмінності статистично значущі."
                )
            else:
                print(
                    "Висновок: статистично значущого впливу не виявлено. Різниця між перевізниками може бути випадковою."
                )
        else:
            print("\nНедостатньо перевізників для проведення тесту.")

        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid")

        ax = sns.barplot(
            data=df_sorted,
            x="shipper_name",
            y="return_rate",
            palette="muted",
            hue="shipper_name",
            legend=False,
        )

        for i, p in enumerate(ax.patches):
            height = p.get_height()

            avg_time = df_sorted.iloc[i]["avg_delivery_time"]
            ax.annotate(
                f"{height:.1f}%\n({avg_time:.1f} дн.)",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                xytext=(0, 5),
                textcoords="offset points",
            )

        plt.title(
            "Доля повернень та середній час транспортування по перевізникам",
            fontsize=14,
        )
        plt.xlabel("Служба доставки (Перевізник)", fontsize=12)
        plt.ylabel("Доля повернень (Return Rate, %)", fontsize=12)
        plt.ylim(0, df_sorted["return_rate"].max() * 1.2)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка при виконанні аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_shipper_influence()

# Проаналізувати причини поверення по перевізниках.
def analyze_return_reasons_by_shipper():
    conn = get_connection()

    query = """
        SELECT 
            s.name AS shipper_name,
            r.reason AS return_reason,
            COUNT(r.return_id) AS return_count
        FROM returns r
        JOIN orders o ON r.order_id = o.order_id
        JOIN shipments sh ON o.order_id = sh.order_id
        JOIN shippers s ON sh.shipper_id = s.shipper_id
        WHERE r.reason IS NOT NULL AND r.reason != ''
        GROUP BY s.name, r.reason
    """

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Дані про причини повернень у таблиці returns відсутні.")
            return

        pivot_df = df.pivot(
            index="return_reason", columns="shipper_name", values="return_count"
        ).fillna(0)

        pivot_df = pivot_df.astype(int)

        pivot_df["Всього"] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values(by="Всього", ascending=False)

        print("МАТРИЦЯ ПРИЧИН ПОВЕРНЕННЯ ПО ПЕРЕВІЗНИКАХ")
        print(pivot_df.to_string())

        print("\nЧАСТКА ПРИЧИН ВСЕРЕДИНІ КОЖНОГО ПЕРЕВІЗНИКА (%)")
        pure_pivot = pivot_df.drop(columns=["Всього"])
        pct_pivot = pure_pivot.div(pure_pivot.sum(axis=0), axis=1) * 100
        print(pct_pivot.round(1).to_string(formatters={c: "{:.1f}%".format for c in pct_pivot.columns}))

        plt.figure(figsize=(10, 6))

        sns.heatmap(
            pure_pivot,
            annot=True,
            fmt="d",
            cmap="YlOrRd",
            linewidths=0.5,
            cbar_kws={"label": "Кількість повернень"},
        )

        plt.title("Теплова карта причин повернення по перевізниках", fontsize=14)
        plt.xlabel("Служба доставки (Перевізник)", fontsize=12)
        plt.ylabel("Причина повернення", fontsize=12)
        plt.xticks(rotation=45, ha="right")

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Помилка під час виконання аналізу: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_return_reasons_by_shipper()
