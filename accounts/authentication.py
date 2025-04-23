import jwt
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication
from rest_framework import exceptions

class StaticClientJWTAuthentication(authentication.BaseAuthentication):
    """
    Authenticates requests based on a static, pre-generated JWT
    sent in the 'Authorization: Bearer <token>' header.
    Authenticates the *client application*, not a specific user.
    """
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        secret_key = getattr(settings, 'JWT_CLIENT_SECRET_KEY', None)
        algorithm = getattr(settings, 'JWT_CLIENT_ALGORITHM', 'HS256')
        audience = getattr(settings, 'JWT_CLIENT_AUDIENCE', None)
        issuer = getattr(settings, 'JWT_CLIENT_ISSUER', None)

        if not secret_key:
            raise exceptions.AuthenticationFailed(_('Server configuration error: JWT secret key not set.'))

        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                audience=audience,
                issuer=issuer,
                # Leeway accounts for clock skew between servers
                leeway=timedelta(seconds=10)
            )

            return (None, payload)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed(_('Token has expired.'))
        except jwt.InvalidAudienceError:
             raise exceptions.AuthenticationFailed(_('Invalid token audience.'))
        except jwt.InvalidIssuerError:
             raise exceptions.AuthenticationFailed(_('Invalid token issuer.'))
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(_(f'Invalid token: {e}'))

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a 401 Unauthorized response, or `None` if the
        authentication scheme should return 403 Forbidden responses.
        """
        return f'{self.keyword} realm="api"'