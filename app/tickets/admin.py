import json
import datetime

from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape
from django.core.serializers.json import DjangoJSONEncoder

from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from tools.permissions import get_nomenclature_user
from .models import *


class BasicTicketAdmin(ConfigurableTable):
    form = BasicTicketForm
    fields = ('title', 'description', 'due_date', 'directed_to',)
    list_display = (
        'title', 'current_state_decorator',
        'creation_date', 'due_date', 'created_by', 'directed_to',
        'next_step_decorator',)
    list_filter = (
        ('created_by__username', ForeignKeyFilter),
        ('directed_to__username', ForeignKeyFilter),
    )
    ordering = ('-due_date', '-creation_date', )

    def save_model(self, request, obj, form, change):
        obj = form.save(commit=False)
        if not hasattr(obj, 'created_by'):
            obj.created_by = request.user
        obj.save()

    def get_queryset(self, request):
        qset = BasicTicket.objects.filter(ticket_type="basic")
        return qset

    def get_changeform_initial_data(self, request):
        dic = super(BasicTicketAdmin, self).get_changeform_initial_data(request)
        # default is to self
        dic["directed_to"] = request.user
        dic["due_date"] = datetime.date.today()
        return dic

    class Media:
        css = { "all": ("tickets/tickets.css",) }


class Etikett_IndividualForm(AutoCompleteForm(Etikett_Individual)):
    exclude_autocomplete = ("etikett_type", )

    def __init__(self, *args, **kwargs):
        super(Etikett_IndividualForm, self).__init__(*args, **kwargs)
        from labels import get_label_choices
        choices = [(None, "----")] + list(get_label_choices("individual"))
        self.fields['etikett_type'].widget = forms.Select(choices=choices)


class Etikett_IndividualInline(admin.TabularInline):
    #raw_id_fields = ("individual",)
    extra = 10

    form = Etikett_IndividualForm
    model = Etikett_Individual


class LaserGravurTicketAdmin(BasicTicketAdmin):
    form = LaserGravurTicketForm
    fields = ('title', 'description', 'due_date', 'directed_to')
    inlines = [Etikett_IndividualInline]
    save_on_top = True
    change_form_template = "tickets/change_form.html"

    def save_model(self, request, obj, form, change):
        obj = form.save(commit=False)
        if not hasattr(obj, 'created_by'):
            obj.created_by = request.user
        obj.save()

    def get_queryset(self, request):
        qset = LaserGravurTicket.objects.all()#filter(ticket_type="laser")
        return qset

    def get_changeform_initial_data(self, request):
        dic = super(LaserGravurTicketAdmin, self).get_changeform_initial_data(request)
        dic["directed_to"] = get_nomenclature_user() or request.user
        return dic

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = dict()
        extra_context.update({
            "bg_translations": escape(json.dumps({
                "change_many": _("change many"),
                "change_all": _("change all"),
                "change_unattributes": _("change unattributes"),
                "cancel": _("cancel"),
            }, cls=DjangoJSONEncoder)),
        })
        return super().change_view(request, object_id, form_url, extra_context)

    class Media:
        js = ("/tickets/label-tickets-inline.js", )


class MyTicketAdmin(BasicTicketAdmin):

    def get_queryset(self, request):
        from tools.global_request import get_current_user
        return BasicTicket.objects.filter(directed_to=get_current_user())


admin.site.register(BasicTicket, BasicTicketAdmin)
admin.site.register(LaserGravurTicket, LaserGravurTicketAdmin)
admin.site.register(MyTicket, MyTicketAdmin)
