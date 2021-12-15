from django.utils.text import capfirst
from django.contrib import admin


def minimal_admin_context(request, Model, title=None, extra=None):
    """
    Returns a template context for a minimal admin page layout
    see /botman/template/botman/minimal-admin.html
    """
    opts = Model._meta
    each_context = admin.site.each_context(request)
    ctx = extra or {}
    ctx.update(dict(
        each_context,
        # to use: {% extend admin_base_tmpl %}
        admin_base_tmpl="botman/minimal-admin.html",
        opts=opts,
        app_label=opts.app_label,
        title=title or capfirst(opts.verbose_name),
        module_name=title or capfirst(opts.verbose_name),
        show_admin_links=opts.app_label != "admin",
    ))
    return ctx


