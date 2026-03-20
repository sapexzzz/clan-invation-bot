"""
ClanPanel — утилита управления пользователями бота.
Запуск: .venv/bin/python clanpanel.py
"""

import sqlite3
import sys
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.text import Text
    RICH = True
except ImportError:
    RICH = False

DB_PATH = "clan_bot.db"

console = Console() if RICH else None


# ─── DB helpers (sync) ────────────────────────────────────────────────────────

def db_migrate() -> None:
    """Применяет миграции к существующей БД (безопасно повторять)."""
    with _get_conn() as conn:
        # Создаём таблицы, если их нет
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                last_application_time REAL,
                is_blocked INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username TEXT,
                nickname TEXT,
                game_id TEXT,
                rank_comp TEXT,
                rank_allies TEXT,
                rank_duels TEXT,
                hours INTEGER,
                kd REAL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT,
                group_message_id INTEGER
            )
        """)
        # Добавляем is_blocked в старые БД
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # колонка уже есть


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_get_users() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT
                u.telegram_id,
                u.is_blocked,
                u.last_application_time,
                COUNT(a.id)                                               AS total,
                SUM(CASE WHEN a.status = 'pending'       THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN a.status = 'accepted'      THEN 1 ELSE 0 END) AS accepted,
                SUM(CASE WHEN a.status = 'rejected'      THEN 1 ELSE 0 END) AS rejected,
                SUM(CASE WHEN a.status = 'rejected_auto' THEN 1 ELSE 0 END) AS rejected_auto,
                MAX(a.username)  AS username,
                MAX(a.nickname)  AS nickname
            FROM users u
            LEFT JOIN applications a ON a.telegram_id = u.telegram_id
            GROUP BY u.telegram_id
            ORDER BY u.last_application_time DESC NULLS LAST
        """).fetchall()
        return [dict(r) for r in rows]


