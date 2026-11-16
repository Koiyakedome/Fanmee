
import json
from pathlib import Path

DATA_FILE = Path("data/checked_tickets.json")


def load_previous_tickets():
    """前回確認した出品一覧を読み込む"""
    if not DATA_FILE.exists():
        return None

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_current_tickets(tickets):
    """今回の出品一覧を保存する"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(tickets, file, ensure_ascii=False, indent=4)


def find_new_tickets(current_tickets):
    """新しく追加された出品だけを返す"""

    # 出品を区別するためのIDが必要
    for ticket in current_tickets:
        if "id" not in ticket:
            raise ValueError("出品データにidがありません")

    previous_tickets = load_previous_tickets()

    # 初回は比較対象がないため、現在の一覧を保存するだけ
    if previous_tickets is None:
        save_current_tickets(current_tickets)
        return []

    previous_ids = {
        ticket["id"] for ticket in previous_tickets
    }

    new_tickets = [
        ticket for ticket in current_tickets
        if ticket["id"] not in previous_ids
    ]

    # 今回の一覧を次回の比較用に保存
    save_current_tickets(current_tickets)

    return new_tickets
