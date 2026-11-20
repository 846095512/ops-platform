import base64
import os
from typing import Tuple

import asyncssh
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from loguru import logger

from src.core.config import get_settings, Settings
from src.core.security import security

settings: Settings = get_settings()
CURRENT_APP_ID: str = "f9db678c19974379acad94e5b5ab0000"


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


class SSHManager:
    """
      SSH 管理工具
      generate_key_pair: 生成RSA密钥
      test_connection: 密码测试连接
    """

    def __init__(self, key_storage_dir: str = "~/.ssh"):
        self.key_storage_dir = key_storage_dir
        os.makedirs(self.key_storage_dir, exist_ok=True)

    def generate_key_pair(self) -> Tuple[str, str]:
        """
        为指定主机生成 RSA 密钥对
        :returns private_key_path 私钥路径, public_key_content 公钥内容
        """
        private_key_path = os.path.join(self.key_storage_dir, "id_rsa_ops_platform")
        public_key_path = f"{private_key_path}.pub"

        if not os.path.exists(private_key_path):
            key = asyncssh.generate_private_key('ssh-rsa', "2048")
            key.write_private_key(private_key_path)
            key.write_public_key(public_key_path)
            os.chmod(private_key_path, 0o600)
        with open(public_key_path, 'r') as f:
            public_key_content = f.read().strip()
        return private_key_path, public_key_content

    async def test_connection(self, ip: str, port: int,
                              username: str, password: str) -> str:
        """
        1. 使用密码测试连接
        2. 生成密钥对
        3. 将公钥下发到目标主机
        4. 返回私钥路径
        """
        private_key_path, public_key_content = self.generate_key_pair()
        conn = None
        try:
            logger.info(f"{ip} is testing the connection with  password.")
            conn = await asyncssh.connect(
                host=ip, port=port, username=username, password=password,
                known_hosts=None, connect_timeout=10
            )

            # 2. 下发公钥到目标主机的 authorized_keys
            remote_cmd = f"mkdir -p ~/.ssh && chmod 600 ~/.ssh && " \
                         f"grep -q '{public_key_content}' ~/.ssh/authorized_keys 2>/dev/null || " \
                         f"echo '{public_key_content}' >> ~/.ssh/authorized_keys && " \
                         f"chmod 600 ~/.ssh/authorized_keys"

            logger.info(f"{ip} is sending the public key.")
            await conn.run(remote_cmd, check=True)

            logger.info(f"The public key has been successfully issued.")
            return private_key_path

        except asyncssh.Error as e:
            logger.error(f"SSH connection or public key deployment failed: {e}")
            raise ValueError(f"SSH connection failed or public key deployment failed: {e}")
        finally:
            if conn:
                conn.close()
                await conn.wait_closed()

    async def execute(self, ip: str, port: int,
                      username: str, private_key_path: str, command: str):
        """
        使用私钥执行远程命令
        """
        conn = None
        try:
            conn = await asyncssh.connect(
                host=ip, port=port, username=username,
                client_keys=private_key_path,  # 指定私钥路径
                known_hosts=None, connect_timeout=10
            )
            logger.debug(f"Execute command is: {command}")
            result = await conn.run(command, check=True)
            if result is None:
                raise RuntimeError("result is None, Please check the execution script.")
            return result.stdout.strip()
        finally:
            if conn:
                conn.close()
                await conn.wait_closed()


ssh_manager = SSHManager()
