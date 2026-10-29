from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import StudentRegistrationForm

from academics.models import (
    SchoolProfile,
    TeacherAssignment,
    StudentEnrollment,
    Term,
)

from fees.models import TermFee, FeePayment
from grades.models import (
    Assessment,
    StudentGrade,
    TermReport,
)


def get_letter_grade(percentage):
    if percentage is None:
        return "-"

    if percentage >= 70:
        return "A"
    if percentage >= 60:
        return "B"
    if percentage >= 50:
        return "C"
    if percentage >= 45:
        return "D"
    if percentage >= 40:
        return "E"
    return "U"

def build_student_term_summary(enrollment, selected_term=None):
    grades = StudentGrade.objects.filter(
        student_enrollment=enrollment,
        assessment__is_published=True,
    )

    if selected_term is not None:
        grades = grades.filter(assessment__term=selected_term)

    grades = grades.select_related(
        "assessment",
        "assessment__term",
        "assessment__teacher_assignment",
        "assessment__teacher_assignment__subject",
    ).order_by(
        "assessment__term__number",
        "assessment__teacher_assignment__subject__name",
        "assessment__assessment_date",
    )

    grade_rows = []
    summary_data = {}

    for grade in grades:
        assessment = grade.assessment
        subject = assessment.teacher_assignment.subject
        term = assessment.term
        percentage = grade.percentage

        grade_rows.append({
            "subject": subject,
            "assessment": assessment,
            "grade": grade,
            "letter_grade": get_letter_grade(percentage),
        })

        summary_key = (
            subject.id,
            term.id,
        )

        if summary_key not in summary_data:
            summary_data[summary_key] = {
                "subject": subject,
                "term": term,
                "weighted_points": Decimal("0"),
                "total_weight": Decimal("0"),
            }

        if percentage is not None and assessment.weight > 0:
            summary_data[summary_key]["weighted_points"] += (
                percentage * assessment.weight
            )

            summary_data[summary_key]["total_weight"] += (
                assessment.weight
            )

    subject_summaries = []

    for item in summary_data.values():
        average = None

        if item["total_weight"] > 0:
            average = (
                item["weighted_points"]
                / item["total_weight"]
            )

        subject_summaries.append({
            "subject": item["subject"],
            "term": item["term"],
            "average": average,
            "letter_grade": get_letter_grade(average),
        })

    subject_summaries.sort(
        key=lambda item: (
            item["term"].number,
            item["subject"].name,
        )
    )

    return grade_rows, subject_summaries


def portal_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "profile"):

            if request.user.profile.role == "TEACHER":
                return redirect("accounts:teacher_dashboard")

            if request.user.profile.role == "STUDENT":
                return redirect("accounts:student_dashboard")

        return redirect("/admin/")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)

            if hasattr(user, "profile"):

                if user.profile.role == "TEACHER":
                    return redirect("accounts:teacher_dashboard")

                if user.profile.role == "STUDENT":
                    return redirect("accounts:student_dashboard")

            messages.error(
                request,
                "This account does not have portal access."
            )

            logout(request)

        else:
            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "accounts/login.html"
    )


def student_registration(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save(admission_date=timezone.localdate())
            except IntegrityError:
                form.add_error(
                    "student_number",
                    "This student number is already registered.",
                )
            else:
                return redirect("accounts:student_registration_complete")
    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/student_registration.html",
        {
            "form": form,
            "has_active_classes": form.fields["classroom"].queryset.exists(),
        },
    )


def student_registration_complete(request):
    return render(
        request,
        "accounts/student_registration_complete.html",
    )


@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")

    if request.user.profile.role != "TEACHER":
        return redirect("accounts:login")

    teacher_profile = request.user.profile.teacher_profile

    assignments = TeacherAssignment.objects.filter(
        teacher=teacher_profile,
        is_active=True,
    ).select_related(
        "subject",
        "classroom",
        "school_year",
    )

    total_assessments = 0
    published_assessments = 0
    for _a in assignments:
        _qs = Assessment.objects.filter(teacher_assignment=_a)
        total_assessments += _qs.count()
        published_assessments += _qs.filter(is_published=True).count()
    context = {
        "teacher": teacher_profile,
        "assignments": assignments,
        "total_assessments": total_assessments,
        "published_assessments": published_assessments,
    }

    return render(
        request,
        "accounts/teacher_dashboard.html",
        context,
    )


