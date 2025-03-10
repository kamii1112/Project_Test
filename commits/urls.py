from django.urls import path
from .views import GitHubStorage

urlpatterns = [
    path('storage/', GitHubStorage.as_view(), name='store-data'),
    path('storage/<str:file_name>/', GitHubStorage.as_view(), name='get-data'),
    path('storage/delete/', GitHubStorage.as_view(), name='delete-data'),  # DELETE route
]
