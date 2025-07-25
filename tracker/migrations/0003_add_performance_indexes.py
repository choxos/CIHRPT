# Generated by Django 5.2.4 on 2025-07-25 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0002_alter_cihrproject_adaptive_design_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["research_institution"], name="cihr_projec_researc_1d0a7e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["broad_study_type", "therapeutic_area"],
                name="cihr_projec_broad_s_34ea64_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["primary_institute", "competition_year_month"],
                name="cihr_projec_primary_19b0f1_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["cihr_amounts"], name="cihr_projec_cihr_am_ab393e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["project_title"], name="cihr_projec_project_55f32c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["principal_investigators"],
                name="cihr_projec_princip_c7c972_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cihrproject",
            index=models.Index(
                fields=["competition_year_month", "broad_study_type"],
                name="cihr_projec_competi_29e1f2_idx",
            ),
        ),
    ]