@login_required
def teacher_class_detail(request, assignment_id):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")

    if request.user.profile.role != "TEACHER":
        return redirect("accounts:login")

    teacher_profile = request.user.profile.teacher_profile

    assignment = get_object_or_404(
        TeacherAssignment.objects.select_related(
            "teacher",
            "subject",
            "classroom",
            "school_year",
        ),
        id=assignment_id,
        teacher=teacher_profile,
        is_active=True,
    )

    students = StudentEnrollment.objects.filter(
        classroom=assignment.classroom,
        school_year=assignment.school_year,
        is_active=True,
    ).select_related(
        "student"
    ).order_by(
        "student__last_name",
        "student__first_name",
    )

    assessments = Assessment.objects.filter(
        teacher_assignment=assignment
    ).select_related(
        "term"
    ).order_by(
        "term__number",
        "assessment_date",
    )

    grade_rows = []

    for student in students:
        student_grades = []

        for assessment in assessments:
            grade = StudentGrade.objects.filter(
                assessment=assessment,
                student_enrollment=student,
            ).first()

            student_grades.append({
                "assessment": assessment,
                "grade": grade,
            })

        grade_rows.append({
            "student": student,
            "grades": student_grades,
        })

    context = {
        "teacher": teacher_profile,
        "assignment": assignment,
        "students": students,
        "assessments": assessments,
        "grade_rows": grade_rows,
    }

    return render(
        request,
        "accounts/teacher_class_detail.html",
        context,
    )


@login_required
def teacher_create_assessment(request, assignment_id):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")

    if request.user.profile.role != "TEACHER":
        return redirect("accounts:login")

    teacher_profile = request.user.profile.teacher_profile

    assignment = get_object_or_404(
        TeacherAssignment.objects.select_related(
            "teacher",
            "subject",
            "classroom",
            "school_year",
        ),
        id=assignment_id,
        teacher=teacher_profile,
        is_active=True,
    )

    terms = Term.objects.filter(
        school_year=assignment.school_year
    ).order_by(
        "number"
    )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()

        assessment_type = request.POST.get(
            "assessment_type",
            ""
        ).strip()

        term_id = request.POST.get("term")

        maximum_score_value = request.POST.get(
            "maximum_score",
            ""
        ).strip()

        weight_value = request.POST.get(
            "weight",
            ""
        ).strip()

        assessment_date_value = request.POST.get(
            "assessment_date",
            ""
        ).strip()

        error_found = False

        if not title:
            messages.error(
                request,
                "Assessment title is required."
            )
            error_found = True

        valid_types = [
            choice[0]
            for choice in Assessment.ASSESSMENT_TYPES
        ]

        if assessment_type not in valid_types:
            messages.error(
                request,
                "Please select a valid assessment type."
            )
            error_found = True

        try:
            term = terms.get(
                id=term_id
            )

        except (Term.DoesNotExist, ValueError, TypeError):
            term = None

            messages.error(
                request,
                "Please select a valid term."
            )

            error_found = True

        try:
            maximum_score = Decimal(
                maximum_score_value
            )

            if maximum_score <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            maximum_score = None

            messages.error(
                request,
                "Maximum score must be greater than 0."
            )

            error_found = True

        try:
            weight = Decimal(
                weight_value
            )

            if weight < 0 or weight > 100:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            weight = None

            messages.error(
                request,
                "Weight must be between 0 and 100."
            )

            error_found = True

        assessment_date = parse_date(
            assessment_date_value
        )

        if assessment_date is None:
            messages.error(
                request,
                "Please enter a valid assessment date."
            )

            error_found = True

        if not error_found:
            Assessment.objects.create(
                teacher_assignment=assignment,
                term=term,
                title=title,
                assessment_type=assessment_type,
                maximum_score=maximum_score,
                weight=weight,
                assessment_date=assessment_date,
                is_published=False,
            )

            messages.success(
                request,
                f"{title} was created successfully."
            )

            return redirect(
                "accounts:teacher_class_detail",
                assignment_id=assignment.id,
            )

    context = {
        "teacher": teacher_profile,
        "assignment": assignment,
        "terms": terms,
        "assessment_types": Assessment.ASSESSMENT_TYPES,
    }

    return render(
        request,
        "accounts/teacher_assessment_create.html",
        context,
    )


