from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from config_tables.admin import Configurable, configurable
from ajax.autocomplete import AutoCompleteForm


State_Choices = (
    ('N', _('new')),
    ('C', _('audited')),
    ('A', _('in progress')),
    ('F', _('finished')),
    ('D', _('discarded')),
)


def get_name_for_state(s):
    for i in State_Choices:
        if s == i[0]:
            return i[1]
    return _("unknown")


# to register a specialized ticket type add it here
ticket_types = (
    'lasergravurticket',
)


class BasicTicket(models.Model, Configurable):

    class Meta:
        verbose_name = _('basic ticket')
        verbose_name_plural = _('basic tickets')

    _id_field = "title"

    # 	Basic Ticket infos
    title = models.CharField(max_length=50, verbose_name=_("titel"), db_index=True, blank=False)
    description = models.TextField(verbose_name=_("description"), blank=True)
    creation_date = models.DateTimeField(verbose_name=_("ticket created"), auto_now_add=True)
    due_date = models.DateField(verbose_name=_("due to"), blank=False)
    ticket_type = models.CharField(verbose_name=_("type"), default="basic", max_length=10,
                                   editable=False,
                                   choices=(("basic", _("basic")), ("laser", _("laser gravure"))))

    #	The Ticket States
    current_state = models.CharField(max_length=2, choices=State_Choices, verbose_name=_("current state"), blank=False,
                                     default='N')
    # ^ initial state is checked. if a ticket requires additional user checking
    # the implementation of the certain tickets needs to override this in its save method!

    # 	Users responsible for the Ticket
    created_by = models.ForeignKey(User, related_name='%(class)s_created_by_related', verbose_name=_('creator'),
                                   on_delete=models.CASCADE)
    directed_to = models.ForeignKey(User, related_name='%(class)s_directed_to_related', verbose_name=_('receiver'),
                                    on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.title

    def get_verbose_name(self):
        """The user-friendly name of this class"""
        return _("ticket")

    def get_full_ticket(self):
        """This method returns the ticket object in case we deal with a ticket type inherited from BasicTicket"""
        return_value = self
        for ticket_type in ticket_types:
            try:
                return_value = getattr(self, ticket_type)
                #print(self.lasergravurticket)
                #print(type(self), type(return_value))
                break
            except:
                pass
        return return_value

    def abandon_ticket(self):
        self.current_state = 'D'
        self.save()

    def reopen_ticket(self):
        self.current_state = 'N'
        self.save()

    def change_state(self):
        prev = self.current_state
        if self.current_state == 'N':
            self.current_state = 'C'
        elif self.current_state == 'C':
            self.current_state = 'A'
        elif self.current_state == 'A':
            self.current_state = 'F'
        elif self.current_state == 'F':
            self.reopen_ticket()
        #print("CHANGE STATE %s -> %s" % (prev, self.current_state))
        self.save()

    def type_string(self):
        return str(self.get_full_ticket().__class__).split('.')[-1][0:-2]

    #@configurable
    #def type_decorator(self):
    #    return self.get_full_ticket().get_verbose_name()
    #type_decorator.short_description = _("type")

    def current_state_name(self):
        return get_name_for_state(self.current_state)

    @configurable
    def current_state_decorator(self):
        """Return state in <div> block with appropriate css class"""
        s = self.current_state
        return mark_safe('<div class="ticket_state_%s">%s</div>' % (s, get_name_for_state(s)))
    current_state_decorator.short_description = _("state")
    current_state_decorator.searchable_field = "current_state"

    @configurable
    def next_step_decorator(self):
        if self.current_state == 'N':
            link_text = _("check")
        elif self.current_state == 'C':
            link_text = _("check")
        elif self.current_state == 'A':
            link_text = _("close")
        elif self.current_state == 'F':
            link_text = _("reopen")
        else: # self.current_state == 'D':
            link_text = _("reopen<br/>(ticket was discarded)")
        url = reverse("tickets:state", args=(self.pk,))
        return mark_safe('<a href="%s" class="ticket_state_%s">%s</a>' % (url, self.current_state, link_text))
    next_step_decorator.short_description = _("next step")


class Etikett_Individual(models.Model, Configurable):
    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")

    individual = models.ForeignKey('individuals.Individual', blank=False, verbose_name=_("individal"),
                                   on_delete=models.CASCADE)
    etikett_type = models.CharField(max_length=30, blank=False, #choices=(("dummy", "dummy"),),#GRAVURE_TICKET_CHOICES,
                                    verbose_name=_("label type"), db_index=True)
    LaserGravur = models.ForeignKey('tickets.LaserGravurTicket', on_delete=models.CASCADE)

    is_done = models.BooleanField(verbose_name=_("is done"), default=False, editable=False)

    def __str__(self):
        return "%s(%s)" % (self.individual, self.etikett_type)

    def get_label_type_name(self):
        """Returns the friendly type name of the label"""
        from labels.models import LabelDefinition
        try:
            return LabelDefinition.objects.get(type="individual", id_name=self.etikett_type).display_name
        except LabelDefinition.DoesNotExist:
            return _("unknown label id")

    def get_label_url(self):
        """Returns the generator url for the pdf"""
        from labels.models import LabelDefinition
        try:
            label = LabelDefinition.objects.get(type="individual", id_name=self.etikett_type)
            format = "pdf"
            return "%s?filename=%s&format=%s" % (
                reverse("labels:individual", args=(label.pk, self.individual.pk)),
                "%s-%s.%s" % (self.individual.ipen_generated, self.etikett_type, format),
                format,
            )
        except LabelDefinition.DoesNotExist:
            return "%s?type=individual&id_name=%s" % (
                reverse("admin:labels_labeldefinition_add"),
                self.etikett_type
            )

    def get_set_done_url(self):
        from labels.models import LabelDefinition
        try:
            LabelDefinition.objects.get(type="individual", id_name=self.etikett_type)
            return reverse("tickets:set_label_done", args=(self.pk,))
        except LabelDefinition.DoesNotExist:
            return ""

    def is_done_decorator(self):
        if self.is_done:
            return "✓"
        return """<span class="label-done-indicator" data-label-url="%s"></span>""" % self.get_set_done_url()

    # override save, if the nomenclature of the selected individual is not checked the ticket goes to state N
    def save(self, *args, **kwargs):
        if not self.individual.species.nomenclature_checked:
            self.LaserGravur.current_state = 'N'
            self.LaserGravur.save()
        super(Etikett_Individual, self).save(*args, **kwargs)


class LaserGravurTicket(BasicTicket):
    class Meta:
        verbose_name = _('laser gravure ticket')
        verbose_name_plural = _('laser gravure tickets')

    def is_nomenclature_checked(self):
        for ettiket in self.etikett_individual_set.all():
            if not ettiket.individual.species.nomenclature_checked:
                return False
        return True

    def reopen_ticket(self):
        self.current_state = 'C' if self.is_nomenclature_checked() else 'N'
        self.save()
        for e in Etikett_Individual.objects.filter(LaserGravur=self):
            e.is_done = False
            e.save()

    def change_state(self):
        if not self.is_nomenclature_checked():
            self.reopen_ticket()
            return
        super(LaserGravurTicket, self).change_state()

    def get_verbose_name(self):
        return _("laser gravure ticket")

    def save(self, *args, **kwargs):
        self.ticket_type = "laser"
        super(LaserGravurTicket, self).save(*args, **kwargs)



class BasicTicketForm(AutoCompleteForm(BasicTicket)):
    exclude_autocomplete = {"directed_to"}


class LaserGravurTicketForm(AutoCompleteForm(LaserGravurTicket)):
    exclude_autocomplete = {"directed_to"}


class MyTicket(BasicTicket):
    class Meta:
        proxy = True
        verbose_name = _('ticket for me')
        verbose_name_plural = _('tickets for me')


class MyTicketForm(AutoCompleteForm(MyTicket)):
    exclude_autocomplete = {"directed_to"}
