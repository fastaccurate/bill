from datetime import datetime
from app.extensions import db, bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group_memberships = db.relationship('GroupMembership', back_populates='user', lazy='dynamic')
    expenses_created = db.relationship('Expense', foreign_keys='Expense.created_by_id', 
                                     back_populates='created_by', lazy='dynamic')
    expense_participations = db.relationship('ExpenseParticipant', back_populates='user', lazy='dynamic')
    settlements_from = db.relationship('Settlement', foreign_keys='Settlement.from_user_id', 
                                     back_populates='from_user', lazy='dynamic')
    settlements_to = db.relationship('Settlement', foreign_keys='Settlement.to_user_id', 
                                   back_populates='to_user', lazy='dynamic')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_tokens(self):
        """Generate JWT access and refresh tokens"""
        access_token = create_access_token(identity=self.id)
        refresh_token = create_refresh_token(identity=self.id)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def get_groups(self):
        """Get all groups user belongs to"""
        return [membership.group for membership in self.group_memberships if membership.is_active]

    def get_balance_with_user(self, other_user_id):
        """Calculate balance between this user and another user across all groups"""
        # This is a simplified version - in production, you'd want to optimize this query
        total_balance = 0

        # Get all expenses involving both users
        from .expense import ExpenseParticipant
        participations = ExpenseParticipant.query.join(Expense).filter(
            db.or_(
                db.and_(ExpenseParticipant.user_id == self.id, 
                       ExpenseParticipant.query.join(Expense).join(ExpenseParticipant, 
                                                                  ExpenseParticipant.expense_id == Expense.id).filter(
                           ExpenseParticipant.user_id == other_user_id).exists()),
                db.and_(ExpenseParticipant.user_id == other_user_id,
                       ExpenseParticipant.query.join(Expense).join(ExpenseParticipant,
                                                                  ExpenseParticipant.expense_id == Expense.id).filter(
                           ExpenseParticipant.user_id == self.id).exists())
            )
        ).all()

        # Calculate net balance (simplified - would need more complex calculation for real app)
        for participation in participations:
            if participation.user_id == self.id:
                total_balance += participation.amount_owed
            else:
                total_balance -= participation.amount_owed

        return total_balance

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'phone_number': self.phone_number,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_sensitive:
            data['groups'] = [group.to_dict() for group in self.get_groups()]

        return data

    def __repr__(self):
        return f'<User {self.email}>'
