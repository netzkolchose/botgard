from django.shortcuts import render
from django.http import JsonResponse
from django.apps import apps
from django.core.exceptions import FieldError, ValidationError
from django.db import OperationalError, ProgrammingError
from django.db.models import Func

from tools.permissions import login_required


@login_required
def model_fieldvalues_json(request):
    """Return JsonResponse with list of values of model fields based on 'id' and 'term' GET variables.
    'id' must be: appname-modelname-fieldname
    """
    max_unique_items = 10
    max_items = 1000  # num items to read from db in case of duplicates within the first `max_unique_items`

    def _order_qset(qset, order_field):
        """On PostgreSQL use "C" collation instead of default unicode collation for ordering"""
        try:
            orderer = Func(order_field, template='(%(expressions)s) COLLATE "C"')
            ordset = qset.order_by(orderer)
            # force eval
            dummy = ordset[0]
            return ordset
        except (OperationalError, ProgrammingError):
            return qset.order_by(order_field)

    def _filter(Model, filters, order_field):
        try:
            try:
                entries = Model.objects.filter(**filters[0]).distinct()
            except ValidationError:
                return None
            for i in filters[1:]:
                entries &= Model.objects.filter(**i).distinct()
            if not entries.exists():
                return []
            entries = _order_qset(entries, order_field)
            # force eval
            dummy = entries[0]
            return entries
        except FieldError:
            return None

    def _get_filters(fieldname, terms, filter_mode):
        """construct list of db queries"""
        filters = []
        if filter_mode == "startswith":
            sqlish = "istartswith"
        elif filter_mode == "contains":
            sqlish = "icontains"
        else:#if filter_mode == "exact":
            return [{"%s__exact" % fieldname: terms}]
        for t in terms.split():
            filters.append({"%s__%s" % (fieldname, sqlish): t.strip()})
            sqlish = "icontains"
        return filters

    def _reduce(Model, fieldname):
        """Returns Model, fieldname tuple
        This will change the model if fieldname is a foreign key query
        Example: Individual, 'species__family__genus__icontains' 
        will turn into
        Family, genus__icontains
        """
        if not "__" in fieldname:
            return Model, fieldname
        names = fieldname.split("__")
        for field in Model._meta.fields:
            if field.name == names[0]:
                if hasattr(field, "related_model"):
                    FModel = field.related_model
                    return _reduce(FModel, "__".join(names[1:]))
        return Model, fieldname

    def _get_entries(Model, fieldname, terms, filter_mode):
        Model, fieldname = _reduce(Model, fieldname)
        # find entries that start with first term
        filters = _get_filters(fieldname, terms, filter_mode)
        entries = _filter(Model, filters, fieldname)
        if entries is None:
            if filter_mode == "startswith":
                return None
            # find entries that contain terms
            filters = _get_filters(fieldname, terms, False)
            entries = _filter(Model, filters, fieldname)
            if entries is None:
                return None
        #print(Model, fieldname, filters)

        short = [("%s" % getattr(x, fieldname)).strip() for x in entries[:max_unique_items]]

        # when duplicates, filter unique values from larger set
        if len(set(short)) < len(short):
            short = []
            shortset = set()
            for e in [("%s" % getattr(x, fieldname)).strip() for x in entries[:max_items]]:
                if e not in shortset:
                    short.append(e)
                    shortset.add(e)
                    if len(short) >= max_unique_items:
                        break
        return short

    def _get_list(request):
        app, modelname, fieldname = request.GET.get("id").split("-")
        terms = request.GET.get("term")
        Model = apps.get_model(app, modelname)

        if not terms:
            return JsonResponse({"state": "empty"})

        ret_state = None

        entries = _get_entries(Model, fieldname, terms, "exact")
        if entries and len(entries) == 1:
            ret_state = "one"

        if not entries:
            entries = _get_entries(Model, fieldname, terms, "startswith")

        if not entries or len(entries) < max_unique_items:
            entries2 = _get_entries(Model, fieldname, terms, "contains")
            if entries2 is not None:
                eset = set(entries)
                for e in entries2:
                    if e not in eset and len(entries) < max_unique_items:
                        entries.append(e)

        if ret_state is None:
            ret_state = "many" if len(entries) > 1 else "one" if len(entries) == 1 else "none"

        ret = {
            "state": ret_state,
            "items": entries,
        }
        if len(entries) == 1:
            filters = {fieldname+"__icontains": terms}
            try:
                ret["fk"] = Model.objects.filter(**filters)[0].id
            except IndexError:
                ret = {"state": "none"}
        print(ret)
        return JsonResponse(ret)

    return _get_list(request)
    try:
        return _get_list(request)
    except BaseException as e:
        return JsonResponse({
            "error": f"{e.__class__.__name__}: {e}"
        }, status=500)


@login_required
def choice_fieldvalues_json(request):
    max_unique_items = 10

    app, modelname, fieldname = request.GET.get("id").split("-")
    term = request.GET.get("term", "").lower()
    Model = apps.get_model(app, modelname)

    if not term:
        return JsonResponse({"state": "empty"})

    field = Model._meta.get_field(fieldname)
    choices = [(c[1].lower(), c[1]) for c in field.choices]
    items = []

    if term:
        for c in choices:
            if c[0].startswith(term):
                items.append(c[1])
                if len(items) >= max_unique_items:
                    break
        items = sorted(items)

        if len(items) < max_unique_items:
            moreitems = []
            for c in choices:
                if term in c[0] and c[1] not in items:
                    moreitems.append(c[1])
                    if len(items) + len(moreitems) >= max_unique_items:
                        break
            items += sorted(moreitems)

    ret = {
        "state": "many" if len(items) > 1 else "one" if len(items) == 1 else "none",
        "items": items,
    }

    return JsonResponse(ret)