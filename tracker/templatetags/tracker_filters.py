from django import template
from django.utils.safestring import mark_safe
from urllib.parse import quote

register = template.Library()

@register.filter
def split(value, delimiter):
    """Split a string by delimiter and return a list"""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)

@register.filter
def pubmed_links(value):
    """Convert a semicolon-separated list of names to PubMed search links"""
    if not value:
        return ""
    
    names = [name.strip() for name in value.split(';') if name.strip()]
    if not names:
        return ""
    
    links = []
    for name in names:
        # Format: "LastName, FirstName" for PubMed search
        encoded_name = quote(f'"{name}"[Author]')
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_name}"
        links.append(f'<a href="{pubmed_url}" target="_blank" class="pubmed-link" title="Search {name} on PubMed">{name}</a>')
    
    return mark_safe('; '.join(links))

@register.filter
def single_pubmed_link(value):
    """Convert a single name to PubMed search link"""
    if not value:
        return ""
    
    name = value.strip()
    if not name:
        return ""
    
    encoded_name = quote(f'"{name}"[Author]')
    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_name}"
    return mark_safe(f'<a href="{pubmed_url}" target="_blank" class="pubmed-link" title="Search {name} on PubMed">{name}</a>') 