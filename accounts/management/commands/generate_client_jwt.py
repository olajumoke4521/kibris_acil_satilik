import jwt
import time
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Generates a static JWT for client application authentication.'

    def handle(self, *args, **options):

        secret_key = getattr(settings, 'JWT_CLIENT_SECRET_KEY', None)
        algorithm = getattr(settings, 'JWT_CLIENT_ALGORITHM', 'HS256')
        ttl_seconds = getattr(settings, 'JWT_CLIENT_TTL_SECONDS', 3600) # Default 1 hour if not set
        issuer = getattr(settings, 'JWT_CLIENT_ISSUER', None)
        audience = getattr(settings, 'JWT_CLIENT_AUDIENCE', None)

        if not secret_key:
            self.stdout.write(self.style.ERROR('JWT_CLIENT_SECRET_KEY is not set in settings.'))
            return

        now = datetime.now(timezone.utc)
        exp_time = now + timedelta(seconds=ttl_seconds)
        exp_timestamp = int(exp_time.timestamp())
        iat_timestamp = int(now.timestamp())

        payload = {
            'exp': exp_timestamp,
            'iat': iat_timestamp,
            # Add issuer and audience if configured
            # You could add other claims like 'client_type': 'web/mobile' if needed later
        }
        if issuer:
            payload['iss'] = issuer
        if audience:
            payload['aud'] = audience

        try:
            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            self.stdout.write(self.style.SUCCESS('Successfully generated client JWT:'))
            self.stdout.write(token)
            self.stdout.write(f"\nExpires at: {exp_time.isoformat()}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating token: {e}"))