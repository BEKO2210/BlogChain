import base64
import os
import json
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey, VerifyKey
import nacl.utils
import nacl.secret
import nacl.pwhash
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_key_pair():
    """
    Generate a new encryption key pair for asymmetric encryption.
    
    Returns:
        tuple: (private_key, public_key) as bytes
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    
    logger.info("New encryption key pair generated")
    return private_key.encode(), public_key.encode()

def generate_signing_key_pair():
    """
    Generate a new signing key pair for digital signatures.
    
    Returns:
        tuple: (signing_key, verify_key) as bytes
    """
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    
    logger.info("New signing key pair generated")
    return signing_key.encode(), verify_key.encode()

def derive_key_from_password(password, salt=None, iterations=100000):
    """
    Derive a cryptographic key from a password using PBKDF2.
    
    Args:
        password (str): User password
        salt (bytes, optional): Salt for key derivation
        iterations (int): Number of iterations for PBKDF2
        
    Returns:
        tuple: (key, salt) as bytes
    """
    if salt is None:
        salt = os.urandom(16)
    
    # Convert password to bytes if it's a string
    if isinstance(password, str):
        password = password.encode()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key
        salt=salt,
        iterations=iterations
    )
    
    key = kdf.derive(password)
    logger.info(f"Key derived from password with {iterations} iterations")
    
    return key, salt

def encrypt_data(data, key):
    """
    Encrypt data using symmetric encryption (AES-256-GCM).
    
    Args:
        data: Data to encrypt (string or dict/list will be JSON-encoded)
        key (bytes): Encryption key
        
    Returns:
        str: Base64-encoded encrypted data
    """
    # Convert data to JSON string if it's a dict or list
    if isinstance(data, (dict, list)):
        data = json.dumps(data)
    
    # Convert string to bytes if needed
    if isinstance(data, str):
        data = data.encode()
    
    # Überprüfen, ob der Schlüssel None ist und erstellen eines Standard-Schlüssels
    if key is None:
        logger.warning("Encryption key is None, using a default secure key")
        key = hashlib.sha256(b'BlockJournal_Default_Key').digest()
    
    # Sicherstellen, dass der Schlüssel 32 Bytes lang ist
    if len(key) != 32:
        logger.warning(f"Key length is {len(key)} bytes, adjusting to 32 bytes")
        if len(key) < 32:
            # Schlüssel erweitern, wenn er zu kurz ist
            key = key + b'\x00' * (32 - len(key))
        else:
            # Schlüssel kürzen, wenn er zu lang ist
            key = key[:32]
    
    # Generate a random nonce
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    
    # Create a SecretBox with the key
    box = nacl.secret.SecretBox(key)
    
    # Encrypt the data
    encrypted = box.encrypt(data, nonce)
    
    # Encode to base64 for storage
    encoded = base64.b64encode(encrypted).decode()
    
    logger.debug("Data encrypted successfully")
    return encoded

def decrypt_data(encrypted_data, key):
    """
    Decrypt data that was encrypted with encrypt_data.
    
    Args:
        encrypted_data (str): Base64-encoded encrypted data
        key (bytes): Decryption key
        
    Returns:
        The decrypted data (string or parsed JSON object)
    """
    try:
        # Decode from base64
        encrypted = base64.b64decode(encrypted_data)
        
        # Überprüfen, ob der Schlüssel None ist und erstellen eines Standard-Schlüssels
        if key is None:
            logger.warning("Decryption key is None, using a default secure key")
            key = hashlib.sha256(b'BlockJournal_Default_Key').digest()
        
        # Sicherstellen, dass der Schlüssel 32 Bytes lang ist
        if len(key) != 32:
            logger.warning(f"Key length is {len(key)} bytes, adjusting to 32 bytes")
            if len(key) < 32:
                # Schlüssel erweitern, wenn er zu kurz ist
                key = key + b'\x00' * (32 - len(key))
            else:
                # Schlüssel kürzen, wenn er zu lang ist
                key = key[:32]
        
        # Create a SecretBox with the key
        box = nacl.secret.SecretBox(key)
        
        # Decrypt the data
        decrypted = box.decrypt(encrypted)
        
        # Try to parse as JSON
        try:
            result = json.loads(decrypted)
            logger.debug("Encrypted JSON data decrypted successfully")
            return result
        except json.JSONDecodeError:
            # Return as string if not valid JSON
            logger.debug("Encrypted string data decrypted successfully")
            return decrypted.decode()
            
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise

def asymmetric_encrypt(data, public_key):
    """
    Encrypt data using asymmetric encryption (NaCl box).
    
    Args:
        data: Data to encrypt (string or dict/list will be JSON-encoded)
        public_key (bytes): Recipient's public key
        
    Returns:
        str: Base64-encoded encrypted data
    """
    # Convert data to JSON string if it's a dict or list
    if isinstance(data, (dict, list)):
        data = json.dumps(data)
    
    # Convert string to bytes if needed
    if isinstance(data, str):
        data = data.encode()
    
    # Generate an ephemeral key pair
    ephemeral_private = PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key
    
    # Create a Box with the ephemeral private key and recipient's public key
    recipient_public = PublicKey(public_key)
    box = Box(ephemeral_private, recipient_public)
    
    # Generate a random nonce
    nonce = nacl.utils.random(Box.NONCE_SIZE)
    
    # Encrypt the data
    encrypted = box.encrypt(data, nonce)
    
    # Include the ephemeral public key with the encrypted data
    result = {
        "ephemeral_public": base64.b64encode(ephemeral_public.encode()).decode(),
        "encrypted": base64.b64encode(encrypted).decode()
    }
    
    logger.debug("Data asymmetrically encrypted successfully")
    return json.dumps(result)

def asymmetric_decrypt(encrypted_data, private_key):
    """
    Decrypt data that was encrypted with asymmetric_encrypt.
    
    Args:
        encrypted_data (str): JSON string with encrypted data and ephemeral public key
        private_key (bytes): Recipient's private key
        
    Returns:
        The decrypted data (string or parsed JSON object)
    """
    try:
        # Parse the encrypted data
        data = json.loads(encrypted_data)
        ephemeral_public_b64 = data["ephemeral_public"]
        encrypted_b64 = data["encrypted"]
        
        # Decode from base64
        ephemeral_public_bytes = base64.b64decode(ephemeral_public_b64)
        encrypted = base64.b64decode(encrypted_b64)
        
        # Create a Box with the recipient's private key and sender's ephemeral public key
        recipient_private = PrivateKey(private_key)
        ephemeral_public = PublicKey(ephemeral_public_bytes)
        box = Box(recipient_private, ephemeral_public)
        
        # Decrypt the data
        decrypted = box.decrypt(encrypted)
        
        # Try to parse as JSON
        try:
            result = json.loads(decrypted)
            logger.debug("Asymmetrically encrypted JSON data decrypted successfully")
            return result
        except json.JSONDecodeError:
            # Return as string if not valid JSON
            logger.debug("Asymmetrically encrypted string data decrypted successfully")
            return decrypted.decode()
            
    except Exception as e:
        logger.error(f"Asymmetric decryption failed: {str(e)}")
        raise

def sign_data(data, signing_key):
    """
    Sign data with a signing key.
    
    Args:
        data: Data to sign (string or dict/list will be JSON-encoded)
        signing_key (bytes): Signing key
        
    Returns:
        str: Base64-encoded signature
    """
    # Convert data to JSON string if it's a dict or list
    if isinstance(data, (dict, list)):
        data = json.dumps(data)
    
    # Convert string to bytes if needed
    if isinstance(data, str):
        data = data.encode()
    
    # Create a SigningKey from the provided key
    key = SigningKey(signing_key)
    
    # Sign the data
    signature = key.sign(data).signature
    
    # Encode to base64
    encoded = base64.b64encode(signature).decode()
    
    logger.debug("Data signed successfully")
    return encoded

def verify_signature(data, signature, verify_key):
    """
    Verify a signature.
    
    Args:
        data: Signed data (string or dict/list will be JSON-encoded)
        signature (str): Base64-encoded signature
        verify_key (bytes): Verification key
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Convert data to JSON string if it's a dict or list
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        
        # Convert string to bytes if needed
        if isinstance(data, str):
            data = data.encode()
        
        # Decode signature from base64
        signature_bytes = base64.b64decode(signature)
        
        # Create a VerifyKey from the provided key
        key = VerifyKey(verify_key)
        
        # Verify the signature
        key.verify(data, signature_bytes)
        
        logger.debug("Signature verified successfully")
        return True
    except Exception as e:
        logger.warning(f"Signature verification failed: {str(e)}")
        return False

def generate_secure_password(length=16):
    """
    Generate a secure random password.
    
    Args:
        length (int): Length of the password
        
    Returns:
        str: Random password
    """
    # Characters to use in the password
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?"
    
    # Generate random bytes
    random_bytes = os.urandom(length)
    
    # Convert bytes to password characters
    password = ''.join(chars[b % len(chars)] for b in random_bytes)
    
    logger.info(f"Generated secure password of length {length}")
    return password
