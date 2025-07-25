from rest_framework import serializers
from .models import CIHRProject


class CIHRProjectSerializer(serializers.ModelSerializer):
    """Serializer for CIHR projects API"""
    
    competition_year = serializers.SerializerMethodField()
    funding_amount_display = serializers.SerializerMethodField() 
    yes_fields = serializers.SerializerMethodField()
    
    class Meta:
        model = CIHRProject
        fields = '__all__'
        
    def get_competition_year(self, obj):
        return obj.competition_year
        
    def get_funding_amount_display(self, obj):
        return obj.funding_amount_display
        
    def get_yes_fields(self, obj):
        return obj.get_yes_fields()


class CIHRProjectListSerializer(serializers.ModelSerializer):
    """Simplified serializer for project list views"""
    
    competition_year = serializers.SerializerMethodField()
    funding_amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CIHRProject
        fields = [
            'project_id', 'project_title', 'principal_investigators',
            'broad_study_type', 'therapeutic_area', 'primary_institute',
            'primary_theme', 'competition_year_month', 'competition_year',
            'cihr_amounts', 'funding_amount_display', 'abstract_summary'
        ]
        
    def get_competition_year(self, obj):
        return obj.competition_year
        
    def get_funding_amount_display(self, obj):
        return obj.funding_amount_display 