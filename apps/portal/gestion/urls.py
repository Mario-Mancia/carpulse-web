from django.urls import path

from apps.portal.gestion import views

app_name = "gestion"

urlpatterns = [
    path("", views.PanelView.as_view(), name="panel"),
    path("configuracion/", views.ConfiguracionView.as_view(), name="configuracion"),
]
