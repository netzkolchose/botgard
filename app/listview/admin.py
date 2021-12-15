from django.contrib import admin
from django.shortcuts import render
from django.views.generic import ListView
from django.http import JsonResponse
from django.core import serializers
from django.db import models
# from django.apps import apps


class JsonModelView(ListView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'objects': serializers.serialize('json', kwargs['model'].objects.all())})


class TreeMixing(object):
    def get_model_attribute_tree(self, model, path='', settings=None):
        return [(attr.verbose_name,
                 path + '__' + attr.name if path else attr.name,
                 None if not isinstance(attr, models.ForeignKey) else attr.related_model,
                 True if settings.get(attr.name) else False)
                for attr in model._meta.fields]


class ModelTableView(ListView, TreeMixing):
    selection = {'id': True}

    def get(self, request, *args, **kwargs):
        path = kwargs.get('ttt')
        path = path or ''
        model = self.model
        if path:
            attr = self.model
            for el in path.split('__'):
                try:
                    attr = attr._meta.get_field(el).related_model
                except AttributeError:
                    break
            model = attr
        return render(request, 'list_view.html',
                                  {'attributes': self.get_model_attribute_tree(model, path, self.selection)})


class CustomListAdmin(admin.ModelAdmin):
    change_list_template = 'change_list.html'

    def changelist_view(self, request, extra_context=''):
        res = super(CustomListAdmin, self).changelist_view(request, extra_context)
        if request.is_ajax():
            return ModelTableView.as_view(model=self.model)(
                request,
                queryset=self.get_queryset(request),
                ttt=request.GET.get('ttt')
            )
        return res

