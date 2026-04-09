"""
approve_polygon.py — Одноразовый скрипт для approve USDC и CTF токенов
на все контракты Polymarket (Polygon mainnet).

Запуск:
  cd ~/Documents/Claude/Scheduled/polyscore-bot
  source venv/bin/activate
  pip install web3
  python approve_polygon.py
"""
import os, sys, json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY", "")
if not PRIVATE_KEY.startswith("0x"):
    PRIVATE_KEY = "0x" + PRIVATE_KEY

# Polygon RPC (public) — несколько fallback
RPC_URLS = [
    "https://polygon.llamarpc.com",
    "https://rpc.ankr.com/polygon",
    "https://polygon.drpc.org",
    "https://1rpc.io/matic",
]
RPC_URL = None  # будет выбран первый рабочий

# ═══ Контракты Polymarket (Polygon) ═══
# Оба USDC-контракта — Polymarket может использовать любой
USDC_CONTRACTS = {
    "USDC.e (Bridged)": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDC (Native)":    "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
}
# Conditional Tokens Framework (CTF)
CTF_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"

# Exchange контракты которым нужен approve
EXCHANGE_CONTRACTS = {
    "CTF Exchange":       "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
    "Neg Risk Exchange":  "0xC5d563A36AE78145C45a50134d48A1215220f80a",
    "Neg Risk Adapter":   "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",
}

# ERC20 ABI (только approve и allowance)
ERC20_ABI = json.loads('[{"constant":false,"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')

# CTF ABI (setApprovalForAll)
CTF_ABI = json.loads('[{"constant":false,"inputs":[{"name":"operator","type":"address"},{"name":"approved","type":"bool"}],"name":"setApprovalForAll","outputs":[],"type":"function"},{"constant":true,"inputs":[{"name":"owner","type":"address"},{"name":"operator","type":"address"}],"name":"isApprovedForAll","outputs":[{"name":"","type":"bool"}],"type":"function"}]')

MAX_UINT256 = 2**256 - 1


def main():
    from web3 import Web3

    w3 = None
    for rpc in RPC_URLS:
        try:
            _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
            if _w3.is_connected():
                print(f"✅ Подключено к {rpc}")
                w3 = _w3
                break
        except Exception:
            pass
        print(f"   ⏭️ {rpc} — не отвечает")
    if not w3:
        print("❌ Не удалось подключиться ни к одному Polygon RPC")
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    wallet = account.address
    print(f"🔑 Кошелёк: {wallet}")
    print(f"💰 MATIC баланс: {w3.from_wei(w3.eth.get_balance(wallet), 'ether'):.4f} POL")
    print()

    ctf = w3.eth.contract(address=Web3.to_checksum_address(CTF_ADDRESS), abi=CTF_ABI)

    nonce = w3.eth.get_transaction_count(wallet)
    gas_price = int(w3.eth.gas_price * 1.5)
    print(f"⛽ Gas price: {w3.from_wei(gas_price, 'gwei'):.1f} gwei\n")
    tx_count = 0

    for name, addr in EXCHANGE_CONTRACTS.items():
        spender = Web3.to_checksum_address(addr)
        print(f"── {name} ({addr[:10]}...) ──")

        # ── USDC approve (оба контракта) ──
        for usdc_name, usdc_addr in USDC_CONTRACTS.items():
            usdc = w3.eth.contract(address=Web3.to_checksum_address(usdc_addr), abi=ERC20_ABI)
            current_allowance = usdc.functions.allowance(wallet, spender).call()
            if current_allowance >= MAX_UINT256 // 2:
                print(f"  ✅ {usdc_name} → уже approved")
            else:
                print(f"  🔄 {usdc_name} → approve нужен (allowance={current_allowance})")
                tx = usdc.functions.approve(spender, MAX_UINT256).build_transaction({
                    'from': wallet,
                    'nonce': nonce,
                    'gas': 65000,
                    'gasPrice': gas_price,
                    'chainId': 137,
                })
                signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                print(f"     TX: {tx_hash.hex()}")
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                if receipt.status == 1:
                    print(f"     ✅ Approved!")
                else:
                    print(f"     ❌ FAILED (status={receipt.status})")
                nonce += 1
                tx_count += 1

        # ── CTF (Conditional Tokens) setApprovalForAll ──
        is_approved = ctf.functions.isApprovedForAll(wallet, spender).call()
        if is_approved:
            print(f"  ✅ CTF → уже approved")
        else:
            print(f"  🔄 CTF → setApprovalForAll нужен")
            tx = ctf.functions.setApprovalForAll(spender, True).build_transaction({
                'from': wallet,
                'nonce': nonce,
                'gas': 65000,
                'gasPrice': gas_price,
                'chainId': 137,
            })
            signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"     TX: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt.status == 1:
                print(f"     ✅ CTF approved!")
            else:
                print(f"     ❌ CTF FAILED (status={receipt.status})")
            nonce += 1
            tx_count += 1

        print()

    print(f"{'='*50}")
    print(f"Готово! Отправлено {tx_count} транзакций.")
    print(f"Теперь бот может торговать через CLOB без ошибок allowance.")


if __name__ == "__main__":
    main()
