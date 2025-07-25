from django.db import models
from django.urls import reverse
from django.utils import timezone
import json


class CIHRProject(models.Model):
    """Model for CIHR projects combining JSON analysis and CSV metadata"""
    
    # Basic identifiers and metadata from CSV
    project_id = models.CharField(max_length=50, unique=True, help_text="CIHR project unique identifier")
    project_title = models.TextField(help_text="Title of the project")
    
    # Principal and co-investigators
    principal_investigators = models.TextField(blank=True, null=True, help_text="Principal investigators")
    co_investigators = models.TextField(blank=True, null=True, help_text="Co-investigators")
    supervisors = models.TextField(blank=True, null=True, help_text="Supervisors")
    
    # Institution information
    institution_paid = models.CharField(max_length=500, blank=True, null=True, help_text="Institution receiving payment")
    research_institution = models.CharField(max_length=500, blank=True, null=True, help_text="Research institution")
    department = models.CharField(max_length=300, blank=True, null=True, help_text="Department")
    
    # Funding information
    program = models.CharField(max_length=300, blank=True, null=True, help_text="CIHR program")
    competition_year_month = models.CharField(max_length=10, blank=True, null=True, help_text="Competition year/month")
    peer_review_committee = models.CharField(max_length=300, blank=True, null=True, help_text="Peer review committee")
    primary_institute = models.CharField(max_length=300, blank=True, null=True, help_text="Primary CIHR institute")
    primary_theme = models.CharField(max_length=300, blank=True, null=True, help_text="Primary research theme")
    term_years_months = models.CharField(max_length=50, blank=True, null=True, help_text="Term duration")
    
    # Research content
    keywords = models.TextField(blank=True, null=True, help_text="Research keywords")
    abstract_summary = models.TextField(blank=True, null=True, help_text="Abstract summary")
    
    # Financial information
    cihr_amounts = models.CharField(max_length=100, blank=True, null=True, help_text="CIHR funding amounts")
    cihr_equipment = models.CharField(max_length=100, blank=True, null=True, help_text="CIHR equipment funding")
    external_funding_partners = models.TextField(blank=True, null=True, help_text="External funding partners")
    external_funding_amounts = models.CharField(max_length=100, blank=True, null=True, help_text="External funding amounts")
    
    # Study Design Classification (from JSON analysis)
    broad_study_type = models.CharField(max_length=50, default="unclear", 
                                       choices=[
                                           ('trial', 'Trial'),
                                           ('observational', 'Observational'),
                                           ('evidence_synthesis', 'Evidence Synthesis'),
                                           ('other', 'Other'),
                                           ('unclear', 'Unclear')
                                       ])
    narrow_study_type = models.CharField(max_length=100, blank=True, null=True)
    trial_phase = models.CharField(max_length=10, default="N/A")
    observational_timeframe = models.CharField(max_length=50, default="N/A")
    justification = models.TextField(blank=True, null=True)
    
    # Data and Methodology
    data_type = models.CharField(max_length=20, default="unclear",
                                choices=[
                                    ('canadian', 'Canadian'),
                                    ('global', 'Global'),
                                    ('mixed', 'Mixed'),
                                    ('unclear', 'Unclear')
                                ])
    ipd_used = models.CharField(max_length=20, default="unclear")
    novelty_statement = models.TextField(blank=True, null=True)
    replication_study = models.CharField(max_length=10, default="no")
    
    # Population Characteristics
    target_population_size = models.CharField(max_length=50, blank=True, null=True)
    age_range = models.CharField(max_length=50, default="unclear")
    gender_focus = models.CharField(max_length=20, default="unclear")
    vulnerable_populations = models.CharField(max_length=10, default="no")
    rare_disease = models.CharField(max_length=10, default="no")
    population_description = models.TextField(blank=True, null=True)
    
    # Intervention Details
    intervention_category = models.CharField(max_length=50, blank=True, null=True)
    intervention_name = models.CharField(max_length=200, blank=True, null=True)
    control_type = models.CharField(max_length=50, blank=True, null=True)
    dose_response = models.CharField(max_length=10, default="no")
    combination_therapy = models.CharField(max_length=10, default="no")
    personalized_medicine = models.CharField(max_length=10, default="no")
    
    # Outcomes
    primary_outcome = models.TextField(blank=True, null=True)
    primary_outcome_type = models.CharField(max_length=50, default="unclear")
    safety_focus = models.CharField(max_length=10, default="no")
    quality_of_life = models.CharField(max_length=10, default="no")
    biomarker_endpoints = models.CharField(max_length=10, default="no")
    time_to_event = models.CharField(max_length=10, default="no")
    composite_endpoint = models.CharField(max_length=10, default="no")
    
    # Technology and Innovation
    ai_machine_learning = models.CharField(max_length=10, default="no")
    digital_health = models.CharField(max_length=10, default="no")
    telemedicine = models.CharField(max_length=10, default="no")
    wearable_technology = models.CharField(max_length=10, default="no")
    big_data_analytics = models.CharField(max_length=10, default="no")
    blockchain = models.CharField(max_length=10, default="no")
    
    # Health Economics
    cost_effectiveness = models.CharField(max_length=10, default="no")
    budget_impact = models.CharField(max_length=10, default="no")
    health_technology_assessment = models.CharField(max_length=10, default="no")
    resource_utilization = models.CharField(max_length=10, default="no")
    productivity_outcomes = models.CharField(max_length=10, default="no")
    
    # Implementation and Translation
    implementation_science = models.CharField(max_length=10, default="no")
    policy_evaluation = models.CharField(max_length=10, default="no")
    health_system_integration = models.CharField(max_length=10, default="no")
    scalability_assessment = models.CharField(max_length=10, default="no")
    barrier_identification = models.CharField(max_length=10, default="no")
    
    # Statistical and Analytical Methods
    adaptive_design = models.CharField(max_length=10, default="no")
    bayesian_methods = models.CharField(max_length=10, default="no")
    machine_learning_analysis = models.CharField(max_length=10, default="no")
    novel_biostatistics = models.CharField(max_length=10, default="no")
    
    # Evidence and Engagement
    patient_reported_outcomes = models.CharField(max_length=10, default="no")
    real_world_evidence = models.CharField(max_length=10, default="no")
    industry_partnership = models.CharField(max_length=10, default="no")
    patient_engagement = models.CharField(max_length=10, default="no")
    community_based = models.CharField(max_length=10, default="no")
    
    # Collaboration and Ethics
    indigenous_collaboration = models.CharField(max_length=10, default="no")
    international_collaboration = models.CharField(max_length=10, default="no")
    international_network = models.CharField(max_length=10, default="no")
    regulatory_pathway = models.CharField(max_length=10, default="no")
    ethics_focus = models.CharField(max_length=10, default="no")
    consent_innovation = models.CharField(max_length=10, default="no")
    data_sharing = models.CharField(max_length=10, default="no")
    
    # Clinical and Research Context
    therapeutic_area = models.CharField(max_length=100, blank=True, null=True)
    disease_stage = models.CharField(max_length=50, default="unclear")
    comorbidity_focus = models.CharField(max_length=10, default="no")
    pandemic_related = models.CharField(max_length=10, default="no")
    environmental_health = models.CharField(max_length=10, default="no")
    social_determinants = models.CharField(max_length=10, default="no")
    health_equity = models.CharField(max_length=10, default="no")
    climate_health = models.CharField(max_length=10, default="no")
    
    # Study Design and Conduct
    urban_rural = models.CharField(max_length=20, default="unclear")
    biobank_use = models.CharField(max_length=10, default="no")
    registry_linkage = models.CharField(max_length=10, default="no")
    cohort_establishment = models.CharField(max_length=10, default="no")
    platform_trial = models.CharField(max_length=10, default="no")
    study_duration = models.CharField(max_length=20, default="unclear")
    multicenter = models.CharField(max_length=10, default="no")
    healthcare_setting = models.CharField(max_length=50, default="unclear")
    
    # Additional Classification
    disease_area = models.TextField(blank=True, null=True)
    methodology_innovation = models.TextField(blank=True, null=True)
    knowledge_translation_focus = models.CharField(max_length=10, default="no")
    equity_considerations = models.CharField(max_length=10, default="no")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cihr_projects'
        ordering = ['-project_id']
        indexes = [
            models.Index(fields=['project_id']),
            models.Index(fields=['broad_study_type']),
            models.Index(fields=['therapeutic_area']),
            models.Index(fields=['primary_institute']),
            models.Index(fields=['primary_theme']),
            models.Index(fields=['competition_year_month']),
        ]
    
    def __str__(self):
        return f"{self.project_id}: {self.project_title[:100]}..." if len(self.project_title) > 100 else f"{self.project_id}: {self.project_title}"
    
    def get_absolute_url(self):
        return reverse('tracker:project_detail', kwargs={'project_id': self.project_id})
    
    def get_yes_fields(self):
        """Return only fields with 'yes' values for the detail view"""
        yes_fields = {}
        field_mapping = {
            # Technology and Innovation
            'ai_machine_learning': 'AI/Machine Learning',
            'digital_health': 'Digital Health',
            'telemedicine': 'Telemedicine',
            'wearable_technology': 'Wearable Technology',
            'big_data_analytics': 'Big Data Analytics',
            'blockchain': 'Blockchain',
            
            # Health Economics
            'cost_effectiveness': 'Cost Effectiveness',
            'budget_impact': 'Budget Impact',
            'health_technology_assessment': 'Health Technology Assessment',
            'resource_utilization': 'Resource Utilization',
            'productivity_outcomes': 'Productivity Outcomes',
            
            # Implementation and Translation
            'implementation_science': 'Implementation Science',
            'policy_evaluation': 'Policy Evaluation',
            'health_system_integration': 'Health System Integration',
            'scalability_assessment': 'Scalability Assessment',
            'barrier_identification': 'Barrier Identification',
            
            # Statistical and Analytical Methods
            'adaptive_design': 'Adaptive Design',
            'bayesian_methods': 'Bayesian Methods',
            'machine_learning_analysis': 'Machine Learning Analysis',
            'novel_biostatistics': 'Novel Biostatistics',
            
            # Evidence and Engagement
            'patient_reported_outcomes': 'Patient Reported Outcomes',
            'real_world_evidence': 'Real World Evidence',
            'industry_partnership': 'Industry Partnership',
            'patient_engagement': 'Patient Engagement',
            'community_based': 'Community Based',
            
            # Collaboration and Ethics
            'indigenous_collaboration': 'Indigenous Collaboration',
            'international_collaboration': 'International Collaboration',
            'international_network': 'International Network',
            'regulatory_pathway': 'Regulatory Pathway',
            'ethics_focus': 'Ethics Focus',
            'consent_innovation': 'Consent Innovation',
            'data_sharing': 'Data Sharing',
            
            # Clinical and Research Context
            'comorbidity_focus': 'Comorbidity Focus',
            'pandemic_related': 'Pandemic Related',
            'environmental_health': 'Environmental Health',
            'social_determinants': 'Social Determinants',
            'health_equity': 'Health Equity',
            'climate_health': 'Climate Health',
            
            # Study Design and Conduct
            'biobank_use': 'Biobank Use',
            'registry_linkage': 'Registry Linkage',
            'cohort_establishment': 'Cohort Establishment',
            'platform_trial': 'Platform Trial',
            'multicenter': 'Multicenter',
            'knowledge_translation_focus': 'Knowledge Translation Focus',
            'equity_considerations': 'Equity Considerations',
            
            # Outcomes
            'safety_focus': 'Safety Focus',
            'quality_of_life': 'Quality of Life',
            'biomarker_endpoints': 'Biomarker Endpoints',
            'time_to_event': 'Time to Event',
            'composite_endpoint': 'Composite Endpoint',
            
            # Population and Design
            'vulnerable_populations': 'Vulnerable Populations',
            'rare_disease': 'Rare Disease',
            'dose_response': 'Dose Response',
            'combination_therapy': 'Combination Therapy',
            'personalized_medicine': 'Personalized Medicine',
        }
        
        for field_name, display_name in field_mapping.items():
            field_value = getattr(self, field_name, None)
            if field_value == 'yes':
                yes_fields[display_name] = field_value
                
        return yes_fields
    
    @property
    def funding_amount_display(self):
        """Format funding amount for display"""
        if self.cihr_amounts:
            return self.cihr_amounts.replace('"', '').replace('$', '').replace(',', '')
        return None
    
    @property
    def competition_year(self):
        """Extract year from competition_year_month"""
        if self.competition_year_month:
            return self.competition_year_month[:4]
        return None
