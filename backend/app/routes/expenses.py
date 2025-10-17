from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMembership
from app.models.expense import Expense, ExpenseParticipant
from app.models.settlement import Settlement
from datetime import datetime, timedelta
from decimal import Decimal
import re

expenses_bp = Blueprint('expenses', __name__)

def validate_expense_data(data):
    """Validate expense data"""
    errors = []

    if not data.get('title'):
        errors.append('Title is required')

    if not data.get('amount'):
        errors.append('Amount is required')

    try:
        amount = float(data['amount'])
        if amount <= 0:
            errors.append('Amount must be positive')
    except (ValueError, TypeError):
        errors.append('Invalid amount format')

    if not data.get('group_id'):
        errors.append('Group ID is required')

    if not data.get('paid_by_id'):
        errors.append('Paid by user ID is required')

    split_method = data.get('split_method', 'equal')
    if split_method not in ['equal', 'exact', 'percentage']:
        errors.append('Invalid split method')

    return errors

@expenses_bp.route('', methods=['POST'])
@jwt_required()
def create_expense():
    """Create a new expense"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validate expense data
        errors = validate_expense_data(data)
        if errors:
            return jsonify({'errors': errors}), 400

        group_id = data['group_id']

        # Verify user is a member of this group
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Group not found or access denied'}), 404

        # Verify paid_by user is also a group member
        paid_by_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=data['paid_by_id'],
            is_active=True
        ).first()

        if not paid_by_membership:
            return jsonify({'error': 'Paid by user is not a member of this group'}), 400

        # Parse expense date
        expense_date = datetime.utcnow()
        if data.get('expense_date'):
            try:
                expense_date = datetime.fromisoformat(data['expense_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expense date format'}), 400

        # Create expense
        expense = Expense(
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            amount=Decimal(str(data['amount'])),
            category=data.get('category', 'general').strip(),
            paid_by_id=data['paid_by_id'],
            group_id=group_id,
            created_by_id=current_user_id,
            split_method=data.get('split_method', 'equal'),
            expense_date=expense_date
        )

        db.session.add(expense)
        db.session.flush()  # Get expense ID

        # Handle splitting based on method
        split_method = data.get('split_method', 'equal')

        if split_method == 'equal':
            participant_ids = data.get('participant_ids', [])
            if not participant_ids:
                return jsonify({'error': 'Participant IDs required for equal split'}), 400

            # Verify all participants are group members
            for user_id in participant_ids:
                participant_membership = GroupMembership.query.filter_by(
                    group_id=group_id,
                    user_id=user_id,
                    is_active=True
                ).first()
                if not participant_membership:
                    return jsonify({'error': f'User {user_id} is not a member of this group'}), 400

            expense.split_equally(participant_ids)

        elif split_method == 'exact':
            exact_amounts = data.get('exact_amounts', {})
            if not exact_amounts:
                return jsonify({'error': 'Exact amounts required for exact split'}), 400

            # Convert string keys to integers and validate
            validated_amounts = {}
            for user_id_str, amount in exact_amounts.items():
                try:
                    user_id = int(user_id_str)
                    amount = float(amount)

                    # Verify user is group member
                    participant_membership = GroupMembership.query.filter_by(
                        group_id=group_id,
                        user_id=user_id,
                        is_active=True
                    ).first()
                    if not participant_membership:
                        return jsonify({'error': f'User {user_id} is not a member of this group'}), 400

                    validated_amounts[user_id] = amount
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid user ID or amount in exact_amounts'}), 400

            expense.split_by_exact_amounts(validated_amounts)

        elif split_method == 'percentage':
            percentages = data.get('percentages', {})
            if not percentages:
                return jsonify({'error': 'Percentages required for percentage split'}), 400

            # Convert and validate percentages
            validated_percentages = {}
            for user_id_str, percentage in percentages.items():
                try:
                    user_id = int(user_id_str)
                    percentage = float(percentage)

                    # Verify user is group member
                    participant_membership = GroupMembership.query.filter_by(
                        group_id=group_id,
                        user_id=user_id,
                        is_active=True
                    ).first()
                    if not participant_membership:
                        return jsonify({'error': f'User {user_id} is not a member of this group'}), 400

                    validated_percentages[user_id] = percentage
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid user ID or percentage in percentages'}), 400

            expense.split_by_percentages(validated_percentages)

        db.session.commit()

        return jsonify({
            'message': 'Expense created successfully',
            'expense': expense.to_dict()
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/group/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group_expenses(group_id):
    """Get all expenses for a group"""
    try:
        current_user_id = get_jwt_identity()

        # Verify user is a member of this group
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Group not found or access denied'}), 404

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')

        # Build query
        query = Expense.query.filter_by(group_id=group_id, is_active=True)

        if category:
            query = query.filter_by(category=category)

        query = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc())

        # Paginate
        expenses_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'expenses': [expense.to_dict() for expense in expenses_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': expenses_paginated.total,
                'pages': expenses_paginated.pages,
                'has_next': expenses_paginated.has_next,
                'has_prev': expenses_paginated.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>', methods=['GET'])
@jwt_required()
def get_expense(expense_id):
    """Get specific expense details"""
    try:
        current_user_id = get_jwt_identity()

        expense = Expense.query.get(expense_id)
        if not expense or not expense.is_active:
            return jsonify({'error': 'Expense not found'}), 404

        # Verify user is a member of the expense's group
        membership = GroupMembership.query.filter_by(
            group_id=expense.group_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Access denied'}), 403

        return jsonify({
            'expense': expense.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """Update an expense"""
    try:
        current_user_id = get_jwt_identity()

        expense = Expense.query.get(expense_id)
        if not expense or not expense.is_active:
            return jsonify({'error': 'Expense not found'}), 404

        # Only expense creator or group admin can update
        membership = GroupMembership.query.filter_by(
            group_id=expense.group_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Access denied'}), 403

        is_admin = membership.role == 'admin'
        is_creator = expense.created_by_id == current_user_id

        if not (is_admin or is_creator):
            return jsonify({'error': 'Insufficient permissions'}), 403

        data = request.get_json()

        # Update basic fields
        if 'title' in data:
            expense.title = data['title'].strip()

        if 'description' in data:
            expense.description = data['description'].strip()

        if 'category' in data:
            expense.category = data['category'].strip()

        if 'expense_date' in data:
            try:
                expense.expense_date = datetime.fromisoformat(data['expense_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expense date format'}), 400

        # Handle amount and split changes (more complex)
        if 'amount' in data or 'split_method' in data:
            # Check if any participants have already settled
            settled_participants = expense.participants.filter_by(is_settled=True).first()
            if settled_participants:
                return jsonify({
                    'error': 'Cannot modify amount or split method - some participants have already settled'
                }), 400

            if 'amount' in data:
                try:
                    new_amount = float(data['amount'])
                    if new_amount <= 0:
                        return jsonify({'error': 'Amount must be positive'}), 400
                    expense.amount = Decimal(str(new_amount))
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid amount format'}), 400

            # Re-split if split parameters provided
            split_method = data.get('split_method', expense.split_method)

            if split_method == 'equal' and 'participant_ids' in data:
                expense.split_equally(data['participant_ids'])
            elif split_method == 'exact' and 'exact_amounts' in data:
                validated_amounts = {}
                for user_id_str, amount in data['exact_amounts'].items():
                    validated_amounts[int(user_id_str)] = float(amount)
                expense.split_by_exact_amounts(validated_amounts)
            elif split_method == 'percentage' and 'percentages' in data:
                validated_percentages = {}
                for user_id_str, percentage in data['percentages'].items():
                    validated_percentages[int(user_id_str)] = float(percentage)
                expense.split_by_percentages(validated_percentages)

        db.session.commit()

        return jsonify({
            'message': 'Expense updated successfully',
            'expense': expense.to_dict()
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        current_user_id = get_jwt_identity()

        expense = Expense.query.get(expense_id)
        if not expense or not expense.is_active:
            return jsonify({'error': 'Expense not found'}), 404

        # Only expense creator or group admin can delete
        membership = GroupMembership.query.filter_by(
            group_id=expense.group_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Access denied'}), 403

        is_admin = membership.role == 'admin'
        is_creator = expense.created_by_id == current_user_id

        if not (is_admin or is_creator):
            return jsonify({'error': 'Insufficient permissions'}), 403

        # Check if any participants have settled
        settled_participants = expense.participants.filter_by(is_settled=True).first()
        if settled_participants:
            return jsonify({
                'error': 'Cannot delete expense - some participants have already settled'
            }), 400

        # Soft delete
        expense.is_active = False
        db.session.commit()

        return jsonify({
            'message': 'Expense deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>/settle', methods=['POST'])
@jwt_required()
def settle_expense_participation(expense_id):
    """Mark user's participation in an expense as settled"""
    try:
        current_user_id = get_jwt_identity()

        expense = Expense.query.get(expense_id)
        if not expense or not expense.is_active:
            return jsonify({'error': 'Expense not found'}), 404

        # Find user's participation in this expense
        participation = ExpenseParticipant.query.filter_by(
            expense_id=expense_id,
            user_id=current_user_id
        ).first()

        if not participation:
            return jsonify({'error': 'You are not a participant in this expense'}), 404

        if participation.is_settled:
            return jsonify({'error': 'Your participation is already marked as settled'}), 400

        # Create settlement record if specified
        data = request.get_json() or {}
        if data.get('create_settlement', False):
            Settlement.create_settlement(
                from_user_id=current_user_id,
                to_user_id=expense.paid_by_id,
                amount=participation.amount_owed,
                group_id=expense.group_id,
                reference_expense_id=expense_id,
                description=f"Settlement for: {expense.title}",
                payment_method=data.get('payment_method', 'cash'),
                settlement_date=datetime.utcnow()
            )

        # Mark as settled
        participation.mark_as_settled()

        return jsonify({
            'message': 'Participation marked as settled',
            'expense': expense.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/statistics/group/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group_expense_statistics(group_id):
    """Get expense statistics for a group"""
    try:
        current_user_id = get_jwt_identity()

        # Verify user is a member of this group
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Group not found or access denied'}), 404

        # Get date range (default to last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date'))

        # Get expenses in date range
        expenses = Expense.query.filter(
            Expense.group_id == group_id,
            Expense.is_active == True,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).all()

        # Calculate statistics
        total_amount = sum(float(expense.amount) for expense in expenses)
        expense_count = len(expenses)

        # Category breakdown
        category_stats = {}
        for expense in expenses:
            category = expense.category
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'amount': 0}
            category_stats[category]['count'] += 1
            category_stats[category]['amount'] += float(expense.amount)

        # Top spenders
        spender_stats = {}
        for expense in expenses:
            user_id = expense.paid_by_id
            if user_id not in spender_stats:
                spender_stats[user_id] = {
                    'user': expense.paid_by.to_dict(),
                    'count': 0,
                    'amount': 0
                }
            spender_stats[user_id]['count'] += 1
            spender_stats[user_id]['amount'] += float(expense.amount)

        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_amount': total_amount,
                'expense_count': expense_count,
                'average_expense': total_amount / expense_count if expense_count > 0 else 0
            },
            'category_breakdown': category_stats,
            'top_spenders': sorted(spender_stats.values(), key=lambda x: x['amount'], reverse=True)[:5]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