@login_required
def teacher_grade_entry(request, assessment_id):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")

    if request.user.profile.role != "TEACHER":
        return redirect("accounts:login")

    teacher_profile = request.user.profile.teacher_profile

    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "teacher_assignment",
            "teacher_assignment__teacher",
            "teacher_assignment__subject",
            "teacher_assignment__classroom",
            "teacher_assignment__school_year",
            "term",
        ),
        id=assessment_id,
        teacher_assignment__teacher=teacher_profile,
        teacher_assignment__is_active=True,
    )

    assignment = assessment.teacher_assignment

    students = StudentEnrollment.objects.filter(
        classroom=assignment.classroom,
        school_year=assignment.school_year,
        is_active=True,
    ).select_related(
        "student"
    ).order_by(
        "student__last_name",
        "student__first_name",
    )

    if request.method == "POST":
        errors = False

        for enrollment in students:
            score_value = request.POST.get(
                f"score_{enrollment.id}",
                ""
            ).strip()

            comment_value = request.POST.get(
                f"comment_{enrollment.id}",
                ""
            ).strip()

            if score_value == "":
                continue

            try:
                score = Decimal(score_value)

            except InvalidOperation:
                messages.error(
                    request,
                    f"Invalid score for "
                    f"{enrollment.student.first_name} "
                    f"{enrollment.student.last_name}."
                )

                errors = True
                continue

            if (
                score < 0
                or score > assessment.maximum_score
            ):
                messages.error(
                    request,
                    f"Score for "
                    f"{enrollment.student.first_name} "
                    f"{enrollment.student.last_name} "
                    f"must be between 0 and "
                    f"{assessment.maximum_score}."
                )

                errors = True
                continue

            StudentGrade.objects.update_or_create(
                assessment=assessment,
                student_enrollment=enrollment,
                defaults={
                    "score": score,
                    "comment": comment_value,
                }
            )

        if not errors:
            messages.success(
                request,
                "Grades saved successfully."
            )

            return redirect(
                "accounts:teacher_class_detail",
                assignment_id=assignment.id,
            )

    grade_rows = []

    for enrollment in students:
        grade = StudentGrade.objects.filter(
            assessment=assessment,
            student_enrollment=enrollment,
        ).first()

        grade_rows.append({
            "enrollment": enrollment,
            "grade": grade,
        })

    context = {
        "teacher": teacher_profile,
        "assignment": assignment,
        "assessment": assessment,
        "grade_rows": grade_rows,
    }

    return render(
        request,
        "accounts/teacher_grade_entry.html",
        context,
    )


@login_required
def teacher_toggle_publish(request, assessment_id):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")

    if request.user.profile.role != "TEACHER":
        return redirect("accounts:login")

    if request.method != "POST":
        return redirect(
            "accounts:teacher_dashboard"
        )

    teacher_profile = request.user.profile.teacher_profile

    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "teacher_assignment",
            "teacher_assignment__teacher",
            "teacher_assignment__classroom",
            "teacher_assignment__subject",
        ),
        id=assessment_id,
        teacher_assignment__teacher=teacher_profile,
        teacher_assignment__is_active=True,
    )

    assessment.is_published = not assessment.is_published

    assessment.save(
        update_fields=[
            "is_published"
        ]
    )

    if assessment.is_published:
        messages.success(
            request,
            f"{assessment.title} has been published."
        )

    else:
        messages.success(
            request,
            f"{assessment.title} has been unpublished."
        )

    return redirect(
        "accounts:teacher_class_detail",
        assignment_id=assessment.teacher_assignment.id,
    )


@login_required
def student_dashboard(request):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")

    if request.user.profile.role != "STUDENT":
        return redirect("accounts:login")

    student_profile = request.user.profile.student_profile

    enrollment = StudentEnrollment.objects.filter(
        student=student_profile,
        is_active=True,
    ).select_related(
        "classroom",
        "school_year",
    ).order_by(
        "-school_year__start_date"
    ).first()

    grade_rows = []
    subject_summaries = []

    if enrollment:
        grade_rows, subject_summaries = (
            build_student_term_summary(enrollment)
        )

    from decimal import Decimal as _D2
    _s_payments_usd = _D2("0")
    _s_fees_usd = _D2("0")
    if enrollment:
        for _t2 in enrollment.school_year.terms.all():
            for _fp in FeePayment.objects.filter(student=student_profile, term=_t2):
                if _fp.currency == "USD":
                    _s_payments_usd += _fp.amount
            try:
                _tfs = _t2.fee_schedule
                if _tfs.is_published:
                    _s_fees_usd += _tfs.total_usd
            except TermFee.DoesNotExist:
                pass
    _s_bal = _s_fees_usd - _s_payments_usd

    context = {
        "student": student_profile,
        "enrollment": enrollment,
        "grade_rows": grade_rows,
        "subject_summaries": subject_summaries,
        "total_payments_usd": _s_payments_usd if _s_fees_usd else None,
        "balance_usd": _s_bal if _s_fees_usd else None,
    }

    return render(
        request,
        "accounts/student_dashboard.html",
        context,
    )


