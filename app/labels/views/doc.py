import inspect
from typing import List, Type

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.shortcuts import render
from django.db import models

from tools.admin_extensions import minimal_admin_context

from labels.models import (
    LabelDefinition, LABEL_FORMAT_TO_FILE_FORMAT, LABEL_TYPE_CHOICES
)
from individuals.models import Individual
from botman.models import BotanicGarden
from tools.permissions import login_required



@login_required
def label_template_doc(request):
    """
    View to render documentation for label template variables
    """
    context = minimal_admin_context(
        request, LabelDefinition, _("Label template documentation"),
        extra={
            "label_type_choices": [
                (id, name, id == request.GET.get("label_type"))
                for id, name in LABEL_TYPE_CHOICES
            ],
        }
    )
    try:
        context.update(get_template_doc_context(request))
    except IOError as e:
        context["error"] = f"{type(e).__name__}: {e}"

    return render(request, "labels/template_doc.html", context)


def get_template_doc_context(request) -> dict:
    label_type = request.GET.get("label_type", "garden")
    instance_id = request.GET.get("instance_id", None)

    if label_type == "garden":
        model = BotanicGarden
        id_field_name = BotanicGarden._id_field
    elif label_type == "individual":
        model = Individual
        id_field_name = Individual._id_field
    else:
        raise ValueError(f"Invalid label type '{label_type}'")

    try:
        instance = model.objects.get(**{id_field_name: instance_id})
    except model.DoesNotExist:
        instance = None
        instance_id = ""

    return {
        "docs": get_template_doc_from_model(model, instance),
        "has_example": instance is not None,
        "instance_id": instance_id,
        "instance_field": {
            "json_url": reverse("ajax:model_json"),
            "id": "%s-%s-%s" % (model._meta.app_label, model._meta.model_name, id_field_name)
        }
    }


def get_template_doc_from_model(
        model: Type[models.Model],
        instance: models.Model = None,
        models_parsed: set = None
) -> List[dict]:
    models_parsed = models_parsed or set()
    models_parsed.add(model)
    docs = []
    for field in model._meta.fields:
        if isinstance(field, models.ForeignKey):
            related_model = field.related_model
            if related_model not in models_parsed:
                sub_docs = get_template_doc_from_model(related_model, None, models_parsed)
                for d in sub_docs:
                    d["name"] = f"{related_model._meta.model_name}.{d['name']}"
                    docs.append(d)
        else:
            desc = {
                "name": field.name,
                "verbose_name": field.verbose_name,
            }
            if instance:
                desc["example"] = getattr(instance, field.name)
            docs.append(desc)

    for attr_name in dir(model):
        if attr_name.endswith("_decorator"):
            continue
        if callable(getattr(model, attr_name)):
            func = getattr(model, attr_name)
            if hasattr(func, "short_description") or hasattr(func, "template_doc"):
                #args, varargs, varkw = inspect.getargs(func)
                #if args == 1:
                desc = {
                    "name": attr_name,
                    "verbose_name": getattr(func, "template_doc", None) or getattr(func, "short_description"),
                }
                if instance:
                    desc["example"] = getattr(instance, attr_name)()
                docs.append(desc)

    return docs



