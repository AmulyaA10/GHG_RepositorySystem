import secrets
import string

# Generate a secure random secret key
alphabet = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
print(secret_key)
