import json
import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from tracker.models import CIHRProject


class Command(BaseCommand):
    help = 'Import CIHR projects from JSON files and CSV metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-dir',
            type=str,
            default=settings.CIHRPT_DATA_DIR,
            help='Directory containing JSON files'
        )
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

    def handle(self, *args, **options):
        json_dir = options['json_dir']
        csv_file = options['csv_file']
        limit = options['limit']
        
        self.stdout.write(f'Loading CSV metadata from: {csv_file}')
        
        # First, load CSV data into a dictionary
        csv_data = {}
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    project_id = row.get('project_id', '').strip()
                    if project_id:
                        csv_data[project_id] = row
        except Exception as e:
            self.stderr.write(f'Error reading CSV file: {e}')
            return
        
        self.stdout.write(f'Loaded {len(csv_data)} projects from CSV')
        
        # Now process JSON files
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        if limit:
            json_files = json_files[:limit]
        
        self.stdout.write(f'Processing {len(json_files)} JSON files from: {json_dir}')
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for i, filename in enumerate(json_files):
            if i % 50 == 0:
                self.stdout.write(f'Processed {i}/{len(json_files)} files...')
            
            try:
                # Extract project ID from filename
                project_id = filename.replace('project_', '').replace('.json', '')
                
                # Load JSON data
                json_path = os.path.join(json_dir, filename)
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Get corresponding CSV data
                csv_row = csv_data.get(project_id, {})
                
                # Create or update project
                project, created = CIHRProject.objects.update_or_create(
                    project_id=project_id,
                    defaults={
                        # Basic information from CSV
                        'project_title': csv_row.get('project_title', ''),
                        'principal_investigators': csv_row.get('principal_investigators', ''),
                        'co_investigators': csv_row.get('co_investigators', ''),
                        'supervisors': csv_row.get('supervisors', ''),
                        'institution_paid': csv_row.get('institution_paid', ''),
                        'research_institution': csv_row.get('research_institution', ''),
                        'department': csv_row.get('department', ''),
                        'program': csv_row.get('program', ''),
                        'competition_year_month': csv_row.get('competition_year_month', ''),
                        'peer_review_committee': csv_row.get('peer_review_committee', ''),
                        'primary_institute': csv_row.get('primary_institute', ''),
                        'primary_theme': csv_row.get('primary_theme', ''),
                        'term_years_months': csv_row.get('term_years_months', ''),
                        'keywords': csv_row.get('keywords', ''),
                        'abstract_summary': csv_row.get('abstract_summary', ''),
                        'cihr_amounts': csv_row.get('cihr_amounts', ''),
                        'cihr_equipment': csv_row.get('cihr_equipment', ''),
                        'external_funding_partners': csv_row.get('external_funding_partners', ''),
                        'external_funding_amounts': csv_row.get('external_funding_amounts', ''),
                        
                        # Analysis fields from JSON
                        'broad_study_type': json_data.get('broad_study_type', 'unclear'),
                        'narrow_study_type': json_data.get('narrow_study_type', ''),
                        'trial_phase': json_data.get('trial_phase', 'N/A'),
                        'observational_timeframe': json_data.get('observational_timeframe', 'N/A'),
                        'justification': json_data.get('justification', ''),
                        'data_type': json_data.get('data_type', 'unclear'),
                        'ipd_used': json_data.get('ipd_used', 'unclear'),
                        'novelty_statement': json_data.get('novelty_statement', ''),
                        'replication_study': json_data.get('replication_study', 'no'),
                        'target_population_size': json_data.get('target_population_size', ''),
                        'age_range': json_data.get('age_range', 'unclear'),
                        'gender_focus': json_data.get('gender_focus', 'unclear'),
                        'vulnerable_populations': json_data.get('vulnerable_populations', 'no'),
                        'rare_disease': json_data.get('rare_disease', 'no'),
                        'population_description': json_data.get('population_description', ''),
                        'intervention_category': json_data.get('intervention_category', ''),
                        'intervention_name': json_data.get('intervention_name', ''),
                        'control_type': json_data.get('control_type', ''),
                        'dose_response': json_data.get('dose_response', 'no'),
                        'combination_therapy': json_data.get('combination_therapy', 'no'),
                        'personalized_medicine': json_data.get('personalized_medicine', 'no'),
                        'primary_outcome': json_data.get('primary_outcome', ''),
                        'primary_outcome_type': json_data.get('primary_outcome_type', 'unclear'),
                        'safety_focus': json_data.get('safety_focus', 'no'),
                        'quality_of_life': json_data.get('quality_of_life', 'no'),
                        'biomarker_endpoints': json_data.get('biomarker_endpoints', 'no'),
                        'time_to_event': json_data.get('time_to_event', 'no'),
                        'composite_endpoint': json_data.get('composite_endpoint', 'no'),
                        'ai_machine_learning': json_data.get('ai_machine_learning', 'no'),
                        'digital_health': json_data.get('digital_health', 'no'),
                        'telemedicine': json_data.get('telemedicine', 'no'),
                        'wearable_technology': json_data.get('wearable_technology', 'no'),
                        'big_data_analytics': json_data.get('big_data_analytics', 'no'),
                        'blockchain': json_data.get('blockchain', 'no'),
                        'cost_effectiveness': json_data.get('cost_effectiveness', 'no'),
                        'budget_impact': json_data.get('budget_impact', 'no'),
                        'health_technology_assessment': json_data.get('health_technology_assessment', 'no'),
                        'resource_utilization': json_data.get('resource_utilization', 'no'),
                        'productivity_outcomes': json_data.get('productivity_outcomes', 'no'),
                        'implementation_science': json_data.get('implementation_science', 'no'),
                        'policy_evaluation': json_data.get('policy_evaluation', 'no'),
                        'health_system_integration': json_data.get('health_system_integration', 'no'),
                        'scalability_assessment': json_data.get('scalability_assessment', 'no'),
                        'barrier_identification': json_data.get('barrier_identification', 'no'),
                        'adaptive_design': json_data.get('adaptive_design', 'no'),
                        'bayesian_methods': json_data.get('bayesian_methods', 'no'),
                        'machine_learning_analysis': json_data.get('machine_learning_analysis', 'no'),
                        'novel_biostatistics': json_data.get('novel_biostatistics', 'no'),
                        'patient_reported_outcomes': json_data.get('patient_reported_outcomes', 'no'),
                        'real_world_evidence': json_data.get('real_world_evidence', 'no'),
                        'industry_partnership': json_data.get('industry_partnership', 'no'),
                        'patient_engagement': json_data.get('patient_engagement', 'no'),
                        'community_based': json_data.get('community_based', 'no'),
                        'indigenous_collaboration': json_data.get('indigenous_collaboration', 'no'),
                        'international_collaboration': json_data.get('international_collaboration', 'no'),
                        'international_network': json_data.get('international_network', 'no'),
                        'regulatory_pathway': json_data.get('regulatory_pathway', 'no'),
                        'ethics_focus': json_data.get('ethics_focus', 'no'),
                        'consent_innovation': json_data.get('consent_innovation', 'no'),
                        'data_sharing': json_data.get('data_sharing', 'no'),
                        'therapeutic_area': json_data.get('therapeutic_area', ''),
                        'disease_stage': json_data.get('disease_stage', 'unclear'),
                        'comorbidity_focus': json_data.get('comorbidity_focus', 'no'),
                        'pandemic_related': json_data.get('pandemic_related', 'no'),
                        'environmental_health': json_data.get('environmental_health', 'no'),
                        'social_determinants': json_data.get('social_determinants', 'no'),
                        'health_equity': json_data.get('health_equity', 'no'),
                        'climate_health': json_data.get('climate_health', 'no'),
                        'urban_rural': json_data.get('urban_rural', 'unclear'),
                        'biobank_use': json_data.get('biobank_use', 'no'),
                        'registry_linkage': json_data.get('registry_linkage', 'no'),
                        'cohort_establishment': json_data.get('cohort_establishment', 'no'),
                        'platform_trial': json_data.get('platform_trial', 'no'),
                        'study_duration': json_data.get('study_duration', 'unclear'),
                        'multicenter': json_data.get('multicenter', 'no'),
                        'healthcare_setting': json_data.get('healthcare_setting', 'unclear'),
                        'disease_area': json_data.get('disease_area', ''),
                        'methodology_innovation': json_data.get('methodology_innovation', ''),
                        'knowledge_translation_focus': json_data.get('knowledge_translation_focus', 'no'),
                        'equity_considerations': json_data.get('equity_considerations', 'no'),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stderr.write(f'Error processing {filename}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed! Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
            )
        ) 