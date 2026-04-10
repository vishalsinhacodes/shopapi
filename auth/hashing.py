from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

# List both hashers. The FIRST one in the list is used for NEW hashes.
# The others are only used to VERIFY old existing hashes.
pwd_hash = PasswordHash([
    Argon2Hasher(),  # New passwords will use Argon2
    BcryptHasher(),  # Old passwords can still be verified
])

def hash_password(password: str) -> str:
    return pwd_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_hash.verify(plain_password, hashed_password)