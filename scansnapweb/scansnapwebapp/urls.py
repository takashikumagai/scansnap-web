from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"scans", views.ScanViewSet)

urlpatterns = [
    path("", views.home, name="home"),
    path("", include(router.urls)),
    path("get-scanner-info/", views.get_scanner_info, name="get-scanner-info"),
    # path("scan/", views.scan, name="scan"),
    path("ping/", views.ping, name="ping"),
]
