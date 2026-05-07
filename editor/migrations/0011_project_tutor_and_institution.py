# Generated migration for tutor-owned Arduino projects (same model as student).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_project_institution(apps, schema_editor):
    Project = apps.get_model('editor', 'Project')
    Student = apps.get_model('editor', 'Student')
    StudentGroup = apps.get_model('editor', 'StudentGroup')
    Course = apps.get_model('editor', 'Course')
    for p in Project.objects.filter(institution_id__isnull=True).iterator():
        if not p.student_id:
            continue
        try:
            s = Student.objects.get(pk=p.student_id)
        except Student.DoesNotExist:
            continue
        inst_id = s.institution_id
        if not inst_id and s.group_id:
            try:
                g = StudentGroup.objects.get(pk=s.group_id)
                inst_id = g.institution_id
            except StudentGroup.DoesNotExist:
                pass
        if not inst_id and s.course_id:
            try:
                c = Course.objects.get(pk=s.course_id)
                inst_id = c.institution_id
            except Course.DoesNotExist:
                pass
        if inst_id:
            Project.objects.filter(pk=p.pk).update(institution_id=inst_id)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('editor', '0010_sqlite_uuid_compat'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='institution',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='arduino_projects',
                to='editor.institution',
                verbose_name='Institución',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='tutor_owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tutor_projects_saved',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Tutor (propietario)',
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='student',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='projects',
                to='editor.student',
                verbose_name='Estudiante',
            ),
        ),
        migrations.RunPython(backfill_project_institution, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(student__isnull=False, tutor_owner__isnull=True)
                    | models.Q(student__isnull=True, tutor_owner__isnull=False)
                ),
                name='project_student_xor_tutor_owner',
            ),
        ),
    ]