def db_get_applications(status_filter: str | None = None) -> list[dict]:
    with _get_conn() as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC",
                (status_filter,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def db_block(telegram_id: int) -> None:
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO users (telegram_id, is_blocked)
            VALUES (?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET is_blocked = 1
        """, (telegram_id,))
        conn.commit()


def db_unblock(telegram_id: int) -> None:
    with _get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_blocked = 0 WHERE telegram_id = ?", (telegram_id,)
        )
        conn.commit()


def db_user_exists(telegram_id: int) -> bool:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return row is not None


# ─── UI helpers ───────────────────────────────────────────────────────────────

def fmt_time(ts: float | None) -> str:
    if ts is None:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


def clear() -> None:
    console.clear() if RICH else print("\n" * 3)


def print_header() -> None:
    if RICH:
        console.print(Panel(
            Text("ClanPanel  •  Standoff 2 Bot", justify="center", style="bold cyan"),
            subtitle="[dim]clan_bot.db[/dim]",
            box=box.DOUBLE_EDGE,
        ))
    else:
        print("=" * 50)
        print("  ClanPanel — Standoff 2 Bot")
        print("=" * 50)


def print_menu() -> None:
    if RICH:
        console.print(
            "\n[bold white][[cyan]1[/cyan]][/bold white] Список пользователей\n"
            "[bold white][[cyan]2[/cyan]][/bold white] Заблокировать пользователя\n"
            "[bold white][[cyan]3[/cyan]][/bold white] Разблокировать пользователя\n"
            "[bold white][[cyan]4[/cyan]][/bold white] Список заявок\n"
            "[bold white][[cyan]0[/cyan]][/bold white] Выход\n"
        )
    else:
        print("\n1. Список пользователей")
        print("2. Заблокировать пользователя")
        print("3. Разблокировать пользователя")
        print("4. Список заявок")
        print("0. Выход\n")


def ask(prompt: str) -> str:
    if RICH:
        return Prompt.ask(f"[yellow]{prompt}[/yellow]").strip()
    return input(f"{prompt}: ").strip()


def confirm(prompt: str) -> bool:
    if RICH:
        return Confirm.ask(f"[yellow]{prompt}[/yellow]")
    return input(f"{prompt} (y/n): ").strip().lower() == "y"


def ok(msg: str) -> None:
    if RICH:
        console.print(f"[bold green]✓[/bold green] {msg}")
    else:
        print(f"OK: {msg}")


def err(msg: str) -> None:
    if RICH:
        console.print(f"[bold red]✗[/bold red] {msg}")
    else:
        print(f"ERROR: {msg}")


# ─── Screens ──────────────────────────────────────────────────────────────────

def screen_users() -> None:
    clear()
    print_header()
    users = db_get_users()

    if not users:
        err("Нет пользователей в базе.")
        input("\nEnter для продолжения...")
        return

    if RICH:
        t = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE_HEAVY,
            expand=True,
        )
        t.add_column("TG ID",        style="cyan",  no_wrap=True)
        t.add_column("Username",     style="white")
        t.add_column("Ник",          style="white")
        t.add_column("Блок",         justify="center")
        t.add_column("Всего",        justify="right")
        t.add_column("Pending",      justify="right", style="yellow")
        t.add_column("Принято",      justify="right", style="green")
        t.add_column("Отклонено",    justify="right", style="red")
        t.add_column("Авто-откл.",   justify="right", style="dim red")
        t.add_column("Последняя",    style="dim")

        for u in users:
            blocked = "[bold red]🚫 ДА[/bold red]" if u["is_blocked"] else "[green]—[/green]"
            t.add_row(
                str(u["telegram_id"]),
                f"@{u['username']}" if u["username"] else "—",
                u["nickname"] or "—",
                blocked,
                str(u["total"] or 0),
                str(u["pending"] or 0),
                str(u["accepted"] or 0),
                str(u["rejected"] or 0),
                str(u["rejected_auto"] or 0),
                fmt_time(u["last_application_time"]),
            )
        console.print(t)
    else:
        header = f"{'TG ID':<15} {'Username':<18} {'Blocked':<8} {'Всего':<7} {'Last'}"
        print(header)
        print("-" * len(header))
        for u in users:
            print(
                f"{u['telegram_id']:<15} "
                f"@{u['username'] or '—':<17} "
                f"{'ДА' if u['is_blocked'] else 'нет':<8} "
                f"{u['total'] or 0:<7} "
                f"{fmt_time(u['last_application_time'])}"
            )

    input("\nEnter для продолжения...")


def screen_block() -> None:
    clear()
    print_header()
    if RICH:
        console.print("\n[bold red]🚫 Заблокировать пользователя[/bold red]\n")
    else:
        print("\n--- Заблокировать ---\n")

    raw = ask("Введи Telegram ID")
    if not raw.lstrip("-").isdigit():
        err("Неверный ID")
        input("\nEnter для продолжения...")
        return

    tg_id = int(raw)
    if not confirm(f"Заблокировать пользователя {tg_id}?"):
        return

    db_block(tg_id)
    ok(f"Пользователь {tg_id} заблокирован.")
    input("\nEnter для продолжения...")


def screen_unblock() -> None:
    clear()
    print_header()
    if RICH:
        console.print("\n[bold green]✅ Разблокировать пользователя[/bold green]\n")
    else:
        print("\n--- Разблокировать ---\n")

    raw = ask("Введи Telegram ID")
    if not raw.lstrip("-").isdigit():
        err("Неверный ID")
        input("\nEnter для продолжения...")
        return

    tg_id = int(raw)
    if not db_user_exists(tg_id):
        err(f"Пользователь {tg_id} не найден в базе.")
        input("\nEnter для продолжения...")
        return

    if not confirm(f"Разблокировать пользователя {tg_id}?"):
        return

    db_unblock(tg_id)
    ok(f"Пользователь {tg_id} разблокирован.")
    input("\nEnter для продолжения...")


STATUS_LABELS = {
    "pending":       "⏳ pending",
    "accepted":      "✅ accepted",
    "rejected":      "❌ rejected",
    "rejected_auto": "🤖 rejected_auto",
}


def screen_applications() -> None:
    clear()
    print_header()

    if RICH:
        console.print(
            "\n[bold]Фильтр по статусу:[/bold]\n"
            " [cyan]1[/cyan] pending  "
            " [cyan]2[/cyan] accepted  "
            " [cyan]3[/cyan] rejected  "
            " [cyan]4[/cyan] rejected_auto  "
            " [cyan]0[/cyan] все\n"
        )
    else:
        print("\nФильтр: 1-pending  2-accepted  3-rejected  4-rejected_auto  0-все\n")

    choice = ask("Выбери")
    status_map = {"1": "pending", "2": "accepted", "3": "rejected", "4": "rejected_auto"}
    status_filter = status_map.get(choice)

    apps = db_get_applications(status_filter)

    if not apps:
        err("Заявок не найдено.")
        input("\nEnter для продолжения...")
        return

    if RICH:
        t = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE_HEAVY,
            expand=True,
        )
        t.add_column("ID",     style="cyan", no_wrap=True)
        t.add_column("TG ID",  style="cyan", no_wrap=True)
        t.add_column("Username")
        t.add_column("Ник")
        t.add_column("Игр. ID")
        t.add_column("Comp")
        t.add_column("Allies")
        t.add_column("Duels")
        t.add_column("Ч", justify="right")
        t.add_column("KD",  justify="right")
        t.add_column("Статус")
        t.add_column("Создана",  style="dim")

        status_styles = {
            "pending":       "yellow",
            "accepted":      "green",
            "rejected":      "red",
            "rejected_auto": "dim red",
        }

        for a in apps:
            st = a["status"]
            style = status_styles.get(st, "")
            t.add_row(
                str(a["id"]),
                str(a["telegram_id"]),
                f"@{a['username']}" if a["username"] else "—",
                a["nickname"] or "—",
                a["game_id"] or "—",
                a["rank_comp"] or "—",
                a["rank_allies"] or "—",
                a["rank_duels"] or "—",
                str(a["hours"] or "—"),
                str(a["kd"] or "—"),
                f"[{style}]{STATUS_LABELS.get(st, st)}[/{style}]" if style else st,
                (a["created_at"] or "")[:16],
            )
        console.print(t)
    else:
        for a in apps:
            print(
                f"#{a['id']}  tg:{a['telegram_id']}  "
                f"nick:{a['nickname'] or '—'}  "
                f"hours:{a['hours']}  kd:{a['kd']}  "
                f"status:{a['status']}  {(a['created_at'] or '')[:16]}"
            )

    input("\nEnter для продолжения...")


# ─── Main loop ────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        db_migrate()
    except Exception as e:
        print(f"Ошибка подключения к БД ({DB_PATH}): {e}")
        sys.exit(1)

    while True:
        clear()
        print_header()
        print_menu()

        choice = ask("Выбери пункт меню")

        if choice == "1":
            screen_users()
        elif choice == "2":
            screen_block()
        elif choice == "3":
            screen_unblock()
        elif choice == "4":
            screen_applications()
        elif choice == "0":
            if RICH:
                console.print("[dim]Выход...[/dim]")
            else:
                print("Выход...")
            break
        else:
            err("Неверный выбор")


if __name__ == "__main__":
    main()
