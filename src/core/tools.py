import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import text

from src.core.config import get_settings, Settings
from src.core.database import get_session_maker
from src.core.security import security

settings: Settings = get_settings()
CURRENT_APP_ID: str = "f9db678c19974379acad94e5b5ab0000"


async def get_data_from_db(sql: str):
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            result = await session.execute(text(f"{sql}"))
            data = result.fetchall()
            await session.commit()
            return data
        except Exception as e:
            await session.rollback()
            raise RuntimeError(f"Execute SQL failed, Message: {e}")


async def encrypt_password(plain_password: str) -> str:
    """
    加密密码，返回 URL-safe Base64 字符串。
    格式：nonce(12B) + ciphertext + tag(16B)，全部拼接后编码。
    """

    if not plain_password:
        raise ValueError("Password cannot be empty...")

    codec: AESGCM = AESGCM(bytes.fromhex(security.SECRET_KEY))

    if codec is None:
        raise RuntimeError(
            "SecretCodec has not been initialized yet, please call await SecretCodec.create() first.")

    nonce = os.urandom(12)  # GCM 推荐 12 字节 nonce
    plaintext = plain_password.encode("utf-8")
    ciphertext = codec.encrypt(nonce, plaintext, None)

    # 拼接 nonce + 密文+tag，再 Base64 编码便于存储/传输
    combined = nonce + ciphertext
    return base64.urlsafe_b64encode(combined).decode("ascii")


async def decrypt_password(token: str) -> str:
    """
    解密密码，自动验证完整性。
    若密文被篡改或密钥错误，直接抛出异常。
    """
    if not token:
        raise ValueError("Hashed password cannot be empty...")

    codec: AESGCM = AESGCM(bytes.fromhex(security.SECRET_KEY))

    try:
        combined = base64.urlsafe_b64decode(token.encode("ascii"))
        if len(combined) < 28:  # 最小长度：12(nonce) + 16(tag)
            raise ValueError("Invalid ciphertext format...")

        nonce = combined[:12]
        ciphertext = combined[12:]
        plaintext = codec.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")
