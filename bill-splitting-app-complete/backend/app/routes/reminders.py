from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMembership
from app.models.expense import Expense, ExpenseParticipant
from app.services.sms_service import SMSService
from datetime import datetime, timedelta

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/send-payment-reminder', methods=['POST'])
@jwt_required()
def send_payment_reminder():
    """Send payment reminder to a user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        if not data.get('user_id') or not data.get('group_id'):
            return jsonify({'error': 'User ID and Group ID are required'}), 400

        user_id = data['user_id']
        group_id = data['group_id']

        # Verify current user is admin of the group
        admin_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not admin_membership:
            return jsonify({'error': 'Only group admins can send payment reminders'}), 403

        # Verify target user is a member of the group
        target_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            is_active=True
        ).first()

        if not target_membership:
            return jsonify({'error': 'Target user is not a member of this group'}), 404

        # Get user and group details
        target_user = User.query.get(user_id)
        group = Group.query.get(group_id)
        current_user = User.query.get(current_user_id)

        if not target_user or not group or not current_user:
            return jsonify({'error': 'User or group not found'}), 404

        # Calculate user's outstanding balance in the group
        outstanding_participations = db.session.query(ExpenseParticipant).join(Expense).filter(
            Expense.group_id == group_id,
            Expense.is_active == True,
            ExpenseParticipant.user_id == user_id,
            ExpenseParticipant.is_settled == False
        ).all()

        total_outstanding = sum(float(p.amount_owed) for p in outstanding_participations)

        if total_outstanding <= 0:
            return jsonify({'error': 'User has no outstanding balance'}), 400

        # Prepare reminder message
        message_type = data.get('message_type', 'friendly')  # friendly, urgent, final
        custom_message = data.get('custom_message')

        try:
            sms_service = SMSService()
            result = sms_service.send_payment_reminder(
                user_name=target_user.full_name,
                user_phone=target_user.phone_number,
                group_name=group.name,
                amount=total_outstanding,
                sender_name=current_user.full_name,
                message_type=message_type,
                custom_message=custom_message
            )

            if result['success']:
                return jsonify({
                    'message': 'Payment reminder sent successfully',
                    'details': {
                        'recipient': target_user.full_name,
                        'amount': total_outstanding,
                        'message_type': message_type,
                        'sms_id': result.get('sms_id')
                    }
                }), 200
            else:
                return jsonify({
                    'error': 'Failed to send SMS',
                    'details': result.get('error_message')
                }), 500

        except Exception as e:
            return jsonify({'error': f'SMS service error: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/send-bulk-reminders', methods=['POST'])
@jwt_required()
def send_bulk_reminders():
    """Send payment reminders to all users with outstanding balances in a group"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        if not data.get('group_id'):
            return jsonify({'error': 'Group ID is required'}), 400

        group_id = data['group_id']

        # Verify current user is admin of the group
        admin_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not admin_membership:
            return jsonify({'error': 'Only group admins can send bulk reminders'}), 403

        group = Group.query.get(group_id)
        current_user = User.query.get(current_user_id)

        if not group or not current_user:
            return jsonify({'error': 'Group not found'}), 404

        # Get all members with outstanding balances
        member_balances = group.get_member_balances()
        users_to_remind = []

        for user_id, balance_info in member_balances.items():
            if balance_info['net_balance'] < 0:  # User owes money
                outstanding_amount = abs(balance_info['net_balance'])
                if outstanding_amount >= float(data.get('minimum_amount', 1.0)):
                    user = User.query.get(user_id)
                    if user and user.id != current_user_id:
                        users_to_remind.append({
                            'user': user,
                            'amount': outstanding_amount
                        })

        if not users_to_remind:
            return jsonify({'message': 'No users found with outstanding balances above threshold'}), 200

        # Send reminders
        message_type = data.get('message_type', 'friendly')
        custom_message = data.get('custom_message')
        results = []

        sms_service = SMSService()

        for user_info in users_to_remind:
            try:
                result = sms_service.send_payment_reminder(
                    user_name=user_info['user'].full_name,
                    user_phone=user_info['user'].phone_number,
                    group_name=group.name,
                    amount=user_info['amount'],
                    sender_name=current_user.full_name,
                    message_type=message_type,
                    custom_message=custom_message
                )

                results.append({
                    'user_id': user_info['user'].id,
                    'user_name': user_info['user'].full_name,
                    'amount': user_info['amount'],
                    'success': result['success'],
                    'sms_id': result.get('sms_id'),
                    'error': result.get('error_message')
                })

            except Exception as e:
                results.append({
                    'user_id': user_info['user'].id,
                    'user_name': user_info['user'].full_name,
                    'amount': user_info['amount'],
                    'success': False,
                    'error': str(e)
                })

        successful_sends = sum(1 for r in results if r['success'])

        return jsonify({
            'message': f'Bulk reminders completed. {successful_sends}/{len(results)} sent successfully',
            'results': results
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/schedule-reminder', methods=['POST'])
@jwt_required()
def schedule_reminder():
    """Schedule a payment reminder for future sending"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        required_fields = ['user_id', 'group_id', 'send_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        user_id = data['user_id']
        group_id = data['group_id']

        # Verify current user is admin of the group
        admin_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not admin_membership:
            return jsonify({'error': 'Only group admins can schedule reminders'}), 403

        # Parse send date
        try:
            send_date = datetime.fromisoformat(data['send_date'].replace('Z', '+00:00'))
            if send_date <= datetime.utcnow():
                return jsonify({'error': 'Send date must be in the future'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid send date format'}), 400

        # In a production app, you would store this in a job queue (like Celery with Redis)
        # For now, we'll return a success message
        # TODO: Implement with Celery/Redis for production

        return jsonify({
            'message': 'Reminder scheduled successfully',
            'details': {
                'user_id': user_id,
                'group_id': group_id,
                'send_date': send_date.isoformat(),
                'status': 'scheduled'
            },
            'note': 'Scheduled reminders will be implemented with background job processing'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/group/<int:group_id>/reminder-candidates', methods=['GET'])
@jwt_required()
def get_reminder_candidates(group_id):
    """Get list of users who could receive payment reminders"""
    try:
        current_user_id = get_jwt_identity()

        # Verify current user is admin of the group
        admin_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not admin_membership:
            return jsonify({'error': 'Only group admins can view reminder candidates'}), 403

        group = Group.query.get(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404

        # Get member balances
        member_balances = group.get_member_balances()
        candidates = []

        for user_id, balance_info in member_balances.items():
            if balance_info['net_balance'] < 0 and user_id != current_user_id:
                user = User.query.get(user_id)
                if user:
                    # Get unsettled expenses for this user
                    unsettled_expenses = db.session.query(Expense).join(ExpenseParticipant).filter(
                        Expense.group_id == group_id,
                        Expense.is_active == True,
                        ExpenseParticipant.user_id == user_id,
                        ExpenseParticipant.is_settled == False
                    ).all()

                    candidates.append({
                        'user': user.to_dict(),
                        'outstanding_amount': abs(balance_info['net_balance']),
                        'unsettled_expense_count': len(unsettled_expenses),
                        'unsettled_expenses': [
                            {
                                'id': expense.id,
                                'title': expense.title,
                                'amount_owed': float(next(
                                    p.amount_owed for p in expense.participants 
                                    if p.user_id == user_id
                                )),
                                'expense_date': expense.expense_date.isoformat()
                            }
                            for expense in unsettled_expenses
                        ]
                    })

        # Sort by outstanding amount (highest first)
        candidates.sort(key=lambda x: x['outstanding_amount'], reverse=True)

        return jsonify({
            'candidates': candidates,
            'total_count': len(candidates),
            'total_outstanding': sum(c['outstanding_amount'] for c in candidates)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/test-sms', methods=['POST'])
@jwt_required()
def test_sms():
    """Test SMS functionality (for development/testing)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        test_message = data.get('message', 'This is a test message from Bill Splitting App')

        sms_service = SMSService()
        result = sms_service.send_test_message(
            phone_number=current_user.phone_number,
            message=test_message
        )

        if result['success']:
            return jsonify({
                'message': 'Test SMS sent successfully',
                'sms_id': result.get('sms_id')
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send test SMS',
                'details': result.get('error_message')
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
