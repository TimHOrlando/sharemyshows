import os
from dotenv import load_dotenv

# Explicitly load .env file
load_dotenv('.env')

print("=" * 60)
print("CHECKING IF .ENV FILE IS LOADED")
print("=" * 60)

print("\nDirect os.getenv() check:")
print(f"MAIL_SERVER: {os.getenv('MAIL_SERVER')}")
print(f"MAIL_PORT: {os.getenv('MAIL_PORT')}")
print(f"MAIL_USE_TLS: {os.getenv('MAIL_USE_TLS')}")
print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD: {os.getenv('MAIL_PASSWORD')}")

print("\n" + "=" * 60)
print("CHECKING CONFIG.PY")
print("=" * 60)

from config.config import config

dev_config = config['development']
print(f"\nMAIL_SERVER in Config: {getattr(dev_config, 'MAIL_SERVER', 'NOT FOUND')}")
print(f"MAIL_PORT in Config: {getattr(dev_config, 'MAIL_PORT', 'NOT FOUND')}")
print(f"MAIL_USERNAME in Config: {getattr(dev_config, 'MAIL_USERNAME', 'NOT FOUND')}")
print(f"MAIL_PASSWORD in Config: {getattr(dev_config, 'MAIL_PASSWORD', 'NOT FOUND')}")

print("\n" + "=" * 60)
print("CHECKING FLASK APP CONFIG")
print("=" * 60)

from app import create_app
app = create_app()

print(f"\nMAIL_SERVER: {app.config.get('MAIL_SERVER')}")
print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD: {'✅ SET (' + str(len(app.config.get('MAIL_PASSWORD', ''))) + ' chars)' if app.config.get('MAIL_PASSWORD') else '❌ NOT SET'}")
