import os
import time

from playwright.sync_api import sync_playwright

from check_MAZZEL import check_tickets
from filter import filter_tickets
from checker import find_new_tickets
from notifier import send_discord_notification, send_discord_message

# RUN_MINUTES=0(未設定)なら1回だけ実行。Actionsでは 58 などを指定してループさせる
RUN_SEC = int(os.getenv("RUN_MINUTES", "0")) * 60
INTERVAL = int(os.getenv("INTERVAL_SEC", "120"))
HEADLESS = os.getenv("HEADLESS", "1") != "0"   # ローカルで画面を見たいときは HEADLESS=0


def run_once(browser):
    current_tickets = check_tickets(browser)
    print(f"取得件数：{len(current_tickets)}件")

    filtered_tickets = filter_tickets(current_tickets)
    print(f"絞り込み結果：{len(filtered_tickets)}件")

    new_tickets = find_new_tickets(filtered_tickets)
    print(f"新着出品：{len(new_tickets)}件")

    if new_tickets:
        send_discord_notification(new_tickets)


def main():
    start = time.monotonic()
    fails = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)

        try:
            while True:
                t0 = time.monotonic()
                print(f"\n--- 確認開始 {time.strftime('%H:%M:%S')} ---")

                try:
                    run_once(browser)
                    fails = 0
                except Exception as e:
                    fails += 1
                    print(f"エラー({fails}回連続)：{e}")

                    if fails == 5:
                        try:
                            send_discord_message(
                                "⚠️ 検索が5回連続で失敗しています"
                                "(ブロックやサイト仕様変更の可能性)"
                            )
                        except Exception as ne:
                            print("エラー通知も失敗：", ne)

                    # ブラウザ自体が壊れている場合に備えて起動し直す
                    try:
                        browser.close()
                    except Exception:
                        pass
                    browser = p.chromium.launch(headless=HEADLESS)

                # 次の実行が時間枠に収まらなければ終了
                if time.monotonic() - start + INTERVAL >= RUN_SEC:
                    break

                # 処理時間を差し引いて待つ(間隔のずれを防ぐ)
                time.sleep(max(0, INTERVAL - (time.monotonic() - t0)))
        finally:
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
