from django.urls import path
from . import views

urlpatterns = [

    # auth
    path("login/", views.scansnapweb_login, name="scansnapweb-login"),
    path("logout/", views.scansnapweb_logout, name="scansnapweb-logout"),
    path("register/", views.register, name="register"),

    # scan
    path("hello/", views.hello, name="hello"),
    path("", views.home, name="home"),
    path("get-scanner-info/", views.get_scanner_info, name="get-scanner-info"),
    path("scan/", views.scan, name="scan"),
]
