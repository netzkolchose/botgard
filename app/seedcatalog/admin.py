from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import *
from tools import readOnlyAdmin


class SeedCatalogAdmin(readOnlyAdmin.ReadPermissionModelAdmin):
    fieldsets = (
        (None, {
            'fields' : (('release_date', 'valid_until_date'),)
        }),
        (_('title'), {
            'fields' : (('title', 'title_sub'),)
        }),
        (_('organisational text'), {
            'classes' : 'collapse',
            'fields' : (('copyright_note','notes'),)
        }),
        (_('text'), {
            'fields' : ('preface', )
        })
    )
    list_display = ('__str__', 'manage_seed_decorator', 'generate_catalog_decorator',
                    'pdf_file_decorator')

    #save_on_top = True
    change_form_template = "seedcatalog/change_form.html"

    class Media:
        css = {"screen": ('seedcatalog/change_form.css',)}

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Insert finalize permission to render-context
        """
        context = context or {}
        context["can_finalize"] = \
            "seedcatalog.can_finalize_catalog" in request.user.get_all_permissions()
        if obj is None:
            context["is_new"] = True

        return super(SeedCatalogAdmin, self).render_change_form(
            request, context, add, change, form_url, obj
        )


admin.site.register(SeedCatalog, SeedCatalogAdmin)
