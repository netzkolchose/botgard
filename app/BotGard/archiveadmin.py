from typing import Union

from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction, router
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.template.response import TemplateResponse
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import unquote, model_ngettext
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import TO_FIELD_VAR, IS_POPUP_VAR
from django.contrib.admin.decorators import action
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import AbstractUser, AnonymousUser

from BotGard.models import ArchiveBaseModel


csrf_protect_m = method_decorator(csrf_protect)


class ArchiveModelAdmin(admin.ModelAdmin):
    """
    Base ModelAdmin class for archivable models (ArchiveBaseModel).

    If the model is based on ArchiveBaseModel,
    the delete actions will be replaced by archive actions.

    Does not change behaviour is model is not based on ArchiveBaseModel.
    """
    def is_archive_model(self) -> bool:
        """Returns true of the model of this ModelAdmin class is based on the ArchiveBaseModel"""
        return issubclass(self.model, ArchiveBaseModel)

    def has_show_deleted_permission(self, user: Union[AbstractUser, AnonymousUser]) -> bool:
        """
        Returns true if the user has the permission to show deleted objects for this ModelAdmins' class.
        Administrators have this permission automatically.
        """
        return user.has_perm(f"{self.opts.app_label}.show_deleted_{self.opts.model_name}")

    def get_queryset(self, request):
        qset = super().get_queryset(request)
        if self.is_archive_model() and not self.has_show_deleted_permission(request.user):
            qset = qset.filter(is_deleted=False)
        return qset

    def get_list_display(self, request):
        names = super().get_list_display(request)
        if self.is_archive_model() and self.has_show_deleted_permission(request.user):
            for key in ("is_deleted", "date_deleted"):
                if key not in names:
                    if isinstance(names, tuple):
                        names = list(names)
                    names.append(key)
        return names

    def get_urls(self):
        urls = super().get_urls()

        if self.is_archive_model():
            # replace delete urls to point to self.archive_instead_of_delete_view
            delete_link_name = f"{self.opts.app_label}_{self.opts.model_name}_delete"
            for i, url in enumerate(urls):
                if url.name == delete_link_name:
                    urls[i] = path(
                        "<path:object_id>/delete/",
                        self.admin_site.admin_view(self.archive_instead_of_delete_view),
                        name=delete_link_name,
                    )

        return urls

    def get_actions(self, request) -> dict:
        actions = super().get_actions(request)
        if not self.is_archive_model():
            return actions

        # replace delete-objects action
        if "delete_selected" in actions:
            func, name, desc = actions["delete_selected"]
            actions["delete_selected"] = (archive_selected, name, desc)

        if self.has_show_deleted_permission(request.user):
            actions["undelete_selected"] = (
                unarchive_selected,
                "undelete_selected",
                _("Undelete selected %(verbose_name_plural)s"),
            )

        return actions

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # first of all, remove `is_deleted` and `date_deleted` from auto-generated fieldsets
        for name, options in fieldsets:
            if options.get("fields"):
                options["fields"] = [
                    field for field in options["fields"]
                    if field not in ("is_deleted", "date_deleted")
                ]
        # then add the fields to the bottom if applicable
        if self.is_archive_model() and self.has_show_deleted_permission(request.user):
            fieldsets = (
                *fieldsets,
                (
                    _("Deletion status"),
                    {
                        "fields": ["is_deleted", "date_deleted"],
                        "classes": ["collapse"],
                    }
                )
            )
        return fieldsets

    def save_model(self, request, obj, form, change):
        # Set `date_deleted` to now if `is_deleted` flag was set in changeview
        if self.is_archive_model():
            if obj.is_deleted and not obj.date_deleted:
                obj.date_deleted = timezone.now()
        super().save_model(request, obj, form, change)

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if self.is_archive_model():
            if self.has_show_deleted_permission(request.user):
                if not extra_context:
                    extra_context = {}
                extra_context

        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._changeform_view(request, object_id, form_url, extra_context)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._changeform_view(request, object_id, form_url, extra_context)


    @csrf_protect_m
    def archive_instead_of_delete_view(self, request, object_id, extra_context=None):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._archive_instead_of_delete_view(request, object_id, extra_context)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._archive_instead_of_delete_view(request, object_id, extra_context)

    def _archive_instead_of_delete_view(self, request, object_id, extra_context):
        app_label = self.opts.app_label

        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, self.opts, object_id)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = self.get_deleted_objects([obj], request)

        if request.POST and not protected:  # The user has confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = str(obj)
            attr = str(to_field) if to_field else self.opts.pk.attname
            obj_id = obj.serializable_value(attr)
            self.log_deletions(request, [obj])

            # This is the part that is changed from the django.contrib.admin.ModelAdmin code
            obj.is_deleted = True
            obj.date_deleted = timezone.now()
            obj.save()

            response = self.response_delete(request, obj_display, obj_id)
            # instead of duplicating the whole response_delete code, just attach another
            # message that informs about the archiving
            self.message_user(
                request,
                _("The deletion is not permanent. The object has only been archived."),
                messages.INFO,
            )
            return response

        object_name = str(self.opts.verbose_name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": object_name}
        else:
            title = _("Delete")

        context = {
            **self.admin_site.each_context(request),
            "title": title,
            "subtitle": None,
            "object_name": object_name,
            "object": obj,
            "deleted_objects": deleted_objects,
            "model_count": dict(model_count).items(),
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": self.opts,
            "app_label": app_label,
            "preserved_filters": self.get_preserved_filters(request),
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "is_archive_model": self.is_archive_model(),
            **(extra_context or {}),
        }

        return self.render_delete_form(request, context)



@action(
    permissions=["delete"],
    description=_("Delete selected %(verbose_name_plural)s"),
)
def archive_selected(modeladmin, request, queryset):
    """
    Default action which not deletes but archives the selected objects.
    (copied from django/contrib/admin/actions.py and adjusted)

    This action first displays a confirmation page which shows all the
    deletable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it deletes all selected objects and redirects back to the change list.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    (
        deletable_objects,
        model_count,
        perms_needed,
        protected,
    ) = modeladmin.get_deleted_objects(queryset, request)

    # The user has already confirmed the deletion.
    # Do the deletion and return None to display the change list view again.
    if request.POST.get("post") and not protected:
        if perms_needed:
            raise PermissionDenied
        n = len(queryset)
        if n:
            modeladmin.log_deletions(request, queryset)

            # here's the part that is changed from normal django delete action
            #modeladmin.delete_queryset(request, queryset)
            queryset.update(is_deleted=True, date_deleted=timezone.now())

            modeladmin.message_user(
                request,
                _("Successfully deleted %(count)d %(items)s.")
                % {"count": n, "items": model_ngettext(modeladmin.opts, n)},
                messages.SUCCESS,
            )
            # make the messages consistent with what the delete endpoint says
            modeladmin.message_user(
                request,
                _("The deletion is not permanent. The objects have only been archived."),
                messages.INFO,
            )
        # Return None to display the change list page again.
        return None

    objects_name = model_ngettext(queryset)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Delete multiple objects")

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": title,
        "subtitle": None,
        "objects_name": str(objects_name),
        "deletable_objects": [deletable_objects],
        "model_count": dict(model_count).items(),
        "queryset": queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "is_archive_model": modeladmin.is_archive_model(),
        "media": modeladmin.media,
    }

    request.current_app = modeladmin.admin_site.name

    # Display the confirmation page
    return TemplateResponse(
        request,
        modeladmin.delete_selected_confirmation_template
        or [
            "admin/%s/%s/delete_selected_confirmation.html"
            % (app_label, opts.model_name),
            "admin/%s/delete_selected_confirmation.html" % app_label,
            "admin/delete_selected_confirmation.html",
            ],
        context,
        )


def unarchive_selected(modeladmin: ArchiveModelAdmin, request, queryset):
    if not modeladmin.has_show_deleted_permission(request.user):
        raise PermissionDenied

    if request.method == "POST":
        n = len(queryset)
        if n:
            LogEntry.objects.log_actions(
                user_id=request.user.pk,
                queryset=queryset,
                action_flag=CHANGE,
                change_message="Undeleted",
            )

            queryset.update(is_deleted=False)

            modeladmin.message_user(
                request,
                _("Successfully undeleted %(count)d %(items)s.")
                % {"count": n, "items": model_ngettext(modeladmin.opts, n)},
                messages.SUCCESS,
            )
