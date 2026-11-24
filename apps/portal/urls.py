from django.urls import include, path

from apps.portal.views import RedireccionPorRolView

urlpatterns = [
    path("ir/", RedireccionPorRolView.as_view(), name="redirigir"),
    path("cliente/", include("apps.portal.customer.urls")),
    path("gestion/", include("apps.portal.gestion.urls")),
    path("", include("apps.portal.guest.urls")),
]
