from django.urls import path

from apps.portal.customer import views

app_name = "customer"

urlpatterns = [
    path("", views.PanelView.as_view(), name="panel"),
]
