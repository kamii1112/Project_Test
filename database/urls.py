from django.urls import path
from .views import DatabaseManager

urlpatterns = [
    path("folders/", DatabaseManager.as_view(), name="folder_manager"),
]
