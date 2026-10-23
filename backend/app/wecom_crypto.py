import base64
import hashlib
import hmac
import os
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BLOCK_SIZE = 32


def _aes_key(encoding_aes_key: str) -> bytes:
    key = base64.b64decode(encoding_aes_key + "=")
    if len(key) != 32:
        raise ValueError("EncodingAESKey 必须为 43 位")
    return key


def signature(token: str, timestamp: str, nonce: str, encrypt: str) -> str:
    items = sorted([token, timestamp, nonce, encrypt])
    return hashlib.sha1("".join(items).encode()).hexdigest()


def verify_signature(token: str, timestamp: str, nonce: str, encrypt: str, expected: str) -> bool:
    return hmac.compare_digest(signature(token, timestamp, nonce, encrypt), expected)


def encrypt(encoding_aes_key: str, text: str, receive_id: str, random16: bytes | None = None) -> str:
    key = _aes_key(encoding_aes_key)
    random_bytes = random16 or os.urandom(16)
    msg = text.encode("utf-8")
    data = random_bytes + struct.pack("!I", len(msg)) + msg + receive_id.encode("utf-8")
    pad = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    data += bytes([pad]) * pad

    encryptor = Cipher(algorithms.AES(key), modes.CBC(key[:16])).encryptor()
    return base64.b64encode(encryptor.update(data) + encryptor.finalize()).decode()


def decrypt(encoding_aes_key: str, encrypt_b64: str, receive_id: str = "") -> str:
    key = _aes_key(encoding_aes_key)
    raw = base64.b64decode(encrypt_b64)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(key[:16])).decryptor()
    data = decryptor.update(raw) + decryptor.finalize()

    pad = data[-1]
    if pad < 1 or pad > BLOCK_SIZE:
        raise ValueError("非法填充")
    data = data[:-pad]
    if len(data) < 20:
        raise ValueError("报文过短")

    msg_len = struct.unpack("!I", data[16:20])[0]
    msg = data[20 : 20 + msg_len]
    received_id = data[20 + msg_len :].decode("utf-8", errors="ignore")
    if receive_id and received_id != receive_id:
        raise ValueError("receive_id 不匹配")
    return msg.decode("utf-8")
