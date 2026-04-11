import os
from cryptography.fernet import Fernet
from django.conf import settings

ENCRYPTION_KEY = getattr(settings, 'MESSAGE_ENCRYPTION_KEY', None)

if not ENCRYPTION_KEY:
    key_file = os.path.join(settings.BASE_DIR, 'secret.key')
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            ENCRYPTION_KEY = f.read()
    else:
        ENCRYPTION_KEY = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(ENCRYPTION_KEY)
        print("ВНИМАНИЕ: Сгенерирован новый ключ шифрования. Сохраните его в надёжном месте!")

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_message(text: str) -> str:
    return cipher.encrypt(text.encode('utf-8')).decode('utf-8')

def decrypt_message(encrypted_text: str) -> str:
    return cipher.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')