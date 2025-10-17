from datetime import datetime
from app.extensions import db

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by = db.relationship('User', backref='groups_created')
    memberships = db.relationship('GroupMembership', back_populates='group', lazy='dynamic', 
                                 cascade='all, delete-orphan')
    expenses = db.relationship('Expense', back_populates='group', lazy='dynamic',
                              cascade='all, delete-orphan')

    def get_members(self):
        """Get all active members of the group"""
        return [membership.user for membership in self.memberships if membership.is_active]

    def add_member(self, user, role='member'):
        """Add a member to the group"""
        existing_membership = GroupMembership.query.filter_by(
            group_id=self.id, user_id=user.id
        ).first()

        if existing_membership:
            existing_membership.is_active = True
            existing_membership.role = role
        else:
            membership = GroupMembership(
                group_id=self.id,
                user_id=user.id,
                role=role
            )
            db.session.add(membership)

        db.session.commit()

    def remove_member(self, user):
        """Remove a member from the group"""
        membership = GroupMembership.query.filter_by(
            group_id=self.id, user_id=user.id
        ).first()

        if membership:
            membership.is_active = False
            db.session.commit()

    def get_total_expenses(self):
        """Get total amount of all expenses in the group"""
        return sum(expense.amount for expense in self.expenses if expense.is_active)

    def get_member_balances(self):
        """Get balance summary for all members"""
        members = self.get_members()
        balances = {}

        for member in members:
            balances[member.id] = {
                'user': member.to_dict(),
                'total_paid': 0,
                'total_owed': 0,
                'net_balance': 0
            }

        # Calculate from all active expenses
        for expense in self.expenses:
            if expense.is_active:
                # Add to paid amount for person who paid
                if expense.paid_by_id in balances:
                    balances[expense.paid_by_id]['total_paid'] += expense.amount

                # Add to owed amounts for all participants
                for participant in expense.participants:
                    if participant.user_id in balances:
                        balances[participant.user_id]['total_owed'] += participant.amount_owed

        # Calculate net balances
        for user_id in balances:
            balances[user_id]['net_balance'] = (
                balances[user_id]['total_paid'] - balances[user_id]['total_owed']
            )

        return balances

    def to_dict(self, include_members=False, include_balances=False):
        """Convert group to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by_id': self.created_by_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'total_expenses': self.get_total_expenses(),
            'member_count': self.memberships.filter_by(is_active=True).count()
        }

        if include_members:
            data['members'] = [member.to_dict() for member in self.get_members()]

        if include_balances:
            data['member_balances'] = self.get_member_balances()

        return data

    def __repr__(self):
        return f'<Group {self.name}>'


class GroupMembership(db.Model):
    __tablename__ = 'group_memberships'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'admin', 'member'
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    group = db.relationship('Group', back_populates='memberships')
    user = db.relationship('User', back_populates='group_memberships')

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='unique_group_membership'),)

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'role': self.role,
            'is_active': self.is_active,
            'joined_at': self.joined_at.isoformat()
        }

    def __repr__(self):
        return f'<GroupMembership {self.user_id} in {self.group_id}>'
