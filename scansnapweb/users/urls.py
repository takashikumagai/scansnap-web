from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    # path("login/", views.scansnapweb_login, name="scansnapweb-login"),
    # path("logout/", views.scansnapweb_logout, name="scansnapweb-logout"),
    path("login/", views.CustomLoginView.as_view(), name="scansnapweb-login"),
    path("logout/", LogoutView.as_view(next_page="scansnapweb-login"), name="scansnapweb-logout"),
    path("register/", views.register, name="register"),
]
