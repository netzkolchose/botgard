from django.template import Library
from django.utils.safestring import mark_safe
from django.urls import resolve, reverse, translate_url
from django.utils.safestring import SafeText
from django.template import loader, Context
import sidebar.models as models
from django.urls.exceptions import NoReverseMatch
from config_app import get_value, register_key
from sidebar import url_cleaner
from django.db.models import Q

from django.conf import settings

register = Library()


@register.simple_tag(takes_context=True)
def clean_url(context, *args, **kwargs):
    return url_cleaner(context.request.get_full_path())


@register.simple_tag(takes_context=True)
def bookmark_list(context, *args, **kwargs):
    list_markup = ''

    bookmarks = models.BookMark.objects.filter(user=context.request.user).order_by('order', '-pk').all()

    template = loader.get_template('sidebar/bookmark_item.html')

    path = context['request'].path
    current_clean_url = url_cleaner(path)

    for bookmark in bookmarks:
        list_markup += template.render({ 'bookmark': bookmark,
                                         'current': True if current_clean_url  == bookmark.url else False })
    return SafeText(list_markup)


@register.simple_tag(takes_context=True)
def notes_list(context, *args, **kwargs):
    list_markup = ''
    path = context['request'].path
    current_clean_url = url_cleaner(path, clean_get=True)

    notes = models.Note.objects.filter(
        Q(user=context.request.user) | Q(public=True)
    ).filter(url=current_clean_url).order_by('-modified', '-pk', '-created').all()

    template = loader.get_template('sidebar/note_item.html')


    for note in notes:
        list_markup += template.render({
            'note': note,
            'current': True if current_clean_url  == note.url else False,
            'is_editable': context.request.user.is_superuser or note.user == context.request.user,
            'is_own_note': context.request.user == note.user,
        })

    return SafeText(list_markup)

@register.simple_tag(takes_context=True)


def shortcut_list(context, *args, **kwargs):
    template = loader.get_template('sidebar/shortcut_item.html')
    current_language = context.request.LANGUAGE_CODE

    shortcuts_config = get_value('sidebar_shortcuts')
    shortcuts_markup = ''

    for shortcut in shortcuts_config:
        target = False
        target_url = False

        try:
            icon = shortcut['icon']
            captions = shortcut['caption']

            if 'target' in shortcut:
                target = shortcut['target']
            if 'target_url' in shortcut:
                target_url = shortcut['target_url']

        except KeyError:
            return SafeText('improperly configured')

        groups = shortcut['groups']
        only_superuser = shortcut['only_superuser']

        user = context.request.user

        if only_superuser and not user.is_superuser:
            break

        # Is the current user in any of the groups for this shortcut?
        if (len(groups)) > 0 and \
            (True not in map(lambda group: user.groups.filter(name=group).exists(), groups)):

            break

        # get the caption in the current language

        caption = False
        if current_language in captions:
            caption = captions[current_language]
        else:
            if settings.LANGUAGE_CODE in captions:
                caption = captions[settings.LANGUAGE_CODE]

        if not target_url:
            try:
                target_url = reverse(target)
            except NoReverseMatch:
                target_url = 'improperly configured target'

        shortcuts_markup += template.render({
            'icon': icon,
            'url': target_url,
            'caption': caption,
        })

    return SafeText(shortcuts_markup)

