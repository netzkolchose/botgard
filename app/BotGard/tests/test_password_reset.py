from .base import *
from BotGard.models import PasswordResetCode


class TestPasswordReset(TestBase):

    PW = "fku093lkd9d3ekl39sd"
    NEW_PW = ",d93jo39lsdj94kdnf92"

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=cls.PW,
        )
        cls.user = get_user_model().objects.create_user(
            username="user",
            email="user@example.com",
            password=cls.PW,
            is_staff=True,
        )

    def test_password_reset_no_access(self):
        self.login(username="user", password=self.PW)
        response = self.client.get(reverse("generate-reset-password", args=(self.user.pk, )))
        self.assertEqual(302, response.status_code)
        self.assertIn("no_permission", response.headers["Location"])

    def get_reset_link(self) -> str:
        self.login(username="user", password=self.PW)
        self.client.logout()

        self.login(username="admin", password=self.PW)
        response = self.client.get(reverse("generate-reset-password", args=(self.user.pk, )))
        form = self.get_form_data(response.content)
        response = self.client.post(
            reverse("generate-reset-password", args=(self.user.pk, )),
            data=form,
        )
        soup = self.get_soup(response.content)
        link = soup.find("code", {"class": "reset-link"})
        self.assertTrue(link)
        self.client.logout()

        self.assertEqual(1, PasswordResetCode.objects.count())

        return "/" + link.text.split("/", 3)[-1]

    def test_password_reset(self):
        link = self.get_reset_link()
        response = self.client.get(link)
        data = self.get_form_data(self.get_soup(response.content).find("form", {"class": "password-form"}))

        data.update({
            "email": self.user.email,
            "password1": self.NEW_PW,
            "password2": self.NEW_PW,
        })
        response = self.client.post(link, data=data)
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, PasswordResetCode.objects.count())

        self.login(username="user", password=self.NEW_PW)

    def test_password_reset_fail(self):
        link = self.get_reset_link()
        response = self.client.get(link)

        for update_data in (
                {
                    "email": self.user.email,
                    "password1": "123",
                },
                {
                    "email": self.user.email,
                    "password1": "123",
                    "password2": "123",
                },
                {
                    "email": self.user.email,
                    "password1": self.NEW_PW,
                    "password2": self.NEW_PW + "x",
                },
        ):
            data = self.get_form_data(self.get_soup(response.content).find("form", {"class": "password-form"}))
            data.update(update_data)
            response = self.client.post(link, data=data)
            soup = self.get_soup(response.content)
            self.assertTrue(soup.find("ul", {"class": "errorlist"}))

        # wrong email
        data = self.get_form_data(self.get_soup(response.content).find("form", {"class": "password-form"}))
        data.update({
            "email": "a" + self.user.email,
            "password1": self.NEW_PW,
            "password2": self.NEW_PW,
        })
        response = self.client.post(link, data=data)
        soup = self.get_soup(response.content)
        self.assertIn("has expired", soup.find("p", {"class": "message"}).text)

        # wrong code
        link = link + "a"
        response = self.client.get(link)
        data = self.get_form_data(self.get_soup(response.content).find("form", {"class": "password-form"}))
        data.update({
            "email": self.user.email,
            "password1": self.NEW_PW,
            "password2": self.NEW_PW,
        })
        response = self.client.post(link, data=data)
        soup = self.get_soup(response.content)
        self.assertIn("has expired", soup.find("p", {"class": "message"}).text)
