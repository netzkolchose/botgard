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
- available as column in the table configuration of the changelist
- available as property on the model instance
- visible in the label documentation `/labels/docs/template`
- supported by auto-complete

Models that want to support custom properties need to derive from a custom props base model and 
the ModelAdmin needs to derive from `config_tables.admin.ConfigurableTable`.

```python
from BotGard import BotGardBaseModel
from config_tables.admin import ConfigurableTable

class MyModel(BotGardBaseModel(custom_properties_unique_name="mymodel")):
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
prop = CustomProperty.objects.create(
    model=MyModel._meta.label, 
    name="my attribute", 
    type="text", 
    required=True,      # makes it mandatory in the `PropertyValuesFormField`
)

instance = MyModel.objects.create()
# add a value to this instance
instance.custom_values_text.add(
    PropertyValueText.objects.create(property=prop, value="some text")
)

# assume prop.pk == 1
print(instance.custom_property_1)
# 'some text'
```

MyModel has many-to-many relations called `custom_values_text` and `custom_values_bool`. They link 
to `PropertyValueText` and `PropertyValueBool` models respectively.

The `instance.custom_property_1` trick above is made by overloading the `MyModel.__getattr__` method
and fetching the value from database. It is implemented to make properties available to label templates.
