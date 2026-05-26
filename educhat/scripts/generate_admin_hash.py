
from passlib.context import CryptContext

# Use the exact same context as defined in main.py (in common/auth.py actually, but checking consistency)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "admin"
hashed = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Generated Hash: {hashed}")

# Verify immediately
print(f"Verification: {pwd_context.verify(password, hashed)}")
