"""
Возвращаем $10 USDC с прокси-кошелька (0x9d07...) обратно на MetaMask (0x0265...).
НО: у нас нет приватного ключа от прокси — это смарт-контракт Polymarket.
Поэтому возвращаем то что осталось на MetaMask от исходных $22.84.

Текущая ситуация:
- MetaMask (0x0265...): ~$12.84 native USDC
- Прокси (0x9d07...): $10.00 native USDC (переведено скриптом)

Прокси — это Safe смарт-контракт Polymarket, мы не можем им управлять напрямую.
$10 на прокси доступны только через интерфейс Polymarket (withdraw).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from web3 import Web3

RPC = "https://polygon-bor-rpc.publicnode.com"
PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY", "")

FROM = Web3.to_checksum_address("0x02659D56e31be224D689953397eFA80D61A039D4")  # MetaMask
PROXY = Web3.to_checksum_address("0x9d0724d90f6f3ea13990afd3b7211ff358efc489")  # Polymarket прокси
USDC_NATIVE = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")

w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 15}))
assert w3.is_connected()

def get_balance(address):
    data = f"0x70a08231000000000000000000000000{address[2:].lower()}"
    res = w3.eth.call({"to": USDC_NATIVE, "data": data})
    return int(res.hex(), 16) / 1_000_000

metamask_bal = get_balance(FROM)
proxy_bal = get_balance(PROXY)

print(f"MetaMask (0x0265...): ${metamask_bal:.6f} native USDC")
print(f"Прокси   (0x9d07...): ${proxy_bal:.6f} native USDC")
print()

# Прокси — это Safe контракт Polymarket. Мы не владеем им напрямую.
# Единственный способ вернуть эти $10 — через polymarket.com → Withdraw.
print("⚠️  $10 USDC на прокси (0x9d07...) — это Safe смарт-контракт Polymarket.")
print("   Мы не можем управлять им без приватного ключа прокси.")
print()
print("Для возврата $10 через сайт:")
print("   1. polymarket.com → нажми на баланс → Withdraw")
print("   2. Выведи USDC обратно на MetaMask адрес")
print()
print("Если кнопка Withdraw тоже не работает — напиши, найдём другой способ.")
