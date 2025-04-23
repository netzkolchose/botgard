from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls import include
from django.urls import re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from botman.views import index_page

urlpatterns = i18n_patterns(
    re_path(r'^admin/', admin.site.urls),

    re_path(r'^individual/',    include('individuals.urls')),
    re_path(r'^botman/',        include('botman.urls')),
    re_path(r'^$',              index_page, name="index"),
    re_path(r'^species/',       include('species.urls')),
    re_path(r'^seedcatalog/',   include('seedcatalog.urls')),
    re_path(r'^tickets/',       include('tickets.urls')),
    re_path(r'^labels/',        include('labels.urls')),
    re_path(r'^sidebar/',       include('sidebar.urls')),
    re_path(r'^ajax/',          include('ajax.urls')),
)

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
