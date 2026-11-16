from config import TICKET_QUANTITY


def filter_tickets(tickets):
    """購入したい枚数(TICKET_QUANTITY)以上の出品を残す。

    ばら売り可能な2枚セットなども、1枚で購入できるため対象に含める。
    枚数を読み取れなかった出品(None)は、見逃しを避けるため残す。
    """
    return [
        ticket for ticket in tickets
        if ticket["quantity"] is None or ticket["quantity"] >= TICKET_QUANTITY
    ]
