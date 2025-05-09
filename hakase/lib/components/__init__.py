"""
Components for aspects of Hakase's operation.

Components are what Discord calls the menus, select boxes, buttons,
and other things associated with an application command. All of the
things defined here serve that purpose in some way or another.
"""
from .pagination import pagify
from .validation import Validation, validate, lint_before_exc
from .onboarding import WelcomeView, WelcomeModal


__all__ = [
    "Validation",
    "validate",
    "lint_before_exc",
    "pagify",
    "WelcomeView",
    "WelcomeModal"
]
