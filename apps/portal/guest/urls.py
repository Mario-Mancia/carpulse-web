from django.urls import path

from apps.portal.guest import views

app_name = "guest"

urlpatterns = [
    path("", views.InicioView.as_view(), name="inicio"),
    path("terminos/", views.TerminosView.as_view(), name="terminos"),
]
