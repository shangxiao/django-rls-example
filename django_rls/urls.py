from django.urls import path

from rls.views import view

urlpatterns = [
    path("view/", view),
]
