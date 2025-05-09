from cryptography.fernet import Fernet
import asyncio

def load_key():
    with open("secret.key", "rb") as key_file:
        return key_file.read()

def encrypt_token(token: str) -> str:
    key = load_key()
    f = Fernet(key)
    encrypted = f.encrypt(token.encode())
    print(encrypted.decode())
    return encrypted.decode()

def decrypt_token(encrypted_token: str) -> str:
    key = load_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_token.encode())
    print(decrypted.decode())
    return decrypted.decode()

decrypt_token('gAAAAABoHd1wctkcp7aezpoRKSj7XBh-AdUMfWye9wReD-nI5o_K6HoMV0bFDwTzUwo71E0dkY-qkMhWtkVTf67BqpuHwqS2q6brodUY5NAx7mhd-aOrVMsUN9BwnszHQpWxWVWrODxY')