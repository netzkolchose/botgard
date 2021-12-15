from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User, Permission
from django.http import HttpRequest


def check_user_can_write(user):
    if user.groups.filter(name='readOnly').exists():
        return False
    # TODO: This checks for ANY add/delete permission
    for p in user.get_all_permissions():
        if "add_" in p or "delete_" in p:
            return True
    return False


def is_kustos(request_or_user):
    if isinstance(request_or_user, HttpRequest):
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise ValueError("Expected request or user, got %s" % type(request_or_user))
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
    candis = sorted(candis)
    return candis[0]


## --- decorators ---

def login_required(function=None,
                   redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url="/admin/login/"):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    from: https://docs.djangoproject.com/en/1.10/_modules/django/contrib/auth/decorators/
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator



def write_permission_required(function=None,
                              redirect_field_name=REDIRECT_FIELD_NAME,
                              login_url="/botman/no_permission"):
    """
    Decorator for views that checks that the user is logged in and has write permission,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and check_user_can_write(u),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(function=None,
                   redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url="/botman/no_permission"):
    """
    Decorator for views that checks that the user is logged in and has write permission,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