@login_required
def student_report_card(request):
    if not hasattr(request.user, "profile") or request.user.profile.role != "STUDENT":
        return redirect("accounts:login")

    student_profile = request.user.profile.student_profile
    enrollment = StudentEnrollment.objects.filter(
        student=student_profile, is_active=True
    ).select_related(
        "classroom", "classroom__form_teacher", "school_year"
    ).order_by("-school_year__start_date").first()

    school_profile = SchoolProfile.objects.first()
    terms = Term.objects.none()
    selected_term = None
    subject_summaries = []
    term_report = None
    overall_average = None
    overall_grade = "-"

    if enrollment:
        terms = Term.objects.filter(school_year=enrollment.school_year).order_by("number")
        requested_term_id = request.GET.get("term")
        if requested_term_id:
            selected_term = terms.filter(id=requested_term_id).first()
        if selected_term is None:
            selected_term = terms.filter(is_active=True).first() or terms.first()

        if selected_term:
            _, subject_summaries = build_student_term_summary(enrollment, selected_term)
            term_report = TermReport.objects.filter(
                student_enrollment=enrollment, term=selected_term
            ).first()
            valid_averages = [x["average"] for x in subject_summaries if x["average"] is not None]
            if valid_averages:
                overall_average = sum(valid_averages) / len(valid_averages)
                overall_grade = get_letter_grade(overall_average)

    return render(request, "accounts/student_report_card.html", {
        "student": student_profile, "enrollment": enrollment, "school": school_profile,
        "terms": terms, "selected_term": selected_term, "subject_summaries": subject_summaries,
        "term_report": term_report, "overall_average": overall_average, "overall_grade": overall_grade,
    })


@login_required
def portal_logout(request):
    logout(request)

    return redirect(
        "accounts:login"
    )


from decimal import Decimal as _Decimal


@login_required
def student_financial(request):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")
    if request.user.profile.role != "STUDENT":
        return redirect("accounts:login")
    student = request.user.profile.student_profile
    enrollments = student.enrollments.select_related("classroom", "school_year").order_by("-school_year__start_date")
    term_rows = []
    total_fees_usd = _Decimal("0")
    total_paid_usd = _Decimal("0")
    total_paid_zwg = _Decimal("0")
    seen = set()
    for enrollment in enrollments:
        for term in enrollment.school_year.terms.all().order_by("number"):
            if term.id in seen:
                continue
            seen.add(term.id)
            try:
                fee_sched = term.fee_schedule
                if not fee_sched.is_published:
                    fee_sched = None
            except TermFee.DoesNotExist:
                fee_sched = None
            fees_usd = fee_sched.total_usd if fee_sched else _Decimal("0")
            payments = FeePayment.objects.filter(student=student, term=term).order_by("payment_date")
            paid_usd = sum((p.amount for p in payments if p.currency == "USD"), _Decimal("0"))
            paid_zwg = sum((p.amount for p in payments if p.currency == "ZWG"), _Decimal("0"))
            total_fees_usd += fees_usd
            total_paid_usd += paid_usd
            total_paid_zwg += paid_zwg
            term_rows.append({
                "term": term,
                "fee_schedule": fee_sched,
                "fees_usd": fees_usd,
                "paid_usd": paid_usd,
                "paid_zwg": paid_zwg,
                "balance_usd": fees_usd - paid_usd,
                "payments": payments,
            })
    context = {
        "student": student,
        "term_rows": term_rows,
        "total_fees_usd": total_fees_usd,
        "total_paid_usd": total_paid_usd,
        "total_paid_zwg": total_paid_zwg,
        "balance_usd": total_fees_usd - total_paid_usd,
    }
    return render(request, "accounts/student_financial.html", context)


@login_required
def fee_schedule(request):
    if not hasattr(request.user, "profile"):
        return redirect("accounts:login")
    fee_schedules = TermFee.objects.filter(is_published=True).select_related(
        "term", "term__school_year"
    ).order_by("-term__school_year__start_date", "term__number")
    return render(request, "accounts/fee_schedule.html", {"fee_schedules": fee_schedules})

