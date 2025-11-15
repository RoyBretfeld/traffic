# -*- coding: utf-8 -*-
"""
Sichere API-Key-Verwaltung für FAMO TrafficApp 3.0

Verschlüsselt und entschlüsselt API-Keys für sichere Speicherung.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import json

class SecureKeyManager:
    """Sichere Verwaltung von API-Keys"""
    
    def __init__(self, master_password: Optional[str] = None):
        self.master_password = master_password or os.getenv("MASTER_PASSWORD", "famo_trafficapp_2025")
        self.key_file = "config/secure_keys.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Stellt sicher, dass das config-Verzeichnis existiert"""
        os.makedirs("config", exist_ok=True)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Leitet einen Schlüssel aus Passwort und Salt ab"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _generate_salt(self) -> bytes:
        """Generiert ein zufälliges Salt"""
        return os.urandom(16)
    
    def encrypt_key(self, api_key: str, key_name: str = "openai") -> dict:
        """
        Verschlüsselt einen API-Key
        
        Args:
            api_key: Der zu verschlüsselnde API-Key
            key_name: Name des Keys (z.B. "openai", "google", etc.)
            
        Returns:
            Dict mit verschlüsselten Daten
        """
        # Generiere Salt
        salt = self._generate_salt()
        
        # Leite Schlüssel ab
        key = self._derive_key(self.master_password, salt)
        
        # Verschlüssele API-Key
        fernet = Fernet(key)
        encrypted_key = fernet.encrypt(api_key.encode())
        
        # Erstelle Hash für Verifikation
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return {
            "key_name": key_name,
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "salt": base64.b64encode(salt).decode(),
            "key_hash": key_hash,
            "created_at": os.path.getctime(__file__) if os.path.exists(__file__) else 0
        }
    
    def decrypt_key(self, encrypted_data: dict) -> Optional[str]:
        """
        Entschlüsselt einen API-Key
        
        Args:
            encrypted_data: Dict mit verschlüsselten Daten
            
        Returns:
            Entschlüsselter API-Key oder None bei Fehler
        """
        try:
            # Dekodiere Base64-Daten
            encrypted_key = base64.b64decode(encrypted_data["encrypted_key"])
            salt = base64.b64decode(encrypted_data["salt"])
            
            # Leite Schlüssel ab
            key = self._derive_key(self.master_password, salt)
            
            # Entschlüssele API-Key
            fernet = Fernet(key)
            decrypted_key = fernet.decrypt(encrypted_key).decode()
            
            # Verifiziere Hash
            key_hash = hashlib.sha256(decrypted_key.encode()).hexdigest()
            if key_hash != encrypted_data["key_hash"]:
                raise ValueError("Key hash verification failed")
            
            return decrypted_key
            
        except Exception as e:
            print(f"Fehler beim Entschlüsseln: {e}")
            return None
    
    def save_encrypted_key(self, api_key: str, key_name: str = "openai"):
        """Speichert verschlüsselten API-Key in Datei"""
        encrypted_data = self.encrypt_key(api_key, key_name)
        
        # Lade bestehende Keys
        keys_data = self.load_encrypted_keys()
        keys_data[key_name] = encrypted_data
        
        # Speichere in Datei
        with open(self.key_file, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, indent=2, ensure_ascii=False)
        
        print(f"API-Key '{key_name}' sicher verschlüsselt gespeichert")
    
    def load_encrypted_keys(self) -> dict:
        """Lädt verschlüsselte Keys aus Datei"""
        if not os.path.exists(self.key_file):
            return {}
        
        try:
            with open(self.key_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Keys: {e}")
            return {}
    
    def get_decrypted_key(self, key_name: str = "openai") -> Optional[str]:
        """Gibt entschlüsselten API-Key zurück"""
        keys_data = self.load_encrypted_keys()
        
        if key_name not in keys_data:
            print(f"Key '{key_name}' nicht gefunden")
            return None
        
        return self.decrypt_key(keys_data[key_name])
    
    def list_available_keys(self) -> list:
        """Gibt Liste verfügbarer Keys zurück"""
        keys_data = self.load_encrypted_keys()
        return list(keys_data.keys())
    
    def delete_key(self, key_name: str):
        """Löscht einen verschlüsselten Key"""
        keys_data = self.load_encrypted_keys()
        
        if key_name in keys_data:
            del keys_data[key_name]
            
            with open(self.key_file, 'w', encoding='utf-8') as f:
                json.dump(keys_data, f, indent=2, ensure_ascii=False)
            
            print(f"Key '{key_name}' gelöscht")
        else:
            print(f"Key '{key_name}' nicht gefunden")
    
    def verify_key(self, key_name: str = "openai") -> bool:
        """Verifiziert, ob ein Key korrekt entschlüsselt werden kann"""
        decrypted_key = self.get_decrypted_key(key_name)
        return decrypted_key is not None

# Globale Instanz
key_manager = SecureKeyManager()

def encrypt_and_save_key(api_key: str, key_name: str = "openai"):
    """Hilfsfunktion zum Verschlüsseln und Speichern eines Keys"""
    key_manager.save_encrypted_key(api_key, key_name)

def get_secure_key(key_name: str = "openai") -> Optional[str]:
    """Hilfsfunktion zum Abrufen eines entschlüsselten Keys"""
    return key_manager.get_decrypted_key(key_name)

def list_secure_keys() -> list:
    """Hilfsfunktion zum Auflisten verfügbarer Keys"""
    return key_manager.list_available_keys()
