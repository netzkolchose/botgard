import urllib.parse

from django import views, forms
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model, password_validation
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables
from django.http import HttpResponseRedirect

from tools.admin_extensions import minimal_admin_context
from tools.permissions import admin_required
from tools.urls import full_server_url

from BotGard.models import PasswordResetCode

User = get_user_model()


@admin_required
def generate_password_reset_view(request, user_pk: int):
    ctx = minimal_admin_context(request, User, _("Create a one-time password reset link"))
    ctx["user"] = user = get_object_or_404(User, pk=user_pk)

    if request.method == "POST":

        with transaction.atomic():
            PasswordResetCode.objects.filter(user=user).delete()
            reset_code = PasswordResetCode.objects.create(user=user)

        url = full_server_url(reverse("reset-password", args=(reset_code.code,)))
        ctx["reset_link"] = url
        ctx["reset_link_mailto"] = "mailto:{}?{}".format(
            user.email,
            urllib.parse.urlencode(
                {
                    "subject": _("BotGard password reset link"),
                    "body": url,
                },
                quote_via=urllib.parse.quote,  # %20 instead of +
            )
        )

    return render(request, "BotGard/generate-password-reset.html", ctx)


class PasswordResetForm(forms.Form):
    email = forms.EmailField(required=True, label=_("Email"))
    password1 = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        label=_("Password"),
    )
    password2 = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        label=_("Password (again)"),
    )

    def clean(self):
        self.validate_passwords()
        return super().clean()

    @sensitive_variables("password1", "password2")
    def validate_passwords(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            error = ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
            self.add_error("password2", error)

        if password1:
            try:
                password_validation.validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)


def password_reset_view(request, code: str):
    ctx = minimal_admin_context(request, User, _("Reset password"))

    form = PasswordResetForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            ctx["message"] = _("The password reset link has expired, please request a new one from your administrator.")
            reset_code = PasswordResetCode.objects.filter(code=code).first()
            if reset_code:
                if reset_code.user.email == form.cleaned_data["email"]:
                    with transaction.atomic():
                        reset_code.user.set_password(form.cleaned_data["password1"])
                        reset_code.user.save()
                        reset_code.delete()
                    ctx["message"] = _("Your password has been changed")
                    ctx["show_login_link"] = True

    ctx["form"] = form
    return render(request, "BotGard/password-reset.html", ctx)
