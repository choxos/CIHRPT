import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from tracker.models import CIHRProject


class Command(BaseCommand):
    help = 'Update existing CIHR projects with JSON analysis data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-dir',
            type=str,
            default=settings.CIHRPT_DATA_DIR,
            help='Directory containing JSON files'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of projects to update (for testing)'
        )
        parser.add_argument(
            '--project-id',
            type=str,
            help='Update specific project by ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if JSON analysis already exists'
        )

    def handle(self, *args, **options):
        json_dir = options['json_dir']
        limit = options['limit']
        project_id = options['project_id']
        force = options['force']
        
        self.stdout.write(f'Processing JSON files from: {json_dir}')
        
        # Get list of JSON files
        try:
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        except Exception as e:
            self.stderr.write(f'Error accessing JSON directory: {e}')
            return
        
        # Filter by specific project if requested
        if project_id:
            json_files = [f for f in json_files if f == f'project_{project_id}.json']
            if not json_files:
                self.stderr.write(f'No JSON file found for project {project_id}')
                return
        
        if limit:
            json_files = json_files[:limit]
        
        self.stdout.write(f'Found {len(json_files)} JSON files to process')
        
        updated_count = 0
        skipped_count = 0
        not_found_count = 0
        error_count = 0
        
        for i, filename in enumerate(json_files):
            if i % 50 == 0:
                self.stdout.write(f'Processed {i}/{len(json_files)} files...')
            
            try:
                # Extract project ID from filename
                file_project_id = filename.replace('project_', '').replace('.json', '')
                
                # Find existing project
                try:
                    project = CIHRProject.objects.get(project_id=file_project_id)
                except CIHRProject.DoesNotExist:
                    not_found_count += 1
                    self.stdout.write(f'Project {file_project_id} not found in database, skipping...')
                    continue
                
                # Check if analysis already exists (unless force is used)
                if not force and project.broad_study_type != "unclear":
                    skipped_count += 1
                    continue
                
                # Load JSON data
                json_path = os.path.join(json_dir, filename)
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Update project with JSON analysis fields
                json_fields = {
                    # Study Design Classification
                    'broad_study_type': json_data.get('broad_study_type', 'unclear'),
                    'narrow_study_type': json_data.get('narrow_study_type', ''),
                    'trial_phase': json_data.get('trial_phase', 'N/A'),
                    'observational_timeframe': json_data.get('observational_timeframe', 'N/A'),
                    'justification': json_data.get('justification', ''),
                    
                    # Data and Methodology
                    'data_type': json_data.get('data_type', 'unclear'),
                    'ipd_used': json_data.get('ipd_used', 'unclear'),
                    'novelty_statement': json_data.get('novelty_statement', ''),
                    'replication_study': json_data.get('replication_study', 'no'),
                    
                    # Population Characteristics
                    'target_population_size': json_data.get('target_population_size', ''),
                    'age_range': json_data.get('age_range', 'unclear'),
                    'gender_focus': json_data.get('gender_focus', 'unclear'),
                    'vulnerable_populations': json_data.get('vulnerable_populations', 'no'),
                    'rare_disease': json_data.get('rare_disease', 'no'),
                    'population_description': json_data.get('population_description', ''),
                    
                    # Intervention Details
                    'intervention_category': json_data.get('intervention_category', ''),
                    'intervention_name': json_data.get('intervention_name', ''),
                    'control_type': json_data.get('control_type', ''),
                    'dose_response': json_data.get('dose_response', 'no'),
                    'combination_therapy': json_data.get('combination_therapy', 'no'),
                    'personalized_medicine': json_data.get('personalized_medicine', 'no'),
                    
                    # Outcomes
                    'primary_outcome': json_data.get('primary_outcome', ''),
                    'primary_outcome_type': json_data.get('primary_outcome_type', 'unclear'),
                    'safety_focus': json_data.get('safety_focus', 'no'),
                    'quality_of_life': json_data.get('quality_of_life', 'no'),
                    'biomarker_endpoints': json_data.get('biomarker_endpoints', 'no'),
                    'time_to_event': json_data.get('time_to_event', 'no'),
                    'composite_endpoint': json_data.get('composite_endpoint', 'no'),
                    
                    # Technology and Innovation
                    'ai_machine_learning': json_data.get('ai_machine_learning', 'no'),
                    'digital_health': json_data.get('digital_health', 'no'),
                    'telemedicine': json_data.get('telemedicine', 'no'),
                    'wearable_technology': json_data.get('wearable_technology', 'no'),
                    'big_data_analytics': json_data.get('big_data_analytics', 'no'),
                    'blockchain': json_data.get('blockchain', 'no'),
                    
                    # Health Economics
                    'cost_effectiveness': json_data.get('cost_effectiveness', 'no'),
                    'budget_impact': json_data.get('budget_impact', 'no'),
                    'health_technology_assessment': json_data.get('health_technology_assessment', 'no'),
                    'resource_utilization': json_data.get('resource_utilization', 'no'),
                    'productivity_outcomes': json_data.get('productivity_outcomes', 'no'),
                    
                    # Implementation and Translation
                    'implementation_science': json_data.get('implementation_science', 'no'),
                    'policy_evaluation': json_data.get('policy_evaluation', 'no'),
                    'health_system_integration': json_data.get('health_system_integration', 'no'),
                    'scalability_assessment': json_data.get('scalability_assessment', 'no'),
                    'barrier_identification': json_data.get('barrier_identification', 'no'),
                    
                    # Statistical and Analytical Methods
                    'adaptive_design': json_data.get('adaptive_design', 'no'),
                    'bayesian_methods': json_data.get('bayesian_methods', 'no'),
                    'machine_learning_analysis': json_data.get('machine_learning_analysis', 'no'),
                    'novel_biostatistics': json_data.get('novel_biostatistics', 'no'),
                    
                    # Evidence and Engagement
                    'patient_reported_outcomes': json_data.get('patient_reported_outcomes', 'no'),
                    'real_world_evidence': json_data.get('real_world_evidence', 'no'),
                    'industry_partnership': json_data.get('industry_partnership', 'no'),
                    'patient_engagement': json_data.get('patient_engagement', 'no'),
                    'community_based': json_data.get('community_based', 'no'),
                    
                    # Collaboration and Ethics
                    'indigenous_collaboration': json_data.get('indigenous_collaboration', 'no'),
                    'international_collaboration': json_data.get('international_collaboration', 'no'),
                    'international_network': json_data.get('international_network', 'no'),
                    'regulatory_pathway': json_data.get('regulatory_pathway', 'no'),
                    'ethics_focus': json_data.get('ethics_focus', 'no'),
                    'consent_innovation': json_data.get('consent_innovation', 'no'),
                    'data_sharing': json_data.get('data_sharing', 'no'),
                    
                    # Clinical and Research Context
                    'therapeutic_area': json_data.get('therapeutic_area', ''),
                    'disease_stage': json_data.get('disease_stage', 'unclear'),
                    'comorbidity_focus': json_data.get('comorbidity_focus', 'no'),
                    'pandemic_related': json_data.get('pandemic_related', 'no'),
                    'environmental_health': json_data.get('environmental_health', 'no'),
                    'social_determinants': json_data.get('social_determinants', 'no'),
                    'health_equity': json_data.get('health_equity', 'no'),
                    'climate_health': json_data.get('climate_health', 'no'),
                    
                    # Study Design and Conduct
                    'urban_rural': json_data.get('urban_rural', 'unclear'),
                    'biobank_use': json_data.get('biobank_use', 'no'),
                    'registry_linkage': json_data.get('registry_linkage', 'no'),
                    'cohort_establishment': json_data.get('cohort_establishment', 'no'),
                    'platform_trial': json_data.get('platform_trial', 'no'),
                    'study_duration': json_data.get('study_duration', 'unclear'),
                    'multicenter': json_data.get('multicenter', 'no'),
                    'healthcare_setting': json_data.get('healthcare_setting', 'unclear'),
                    
                    # Additional Classification
                    'disease_area': json_data.get('disease_area', ''),
                    'methodology_innovation': json_data.get('methodology_innovation', ''),
                    'knowledge_translation_focus': json_data.get('knowledge_translation_focus', 'no'),
                    'equity_considerations': json_data.get('equity_considerations', 'no'),
                }
                
                # Update the project
                for field, value in json_fields.items():
                    setattr(project, field, value)
                
                project.save()
                updated_count += 1
                
            except Exception as e:
                error_count += 1
                self.stderr.write(f'Error processing {filename}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'JSON update completed! Updated: {updated_count}, Skipped: {skipped_count}, '
                f'Not found: {not_found_count}, Errors: {error_count}'
            )
        ) 