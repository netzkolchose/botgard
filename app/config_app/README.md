# BotGard config_app

This module provides custom settings for the BotGard database that are persisted in the database.
Specifics of a deployment, like the site name, number generation settings, or extra model fields, 
are controlled here. 


## KeyValue model

At some places in the code, there are definitions of configurable values, like:

```python
import config_app

config_app.register_key(
    key="site_branding",
    default="Botanic Garden",
    description="This name will appear at the top of all pages",
    validator=...,
    translateable=True,     # Text values are translateable by default
)
```

Once registered, a value can be retrieved via:

```python
config_app.get_value("site_branding")
```

Supported value types are text, translateable text, json or gis.PointField.

The defaults from the registration can be overwritten in the database. First store all values to db:

```shell
./manage.py botgard_update_config
```

Then, as an admin, hover over "Welcome user" on the top-right and select "global configuration" in the sub-menu. 


## CustomProperty model

This allows dynamically adding new fields to many models in BotGard. All settings are made in the django admin
in "global configuration".

Once a `CustomProperty` entry for a particular model is created in the admin view, it is
- visible and editable in the change form
  - **TODO** properly rendered in read-only change form 
- available as column in the table configuration of the changelist
  - filterable
  - **TODO** sortable
- available as property on the model instance, e.g. `instance.custom_value_<pk>`
- visible in the label documentation `/labels/docs/template`
- supported by auto-complete
- **TODO** displayed by `InlineModelAdmin`

Models that want to support custom properties need to derive from a custom props base model and 
the ModelAdmin needs to derive from `config_tables.admin.ConfigurableTable`.

```python
from BotGard import BotGardBaseModel
from config_tables.admin import ConfigurableTable

class MyModel(BotGardBaseModel(unique_name="mymodel", custom_properties=True)):
    pass

class MyModelAdmin(ConfigurableTable):
    pass
```

All is managed by the admin and form/field classes. The custom properties are automatically added to the
ModelAdmin `fieldsets`.

However, the internals look like this: 
```python
from config_app.models import *

# create a new property
prop = CustomProperty.objects.create_for_model(
    model=MyModel, 
    name="my attribute", 
    type="text", 
    required=True,      # makes it mandatory in the `PropertyValuesFormField`
)

instance = MyModel.objects.create()
# add a value to this instance
instance.custom_values_text.add(
    PropertyValueText.objects.create(property=prop, value="some text")
)

# models have special methods/attributes to access their custom-prop values:

print(instance.custom_property("my attribute"))

# or without function call (useful in label templates), assume prop.pk == 1
print(instance.custom_property_1)
```

MyModel has many-to-many relations called `custom_values_text`, `custom_values_bool` or `custom_values_user`.
They link to `PropertyValueText`, `PropertyValueBool` and `PropertyValueUser` models respectively.

The `instance.custom_property_1` trick above is made by overloading the `MyModel.__getattr__` method
and fetching the value from database. It is implemented to make properties available to label templates.


### TODO: proper display in read-only changeform

The `PropertyValuesWidget` for the changeform is not rendered in read-only views 
(when user only has view permission). The current quickfix is output property name and value in
the `PropertyValue<Type>.__str__` method. This looks awful for long texts and also only
displays property values that are set, not empty fields or unchecked checkboxes.

In `django/contrib/admin/templates/admin/includes/fieldset.html` widgets are generally not rendered,
when `field.is_readonly == True`. Unfortunately, `field` in this case is a 
`django.contrib.admin.helpers.AdminReadonlyField` which is burried deep behind django's custom extensibility
realm. You'd need to copy/paste & patch the huge `ModelAdmin._changeform_view` plus `helpers.AdminForm`. 
Just patching the `fieldset.html` template does not work because the original widget is not present in the
template context. 

Maybe it's possible to patch the fieldset block in the `admin/change_form.html` template:
```
{% block field_sets %}
{% for fieldset in adminform %}
  {% include "admin/includes/fieldset.html" with heading_level=2 prefix="fieldset" id_prefix=0 id_suffix=forloop.counter0 %}
{% endfor %}
{% endblock %}
```
and somehow, along the way, replace `fieldset` which is a `helpers.Fieldset` with a custom version 
that yields fields that have `is_readonly = False` and render the original widgets in disabled-style.
