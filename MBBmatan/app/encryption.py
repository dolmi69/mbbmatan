from cryptography.fernet import Fernet

ENCRYPTION_KEY = b'LgMvv4Nrkm_0gpGWkgihfRuDo6-fUPCxeGZDJcqY7ik='

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_message(text: str) -> str:
    """Шифрует строку и возвращает зашифрованное значение в виде строки."""
    return cipher.encrypt(text.encode('utf-8')).decode('utf-8')

def decrypt_message(encrypted_text: str) -> str:
    """Расшифровывает строку и возвращает исходный текст."""
    return cipher.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')