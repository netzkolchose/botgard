import secrets

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

PASSWORD_RESET_CODE_LENGTH = 96


def generate_password_reset_code() -> str:
    return secrets.token_urlsafe(PASSWORD_RESET_CODE_LENGTH)[:PASSWORD_RESET_CODE_LENGTH]


class PasswordResetCode(models.Model):

    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="password_reset_code",
    )

    code = models.CharField(
        max_length=PASSWORD_RESET_CODE_LENGTH,
        default=generate_password_reset_code,
    )


