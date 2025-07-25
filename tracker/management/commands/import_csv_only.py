import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from tracker.models import CIHRProject


class Command(BaseCommand):
    help = 'Import CIHR projects from CSV metadata only (without JSON analysis)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default=settings.CIHRPT_CSV_FILE,
            help='CSV file with project metadata'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of projects to import (for testing)'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing projects instead of skipping them'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        limit = options['limit']
        update_existing = options['update_existing']
        
        self.stdout.write(f'Loading CSV metadata from: {csv_file}')
        
        # Load CSV data
        csv_data = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    project_id = row.get('project_id', '').strip()
                    if project_id:
                        csv_data.append(row)
        except Exception as e:
            self.stderr.write(f'Error reading CSV file: {e}')
            return
        
        self.stdout.write(f'Loaded {len(csv_data)} projects from CSV')
        
        if limit:
            csv_data = csv_data[:limit]
            self.stdout.write(f'Limited to {limit} projects for processing')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, row in enumerate(csv_data):
            if i % 50 == 0:
                self.stdout.write(f'Processed {i}/{len(csv_data)} rows...')
            
            try:
                project_id = row.get('project_id', '').strip()
                
                # Check if project already exists
                existing_project = CIHRProject.objects.filter(project_id=project_id).first()
                
                if existing_project and not update_existing:
                    skipped_count += 1
                    continue
                
                # Prepare project data (CSV fields only, JSON fields get defaults)
                project_data = {
                    # Basic information from CSV
                    'project_title': row.get('project_title', ''),
                    'principal_investigators': row.get('principal_investigators', ''),
                    'co_investigators': row.get('co_investigators', ''),
                    'supervisors': row.get('supervisors', ''),
                    'institution_paid': row.get('institution_paid', ''),
                    'research_institution': row.get('research_institution', ''),
                    'department': row.get('department', ''),
                    'program': row.get('program', ''),
                    'competition_year_month': row.get('competition_year_month', ''),
                    'peer_review_committee': row.get('peer_review_committee', ''),
                    'primary_institute': row.get('primary_institute', ''),
                    'primary_theme': row.get('primary_theme', ''),
                    'term_years_months': row.get('term_years_months', ''),
                    'keywords': row.get('keywords', ''),
                    'abstract_summary': row.get('abstract_summary', ''),
                    'cihr_amounts': row.get('cihr_amounts', ''),
                    'cihr_equipment': row.get('cihr_equipment', ''),
                    'external_funding_partners': row.get('external_funding_partners', ''),
                    'external_funding_amounts': row.get('external_funding_amounts', ''),
                }
                
                # Create or update project
                if existing_project:
                    # Update existing project (only CSV fields)
                    for field, value in project_data.items():
                        setattr(existing_project, field, value)
                    existing_project.save()
                    updated_count += 1
                else:
                    # Create new project
                    CIHRProject.objects.create(
                        project_id=project_id,
                        **project_data
                    )
                    created_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stderr.write(f'Error processing project {project_id}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'CSV import completed! Created: {created_count}, Updated: {updated_count}, '
                f'Skipped: {skipped_count}, Errors: {error_count}'
            )
        ) 