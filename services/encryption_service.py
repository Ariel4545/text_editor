'''
This service provides a comprehensive suite of cryptographic and encoding functionalities,
encapsulating logic for symmetric and asymmetric encryption, digital signatures, hashing,
and various encoding schemes. It relies on libraries like PyCryptodome and rsa, with
graceful fallbacks if they are not installed.
'''

import base64
import binascii
import hashlib
from functools import wraps
from typing import Union, Tuple, Optional
from urllib.parse import quote, unquote

__all__ = [
    'Symmetric', 'Asymmetric', 'Hashing', 'Encoding',
    'to_bytes', 'to_text', 'PrivateKey', 'PublicKey',
    'KeyIO', 'Validators'
]

# --- Optional Dependencies & Type Aliases ---
try:
    from cryptography.fernet import Fernet, InvalidToken
    _FERNET_OK = True
except ImportError:
    _FERNET_OK = False
    Fernet = type('Fernet', (), {})
    InvalidToken = type('InvalidToken', (Exception,), {})

try:
    import rsa
    _RSA_LIB_OK = True
    RsaLibPrivateKey = rsa.PrivateKey
    RsaLibPublicKey = rsa.PublicKey
except ImportError:
    _RSA_LIB_OK = False
    rsa = None
    RsaLibPrivateKey = type('RsaLibPrivateKey', (), {})
    RsaLibPublicKey = type('RsaLibPublicKey', (), {})

try:
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Hash import SHA256
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
    from Crypto.Signature import pss
    from Crypto.PublicKey import RSA as PyCryptoRSA
    try:
        from Crypto.Cipher import ChaCha20_Poly1305
        _CHACHA_OK = True
    except Exception:
        ChaCha20_Poly1305 = None
        _CHACHA_OK = False
    _PYCRYPTODOME_OK = True
    PyCryptoPrivateKey = PyCryptoRSA._RSAobj
    PyCryptoPublicKey = PyCryptoRSA.RsaKey
except ImportError:
    _PYCRYPTODOME_OK = False
    AES = PKCS1_OAEP = SHA256 = PBKDF2 = get_random_bytes = pss = PyCryptoRSA = None
    ChaCha20_Poly1305 = None
    _CHACHA_OK = False
    PyCryptoPrivateKey = type('PyCryptoPrivateKey', (), {})
    PyCryptoPublicKey = type('PyCryptoPublicKey', (), {})

