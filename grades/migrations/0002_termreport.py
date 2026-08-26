from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("grades", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="TermReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("days_school_open", models.PositiveIntegerField(default=0)),
                ("days_present", models.PositiveIntegerField(default=0)),
                ("times_late", models.PositiveIntegerField(default=0)),
                ("form_teacher_comment", models.TextField(blank=True)),
                ("principal_comment", models.TextField(blank=True)),
                ("promotion_status", models.CharField(choices=[("PENDING", "Pending"), ("PROMOTED", "Promoted"), ("NOT_PROMOTED", "Not Promoted")], default="PENDING", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("student_enrollment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="term_reports", to="academics.studentenrollment")),
                ("term", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_reports", to="academics.term")),
            ],
            options={"ordering": ["term__number", "student_enrollment__student__last_name"]},
        ),
        migrations.AddConstraint(
            model_name="termreport",
            constraint=models.UniqueConstraint(fields=("student_enrollment", "term"), name="unique_student_term_report"),
        ),
    ]
