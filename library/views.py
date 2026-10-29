from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import LibraryDocument, AIMarkingScheme
from .forms import LibraryDocumentForm
from academics.models import Subject
import json, os


def _get_teacher(request):
    if not hasattr(request.user, "profile"):
        return None
    if request.user.profile.role != "TEACHER":
        return None
    return request.user.profile.teacher_profile


def _get_student(request):
    if not hasattr(request.user, "profile"):
        return None
    if request.user.profile.role != "STUDENT":
        return None
    return request.user.profile.student_profile


# ─── STUDENT VIEWS ────────────────────────────────────────────────────────────

@login_required
def student_library(request):
    if not _get_student(request):
        return redirect("accounts:login")

    docs = LibraryDocument.objects.filter(is_visible=True).select_related("subject", "uploaded_by")

    # Filters
    subject_id = request.GET.get("subject")
    doc_type   = request.GET.get("type")
    q          = request.GET.get("q", "").strip()
    if subject_id:
        docs = docs.filter(subject_id=subject_id)
    if doc_type:
        docs = docs.filter(doc_type=doc_type)
    if q:
        docs = docs.filter(title__icontains=q) | docs.filter(description__icontains=q)

    subjects = Subject.objects.filter(library_docs__is_visible=True).distinct().order_by("name")
    type_choices = LibraryDocument.TYPE_CHOICES

    context = {
        "docs": docs,
        "subjects": subjects,
        "type_choices": type_choices,
        "current_subject": subject_id,
        "current_type": doc_type,
        "q": q,
    }
    return render(request, "library/student_library.html", context)


@login_required
def view_document(request, pk):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")
    doc = get_object_or_404(LibraryDocument, pk=pk, is_visible=True)
    return render(request, "library/view_document.html", {"doc": doc})


# ─── TEACHER VIEWS ────────────────────────────────────────────────────────────

@login_required
def teacher_library(request):
    teacher = _get_teacher(request)
    if not teacher:
        return redirect("accounts:login")

    docs = LibraryDocument.objects.filter(uploaded_by=teacher).select_related("subject")
    subjects = Subject.objects.all().order_by("name")
    doc_type = request.GET.get("type")
    if doc_type:
        docs = docs.filter(doc_type=doc_type)

    context = {
        "teacher": teacher,
        "docs": docs,
        "subjects": subjects,
        "type_choices": LibraryDocument.TYPE_CHOICES,
        "current_type": doc_type,
    }
    return render(request, "library/teacher_library.html", context)


@login_required
def upload_document(request):
    teacher = _get_teacher(request)
    if not teacher:
        return redirect("accounts:login")

    if request.method == "POST":
        form = LibraryDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = teacher
            doc.save()
            messages.success(request, f'"{doc.title}" added to library.')
            return redirect("library:teacher_library")
    else:
        form = LibraryDocumentForm()

    return render(request, "library/upload_document.html", {"form": form, "teacher": teacher})


@login_required
def edit_document(request, pk):
    teacher = _get_teacher(request)
    if not teacher:
        return redirect("accounts:login")
    doc = get_object_or_404(LibraryDocument, pk=pk, uploaded_by=teacher)

    if request.method == "POST":
        form = LibraryDocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated.")
            return redirect("library:teacher_library")
    else:
        form = LibraryDocumentForm(instance=doc)

    return render(request, "library/upload_document.html", {"form": form, "doc": doc, "teacher": teacher})


@login_required
def delete_document(request, pk):
    teacher = _get_teacher(request)
    if not teacher:
        return redirect("accounts:login")
    doc = get_object_or_404(LibraryDocument, pk=pk, uploaded_by=teacher)
    if request.method == "POST":
        doc.delete()
        messages.success(request, "Document deleted.")
    return redirect("library:teacher_library")


# ─── AI MARKING SCHEME ────────────────────────────────────────────────────────