# --- Decorators ---
def _requires_lib(lib_ok_flag: bool, lib_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not lib_ok_flag:
                raise ImportError(f'{lib_name} is not installed.')
            return func(*args, **kwargs)
        return wrapper
    return decorator

requires_fernet = _requires_lib(_FERNET_OK, 'cryptography')
requires_pycryptodome = _requires_lib(_PYCRYPTODOME_OK, 'PyCryptodome')

def requires_asymmetric_lib(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _PYCRYPTODOME_OK and not _RSA_LIB_OK:
            raise ImportError('Neither PyCryptodome nor rsa library is installed.')
        return func(*args, **kwargs)
    return wrapper

# --- Types ---
PrivateKey = Union[PyCryptoPrivateKey, RsaLibPrivateKey]
PublicKey = Union[PyCryptoPublicKey, RsaLibPublicKey]

# --- Utils ---
def to_bytes(s: Union[str, bytes]) -> bytes:
    return s.encode('utf-8') if isinstance(s, str) else s

def to_text(b: Union[bytes, str]) -> str:
    return b.decode('utf-8', errors='ignore') if isinstance(b, (bytes, bytearray)) else b

def _b64_fix_padding(s: Union[str, bytes]) -> str:
    if isinstance(s, bytes):
        s = s.decode('ascii', errors='ignore')
    s = s.strip().replace('\n', '').replace('\r', '')
    missing = (-len(s)) % 4
    return s + ('=' * missing)

# --- Constants ---
_AES_KEY_SIZE = 32
_AES_NONCE_SIZE = 16
_AES_TAG_SIZE = 16
_CHACHA_NONCE_SIZE = 12
_CHACHA_TAG_SIZE = 16
_PBKDF2_COUNT = 100000

class Validators:
    @staticmethod
    def is_base64(s: str) -> bool:
        try:
            base64.urlsafe_b64decode(_b64_fix_padding(s).encode('ascii'))
            return True
        except Exception:
            return False

    @staticmethod
    def is_hex(s: str) -> bool:
        try:
            bytes.fromhex(s)
            return True
        except Exception:
            return False

    @staticmethod
    def is_base32(s: str) -> bool:
        try:
            base64.b32decode(_b64_fix_padding(s), casefold=True)
            return True
        except Exception:
            return False

    @staticmethod
    def is_base85(s: str) -> bool:
        try:
            base64.a85decode(s, adobe=False, ignorechars=' \t\r\n')
            return True
        except Exception:
            return False

class KeyIO:
    '''Key import/export helpers with best-effort detection.'''
    @staticmethod
    @requires_asymmetric_lib
    def import_private_key(pem: bytes) -> PrivateKey:
        if _PYCRYPTODOME_OK:
            try:
                return PyCryptoRSA.import_key(pem)
            except Exception:
                pass
        if _RSA_LIB_OK:
            try:
                return rsa.PrivateKey.load_pkcs1(pem)
            except Exception:
                pass
        raise ValueError('Unsupported private key PEM')

    @staticmethod
    @requires_asymmetric_lib
    def import_public_key(pem: bytes) -> PublicKey:
        if _PYCRYPTODOME_OK:
            try:
                return PyCryptoRSA.import_key(pem)
            except Exception:
                pass
        if _RSA_LIB_OK:
            try:
                return rsa.PublicKey.load_pkcs1(pem)
            except Exception:
                pass
        raise ValueError('Unsupported public key PEM')

    @staticmethod
    def export_private_key(key: PrivateKey) -> bytes:
        if _PYCRYPTODOME_OK and isinstance(key, PyCryptoPrivateKey):
            return key.export_key('PEM')
        if _RSA_LIB_OK and isinstance(key, RsaLibPrivateKey):
            return key.save_pkcs1(format='PEM')
        raise ValueError('Unsupported private key type for export')

    @staticmethod
    def export_public_key(key: PublicKey) -> bytes:
        if _PYCRYPTODOME_OK and isinstance(key, PyCryptoPublicKey):
            return key.export_key('PEM')
        if _RSA_LIB_OK and isinstance(key, RsaLibPublicKey):
            return key.save_pkcs1(format='PEM')
        raise ValueError('Unsupported public key type for export')

class Symmetric:
    @staticmethod
    @requires_fernet
    def generate_fernet_key() -> bytes:
        return Fernet.generate_key()

    @staticmethod
    @requires_pycryptodome
    def generate_aes_key_from_password(password: str, salt: bytes) -> bytes:
        if not password:
            raise ValueError('Password cannot be empty.')
        if not salt:
            raise ValueError('Salt cannot be empty.')
        return PBKDF2(to_bytes(password), salt, dkLen=_AES_KEY_SIZE, count=_PBKDF2_COUNT, hmac_hash_module=SHA256)

    @staticmethod
    @requires_pycryptodome
    def generate_salt(size: int = 16) -> bytes:
        return get_random_bytes(size)

    @staticmethod
    @requires_fernet
    def fernet_encrypt(data: str, key: bytes) -> bytes:
        return Fernet(key).encrypt(to_bytes(data))

    @staticmethod
    @requires_fernet
    def fernet_decrypt(token: bytes, key: bytes) -> str:
        try:
            return to_text(Fernet(key).decrypt(token))
        except InvalidToken:
            raise ValueError('Invalid or corrupted token, or incorrect key.')

    @staticmethod
    @requires_pycryptodome
    def aes_gcm_encrypt(data: str, key: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_GCM)
        ct, tag = cipher.encrypt_and_digest(to_bytes(data))
        return cipher.nonce + tag + ct

    @staticmethod
    @requires_pycryptodome
    def aes_gcm_decrypt(encrypted_data: bytes, key: bytes) -> str:
        if len(encrypted_data) < (_AES_NONCE_SIZE + _AES_TAG_SIZE):
            raise ValueError('Invalid data length for AES-GCM decryption.')
        nonce = encrypted_data[:_AES_NONCE_SIZE]
        tag = encrypted_data[_AES_NONCE_SIZE:_AES_NONCE_SIZE+_AES_TAG_SIZE]
        ct = encrypted_data[_AES_NONCE_SIZE+_AES_TAG_SIZE:]
        try:
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            return to_text(cipher.decrypt_and_verify(ct, tag))
        except (ValueError, KeyError):
            raise ValueError('Decryption failed. Data may be corrupt or key incorrect.')

    @staticmethod
    @requires_pycryptodome
    def chacha20_poly1305_encrypt(data: str, key: bytes) -> bytes:
        if not _CHACHA_OK:
            raise ImportError('ChaCha20-Poly1305 not available.')
        cipher = ChaCha20_Poly1305.new(key=key)
        ct, tag = cipher.encrypt_and_digest(to_bytes(data))
        return cipher.nonce + tag + ct

    @staticmethod
    @requires_pycryptodome
    def chacha20_poly1305_decrypt(encrypted_data: bytes, key: bytes) -> str:
        if not _CHACHA_OK:
            raise ImportError('ChaCha20-Poly1305 not available.')
        if len(encrypted_data) < (_CHACHA_NONCE_SIZE + _CHACHA_TAG_SIZE):
            raise ValueError('Invalid data length for ChaCha20-Poly1305 decryption.')
        nonce = encrypted_data[:_CHACHA_NONCE_SIZE]
        tag = encrypted_data[_CHACHA_NONCE_SIZE:_CHACHA_NONCE_SIZE+_CHACHA_TAG_SIZE]
        ct = encrypted_data[_CHACHA_NONCE_SIZE+_CHACHA_TAG_SIZE:]
        try:
            cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
            return to_text(cipher.decrypt_and_verify(ct, tag))
        except (ValueError, KeyError):
            raise ValueError('Decryption failed. Data may be corrupt or key incorrect.')

class Asymmetric:
    @staticmethod
    @requires_asymmetric_lib
    def generate_rsa_keys(bits: int = 2048) -> Tuple[PublicKey, PrivateKey]:
        if _PYCRYPTODOME_OK:
            key = PyCryptoRSA.generate(bits)
            return key.public_key(), key
        elif _RSA_LIB_OK:
            return rsa.newkeys(bits)

    @staticmethod
    @requires_asymmetric_lib
    def rsa_encrypt(data: str, public_key: PublicKey) -> bytes:
        plain = to_bytes(data)
        if _PYCRYPTODOME_OK and isinstance(public_key, PyCryptoPublicKey):
            session_key = get_random_bytes(_AES_KEY_SIZE)
            cipher_aes = AES.new(session_key, AES.MODE_GCM)
            ct, tag = cipher_aes.encrypt_and_digest(plain)
            cipher_rsa = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
            enc_session_key = cipher_rsa.encrypt(session_key)
            return enc_session_key + cipher_aes.nonce + tag + ct
        if _RSA_LIB_OK and isinstance(public_key, RsaLibPublicKey):
            max_len = rsa.common.byte_size(public_key.n) - 11
            if len(plain) > max_len:
                raise ValueError(f'Content too large for basic RSA (max: {max_len} bytes).')
            return rsa.encrypt(plain, public_key)
        raise TypeError('Unsupported public key type or no suitable RSA library available.')

    @staticmethod
    @requires_asymmetric_lib
    def rsa_decrypt(encrypted_data: bytes, private_key: PrivateKey) -> str:
        if _PYCRYPTODOME_OK and isinstance(private_key, PyCryptoPrivateKey):
            rsa_size = private_key.size_in_bytes()
            min_len = rsa_size + _AES_NONCE_SIZE + _AES_TAG_SIZE
            if len(encrypted_data) < min_len:
                raise ValueError('Invalid data length for hybrid decryption.')
            enc_session_key = encrypted_data[:rsa_size]
            nonce = encrypted_data[rsa_size:rsa_size+_AES_NONCE_SIZE]
            tag = encrypted_data[rsa_size+_AES_NONCE_SIZE:rsa_size+_AES_NONCE_SIZE+_AES_TAG_SIZE]
            ct = encrypted_data[rsa_size+_AES_NONCE_SIZE+_AES_TAG_SIZE:]
            try:
                cipher_rsa = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
                session_key = cipher_rsa.decrypt(enc_session_key)
                cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
                return to_text(cipher_aes.decrypt_and_verify(ct, tag))
            except (ValueError, TypeError):
                raise ValueError('Decryption failed. Data may be corrupt or key incorrect.')
        if _RSA_LIB_OK and isinstance(private_key, RsaLibPrivateKey):
            try:
                return to_text(rsa.decrypt(encrypted_data, private_key))
            except rsa.pkcs1.DecryptionError:
                raise ValueError('Decryption failed. Data may be corrupt or key incorrect.')
        raise TypeError('Unsupported private key type or no suitable RSA library available.')

    @staticmethod
    @requires_pycryptodome
    def rsa_pss_sign(data: str, private_key: PyCryptoPrivateKey) -> bytes:
        if not isinstance(private_key, PyCryptoPrivateKey):
            raise TypeError('A PyCryptodome private key is required.')
        h = SHA256.new(to_bytes(data))
        return pss.new(private_key).sign(h)

    @staticmethod
    @requires_pycryptodome
    def rsa_pss_verify(data: str, signature: bytes, public_key: PyCryptoPublicKey) -> bool:
        if not isinstance(public_key, PyCryptoPublicKey):
            raise TypeError('A PyCryptodome public key is required.')
        h = SHA256.new(to_bytes(data))
        try:
            pss.new(public_key).verify(h, signature)
            return True
        except (ValueError, TypeError):
            return False

class Hashing:
    @staticmethod
    def sha256(data: str) -> str:
        return hashlib.sha256(to_bytes(data)).hexdigest()

    @staticmethod
    def sha512(data: str) -> str:
        return hashlib.sha512(to_bytes(data)).hexdigest()

    @staticmethod
    def md5(data: str) -> str:
        return hashlib.md5(to_bytes(data)).hexdigest()

class Encoding:
    @staticmethod
    def base64_encode(data: str) -> str:
        return base64.urlsafe_b64encode(to_bytes(data)).decode('ascii')

    @staticmethod
    def base64_decode(encoded_data: str) -> str:
        try:
            return to_text(base64.urlsafe_b64decode(_b64_fix_padding(encoded_data)))
        except (binascii.Error, ValueError, TypeError) as e:
            raise ValueError(f'Base64 decoding failed: {e}')

    @staticmethod
    def base32_encode(data: str) -> str:
        return base64.b32encode(to_bytes(data)).decode('ascii')

    @staticmethod
    def base32_decode(encoded_data: str) -> str:
        try:
            return to_text(base64.b32decode(_b64_fix_padding(encoded_data), casefold=True))
        except (binascii.Error, ValueError, TypeError) as e:
            raise ValueError(f'Base32 decoding failed: {e}')

    @staticmethod
    def base85_encode(data: str) -> str:
        return base64.a85encode(to_bytes(data)).decode('ascii')

    @staticmethod
    def base85_decode(encoded_data: str) -> str:
        try:
            return to_text(base64.a85decode(encoded_data, adobe=False, ignorechars=' \t\r\n'))
        except (binascii.Error, ValueError, TypeError) as e:
            raise ValueError(f'Base85 decoding failed: {e}')

    @staticmethod
    def hex_encode(data: str) -> str:
        return to_bytes(data).hex()

    @staticmethod
    def hex_decode(hex_data: str) -> str:
        try:
            return to_text(bytes.fromhex(hex_data))
        except ValueError as e:
            raise ValueError(f'Hex decoding failed: {e}')

    @staticmethod
    def url_encode(data: str) -> str:
        return quote(data, safe='')

    @staticmethod
    def url_decode(encoded_data: str) -> str:
        return unquote(encoded_data)
