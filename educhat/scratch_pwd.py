import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_str = "$2b$12$Xb.kzP7z3JxC1rOH1dAwnehLJT8JpNfFPh9NKs.wC.RNTaZkq/PJa"

passwords = ["admin", "password", "123456", "admin123"]
for p in passwords:
    if pwd_context.verify(p, hash_str):
        print(f"Password is: {p}")
        sys.exit(0)
print("Not found")
