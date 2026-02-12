from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import StudyEntryForm, StudyInstructionForm
from .models import StudyEntry, StudyInstruction
from .services import ExportLockError, export_entries_to_excel, write_audit_event


class EntryCreateView(LoginRequiredMixin, CreateView):
    model = StudyEntry
    form_class = StudyEntryForm
    template_name = "study/entry_form.html"
    success_url = reverse_lazy("entry-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        write_audit_event("entry_create", self.request.user.username, f"entry_id={self.object.id}")
        messages.success(self.request, "Entry created.")
        return response


class EntryListView(LoginRequiredMixin, ListView):
    model = StudyEntry
    template_name = "study/entry_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        queryset = StudyEntry.objects.select_related("created_by", "updated_by").all()
        piz = self.request.GET.get("piz", "").strip()
        start = self.request.GET.get("start_date", "").strip()
        end = self.request.GET.get("end_date", "").strip()
        if piz:
            queryset = queryset.filter(piz__icontains=piz)
        if start:
            queryset = queryset.filter(examination_date__gte=start)
        if end:
            queryset = queryset.filter(examination_date__lte=end)
        return queryset


class EntryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudyEntry
    form_class = StudyEntryForm
    template_name = "study/entry_form.html"
    success_url = reverse_lazy("entry-list")

    def test_func(self):
        entry = self.get_object()
        return self.request.user.is_staff or entry.created_by_id == self.request.user.id

    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to edit this entry.")

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        write_audit_event("entry_update", self.request.user.username, f"entry_id={self.object.id}")
        messages.success(self.request, "Entry updated.")
        return response


@login_required
def export_excel_view(request):
    try:
        output_path = export_entries_to_excel()
    except ExportLockError as exc:
        messages.error(request, str(exc))
        return redirect("entry-list")

    write_audit_event("export_excel", request.user.username, output_path)
    with open(output_path, "rb") as handle:
        response = HttpResponse(
            handle.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    response["Content-Disposition"] = 'attachment; filename="study_entries.xlsx"'
    return response


class InstructionListView(LoginRequiredMixin, ListView):
    model = StudyInstruction
    template_name = "study/instruction_list.html"
    context_object_name = "instructions"


class InstructionUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = StudyInstruction
    form_class = StudyInstructionForm
    template_name = "study/instruction_upload.html"
    success_url = reverse_lazy("instruction-list")

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        write_audit_event(
            "instruction_upload", self.request.user.username, f"instruction_id={self.object.id}"
        )
        messages.success(self.request, "Instruction uploaded.")
        return response


@login_required
def instruction_download_view(request, pk):
    instruction = get_object_or_404(StudyInstruction, pk=pk)
    if not instruction.pdf:
        raise Http404("File missing")
    return FileResponse(instruction.pdf.open("rb"), as_attachment=True, filename=instruction.pdf.name.split("/")[-1])
