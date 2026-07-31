import django.contrib.admin
import django.apps

from .base import *

class TestCustomProps(TestBase):

    GARDENS = [
        {"code": "GARD1", "name": "Garden 1", "g_type": "flowers", "g_size": "small", "g_public": True},
        {"code": "GARD2", "name": "Garden 2", "g_type": "brezels", "g_size": "middle", "g_public": True},
        {"code": "GARD3", "name": "Garden 3", "g_type": "flowers", "g_size": "huge", "g_public": True},
        {"code": "GARD4", "name": "Garden 4", "g_type": "brezels", "g_size": "small"},
        {"code": "GARD5", "name": "Lot 1", "g_type": "flowers", "g_size": "middle", "g_user": "User1"},
        {"code": "GARD6", "name": "Lot 2", "g_type": "brezels", "g_size": "huge", "g_user": "User2"},
    ]
    
    @classmethod
    def setUpTestData(cls):
        from botman.models import BotanicGarden

        UserModel.objects.create_superuser(
            username="User1",
            email="user1@example.com",
            password="the-secret",
        )
        UserModel.objects.create_user(
            username="User2",
            email="user2@example.com",
            password="the-secret",
        )

        cls.CUSTOM_PROPS = {
            "g_type": CustomProperty.objects.create(model="botman.BotanicGarden", name="type", type="text"),
            "g_size": CustomProperty.objects.create(model="botman.BotanicGarden", name="size", type="text"),
            "g_public": CustomProperty.objects.create(model="botman.BotanicGarden", name="public", type="bool"),
            "g_user": CustomProperty.objects.create(model="botman.BotanicGarden", name="user", type="user"),
        }
        def _add_props(model, data):
            for key, prop in cls.CUSTOM_PROPS.items():
                if prop.model == model._meta.label and data.get(key):
                    value = data[key]
                    if prop.type == "bool":
                        mgr = model.custom_values_bool
                        kls = PropertyValueBool
                    elif prop.type in ("text", "text_long"):
                        mgr = model.custom_values_text
                        kls = PropertyValueText
                    elif prop.type == "user":
                        mgr = model.custom_values_user
                        kls = PropertyValueUser
                        value = UserModel.objects.get(username=value)
                    else:
                        raise NotImplementedError(prop.type)

                    mgr.add(kls.objects.create(
                        property=cls.CUSTOM_PROPS[key],
                        value=value,
                    ))

        for data in cls.GARDENS:
            model = BotanicGarden.objects.create(
                code=data["code"],
                name=data["name"],
            )
            _add_props(model, data)

    def setUp(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

    def test_garden_changelist(self):
        self.assert_change_changelist_columns("botman", "botanicgarden", [
            'name', 'code',
            f'custom_property_decorator_{self.CUSTOM_PROPS["g_type"].pk}',
            f'custom_property_decorator_{self.CUSTOM_PROPS["g_size"].pk}',
            f'custom_property_decorator_{self.CUSTOM_PROPS["g_public"].pk}',
            f'custom_property_decorator_{self.CUSTOM_PROPS["g_user"].pk}',
        ])

        cl = self.get_changelist("botman", "botanicgarden")
        def assert_rows(codes: List[str]):
            cl.request()
            self.assertEqual(
                codes,
                [r["code"] for r in cl.rows],
            )
        assert_rows(["GARD1", "GARD2", "GARD3", "GARD4", "GARD5", "GARD6"])

        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_type"].pk}': "brezels",
        })
        assert_rows(["GARD2", "GARD4", "GARD6"])

        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_type"].pk}': "brezels",
            f'custom_property_{self.CUSTOM_PROPS["g_size"].pk}': "small",
        })
        assert_rows(["GARD4"])

        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_type"].pk}': "small",
            f'custom_property_{self.CUSTOM_PROPS["g_size"].pk}': "brezels",
        })
        assert_rows([])

        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_public"].pk}': "1",
        })
        assert_rows(["GARD1", "GARD2", "GARD3"])

        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_type"].pk}': "brezels",
            f'custom_property_{self.CUSTOM_PROPS["g_size"].pk}': "small",
            f'custom_property_{self.CUSTOM_PROPS["g_public"].pk}': "0",
        })
        assert_rows(["GARD4"])

        # changelist user filter is a choice-box. so don't do icontains-comparison
        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_user"].pk}': "User",
        })
        assert_rows([])

        cl.set_filters({
            f'custom_property_{self.CUSTOM_PROPS["g_user"].pk}': "User2",
        })
        assert_rows(["GARD6"])

    def test_custom_props_are_configurable(self):
        """
        Check that all models with custom properties use the
        ConfigurableTable ModelAdmin
        """
        problems = {
            "not based on config_tables.admin.ConfigurableTable": [],
        }
        for model_class, model_admin in self.get_model_admins():
            if getattr(model_class, "_has_custom_properties", None):
                if not isinstance(model_admin, ConfigurableTable):
                    problems["not based on config_tables.admin.ConfigurableTable"].append(model_admin)

        msg = io.StringIO()
        for key, admins in problems.items():
            if admins:
                print(f"\n{key}:\n", file=msg)
                for admin in admins:
                    print(f"  {admin}", file=msg)
        msg.seek(0)
        msg = msg.read()

        if msg:
            raise AssertionError(f"For BotGardBaseModel(custom_properties=True):\n{msg}")
