from django import template
from core.models import RegistrationSettings

register = template.Library()

@register.simple_tag
def get_registration_status():
    return RegistrationSettings.get_settings()
