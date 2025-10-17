from datetime import datetime
from app.extensions import db
from decimal import Decimal, ROUND_HALF_UP

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Using Decimal for precision
    category = db.Column(db.String(50), default='general')  # food, transport, utilities, etc.

    # Who paid for this expense
    paid_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Which group this expense belongs to
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    # Who created this expense entry
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Splitting method: 'equal', 'exact', 'percentage'
    split_method = db.Column(db.String(20), default='equal')

    # Status and timestamps
    is_active = db.Column(db.Boolean, default=True)
    expense_date = db.Column(db.DateTime, nullable=False)  # When the expense occurred
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    paid_by = db.relationship('User', foreign_keys=[paid_by_id], backref='expenses_paid')
    created_by = db.relationship('User', foreign_keys=[created_by_id], back_populates='expenses_created')
    group = db.relationship('Group', back_populates='expenses')
    participants = db.relationship('ExpenseParticipant', back_populates='expense', 
                                  cascade='all, delete-orphan', lazy='dynamic')

    def add_participants(self, participants_data):
        """
        Add participants to the expense
        participants_data: [{'user_id': 1, 'amount_owed': 10.00}, ...]
        """
        # Clear existing participants
        self.participants.delete()

        total_owed = Decimal('0')

        for participant_data in participants_data:
            participant = ExpenseParticipant(
                expense_id=self.id,
                user_id=participant_data['user_id'],
                amount_owed=Decimal(str(participant_data['amount_owed']))
            )
            db.session.add(participant)
            total_owed += participant.amount_owed

        # Validate that total owed matches expense amount
        if abs(total_owed - Decimal(str(self.amount))) > Decimal('0.01'):  # Allow 1 cent tolerance
            raise ValueError(f"Total owed ({total_owed}) doesn't match expense amount ({self.amount})")

        db.session.commit()

    def split_equally(self, user_ids):
        """Split the expense equally among specified users"""
        if not user_ids:
            raise ValueError("No users specified for splitting")

        amount_per_person = Decimal(str(self.amount)) / len(user_ids)
        # Round to 2 decimal places
        amount_per_person = amount_per_person.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        participants_data = []
        total_assigned = Decimal('0')

        # Assign equal amounts to all but the last person
        for i, user_id in enumerate(user_ids[:-1]):
            participants_data.append({
                'user_id': user_id,
                'amount_owed': float(amount_per_person)
            })
            total_assigned += amount_per_person

        # The last person gets the remainder to ensure exact total
        last_person_amount = Decimal(str(self.amount)) - total_assigned
        participants_data.append({
            'user_id': user_ids[-1],
            'amount_owed': float(last_person_amount)
        })

        self.split_method = 'equal'
        self.add_participants(participants_data)

    def split_by_exact_amounts(self, amounts_dict):
        """
        Split by exact amounts
        amounts_dict: {user_id: amount_owed, ...}
        """
        total = sum(amounts_dict.values())
        if abs(total - float(self.amount)) > 0.01:  # Allow 1 cent tolerance
            raise ValueError(f"Total amounts ({total}) don't match expense amount ({self.amount})")

        participants_data = [
            {'user_id': user_id, 'amount_owed': amount}
            for user_id, amount in amounts_dict.items()
        ]

        self.split_method = 'exact'
        self.add_participants(participants_data)

    def split_by_percentages(self, percentages_dict):
        """
        Split by percentages
        percentages_dict: {user_id: percentage, ...} (percentages should sum to 100)
        """
        total_percentage = sum(percentages_dict.values())
        if abs(total_percentage - 100) > 0.01:  # Allow small tolerance
            raise ValueError(f"Percentages ({total_percentage}) don't sum to 100")

        participants_data = []
        total_assigned = Decimal('0')
        expense_amount = Decimal(str(self.amount))

        # Calculate amounts for all but the last person
        users = list(percentages_dict.keys())
        for user_id in users[:-1]:
            percentage = Decimal(str(percentages_dict[user_id]))
            amount = (expense_amount * percentage / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            participants_data.append({
                'user_id': user_id,
                'amount_owed': float(amount)
            })
            total_assigned += amount

        # Last person gets the remainder
        last_person_amount = expense_amount - total_assigned
        participants_data.append({
            'user_id': users[-1],
            'amount_owed': float(last_person_amount)
        })

        self.split_method = 'percentage'
        self.add_participants(participants_data)

    def get_participant_summary(self):
        """Get summary of all participants and their owed amounts"""
        return [
            {
                'user': participant.user.to_dict(),
                'amount_owed': float(participant.amount_owed),
                'is_settled': participant.is_settled
            }
            for participant in self.participants
        ]

    def is_fully_settled(self):
        """Check if all participants have settled their amounts"""
        return all(participant.is_settled for participant in self.participants)

    def to_dict(self, include_participants=True):
        """Convert expense to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'amount': float(self.amount),
            'category': self.category,
            'paid_by_id': self.paid_by_id,
            'paid_by': self.paid_by.to_dict(),
            'group_id': self.group_id,
            'created_by_id': self.created_by_id,
            'split_method': self.split_method,
            'is_active': self.is_active,
            'expense_date': self.expense_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_fully_settled': self.is_fully_settled()
        }

        if include_participants:
            data['participants'] = self.get_participant_summary()

        return data

    def __repr__(self):
        return f'<Expense {self.title}: ${self.amount}>'


class ExpenseParticipant(db.Model):
    __tablename__ = 'expense_participants'

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount_owed = db.Column(db.Numeric(10, 2), nullable=False)
    is_settled = db.Column(db.Boolean, default=False)
    settled_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    expense = db.relationship('Expense', back_populates='participants')
    user = db.relationship('User', back_populates='expense_participations')

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('expense_id', 'user_id', name='unique_expense_participation'),)

    def mark_as_settled(self):
        """Mark this participant's amount as settled"""
        self.is_settled = True
        self.settled_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'expense_id': self.expense_id,
            'user_id': self.user_id,
            'amount_owed': float(self.amount_owed),
            'is_settled': self.is_settled,
            'settled_at': self.settled_at.isoformat() if self.settled_at else None
        }

    def __repr__(self):
        return f'<ExpenseParticipant {self.user_id}: ${self.amount_owed}>'
