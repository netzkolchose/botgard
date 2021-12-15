import types

from django.db import models
from django.contrib import admin
from django.conf.urls import url
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.http import QueryDict
from django.utils.text import capfirst
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.urls import reverse
from operator import itemgetter
import django.core.exceptions
from django.contrib.admin.utils import label_for_field

from .forms import TableSettingsForm
from .models import TableSettings
from tools.csv_response import csv_response


class Configurable(object):
    """
    Base class for registering configurable methods.
    The class to function mapping is done upon instantiation of a derived class.
    Therefore it is needed to have at least one instance of a type before a
    type specific lookup is made.
    """
    _registered_funcs = set()
    _cls2func = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._cls2func:
            attrs = cls.__dict__.values()
            cls._cls2func.setdefault(cls, set())
            for func in cls._registered_funcs:
                if func in attrs:
                    cls._cls2func[cls].add(func)
        return object.__new__(cls)

    @classmethod
    def get_configurable_funcs(cls, classtype):
        return cls._cls2func.get(classtype, set())

    @classmethod
    def register(cls, f):
        cls._registered_funcs.add(f)
        return f

    def apply_blacklist(self, names):
        """Applies 'blacklist' from ModelAdmin class"""
        blacklist = self.blacklist if hasattr(self, "blacklist") else ("id",)
        try:
            ret = []
            for n in names:
                name = n[1] if isinstance(n, tuple) and len(n) == 4 else n
                if name not in blacklist:
                    ret.append(n)
            if not ret:
                raise RuntimeError("apply_blacklist in Configurable returned EMPTY list")
            return ret
        except AttributeError:
            pass
        return names


configurable = Configurable.register

class ForeignKeyFilter(admin.AllValuesFieldListFilter):
    """Class to enable filter-queries of the form ?foreignkeyfield__field__icontains.
    It's not meant for the filter-box but to allow a certain foreign field to be filtered."""
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(ForeignKeyFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]

    def lookups(self):
        return (('', ''), )

    def choices(self, changelist):
        yield {}

    def has_output(self):
        return False


