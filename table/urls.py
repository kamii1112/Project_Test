from django.urls import path
from .tableSchemaViews import TableSchema
from .createTableViews import CreateTable
from .views import Table

urlpatterns = [
    path("table/", CreateTable.as_view(), name="table"),
    path("schema/", TableSchema.as_view(), name="schema"),
    path("tables/", Table.as_view(), name="schema")
]
