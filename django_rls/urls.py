from django.urls import path

from rls.views import AccountListView, view

urlpatterns = [
    path("view/", view),
    path("accounts/", AccountListView.as_view()),
]
