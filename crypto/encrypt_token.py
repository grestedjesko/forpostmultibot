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

encrypt_token('5318319553:AAGb6HNSu-bRwqkM-0lF0RXCsEZqz55yz1c')