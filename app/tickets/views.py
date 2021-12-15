from .models import *

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from tools.permissions import *
from tools.admin_extensions import minimal_admin_context


@login_required
def my_tickets_list(request):
    # tickets_a = BasicTicket.objects.filter(directed_to = request.user).exclude(
    #   current_state = 'F').exclude(current_state = 'D').order_by('-due_date')

    tickets_for_me = BasicTicket.objects.all().exclude(current_state='F').exclude(current_state='D').order_by(
        '-due_date')

    my_tickets = BasicTicket.objects.filter(created_by=request.user).exclude(current_state='F').order_by('-due_date')

    ctx = minimal_admin_context(request, BasicTicket, _("Meine Tickets"), {
        'tickets_for_me': tickets_for_me,
        'my_tickets': my_tickets,
    })
    return render(request, 'tickets/ticket_list.html', ctx)


# implements the statechange of a ticket
@login_required
def state(request, forId):

    the_ticket = BasicTicket.objects.get(pk=forId)
    the_ticket = the_ticket.get_full_ticket()
    change_list_url = reverse("admin:tickets_%s_changelist" % the_ticket.__class__.__name__.lower())

    if request.GET.get("changeState", False):
        the_ticket.change_state()
        # back to list, if closed
        if the_ticket.current_state == "F":
            return HttpResponseRedirect(change_list_url)
        return HttpResponseRedirect(reverse("tickets:state", args=(forId,)))

    transitions = {
        "BasicTicket": {
            "N": {
                "next_state_text": _("Mark as audited"),
            },
            "C": {
                "next_state_text": _("Mark ticket as in progress"),
            },
            "A": {
                "heading": _("The ticket can be closed now."),
                "next_state_text": _("Close ticket"),
            },
            "F": {
                "heading": _("The ticket has been closed"),
                "next_state_text": _("Re-open"),
            },
        },
        "LaserGravurTicket": {
            "N": {
                "heading": _("State: unchecked<br/>Please verify nomenclature"),
                "next_state_text": _("Check ticket again and continue"),
                "check_species": True,
            },
            "C": {
                "heading": _("Generate labels"),
                "next_state_text": _("All labels generated. Mark as done!"),
                "print_labels": True,
            },
            "A": {
                "heading": _("The ticket can be closed now."),
                "next_state_text": _("Close ticket"),
            },
            "F": {
                "heading": _("The ticket has been closed"),
                "next_state_text": _("Re-open"),
            },
        }
    }

    try:
        the_labels = the_ticket.etikett_individual_set.all()
    except AttributeError:
        the_labels = None

    ctx = minimal_admin_context(request, the_ticket.__class__, "%s" % the_ticket, {
        "ticket": the_ticket,
        "state_name": get_name_for_state(the_ticket.current_state),
        "labels": the_labels,
        "change_list_url": change_list_url,
    })
    ctx.update(transitions[the_ticket.__class__.__name__][the_ticket.current_state])
    return render(request, "tickets/ticket-view.html", ctx)


@login_required
def show_ticket(request, forId):
    return HttpResponse(_('show ticket: ') + str(forId))


@login_required
def set_label_done(request, etikett_individual_pk):
    try:
        et = Etikett_Individual.objects.get(pk=etikett_individual_pk)
    except Etikett_Individual.DoesNotExist:
        raise Http404

    et.is_done = True
    et.save()

    return HttpResponse("Supi")


