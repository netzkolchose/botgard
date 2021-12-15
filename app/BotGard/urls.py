from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#from config_tables.admin import ConfigurableTable
from botman.views import index_page

urlpatterns = i18n_patterns(
    url(r'^admin/', admin.site.urls),

    url(r'^individual/',    include('individuals.urls')),
    url(r'^botman/',        include('botman.urls')),
    url(r'^$',              index_page, name="index"),
    url(r'^species/',       include('species.urls')),
    url(r'^seedcatalog/',   include('seedcatalog.urls')),
    url(r'^tickets/',       include('tickets.urls')),
    url(r'^labels/',        include('labels.urls')),
    url(r'^sidebar/',       include('sidebar.urls')),
    url(r'^ajax/',          include('ajax.urls')),
)

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
