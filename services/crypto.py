# PolyScore — Шифрование приватных ключей
#
# Приватные ключи пользователей НЕ хранятся в открытом виде.
# Используем AES-256-CTR (PyCryptodome) + HMAC-SHA256 для аутентификации.
#
# Мастер-ключ берётся из переменной окружения WALLET_ENCRYPTION_KEY.
# Если переменная не задана — используем fallback на основе BOT_TOKEN (только dev).
#
# Формат хранения: base64(nonce_16 + ciphertext + hmac_32)
# Даже если БД утечёт — ключи без мастер-ключа бесполезны.

import os
import base64
import hashlib
import hmac as hmac_mod

from Crypto.Cipher import AES


def _get_master_key() -> bytes:
    """
    Получить мастер-ключ для шифрования (32 байта = AES-256).
    В продакшне: переменная окружения WALLET_ENCRYPTION_KEY (64 hex символа = 32 байта).
    В разработке: детерминированный fallback на основе BOT_TOKEN.
    """
    raw = os.getenv("WALLET_ENCRYPTION_KEY", "")
    if raw and len(raw) >= 64:
        try:
            return bytes.fromhex(raw[:64])
        except ValueError:
            pass
    if raw and len(raw) >= 32:
        # Не hex — берём SHA-256 от строки для получения ровно 32 байт
        return hashlib.sha256(raw.encode()).digest()
    # Fallback: деривируем из BOT_TOKEN (только для локальной разработки)
    bot_token = os.getenv("BOT_TOKEN", "polyscore_dev_key")
    return hashlib.sha256(bot_token.encode()).digest()


def encrypt_private_key(private_key_hex: str) -> str:
    """
    Зашифровать приватный ключ для хранения в БД.
    AES-256-CTR с рандомным 16-байт nonce + HMAC-SHA256.
    Формат: base64(nonce_16 + ciphertext + hmac_32)
    """
    if not private_key_hex:
        return ""
    master_key = _get_master_key()
    nonce = os.urandom(16)

    # AES-256-CTR шифрование через PyCryptodome
    cipher = AES.new(master_key, AES.MODE_CTR, nonce=nonce[:8], initial_value=nonce[8:])
    ciphertext = cipher.encrypt(private_key_hex.encode('utf-8'))

    # HMAC-SHA256 для проверки целостности (nonce + ciphertext)
    mac = hmac_mod.new(master_key, nonce + ciphertext, hashlib.sha256).digest()
    payload = nonce + ciphertext + mac
    return base64.b64encode(payload).decode('utf-8')


def decrypt_private_key(encrypted: str) -> str:
    """
    Дешифровать приватный ключ из БД.
    Возвращает hex строку приватного ключа или "" если ошибка / подмена данных.
    Обратная совместимость: plaintext ключи (0x... или 64-символьный hex) проходят как есть.
    """
    if not encrypted:
        return ""

    # Обратная совместимость: старые незашифрованные ключи в plaintext
    if encrypted.startswith("0x") or (len(encrypted) == 64 and _is_hex(encrypted)):
        return encrypted

    try:
        master_key = _get_master_key()
        payload = base64.b64decode(encrypted.encode('utf-8'))

        # Минимальная длина: 16 (nonce) + 1 (ciphertext) + 32 (hmac) = 49
        if len(payload) < 49:
            return ""

        nonce = payload[:16]
        mac_received = payload[-32:]
        ciphertext = payload[16:-32]

        # Проверяем HMAC — защита от подмены данных
        mac_expected = hmac_mod.new(master_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac_mod.compare_digest(mac_received, mac_expected):
            return ""

        # AES-256-CTR дешифрование через PyCryptodome
        cipher = AES.new(master_key, AES.MODE_CTR, nonce=nonce[:8], initial_value=nonce[8:])
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode('utf-8')

    except Exception:
        return ""


def _is_hex(s: str) -> bool:
    """Проверить, является ли строка валидным hex."""
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def _self_test():
    """Проверить что шифрование/дешифрование работает корректно."""
    test_key = "a" * 64
    encrypted = encrypt_private_key(test_key)
    decrypted = decrypt_private_key(encrypted)
    assert decrypted == test_key, f"Crypto self-test FAILED: {decrypted!r} != {test_key!r}"

    # Проверяем что каждый раз разный шифртекст (случайный nonce)
    enc1 = encrypt_private_key(test_key)
    enc2 = encrypt_private_key(test_key)
    assert enc1 != enc2, "Nonce should be random — ciphertexts must differ"

    # Проверяем обратную совместимость с plaintext ключами
    assert decrypt_private_key("a" * 64) == "a" * 64, "Old hex keys should pass through"
    assert decrypt_private_key("0xabc123") == "0xabc123", "0x-prefixed keys should pass through"

    # Проверяем обнаружение подмены
    tampered = base64.b64encode(b'\x00' * 80).decode()
    assert decrypt_private_key(tampered) == "", "Tampered data should return empty"

    print("[Crypto] Self-test OK — AES-256-CTR + HMAC-SHA256")


try:
    _self_test()
except AssertionError as e:
    import logging
    logging.getLogger("PolyScore.crypto").error(f"CRYPTO SELF-TEST FAILED: {e}")