class ConfigurableTable(admin.ModelAdmin, Configurable):
    change_list_template = 'config_tables/change_list.html'
    configuretable_template = 'config_tables/configuretable.html'

    def _get_actual_tablesettings_object(self, request):
        user = request.user
        modelstring = '%s.%s' % (self.model._meta.app_label, self.model._meta.model_name)
        try:
            tablesettings = TableSettings.objects.get(user=user, model=modelstring)
        except TableSettings.DoesNotExist:
            tablesettings = TableSettings(user=user, model=modelstring, settings=self.apply_blacklist(self.list_display))
        return tablesettings

    def get_list_display(self, request):
        names = self._get_actual_tablesettings_object(request).settings
        # fix old configurations that require fields that are gone
        names = [n for n in names if hasattr(self.model, n)]
        return names

    def get_list_display_csv(self, request):
        l = list(self.get_list_display(request))
        ret = []
        for x in l:
            if hasattr(self.model, x):
                X = getattr(self.model, x)
                if hasattr(X, "exclude_csv") and X.exclude_csv:
                    continue
            ret.append(x)
        return tuple(ret)

    def get_urls(self):
        urls = super(ConfigurableTable, self).get_urls()
        admin_site = self.admin_site
        opts = self.model._meta
        info = opts.app_label, opts.model_name
        configtable_urls = [
            url(r"^configuretable/$", admin_site.admin_view(self.configuretable_view), name='%s_%s_configuretable' % info),
            url(r"^configuretable/tree/$", admin_site.admin_view(self.tree_view), name='%s_%s_configuretable_tree' % info),
            url(r"^csv/$",   admin_site.admin_view(self.csv_view), name='%s_%s_csv' % info),
            url(r"^print/$", admin_site.admin_view(self.print_view), name='%s_%s_print' % info),
        ]
        return configtable_urls + urls

    def _get_verbose_name(self, attr_name):
        def _verbose_it(el):
            if isinstance(el, types.MethodType):
                return getattr(el, 'short_description', getattr(el, '__name__', 'error'))
            return el.verbose_name

        obj = self
        s = ''
        if attr_name.startswith('__'):
            return attr_name
        for el in attr_name.split('__'):
            #print( 'run', el, s )
            try:
                tmp = getattr(obj, el)
            except AttributeError:
                try:
                    tmp = getattr(obj.model, el)
                except AttributeError:
                    tmp = obj.model._meta.get_field(el)
            s += _verbose_it(tmp)
            #s += label_for_field(tmp, )
            s += ' --> '
            obj = tmp
        return s.strip(' --> ')

    def configuretable_view(self, request, extra_context=None):
        if not self.has_change_permission(request) or not self.has_add_permission(request):
            raise PermissionDenied

        # POST (save)
        if request.method == 'POST':
            return_url = 'admin:%s_%s_changelist' % (self.model._meta.app_label,
                                                     self.model._meta.model_name)
            tablesettings = self._get_actual_tablesettings_object(request)
            if "_delete" in request.POST:
                try:
                    tablesettings.delete()
                except AssertionError:  # in case, there is no settings yet
                    pass
                return redirect(return_url)
            POST = request.POST.copy()
            POST['user'] = tablesettings.user.pk
            POST['model'] = tablesettings.model
            form = TableSettingsForm(data=POST, instance=tablesettings, extra_opts=self.model._meta)
            if form.is_valid():
                form.save().save()
                return redirect(return_url)
            else:

                # translate / prettyprint selected elements
                selected = []
                for elem in tablesettings.settings:
                    selected.append((elem, label_for_field(elem, self.model, self)))

                form.reset_selection(selected)
                model = self.model
                opts = model._meta
                try:
                    each_context = self.admin_site.each_context(request)
                except TypeError:  # Django <= 1.7 pragma: no cover
                    each_context = self.admin_site.each_context()

                context = dict(
                    each_context,
                    opts=opts,
                    app_label=opts.app_label,
                    module_name=capfirst(opts.verbose_name),
                    title=_("Configure table %(name)s") % {"name": force_text(opts.verbose_name_plural)},
                    form=form,
                    media=form.media
                )
                context.update(extra_context or {})
                return render(request, self.configuretable_template, context)

        # GET
        model = self.model
        opts = model._meta
        try:
            each_context = self.admin_site.each_context(request)
        except TypeError:  # Django <= 1.7 pragma: no cover
            each_context = self.admin_site.each_context()

        # get actual table settings for this model
        tablesettings = self._get_actual_tablesettings_object(request)

        # translate / prettyprint selected elements
        selected = []
        for elem in tablesettings.settings:
            # fix old configurations that require fields that are gone
            if hasattr(self.model, elem):
                selected.append((elem, label_for_field(elem, self.model, self)))

        form = TableSettingsForm(instance=tablesettings, selected=selected, extra_opts=opts)

        context = dict(
            each_context,
            opts=opts,
            app_label=opts.app_label,
            module_name=capfirst(opts.verbose_name),
            title=_("Configure table %(name)s") % {"name": force_text(opts.verbose_name_plural)},
            form=form,
            media=form.media,
        )
        context.update(extra_context or {})
        return render(request, self.configuretable_template, context)

    def get_modelattributes_treepart(self, model, path='', settings=None):
        """
        Get model attributes as a treepart.
        """
        settings = settings or []
        return [(attr.verbose_name,
                 path + '__' + attr.name if path else attr.name,
                 None if not isinstance(attr, models.ForeignKey) else attr.related_model,
                 True if attr.name in settings else False)
                for attr in model._meta.fields]

    def get_decorated_functions(self, model, path='', settings=None):
        """
        Get all decorated function for a treepart.
        Note: This can only get decorator function defined at model level for sub treeparts
        since we have no knowledge about any model associated ModelAdmin class definition.
        """
        # create a dummy model instance to trigger correct function assiciation
        model()
        settings = settings or []

        # fetch decorator functions from model
        funcs = self.get_configurable_funcs(model)

        # if we are at base admin level fetch also ModelAdmin decorator function
        if model == self.model:
            funcs |= self.get_configurable_funcs(self.__class__)

        return [
            (
                str(getattr(f, 'short_description', getattr(f, '__name__', 'error'))),
                f.__name__,
                None,
                True if f.__name__ in settings else False
            )
            for f in funcs
        ]

    def tree_view(self, request, extra_context=None):
        """
        Render a treepart of configurable attributes.
        """
        if not self.has_change_permission(request) or not self.has_add_permission(request):
            raise PermissionDenied

        path = request.GET.get('ttt')
        path = path or ''
        model = self.model

        # commented since not used atm
        #if path:
        #    attr = self.model
        #    for el in path.split('__'):
        #        try:
        #            attr = attr._meta.get_field(el).rel.to
        #        except AttributeError:
        #            break
        #    model = attr

        # generate attributes list from
        # 1) database fields (or POST if in save cycle)
        # 2) decorator functions
        # 3) back relations
        settings = self.get_list_display(request)
        attributes = self.get_modelattributes_treepart(model, path, settings)
        attributes += self.get_decorated_functions(model, path, settings)

        attributes = self.apply_blacklist(attributes)

        # alphabetic sorting
        attributes.sort(key=itemgetter(0))

        ctx = {'attributes': attributes}
        return render(request, 'config_tables/treepart.html', ctx)

    def header_search_widget(self, request, field_name: str, dic: dict):
        """
        Returns html-markup to be inserted into the table of django.admin's change_list_result.html
        Uses request to pre-populate the input.
        Supports model fields, foreign fields and decorators
        :param request: The web request for the change_list view, containing all current GET queries
        :param field_name: The name of the model field or decorator
        :param dic: temporary dict used to identify multiple widgets to the same model-field
                    which causes trouble.
        :return: a html string, or None if field is not filterable
        """

        accepted_fields = (models.CharField, models.TextField,
                           models.ForeignKey,
                           models.IntegerField, models.BigIntegerField, models.DecimalField,
                           models.PositiveIntegerField, models.PositiveSmallIntegerField,
                           models.SmallIntegerField, models.FloatField,
                           models.DateField, models.DateTimeField, models.TimeField,
                           models.EmailField, models.IPAddressField, models.GenericIPAddressField,
                           models.URLField, models.UUIDField, models.BooleanField, models.NullBooleanField,
                           models.FileField, models.FilePathField,
                           )

        ac_model = "%s.%s" % (self.model._meta.app_label, self.model._meta.model_name)
        ac_field_name = field_name

        # see if a model field
        try:
            field = self.model._meta.get_field(field_name)
            if not isinstance(field, accepted_fields):
                return None
            used_field_name = field_name

        # see if decorator function
        except django.core.exceptions.FieldDoesNotExist:
            func = None
            import inspect
            mems = inspect.getmembers(self.model)
            for mem in mems:
                if field_name == mem[0]:
                    func = mem[1]
                    break
            if not func:
                return None
            # get actual field-name from decorator
            used_field_name = func.__dict__.get("searchable_field", None)
            if not used_field_name:
                used_field_name = func.__dict__.get("admin_order_field", None)
            if not used_field_name:
                return None
            ac_field_name = used_field_name

            # try to get field from fieldname
            try:
                field = self.model._meta.get_field(used_field_name)
            except django.core.exceptions.FieldDoesNotExist:
                field = None

            # try foreign field
            if not field:
                tup = used_field_name.split("__")
                # print("tup", tup)
                if len(tup) == 2:  #TODO-3: tup can have len 3 wat now? look below
                    model_name, foreign_field_name = tup

                    try:
                        field = self.model._meta.get_field(model_name)
                    except django.core.exceptions.FieldDoesNotExist:
                        field = None
                    if field and hasattr(field, "related_model") and field.related_model:
                        try:
                            # TODO-3: rel is deprecated, field.related_model._meta instead, look below to next todo
                            meta = field.related_model._meta
                            field = meta.get_field(foreign_field_name)
                        except django.core.exceptions.FieldDoesNotExist:
                            # that would only be a link to foreign decorator!?
                            field = None

            if field and not isinstance(field, accepted_fields):
                return None

        is_choices = isinstance(field, models.CharField) and field.choices
        is_boolean = isinstance(field, models.BooleanField)
        is_date = isinstance(field, (models.DateField, models.DateTimeField))

        # sql-ish query string for this model field
        query_string = "icontains" if not (is_choices or is_boolean) else "exact"

        # add foreign key redirection to query string
        if isinstance(field, models.ForeignKey):
            # the name of the field in related model
            foreign_field_name = None
            for i in self.list_filter:
                # try to get name from installed ForeignKeyFilter
                if len(i) == 2:
                    tup = i[0].split("__")

                    # TODO-3: if not len(tup) == 2: breaks views in case species__family__family...
                    if not len(tup) >= 2:
                        raise SyntaxError("%s.list_filter contains illegal syntax '%s' for ForeignKeyFilter, "
                                          "missing __ redirection" % (type(self), i[0]))
                    if tup[0] == field_name:
                        foreign_field_name = tup[1]
                        break
            if not foreign_field_name:
                return None
            query_string = "%s__%s" % (foreign_field_name, query_string)
            #ac_field_name = foreign_field_name
            # TODO-3: Is that ok?
            field = field.related_model._meta.get_field(foreign_field_name)

        # markup replacement-strings
        context = {
            "query": "%s__%s" % (used_field_name, query_string),
            "alt": _("Remove filter for %s") % field_name,
        }

        # prepopulate value of input field
        input_value = ""
        for j in request.GET.keys():
            if context.get("query") == j:
                input_value = request.GET.get(j, "")
                break

        context.update({
            "value": input_value,
            "inactive": "" if input_value else "inactive",
        })

        # enrichment for jquery autocomplete
        if field:
            ac_model = "%s.%s" % (field.model._meta.app_label, field.model._meta.model_name)
            ac_field_name = field.name
        context.update({
            "data-ac-json-url": reverse("ajax:model_json"),
            "data-ac-id": ("%s.%s" % (ac_model, ac_field_name)).replace(".", "-")
        })

        # avoid if there already is a widget with this query
        if context.get("query") in dic:
            return None
        dic.setdefault(context.get("query"), True)

        if is_choices:
            return self._get_search_widget_choice_box(context, field.choices)
        elif is_boolean:
            return self._get_search_widget_boolean(context)
        else:
            return self._get_search_widget_text(context)

    def _get_search_widget_boolean(self, context):
        return self._get_search_widget_choice_box(context,
                                                  (('1', _('yes')),
                                                   ('0', _('no'))))

    def _get_search_widget_text(self, context):
        ctx = context.copy()
        ctx.update({"id": 'id="%s"' % context["id"] if context.get("id", None) else ""})
        datatags = []
        for key in context:
            if key.startswith("data"):
                datatags.append('%s="%s"' % (key, context[key]))
        ctx["datatags"] = " ".join(datatags)
        return """
        <div class="filter-form-wrapper">
            <input %(id)s name="%(query)s" class='filter-form-element autocomplete-modelfield' value='%(value)s' %(datatags)s>
            <button class="filter-form-reset %(inactive)s"></button>
        </div>
        """ % ctx

    def _get_search_widget_choice_box(self, context, choices):
        html = ""
        for choice in choices:
            html += '<option value="%s" %s>%s</option>' % (
                choice[0],
                'selected="selected"' if context.get("value", "") == choice[0] else '',
                choice[1],
            )
        context.setdefault("choices", html)
        return """
        <div class="filter-form-wrapper">
            <select name="%(query)s" class="filter-form-element">
                <option value="">-</option>
                %(choices)s
            </select>
        </div>
        """ % context

    def header_search_widgets(self, request):
        """
        Returns a list of html-strings to be inserted into the table of django.admin's change_list_result.html
        :param request: The web request for the change_list view, containing all current GET queries
        :return: list of strings, one per model column
        """
        actions = self.get_actions(request)
        widgets = []

        if "_popup" not in request.GET and actions:
            widgets.append("<!-- empty action check field -->")
        dic = {}

        for field_name in self.get_list_display(request):
            html = self.header_search_widget(request, field_name, dic)
            widgets.append(html if html else "-")
        return widgets

    def _prepare_queries_for_subview(self, qd, ofs=-1):
        """Changes the sort columns in the QueryDict because
        we do not show the first action column.
        :return: new QueryDict"""
        import math
        ret = QueryDict(mutable=True, encoding=qd.encoding)
        for k in qd:
            v = qd[k]
            if k == "o" and qd[k]:
                v = ".".join([str(int(math.copysign(abs(int(x))+ofs, int(x)))) for x in v.split(".")])
            ret.setdefault(k, v)
        ret.setdefault("all", "1")
        return ret

    def changelist_view(self, request, extra_context=None, **kwargs):
        """
        Insert header search field markup into render context,
        also add sort/filter queries for csv export
        """
        # get focused element and remove the query param from the request
        focus_input = request.GET.get("_focus_input")
        if focus_input:
            patched_params = request.GET.copy()
            patched_params.pop("_focus_input")
            request.GET = patched_params

        extra_context = extra_context or {}
        cl = self._get_change_list(request)

        num_items = cl.result_list.count()
        num_items_per_sec = 1000000

        # messure time it takes to render the complete django list
        if num_items > 100:
            from django.contrib.admin.templatetags.admin_list import results
            import time
            starttime = time.time()
            endtime = starttime
            count = 0
            cl.result_list = cl.result_list[:30]
            for htmlrow in results(cl):
                count += 1
                endtime = time.time()
                if endtime - starttime > 0.2:
                    break
            print(count, endtime-starttime)
            num_items_per_sec = int(count / max(0.0001, endtime - starttime))

        extra_context.update({
            'change_list_searchable_headers': self.header_search_widgets(request),
            'queries_serialized': self._prepare_queries_for_subview(request.GET).urlencode(),
            # for popup changelists, we need to preserve special variables that django needs
            'django_hidden_fields': (
                ("_popup", request.GET.get("_popup")),
                ("_to_field", request.GET.get("_to_field")),
                ("_focus_input", focus_input),
            ),
            'num_list_items': num_items,
            'num_list_items_per_sec': num_items_per_sec,
        })
        res = super(ConfigurableTable, self).changelist_view(request, extra_context=extra_context)
        return res

    def _get_change_list(self, request):
        """
        copied from django.contrib.admin.options.ModelAdmin
        used to determine the number of lines in an admin change_list
        """
        from django.contrib.admin.options import IncorrectLookupParameters
        opts = self.model._meta
        app_label = opts.app_label
        if not self.has_change_permission(request, None):
            raise PermissionDenied

        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)
        sortable_by = self.get_sortable_by(request)
        list_select_related = self.get_list_select_related(request)

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(
                request, self.model, list_display,
                list_display_links, list_filter, self.date_hierarchy,
                search_fields, list_select_related, 10000000,
                10000000, self.list_editable, self, sortable_by=sortable_by
            )
            cl.formset = None
            return cl
        except IncorrectLookupParameters:
            return None

    def print_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({"_for_print":True})
        return self.csv_view(request, extra_context)

    def csv_view(self, request, extra_context=None):

        def unescape(x):
            return x.replace("&nbsp;", " ").replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

        # first build a minimal admin.ChangeList instance
        # which will handle sorting and filtering
        from django.contrib.admin.options import IncorrectLookupParameters
        from django.contrib.admin.templatetags.admin_list import result_headers, results
        from django.utils.html import escape
        import bs4 as bs

        if not self.has_change_permission(request, None):
            raise PermissionDenied

        opts = self.model._meta
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)
        list_select_related = self.get_list_select_related(request)
        sortable_by = self.get_sortable_by(request)

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(
                request,
                self.model,
                list_display,
                list_display_links,
                list_filter,
                self.date_hierarchy,
                search_fields,
                list_select_related,
                10000000,   # self.list_per_page,
                10000000,   # self.list_max_show_all,
                False,      # self.list_editable,
                self,
                sortable_by=sortable_by
            )
            cl.formset = None
        except IncorrectLookupParameters:
            # An error would have been checked in the admin page that lead to this csv page.
            # This will probably never happen..
            return HttpResponse(status=404)

        for_print = extra_context and "_for_print" in extra_context

        # determine which columns to include in csv
        # (must be done after ChangeList creation because the sort queries
        #  reference the column number)
        include = []
        csv_columns = self.get_list_display_csv(request)
        for x in list_display:
            include.append(True if x in csv_columns else False)

        # now convert the results back to text-only and skip unused columns
        count = cl.result_list.count()
        headers = [unescape(x["text"]) for i, x in enumerate(result_headers(cl)) if include[i]]
        res = []
        for htmlrow in results(cl):
            row = []
            for i, x in enumerate(htmlrow):
                if include[i]:
                    if not for_print:
                        field = getattr(self.model, list_display[i])
                        if hasattr(field, "as_csv"):
                            x = field.as_csv(x)
                        if x.startswith("<"):
                            if "icon-yes" in x:
                                x = "X"
                            elif "icon-no" in x:
                                x = "-"
                            else:
                                soup = bs.BeautifulSoup(x, "html.parser")
                                x = soup.text
                    row.append(unescape(x))
            res.append(row)

        if for_print:
            headers = [x for i, x in enumerate(result_headers(cl)) if include[i]]
            for h in headers:
                h["text"] = escape(h["text"]).replace(" ", "&nbsp;")
            ctx = {
                "headers": headers,
                "rows": res,
                "title": "%s %s" % (len(res), opts.verbose_name_plural),
                "branding": self.admin_site.site_header,
            }
            ctx.update(self.admin_site.each_context(request))
            ctx.update(extra_context or {})
            return render(request, "config_tables/print_change_list.html", ctx)
        else:
            return csv_response("%s.csv" % opts.verbose_name_plural, headers, res)

    class Media:
        css = {"screen": (
            'config_tables/searchable_admin_list.css',
            'config_tables/jquery-ui.min.css',
            )
        }
        js = (
            'config_tables/jquery-ui.min.js',
            'config_tables/searchable_admin_list.js',
            'ajax/autocomplete.js',
        )


class TableSettinsAdmin(admin.ModelAdmin):
    #form = TableSettingsForm

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


admin.site.register(TableSettings, TableSettinsAdmin)