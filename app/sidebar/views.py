from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden, HttpResponseNotModified
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import requires_csrf_token
from django.db.models import ObjectDoesNotExist
from django.db import transaction
from sidebar import url_cleaner

from .models import *

@requires_csrf_token
@staff_member_required
def create_note(request):
    try:
        user = request.user
        url = request.POST['url']
    except MultiValueDictKeyError:
        return HttpResponseBadRequest()
    else:
        new_note = Note.objects.create(url=url_cleaner(url, clean_get=True), user=user, public=False, note='')
        new_note.save()

        return render(request, 'sidebar/note_item.html', {
            'note': new_note,
            'is_editable': True,
            'is_own_note': True,
        })

@requires_csrf_token
@staff_member_required
def delete_note(request, id):
    try:
        note = Note.objects.get(pk=id)
    except ObjectDoesNotExist:
        raise Http404
    else:
        if (note.user != request.user) and (not request.user.is_superuser):
            raise Http404
        else:
            note.delete()
            return HttpResponse('ok')

@requires_csrf_token
@staff_member_required
def publish_note(request, id, publish):
    try:
        note = Note.objects.get(pk=id)
    except ObjectDoesNotExist:
        raise Http404
    else:
        if (note.user != request.user) and (not request.user.is_superuser):
            raise Http404
        else:
            if publish == "1":
                note.public = True
                note.save()
            elif publish == "0":
                note.public = False
                note.save()
            else:
                return HttpResponseBadRequest('')

            return HttpResponse('ok')

@requires_csrf_token
@staff_member_required
def edit_note(request, id):
    try:
        note = Note.objects.get(pk=id)
    except ObjectDoesNotExist:
        raise Http404
    else:
        if (note.user != request.user) and (not request.user.is_superuser):
            raise Http404
        else:
            if "text" not in request.POST:
                return HttpResponseBadRequest('')

            new_note_text = request.POST['text']

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(new_note_text, 'html.parser')
            note.note = soup.text
            note.save()

            return HttpResponse(note.note)


@requires_csrf_token
@staff_member_required
def add_bookmark(request):
    try:
        user = request.user
        title = request.POST['title']
        url = request.POST['url']
    except MultiValueDictKeyError:
        return HttpResponseBadRequest()
    else:
        new_bookmark = BookMark.objects.create(title=title, url=url, user=user)
        new_bookmark.save()

        return render(request, 'sidebar/bookmark_item.html', {
            'bookmark': new_bookmark,
            'current': True,
        })


@requires_csrf_token
@staff_member_required
def update_order(request):
    import json
    elems = json.loads(request.POST['elements'])

    try:
        with transaction.atomic():
            for elem in elems:
                bookmark = BookMark.objects.get(pk=elem['elem'])
                if bookmark.user != request.user:
                    raise Http404
                else:
                    bookmark.order = elem['order']
                    bookmark.save()
    except ObjectDoesNotExist:
        raise Http404

    return HttpResponse('ok')


@requires_csrf_token
@staff_member_required
def delete_bookmark(request, id):
    try:
        bookmark = BookMark.objects.get(pk=id)
    except ObjectDoesNotExist:
        raise Http404
    else:
        if not bookmark.user == request.user:
            raise Http404
        else:
            bookmark.delete()
            return HttpResponse('ok')
