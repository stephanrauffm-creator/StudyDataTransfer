from django.urls import path

from .views import (
    EntryCreateView,
    EntryListView,
    EntryUpdateView,
    InstructionListView,
    InstructionUploadView,
    export_excel_view,
    instruction_download_view,
)

urlpatterns = [
    path("entries", EntryListView.as_view(), name="entry-list"),
    path("entries/new", EntryCreateView.as_view(), name="entry-create"),
    path("entries/<int:pk>/edit", EntryUpdateView.as_view(), name="entry-edit"),
    path("export/excel", export_excel_view, name="export-excel"),
    path("instructions", InstructionListView.as_view(), name="instruction-list"),
    path("instructions/upload", InstructionUploadView.as_view(), name="instruction-upload"),
    path("instructions/<int:pk>/download", instruction_download_view, name="instruction-download"),
]
