import base64
import os
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def generate_key():
    key = os.urandom(32) 
    return key

def encrypt_data(plain_text):
    key = generate_key()  
    iv = os.urandom(16) 

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_text = base64.b64encode(encrypted_data).decode() 

    return encrypted_text, iv, key