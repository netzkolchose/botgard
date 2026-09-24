from typing import Optional, List

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User, Permission
from django.http import HttpRequest
from django.db import models
from django.urls import reverse_lazy


def check_user_can_write(user):
    if not user.is_staff or not user.is_active:
        return False
    # TODO: This checks for ANY add/delete permission
    for p in user.get_all_permissions():
        if "add_" in p or "delete_" in p:
            return True
    return False


def check_user_has_permissions(user, *permissions: str):
    if not user.is_staff or not user.is_active:
        return False
    user_perms = user.get_all_permissions()
    for p in permissions:
        if p not in user_perms:
            # print(f"USER {user} MISSING {p}, has {sorted(user_perms)}")
            return False

    return True


def is_kustos(request_or_user):
    if isinstance(request_or_user, HttpRequest):
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise ValueError("Expected request or user, got %s" % type(request_or_user))
    if not user.is_staff or not user.is_active:
        return False
    return user.groups.filter(name="Kustus").exists()


def get_nomenclature_user():
    """
    Returns a User with the nomenclature-check permission.
    Fallback is admin/superuser
    :return: django.contrib.auth.models.User, or None in worst case
    """
    PERM = "species.can_check_nomenclature"
    candis = set()
    # check for non-admin user with permission from groups
    # ! workaround: User.get_group_permissions() returns also admin permissions :(
    perm = Permission.objects.filter(codename="can_check_nomenclature")
    if perm.exists():
        # groups having the required permission
        groups = perm[0].group_set.all()
        for g in groups:
            for u in g.user_set.all():
                if not u.is_superuser:
                    candis.add(u)
        # superuser with permission from group
        if not candis:
            for g in groups:
                for u in g.user_set.all():
                    candis.add(u)
    # fallback to any user that somehow has this permission
    if not candis:
        for u in User.objects.all():
            if u.has_perm(PERM):
                candis.add(u)
    if not candis:
        return None
    candis = sorted(candis, key=lambda u: u.username)
    return candis[0]


## --- decorators ---

def login_required(
        function=None,
        redirect_field_name=REDIRECT_FIELD_NAME,
        login_url: Optional[str] = None
):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    from: https://docs.djangoproject.com/en/1.10/_modules/django/contrib/auth/decorators/
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url or reverse_lazy("admin:login"),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator



def write_permission_required(
        function=None,
        redirect_field_name=REDIRECT_FIELD_NAME,
        login_url: Optional[str] = None,
):
    """
    Decorator for views that checks that the user is logged in and has write permission,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and check_user_can_write(u),
        login_url=login_url or reverse_lazy("botman:no_permission"),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def permission_required(
        *permissions: str,
        redirect_field_name=REDIRECT_FIELD_NAME,
        login_url: Optional[str] = None,
):
    """
    Decorator for views that checks that the user is logged in and has certain permission,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and check_user_has_permissions(u, *permissions),
        login_url=login_url or reverse_lazy("botman:no_permission"),
        redirect_field_name=redirect_field_name
    )
    return actual_decorator


def admin_required(
        function=None,
        redirect_field_name=REDIRECT_FIELD_NAME,
        login_url: Optional[str] = None,
):
    """
    Decorator for views that checks that the user is logged in and has write permission,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        login_url=login_url or reverse_lazy("botman:no_permission"),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


class SaveModelWrapper:
    """
    Wraps a model instance and raises AttributeError for fields
    for which a user does not have the field-level permissions
    """

    def __init__(
            self,
            instance: models.Model,
            user_permissions: Optional[List[str]] = None,
    ):
        from .global_request import get_current_user
        self.__instance = instance
        self.__field_permissions = getattr(instance, "field_permissions", None) or {}
        if not user_permissions:
            if user := get_current_user():
                user_permissions = user.get_all_permissions()
        self.__user_permissions = user_permissions or []

    def __getattr__(self, name: str):
        if name.startswith("__"):
            return super().__getattribute__(name)

        if required_perm := self.__field_permissions.get(name):
            if required_perm not in self.__user_permissions:
                raise AttributeError(f"{type(self.__instance).__name__} object has no attribute '{name}'")

        value = getattr(self.__instance, name)
        if isinstance(value, models.Model):
            value = SaveModelWrapper(value, self.__user_permissions)

        return value

    def __repr__(self):
        return repr(self.__instance)

    def __str__(self):
        return str(self.__instance)

