# -*- coding: utf-8 -*-
"""This module contains functions to manage submission error codes."""
from django import template
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.filter
def error_code_to_str(code):
    """Transform the given error code
    into a human readable message if possible."""
    message = code
    if code == 0:
        message = _("Ok")
    elif code == 6:
        message = _("Abnormal program termination")
    elif code == 8:
        message = _("Floating point exception")
    elif code == 9:
        message = _("Timelimit")
    elif code == 11:
        message = _("Segmentation fault")
    elif code == 127:
        message = _("Compilation error")
    return message
