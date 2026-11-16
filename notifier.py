import os
import requests

LIMIT = 1900  # Discordの上限は2000文字
HEADER = "【MAZZEL 新着リセール情報】\n\n"
FOOTER = "AnyPASS STOREで確認してください。\nhttps://store.anypass.jp/resale-list"


def send_discord_message(text):
    """任意のテキストをDiscordに送る(エラー通知などにも使う)"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Webhook URLが設定されていません")
        return

    response = requests.post(
        webhook_url,
        json={"content": text[:LIMIT]},
        timeout=10,
    )
    response.raise_for_status()


def format_ticket(ticket):
    lines = []
    if ticket.get("venue"):
        lines.append(f"会場：{ticket['venue']}")
    if ticket.get("date"):
        lines.append(f"公演日：{ticket['date']}")
    lines.append(f"座席：{ticket['seat']}")

    qty = ticket.get("quantity")
    detail = f"枚数：{qty}枚" if qty is not None else "枚数：不明"
    if ticket.get("price"):
        detail += f"　価格：{ticket['price']}/1枚"
    lines.append(detail)

    if ticket.get("fc_label"):
        lines.append(f"区分：{ticket['fc_label']}")
    lines.append(f"出品ID：{ticket['id']}")
    if ticket.get("url"):
        lines.append(f"<{ticket['url']}>")   # <> でプレビュー表示を抑える

    return "\n".join(lines) + "\n\n"


def send_discord_notification(tickets):
    """新着出品をDiscordに通知する(長い場合は複数メッセージに分割)"""

    if not tickets:
        print("新着出品はありません")
        return

    messages = []
    current = HEADER

    for ticket in tickets:
        block = format_ticket(ticket)
        if len(current) + len(block) > LIMIT:
            messages.append(current)
            current = ""
        current += block

    messages.append(current + FOOTER)

    for text in messages:
        send_discord_message(text)

    print(f"Discordに通知しました({len(messages)}件)")
