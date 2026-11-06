from django.contrib import admin
from django.urls import include, path

from apps.documents.views import SearchView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/search/", SearchView.as_view(), name="document-search"),
]
