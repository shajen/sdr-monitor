from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView
import common.urls
import common.urls_account
import sdr.urls

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("account/", include(common.urls_account)),
    path("admin/", admin.site.urls),
    path("c/", include(common.urls)),
    path("sdr/", include(sdr.urls)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
