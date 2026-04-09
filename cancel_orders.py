"""
cancel_orders.py — Отменить все открытые ордера на Polymarket CLOB.
Это освободит заблокированный баланс USDC.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

def main():
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds

    poly_private_key = os.getenv("POLY_PRIVATE_KEY", "")
    api_key = os.getenv("POLY_API_KEY", "")
    api_secret = os.getenv("POLY_SECRET", "")
    api_passphrase = os.getenv("POLY_PASSPHRASE", "")

    if not all([poly_private_key, api_key, api_secret, api_passphrase]):
        print("❌ Не все ключи настроены в .env")
        return

    client = ClobClient(
        host="https://clob.polymarket.com",
        key=poly_private_key,
        chain_id=137,
    )
    client.set_api_creds(ApiCreds(
        api_key=api_key,
        api_secret=api_secret,
        api_passphrase=api_passphrase,
    ))

    # Получаем все открытые ордера
    print("📋 Получаю открытые ордера...")
    try:
        orders = client.get_orders()
        if not orders:
            print("✅ Нет открытых ордеров")
            return

        open_orders = [o for o in orders if o.get("status") == "LIVE" or o.get("status") == "OPEN"]
        if not open_orders:
            # Попробуем отменить все без фильтра
            open_orders = orders

        print(f"📊 Найдено ордеров: {len(open_orders)}")

        for order in open_orders:
            order_id = order.get("id") or order.get("orderID") or order.get("order_id")
            side = order.get("side", "?")
            size = order.get("original_size") or order.get("size", "?")
            price = order.get("price", "?")
            status = order.get("status", "?")
            print(f"  {side} {size} @ {price} [{status}] — ID: {order_id}")

        # Отменяем все
        print(f"\n🔄 Отменяю все {len(open_orders)} ордеров...")
        try:
            resp = client.cancel_all()
            print(f"✅ cancel_all response: {resp}")
        except Exception as e:
            print(f"⚠️ cancel_all не сработал: {e}")
            print("Пробую по одному...")
            for order in open_orders:
                order_id = order.get("id") or order.get("orderID") or order.get("order_id")
                if order_id:
                    try:
                        r = client.cancel(order_id)
                        print(f"  ✅ Отменён: {order_id[:16]}... → {r}")
                    except Exception as e2:
                        print(f"  ❌ Ошибка {order_id[:16]}...: {e2}")

        print("\n✅ Готово! Баланс USDC должен быть освобождён.")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
