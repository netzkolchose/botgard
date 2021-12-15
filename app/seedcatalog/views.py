from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render

from seedcatalog.models import *
from individuals.models import *
from tools.permissions import *
from tools.admin_extensions import minimal_admin_context
from config_app import register_key


def render_catalog_edit(request, catalog: SeedCatalog, inline: bool = False, message: str = None):
    seeds = catalog.seed.all()

    allseeds = Individual.objects.filter(seed_available=True)

    ctx = minimal_admin_context(
        request, SeedCatalog,
        title=_("Samen im Katalog bearbeiten"),
        extra={
            'seeds': seeds,
            'allseeds': allseeds,
            'catalog': catalog,
            'catalog_message': message,
        }
    )

    template = 'seedcatalog/edit_inline.html' if inline else 'seedcatalog/edit_page.html'
    return render(request, template, ctx)


@write_permission_required
def edit_seeds(request, forId):
    try:
        catalog = SeedCatalog.objects.get(id=forId)
    except SeedCatalog.DoesNotExist:
        return HttpResponse(_('Catalog not found.'), status=404)

    return render_catalog_edit(request, catalog)


@write_permission_required
def remove_seed_from_catalog(request, seedId, catalogId):
    try:
        seed = Individual.objects.get(id=seedId)
    except Individual.DoesNotExist:
        return HttpResponse(_('Individual/Seed not found'), status=404)

    try:
        catalog = SeedCatalog.objects.get(id=catalogId)
    except SeedCatalog.DoesNotExist:
        return HttpResponse(_('Seed catalog not found'), status=404)

    catalog.seed.remove(seed)
    catalog.save()

    if "_redirect" in request.GET:
        return HttpResponseRedirect(request.GET["_redirect"])

    message = _('%(seed)s removed from %(catalog)s') % {'seed': seed, 'catalog': catalog}

    return render_catalog_edit(
        request=request, catalog=catalog,
        inline="inline" in request.GET,
        message=message,
    )


@write_permission_required
def add_seed_to_current_catalog(request, seedId):
    try:
        seed = Individual.objects.get(id=seedId)
    except:
        return HttpResponse(_('Individual/seed not found.'))

    try:
        catalog = SeedCatalog.objects.latest('pk')
    except:
        return HttpResponse(_('Seed catalog not found'))

    catalog.seed.add(seed)
    catalog.save()

    seed.seed_available = True
    seed.save()

    if "_redirect" in request.GET:
        return HttpResponseRedirect(request.GET["_redirect"])

    return HttpResponse(
        _('added %(seed)s to %(catalog)s (seeds are automatically marked as present)')
            % { 'seed':str(seed), 'catalog':str(catalog) })


@write_permission_required
def add_seed_to_catalog(request, seedId, catalogId):
    try:
        seed = Individual.objects.get(id=seedId)
    except:
        return HttpResponse(_('Individual/seed not found'))

    try:
        catalog = SeedCatalog.objects.get(id=catalogId)
    except:
        return HttpResponse(_('Seed catalog not found'))

    catalog.seed.add(seed)
    catalog.save()

    if "_redirect" in request.GET:
        return HttpResponseRedirect(request.GET["_redirect"])

    message = _('%(seed)s added to %(catalog)s') % {'seed': seed, 'catalog': catalog}

    return render_catalog_edit(
        request=request, catalog=catalog,
        inline="inline" in request.GET,
        message=message,
    )


