# -*- coding: utf-8
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from config_app import register_key

def url_cleaner(url, clean_get=False):
    if clean_get:
        url = url.split('?')[0]
    url_components = url.split('/')

    if len(url_components) <= 1:
        return url

    lang_prefix_candidate = url_components[1]

    if lang_prefix_candidate in dict(settings.LANGUAGES):
        url_components.pop(1)

    url = "/".join(url_components)

    return url


def _sidebar_validator(value):
    from django.forms import ValidationError

    if not isinstance(value, object):
        raise ValidationError(_('An object is expected'))

    if 'enabled' not in value:
        raise ValidationError(_('A key \'enabled\' must be present.'))

    if not isinstance(value['enabled'], bool):
        raise ValidationError(_('Value for key \'enabled\' must be a boolean.'))

    if 'elements' not in value:
        raise ValidationError(_('A key \'elements\' must be present'))

    if not isinstance(value['elements'], list):
        raise ValidationError(_('A key \'elements\' must be a list.'))



register_key('sidebar', default={
                 "enabled": True,
                 "elements": [
                     'shortcuts',
                     'bookmarks',
                     'notes',
                 ]
             },
             validator=_sidebar_validator,
             description='''
Basic configurations of the Sidebar and it's widgets.<br>
An <b>object</b> is expected. Valid keys are:<br>
<dl>
<dt>enabled</dt>
<dd>Enables oder disables the complete Sidebar. A Boolean value, either <b>true</b> (enabled) or <b>false</b> (disabled).</dd>
<dt>elements</dt>
<dd>A list of strings to enable individual sections in the sidebar and their order. Valid values are <b>shortcuts</b>, <b>bookmarks</b> or <b>notes</b></dd> 
</dl>
''')


def _shortcuts_validator(value):
    from django.forms import ValidationError

    if not isinstance(value, list):
        raise ValidationError(_('A list is expected.'))

    for elem in value:
        if 'icon' not in elem:
            raise ValidationError(_('Each item requires an icon attribute.'))
        if 'target' not in elem and 'target_url' not in elem:
            raise ValidationError(_('Each item requires a target or target_url attribute.'))
        if 'caption' not in elem:
            raise ValidationError(_('Each item requires a caption attribute.'))
        if 'groups' not in elem:
            raise ValidationError(_('Each item requires a group attribute.'))
        if 'only_superuser' not in elem:
            raise ValidationError(_('Each item requires a only_superuser attribute.'))

        if not isinstance(elem['groups'], list):
            raise ValidationError(_('The attribute groups must be a list.'))
        if settings.LANGUAGE_CODE not in elem['caption']:
            raise ValidationError(_('The attribute caption must contain a key %s.')%(settings.LANGUAGE_CODE))


register_key('sidebar_shortcuts', default=
[
    {
        'icon': 'fa fa-address-book',
        'target': 'admin:botman_botanicgarden_changelist',
        'caption': {
            'en': 'Gardens',
            'de': 'Gärten',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-sitemap',
        'target': 'admin:species_family_changelist',
        'caption': {
            'en': 'Genera',
            'de': 'Gattungen',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-code-branch',
        'target': 'admin:species_species_changelist',
        'caption': {
            'en': 'Species',
            'de': 'Arten',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-tree',
        'target': 'admin:individuals_individual_changelist',
        'caption': {
            'en': 'Individuals',
            'de': 'Individuen',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-certificate',
        'target': 'admin:individuals_seed_changelist',
        'caption': {
            'en': 'Seeds',
            'de': 'Samen',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-book',
        'target': 'admin:seedcatalog_seedcatalog_changelist',
        'caption': {
            'en': 'Catalogs',
            'de': 'Kataloge',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-check-square',
        'target': 'admin:tickets_myticket_changelist',
        'caption': {
            'en': 'Tickets',
            'de': 'Tickets',
        },
        'groups': [],
        'only_superuser': False,
    },
    {
        'icon': 'fa fa-user',
        'target': 'admin:auth_user_changelist',
        'caption': {
            'en': 'Users',
            'de': 'Benutzer',
        },
        'groups': [],
        'only_superuser': True,
    },
    {
        'icon': 'fa fa-users',
        'target': 'admin:auth_group_changelist',
        'caption': {
            'en': 'Groups',
            'de': 'Gruppen',
        },
        'groups': [],
        'only_superuser': True,
    },
],
             description='''
Configuration of the Shortcut Items in the Sidebar.<br>
A <b>list of objects</b> is expected.<br>
Valid keys for the object are:
<dl>
<dt>icon</dt>
<dd>Any fontawesome icon-class eg. <b>fa fa-users</b></dd>
<dt>target</dt>
<dd>A Django-Style resolvable. e.g. <b>admin:auth_group_changelist</b><br>Note: either <b>target</b> or <b>target_url</b> must be given.</dd>
<dt>target_url</dt>
<dd>An URL. Can be used as an alternative to the <b>target</b> key.</dd>
<dt>caption</dt>
<dd>An object with the language code as key and the caption-text as value.<br>
The value for the key '<b>%s</b>' is used as a fallback if no entry for the current language key is found.</dd>
<dt>groups</dt>
<dd>A list of group names. Users from those groups will see the item in the shortcuts section of the sidebar.</dd>
<dt>only_superuser</dt>
<dd>A Boolean. If <b>True</b> only superusers will see the item in the shortcuts section of the sidebar.</dd> 
</dl>
'''%settings.LANGUAGE_CODE, validator=_shortcuts_validator)