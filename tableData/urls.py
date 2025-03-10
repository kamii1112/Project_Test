from django.urls import path
from .views import TableData
urlpatterns = [
    path("table-data/", TableData.as_view(), name="table-data"),
]