def generate_catalog(request, catalog: SeedCatalog):
    import os
    import shutil
    import subprocess
    import select

    seeds = catalog.seed.all().exclude(seed_available=False).order_by(
        'species__family__family',
        'species__family__genus', 'species__species',
        'species__subspecies', 'species__variety'
    )
    c = {
        "catalog": catalog,
        "seeds": seeds,
    }
    t = loader.get_template('seedcatalog/latex/catalog.tex')
    texContent = t.render(c)

    texDirectory = os.path.join(settings.MEDIA_ROOT, "pdf/catalog/temp")
    workingDirectory = os.path.join(texDirectory, request.COOKIES['sessionid'])
    if os.path.exists(workingDirectory):
        shutil.rmtree(workingDirectory)
    os.makedirs(workingDirectory)
    #os.chdir(workingDirectory)

    filename = os.path.join(
        workingDirectory,
        "%s.%s" % ("catalog", "tex"),
    )

    with open(filename, "w") as fp:
        fp.write(texContent)

    p = subprocess.Popen(
        """
        cd %(wdir)s
        echo /usr/bin/pdflatex -interaction=nonstopmode -file-line-error -output-format pdf %(fn)s
        cd %(wdir)s
        echo "first run:"
        /usr/bin/pdflatex -interaction=nonstopmode -file-line-error -output-format pdf %(fn)s
        echo "second run:"
        /usr/bin/pdflatex -interaction=nonstopmode -file-line-error -output-format pdf %(fn)s
        """ % {
            "wdir": workingDirectory,
            "fn": filename,
        },
        shell=True, stdout=subprocess.PIPE)

    fd_out = p.stdout.fileno()

    poll_object = select.poll()
    poll_object.register(fd_out, select.POLLIN)

    stdoutString, stderrString = b"", b""

    while p.poll() is None:
        for fd, mask in poll_object.poll(100):
            if mask & select.POLLIN:
                if fd == fd_out:
                    stdoutString += os.read(fd, 65535)

    pdfPath = os.path.join(workingDirectory, "catalog.pdf")
    pdfTargetFn = "catalog-%s.pdf" % catalog.id
    pdfTarget = os.path.join(settings.MEDIA_ROOT, "pdf/catalog", pdfTargetFn)

    debugtxt = ""

    # copy pdf output to /media/pdf/catalog
    try:
        os.remove(pdfTarget)
    except:
        pass
    try:
        shutil.move(pdfPath, pdfTarget)
    except:
        debugtxt += "ERROR: %s\n" % (_("Could not move %(pdf)s to %(targetpdf)s") % {
                                        "pdf": pdfPath,
                                        "targetpdf": pdfTarget })
    # remove temp traces..
    os.chdir(settings.BASE_DIR)
    try:
        shutil.rmtree(workingDirectory)
    except:
        pass

    if stderrString:
        debugtxt += "STDERR: %s\n" % stderrString
    debugtxt += "STDOUT: %s\n" % stdoutString

    catalog.debug_output = debugtxt
    catalog.save()


@write_permission_required
def generate_request(request, catalogId):

    try:
        catalog = SeedCatalog.objects.get(id=catalogId)
    except SeedCatalog.DoesNotExist:
        return HttpResponse(_("Unknown seed catalog %s") % str(catalogId))

    generate_catalog(request, catalog)

    return HttpResponseRedirect(reverse("admin:seedcatalog_seedcatalog_changelist"))


@login_required
def debug_view(request, catalogId):
    try:
        catalog = SeedCatalog.objects.get(id=catalogId)
    except SeedCatalog.DoesNotExist:
        return HttpResponse(_("Unknown seed catalog %s") % str(catalogId))

    ctx = minimal_admin_context(request, SeedCatalog, _("LateX debug output"))
    if catalog.debug_output:
        ctx["page_content"] = "<pre>%s</pre>" % escape(
            catalog.debug_output.replace("\\n", "\n")
        )
    return render(request, ctx["admin_base_tmpl"], ctx)


@write_permission_required
def duplicate_catalog_request(request, catalogId):
    try:
        catalog = SeedCatalog.objects.get(id=catalogId)
    except:
        return HttpResponse(_("Unknown seed catalog %s") % str(catalogId))

    new_catalog = catalog.create_duplicate()

    return HttpResponseRedirect(
        reverse("admin:seedcatalog_seedcatalog_change", args=(new_catalog.id,))
    )


@write_permission_required
def finalize_catalog_request(request, catalogId):
    try:
        catalog = SeedCatalog.objects.get(id=catalogId)
    except SeedCatalog.DoesNotExist:
        return HttpResponse(_("Unknown seed catalog %s") % str(catalogId))

    if "seedcatalog.can_finalize_catalog" not in request.user.get_all_permissions():
        ctx = minimal_admin_context(request, SeedCatalog)
        ctx["error"] = _("Sorry, you do not have the permission to finalize the catalog.")
        ctx["page_content"] = '<a href="%s" class="button">%s</a>' % (
            reverse("admin:seedcatalog_seedcatalog_change", args=(catalog.id,)),
            _("Return to catalog")
        )
        return render(request, ctx["admin_base_tmpl"], ctx)

    catalog.is_finalized = not catalog.is_finalized
    catalog.save()

    return HttpResponseRedirect(
        reverse("admin:seedcatalog_seedcatalog_change", args=(catalog.id,))
    )
