import re

from playwright.sync_api import Browser, Page

from config import TICKET_QUANTITY

BASE_URL = "https://store.anypass.jp"
URL = BASE_URL + "/resale-list"
TOUR_NAME = "MAZZEL 2nd Fan Meeting -Play at the MUZEUM Vol.2-"

# 出品カード(a.resale-list-item)から必要な文字列をまとめて取り出す(ブラウザ側で実行)
EXTRACT_JS = r"""
items => items.map(a => {
  const text = sel => {
    const e = a.querySelector(sel);
    return e ? e.innerText.replace(/\s+/g, ' ').trim() : '';
  };
  const seatIcon = a.querySelector('.seat-icon');
  const qtyEl = (seatIcon && seatIcon.parentElement)
    ? seatIcon.parentElement.querySelector('.ticket-info') : null;
  return {
    href: a.getAttribute('href') || '',
    venue: text('.location'),
    date: text('.date'),
    seat: text('.seat-icon'),
    quantity: qtyEl ? qtyEl.innerText.trim() : '',
    price: text('p.ticket-info'),
    fc_label: text('.fc-label-label'),
  };
})
"""


def select_option(page: Page, index: int, text: str):
    """独自ドロップダウン(.custom-select.seats)の index 番目から text を選ぶ"""
    dropdown = page.locator(".custom-select.seats").nth(index)
    dropdown.locator(".select-selected").click()
    dropdown.locator(".select-items div").filter(has_text=text).click()


def parse_tickets(page: Page):
    """表示中のページの出品を読み取る"""
    rows = page.eval_on_selector_all("a.resale-list-item", EXTRACT_JS)
    tickets = []

    for r in rows:
        # hrefの ?t=... は毎回変わる可能性があるので、IDは /resale/数字 の部分だけを使う
        m = re.search(r"/resale/(\d+)", r["href"])
        if not m:
            continue

        qty = re.search(r"\d+", r["quantity"])
        price = re.search(r"¥[\d,]+", r["price"])
        href = r["href"]

        if qty is None:
            print("枚数を読み取れませんでした(HTML構造が変わった可能性):", m.group(1))

        tickets.append({
            "id": m.group(1),
            "url": BASE_URL + href if href.startswith("/") else href,
            "venue": r["venue"],
            "date": r["date"],
            "seat": r["seat"],
            "quantity": int(qty.group()) if qty else None,
            "price": price.group() if price else "",
            "fc_label": r["fc_label"],
        })

    return tickets


def check_tickets(browser: Browser):
    """起動済みのブラウザを使い回して検索し、出品一覧を返す"""
    context = browser.new_context(locale="ja-JP")
    page = context.new_page()
    page.set_default_timeout(15000)

    try:
        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        #select_option(page, 0, "MAZZEL")
        #select_option(page, 2, TOUR_NAME)
        select_option(page, 3, f"{TICKET_QUANTITY}枚")

        page.get_by_role("button", name="検索", exact=True).click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        body_text = page.locator("body").inner_text()
        if "該当するチケットはありませんでした" in body_text:
            print("対象の出品はありません")
            return []

        # MAZZELは同時の出品が少ないため、1ページ目だけを読む
        tickets = parse_tickets(page)
        print("出品数：", len(tickets))
        if not tickets:
            print("出品情報のHTML構造を確認する必要があります")
        return tickets

    finally:
        context.close()


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        result = check_tickets(b)
        b.close()

    print("\n取得した出品数：", len(result))
    for t in result[:5]:
        print(t)
