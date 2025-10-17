from datetime import datetime
from app.extensions import db
from decimal import Decimal

class Settlement(db.Model):
    __tablename__ = 'settlements'

    id = db.Column(db.Integer, primary_key=True)

    # Who is paying and who is receiving
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Settlement details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)  # Optional: specific to a group

    # Description and reference
    description = db.Column(db.String(200))
    reference_expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)

    # Settlement method: 'cash', 'online', 'bank_transfer', 'other'
    payment_method = db.Column(db.String(50), default='cash')

    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, disputed
    is_confirmed = db.Column(db.Boolean, default=False)

    # Timestamps
    settlement_date = db.Column(db.DateTime, nullable=False)  # When the settlement was made
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id], back_populates='settlements_from')
    to_user = db.relationship('User', foreign_keys=[to_user_id], back_populates='settlements_to')
    group = db.relationship('Group', backref='settlements')
    reference_expense = db.relationship('Expense', backref='settlements')

    def confirm_settlement(self, confirmed_by_user_id=None):
        """Confirm the settlement"""
        self.is_confirmed = True
        self.status = 'confirmed'
        self.confirmed_at = datetime.utcnow()
        db.session.commit()

        # Update related expense participants if this settlement is for a specific expense
        if self.reference_expense_id:
            from .expense import ExpenseParticipant
            participant = ExpenseParticipant.query.filter_by(
                expense_id=self.reference_expense_id,
                user_id=self.from_user_id
            ).first()

            if participant and participant.amount_owed <= self.amount:
                participant.mark_as_settled()

    def dispute_settlement(self, reason=None):
        """Mark settlement as disputed"""
        self.status = 'disputed'
        if reason:
            self.description = f"{self.description or ''} [DISPUTED: {reason}]"
        db.session.commit()

    @classmethod
    def create_settlement(cls, from_user_id, to_user_id, amount, **kwargs):
        """Create a new settlement with validation"""
        # Validate that users are different
        if from_user_id == to_user_id:
            raise ValueError("Cannot create settlement between same user")

        # Validate amount is positive
        if Decimal(str(amount)) <= 0:
            raise ValueError("Settlement amount must be positive")

        settlement = cls(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=Decimal(str(amount)),
            settlement_date=kwargs.get('settlement_date', datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k != 'settlement_date'}
        )

        db.session.add(settlement)
        db.session.commit()
        return settlement

    @classmethod
    def get_user_settlement_summary(cls, user_id):
        """Get settlement summary for a user"""
        # Settlements where user owes money (from_user)
        outgoing = cls.query.filter_by(from_user_id=user_id, is_confirmed=True).all()
        outgoing_total = sum(float(s.amount) for s in outgoing)

        # Settlements where user should receive money (to_user)
        incoming = cls.query.filter_by(to_user_id=user_id, is_confirmed=True).all()
        incoming_total = sum(float(s.amount) for s in incoming)

        # Pending settlements
        pending_outgoing = cls.query.filter_by(from_user_id=user_id, is_confirmed=False).all()
        pending_incoming = cls.query.filter_by(to_user_id=user_id, is_confirmed=False).all()

        return {
            'total_paid': outgoing_total,
            'total_received': incoming_total,
            'net_balance': incoming_total - outgoing_total,
            'pending_outgoing': len(pending_outgoing),
            'pending_incoming': len(pending_incoming),
            'recent_settlements': [s.to_dict() for s in (outgoing + incoming)[-10:]]  # Last 10
        }

    def to_dict(self):
        """Convert settlement to dictionary"""
        return {
            'id': self.id,
            'from_user_id': self.from_user_id,
            'from_user': self.from_user.to_dict(),
            'to_user_id': self.to_user_id,
            'to_user': self.to_user.to_dict(),
            'amount': float(self.amount),
            'group_id': self.group_id,
            'description': self.description,
            'reference_expense_id': self.reference_expense_id,
            'payment_method': self.payment_method,
            'status': self.status,
            'is_confirmed': self.is_confirmed,
            'settlement_date': self.settlement_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }

    def __repr__(self):
        return f'<Settlement ${self.amount}: {self.from_user_id} -> {self.to_user_id}>'