@login_required
def marking_scheme_generator(request):
    teacher = _get_teacher(request)
    if not teacher:
        return redirect("accounts:login")

    papers = LibraryDocument.objects.filter(doc_type="PAPER").select_related("subject").order_by("subject__name", "title")
    recent = AIMarkingScheme.objects.filter(generated_by=teacher).select_related("source_paper").order_by("-created_at")[:10]

    context = {"teacher": teacher, "papers": papers, "recent": recent}
    return render(request, "library/marking_scheme_generator.html", context)


@login_required
@require_POST
def generate_marking_scheme(request):
    teacher = _get_teacher(request)
    if not teacher:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    paper_id = request.POST.get("paper_id")
    paper = get_object_or_404(LibraryDocument, pk=paper_id, doc_type="PAPER")

    scheme_record = AIMarkingScheme.objects.create(
        source_paper=paper,
        generated_by=teacher,
        status="PENDING",
    )

    # Build prompt from paper content or title
    prompt_content = paper.content if paper.content.strip() else f"Question paper titled: {paper.title} — {paper.subject.name} ({paper.get_level_display()})"

    # Try OpenAI or fallback to a rule-based template
    scheme_text = _generate_with_ai(prompt_content, paper)
    scheme_record.scheme_text = scheme_text
    scheme_record.status = "DONE"
    scheme_record.save()

    return JsonResponse({
        "scheme_id": scheme_record.pk,
        "scheme_text": scheme_text,
        "paper_title": paper.title,
    })


@login_required
@require_POST
def save_scheme_to_library(request):
    teacher = _get_teacher(request)
    if not teacher:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    scheme_id = request.POST.get("scheme_id")
    scheme = get_object_or_404(AIMarkingScheme, pk=scheme_id, generated_by=teacher)

    doc = LibraryDocument.objects.create(
        title=f"Marking Scheme — {scheme.source_paper.title}",
        doc_type="SCHEME",
        subject=scheme.source_paper.subject,
        level=scheme.source_paper.level,
        description=f"AI-generated marking scheme for: {scheme.source_paper.title}",
        uploaded_by=teacher,
        content=scheme.scheme_text,
        is_visible=False,  # Teacher reviews before making visible
    )
    scheme.saved_as_doc = doc
    scheme.save()

    return JsonResponse({"doc_id": doc.pk, "message": "Saved to library (hidden — enable visibility in Library Manager)."})


def _generate_with_ai(prompt_content, paper):
    """Try Google Gemini, fallback to structured template."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            import urllib.request, json as _json
            system = (
                "You are an expert Zimbabwe O/A-Level teacher. "
                "Generate a detailed marking scheme for the following question paper content. "
                "Format it clearly: question number, expected answer/points, marks allocation. "
                "Be specific and match Zimbabwe ZIMSEC marking conventions."
            )
            payload = _json.dumps({
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system}\n\n---\nQUESTION PAPER:\n{prompt_content}"}]}
                ],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}
            }).encode()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = _json.loads(resp.read())
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"[AI generation failed: {e}]\n\n" + _template_scheme(paper)
    return _template_scheme(paper)


def _template_scheme(paper):
    return f"""MARKING SCHEME
==============
Subject: {paper.subject.name}
Level: {paper.get_level_display()}
Paper: {paper.title}
Generated: [AI not configured — add GEMINI_API_KEY to environment]

INSTRUCTIONS TO TEACHER:
- Review and edit this scheme before publishing to students
- Add specific mark allocations per question
- Include alternative acceptable answers where applicable

SECTION A — SHORT ANSWERS
Q1. [Insert expected answer] ........ [X] marks
Q2. [Insert expected answer] ........ [X] marks
Q3. [Insert expected answer] ........ [X] marks

SECTION B — STRUCTURED QUESTIONS
Q4. [Insert expected answer with point breakdown]
    (a) [point 1] — 1 mark
    (b) [point 2] — 2 marks

TOTAL: [X] marks

NOTE: To enable AI generation, add GEMINI_API_KEY to /etc/systemd/system/student-portal.service
under [Service] as: Environment=GEMINI_API_KEY=your_key_here
"""
