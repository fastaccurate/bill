from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMembership
from app.models.expense import Expense
from sqlalchemy.orm import joinedload

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('', methods=['POST'])
@jwt_required()
def create_group():
    """Create a new group"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Group name is required'}), 400

        name = data['name'].strip()
        description = data.get('description', '').strip()

        # Create group
        group = Group(
            name=name,
            description=description,
            created_by_id=current_user_id
        )

        db.session.add(group)
        db.session.flush()  # Get the group ID

        # Add creator as admin member
        membership = GroupMembership(
            group_id=group.id,
            user_id=current_user_id,
            role='admin'
        )
        db.session.add(membership)

        # Add initial members if provided
        initial_members = data.get('member_emails', [])
        if initial_members:
            for email in initial_members:
                email = email.lower().strip()
                user = User.query.filter_by(email=email).first()
                if user and user.id != current_user_id:
                    membership = GroupMembership(
                        group_id=group.id,
                        user_id=user.id,
                        role='member'
                    )
                    db.session.add(membership)

        db.session.commit()

        return jsonify({
            'message': 'Group created successfully',
            'group': group.to_dict(include_members=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('', methods=['GET'])
@jwt_required()
def get_user_groups():
    """Get all groups for the current user"""
    try:
        current_user_id = get_jwt_identity()

        # Get all groups where user is a member
        groups = db.session.query(Group).join(GroupMembership).filter(
            GroupMembership.user_id == current_user_id,
            GroupMembership.is_active == True,
            Group.is_active == True
        ).all()

        return jsonify({
            'groups': [group.to_dict(include_members=True) for group in groups]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group(group_id):
    """Get specific group details"""
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

        group = Group.query.get(group_id)
        if not group or not group.is_active:
            return jsonify({'error': 'Group not found'}), 404

        return jsonify({
            'group': group.to_dict(include_members=True, include_balances=True)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    """Update group details"""
    try:
        current_user_id = get_jwt_identity()

        # Verify user is an admin of this group
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Group not found or insufficient permissions'}), 403

        group = Group.query.get(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({'error': 'Group name cannot be empty'}), 400
            group.name = name

        if 'description' in data:
            group.description = data['description'].strip()

        db.session.commit()

        return jsonify({
            'message': 'Group updated successfully',
            'group': group.to_dict(include_members=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members', methods=['POST'])
@jwt_required()
def add_member(group_id):
    """Add member to group"""
    try:
        current_user_id = get_jwt_identity()

        # Verify user is an admin of this group
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Group not found or insufficient permissions'}), 403

        data = request.get_json()
        email = data.get('email', '').lower().strip()

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Find user to add
        user_to_add = User.query.filter_by(email=email).first()
        if not user_to_add:
            return jsonify({'error': 'User not found with this email'}), 404

        # Check if user is already a member
        existing_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=user_to_add.id
        ).first()

        if existing_membership:
            if existing_membership.is_active:
                return jsonify({'error': 'User is already a member of this group'}), 409
            else:
                # Reactivate membership
                existing_membership.is_active = True
                existing_membership.role = data.get('role', 'member')
        else:
            # Create new membership
            new_membership = GroupMembership(
                group_id=group_id,
                user_id=user_to_add.id,
                role=data.get('role', 'member')
            )
            db.session.add(new_membership)

        db.session.commit()

        group = Group.query.get(group_id)

        return jsonify({
            'message': 'Member added successfully',
            'group': group.to_dict(include_members=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(group_id, user_id):
    """Remove member from group"""
    try:
        current_user_id = get_jwt_identity()

        # Verify user is an admin of this group or removing themselves
        admin_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not admin_membership and current_user_id != user_id:
            return jsonify({'error': 'Insufficient permissions'}), 403

        # Find the membership to remove
        membership_to_remove = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            is_active=True
        ).first()

        if not membership_to_remove:
            return jsonify({'error': 'Member not found in this group'}), 404

        # Prevent removing the last admin
        if membership_to_remove.role == 'admin':
            admin_count = GroupMembership.query.filter_by(
                group_id=group_id,
                role='admin',
                is_active=True
            ).count()

            if admin_count <= 1:
                return jsonify({'error': 'Cannot remove the last admin from the group'}), 400

        # Check if user has unsettled expenses
        unsettled_participations = db.session.query(Expense).join(
            'participants'
        ).filter(
            Expense.group_id == group_id,
            Expense.is_active == True,
            ExpenseParticipant.user_id == user_id,
            ExpenseParticipant.is_settled == False
        ).first()

        if unsettled_participations:
            return jsonify({
                'error': 'Cannot remove member with unsettled expenses. Please settle all expenses first.'
            }), 400

        # Deactivate membership
        membership_to_remove.is_active = False
        db.session.commit()

        group = Group.query.get(group_id)

        return jsonify({
            'message': 'Member removed successfully',
            'group': group.to_dict(include_members=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def update_member_role(group_id, user_id):
    """Update member role in group"""
    try:
        current_user_id = get_jwt_identity()

        # Verify user is an admin of this group
        admin_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=current_user_id,
            role='admin',
            is_active=True
        ).first()

        if not admin_membership:
            return jsonify({'error': 'Insufficient permissions'}), 403

        data = request.get_json()
        new_role = data.get('role')

        if new_role not in ['admin', 'member']:
            return jsonify({'error': 'Invalid role. Must be admin or member'}), 400

        # Find the membership to update
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            is_active=True
        ).first()

        if not membership:
            return jsonify({'error': 'Member not found in this group'}), 404

        # Prevent demoting the last admin
        if membership.role == 'admin' and new_role != 'admin':
            admin_count = GroupMembership.query.filter_by(
                group_id=group_id,
                role='admin',
                is_active=True
            ).count()

            if admin_count <= 1:
                return jsonify({'error': 'Cannot demote the last admin'}), 400

        membership.role = new_role
        db.session.commit()

        group = Group.query.get(group_id)

        return jsonify({
            'message': 'Member role updated successfully',
            'group': group.to_dict(include_members=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/balance', methods=['GET'])
@jwt_required()
def get_group_balance(group_id):
    """Get balance summary for group"""
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

        group = Group.query.get(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404

        return jsonify({
            'group_id': group_id,
            'member_balances': group.get_member_balances()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
