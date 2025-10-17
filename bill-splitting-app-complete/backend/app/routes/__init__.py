"""
API Routes for Bill Splitting App

This package contains all the Flask blueprints for different API endpoints:
- auth: User authentication and registration
- groups: Group management and membership
- expenses: Expense tracking and splitting
- reminders: SMS payment reminders
"""

from .auth import auth_bp
from .groups import groups_bp
from .expenses import expenses_bp
from .reminders import reminders_bp

__all__ = ['auth_bp', 'groups_bp', 'expenses_bp', 'reminders_bp']
