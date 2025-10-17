from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import heapq
import logging

logger = logging.getLogger(__name__)

class BillCalculator:
    """
    Advanced bill splitting and balance calculation service

    Handles complex scenarios like:
    - Multiple splitting methods
    - Optimal settlement calculations 
    - Minimum transaction settlements
    - Balance optimization across groups
    """

    @staticmethod
    def split_equally(total_amount: Decimal, participant_ids: List[int]) -> Dict[int, Decimal]:
        """
        Split amount equally among participants

        Args:
            total_amount: Total amount to split
            participant_ids: List of user IDs

        Returns:
            Dict mapping user_id to amount owed
        """
        if not participant_ids:
            raise ValueError("No participants provided")

        if total_amount <= 0:
            raise ValueError("Amount must be positive")

        # Calculate amount per person
        amount_per_person = total_amount / len(participant_ids)
        rounded_amount = amount_per_person.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Distribute amounts
        result = {}
        total_assigned = Decimal('0')

        # Assign rounded amounts to all but last person
        for user_id in participant_ids[:-1]:
            result[user_id] = rounded_amount
            total_assigned += rounded_amount

        # Last person gets remainder to ensure exact total
        result[participant_ids[-1]] = total_amount - total_assigned

        return result

    @staticmethod
    def split_by_exact_amounts(total_amount: Decimal, amounts: Dict[int, Decimal]) -> Dict[int, Decimal]:
        """
        Split by exact amounts with validation

        Args:
            total_amount: Expected total amount
            amounts: Dict mapping user_id to exact amount

        Returns:
            Dict mapping user_id to amount owed (same as input if valid)
        """
        if not amounts:
            raise ValueError("No amounts provided")

        calculated_total = sum(amounts.values())

        # Allow small rounding tolerance (1 cent)
        if abs(calculated_total - total_amount) > Decimal('0.01'):
            raise ValueError(f"Sum of amounts ({calculated_total}) doesn't match total ({total_amount})")

        return amounts.copy()

    @staticmethod
    def split_by_percentages(total_amount: Decimal, percentages: Dict[int, Decimal]) -> Dict[int, Decimal]:
        """
        Split by percentages with proper rounding

        Args:
            total_amount: Total amount to split
            percentages: Dict mapping user_id to percentage (should sum to 100)

        Returns:
            Dict mapping user_id to amount owed
        """
        if not percentages:
            raise ValueError("No percentages provided")

        total_percentage = sum(percentages.values())

        # Allow small tolerance for percentage sum
        if abs(total_percentage - 100) > Decimal('0.01'):
            raise ValueError(f"Percentages sum to {total_percentage}, not 100")

        result = {}
        total_assigned = Decimal('0')
        user_ids = list(percentages.keys())

        # Calculate amounts for all but last person
        for user_id in user_ids[:-1]:
            percentage = percentages[user_id]
            amount = (total_amount * percentage / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            result[user_id] = amount
            total_assigned += amount

        # Last person gets remainder
        result[user_ids[-1]] = total_amount - total_assigned

        return result

    @staticmethod
    def calculate_balances(expenses: List[Dict]) -> Dict[int, Dict]:
        """
        Calculate net balances for users across multiple expenses

        Args:
            expenses: List of expense dictionaries with participants

        Returns:
            Dict mapping user_id to balance info
        """
        balances = defaultdict(lambda: {'paid': Decimal('0'), 'owed': Decimal('0'), 'net': Decimal('0')})

        for expense in expenses:
            if not expense.get('is_active', True):
                continue

            paid_by_id = expense['paid_by_id']
            amount = Decimal(str(expense['amount']))

            # Add to amount paid by payer
            balances[paid_by_id]['paid'] += amount

            # Add to amounts owed by participants
            for participant in expense.get('participants', []):
                user_id = participant['user_id']
                amount_owed = Decimal(str(participant['amount_owed']))
                balances[user_id]['owed'] += amount_owed

        # Calculate net balances
        for user_id in balances:
            balances[user_id]['net'] = balances[user_id]['paid'] - balances[user_id]['owed']

        return dict(balances)

    @staticmethod
    def optimize_settlements(balances: Dict[int, Decimal]) -> List[Dict]:
        """
        Calculate optimal settlements to minimize number of transactions
        Uses a greedy algorithm with heaps

        Args:
            balances: Dict mapping user_id to net balance (positive = owed money, negative = owes money)

        Returns:
            List of settlement transactions [{'from': user_id, 'to': user_id, 'amount': Decimal}]
        """
        if not balances:
            return []

        # Separate creditors (owed money) and debtors (owe money)
        creditors = []  # Max heap (amounts owed TO them)
        debtors = []    # Min heap (amounts they owe, stored as negative)

        for user_id, balance in balances.items():
            if balance > Decimal('0.01'):  # Creditor (ignore tiny amounts)
                heapq.heappush(creditors, (-balance, user_id))  # Negative for max heap
            elif balance < -Decimal('0.01'):  # Debtor
                heapq.heappush(debtors, (balance, user_id))  # Already negative

        settlements = []

        # Process settlements
        while creditors and debtors:
            # Get largest creditor and debtor
            neg_credit_amount, creditor_id = heapq.heappop(creditors)
            debt_amount, debtor_id = heapq.heappop(debtors)

            credit_amount = -neg_credit_amount  # Convert back to positive
            debt_amount = -debt_amount  # Convert to positive amount owed

            # Settlement amount is minimum of credit and debt
            settlement_amount = min(credit_amount, debt_amount)

            settlements.append({
                'from': debtor_id,
                'to': creditor_id,
                'amount': settlement_amount
            })

            # Update remaining balances
            remaining_credit = credit_amount - settlement_amount
            remaining_debt = debt_amount - settlement_amount

            # Put remaining amounts back in heaps if significant
            if remaining_credit > Decimal('0.01'):
                heapq.heappush(creditors, (-remaining_credit, creditor_id))

            if remaining_debt > Decimal('0.01'):
                heapq.heappush(debtors, (-remaining_debt, debtor_id))

        return settlements

    @staticmethod
    def calculate_user_debt_to_user(user1_id: int, user2_id: int, expenses: List[Dict]) -> Decimal:
        """
        Calculate how much user1 owes to user2 across all expenses

        Args:
            user1_id: ID of potential debtor
            user2_id: ID of potential creditor
            expenses: List of expense dictionaries

        Returns:
            Decimal amount user1 owes to user2 (negative if user2 owes user1)
        """
        net_debt = Decimal('0')

        for expense in expenses:
            if not expense.get('is_active', True):
                continue

            paid_by_id = expense['paid_by_id']
            participants = expense.get('participants', [])

            # Find if either user is involved in this expense
            user1_participation = None
            user2_participation = None

            for participant in participants:
                if participant['user_id'] == user1_id:
                    user1_participation = participant
                elif participant['user_id'] == user2_id:
                    user2_participation = participant

            # Case 1: User2 paid, User1 participated
            if paid_by_id == user2_id and user1_participation:
                net_debt += Decimal(str(user1_participation['amount_owed']))

            # Case 2: User1 paid, User2 participated  
            elif paid_by_id == user1_id and user2_participation:
                net_debt -= Decimal(str(user2_participation['amount_owed']))

        return net_debt

    @staticmethod
    def suggest_settlement_plan(balances: Dict[int, Decimal], user_names: Dict[int, str]) -> Dict:
        """
        Create a comprehensive settlement plan with user-friendly descriptions

        Args:
            balances: Dict mapping user_id to net balance
            user_names: Dict mapping user_id to user name

        Returns:
            Dict with settlement plan and summary
        """
        settlements = BillCalculator.optimize_settlements(balances)

        if not settlements:
            return {
                'settlements': [],
                'summary': 'All balances are settled!',
                'total_transactions': 0,
                'total_amount_moving': Decimal('0')
            }

        # Format settlements with user names
        formatted_settlements = []
        total_amount = Decimal('0')

        for settlement in settlements:
            from_user = user_names.get(settlement['from'], f"User {settlement['from']}")
            to_user = user_names.get(settlement['to'], f"User {settlement['to']}")
            amount = settlement['amount']

            formatted_settlements.append({
                'from_user_id': settlement['from'],
                'from_user_name': from_user,
                'to_user_id': settlement['to'],
                'to_user_name': to_user,
                'amount': amount,
                'description': f"{from_user} pays ${amount:.2f} to {to_user}"
            })

            total_amount += amount

        return {
            'settlements': formatted_settlements,
            'summary': f"Settle all balances with {len(settlements)} transaction(s)",
            'total_transactions': len(settlements),
            'total_amount_moving': total_amount
        }

    @staticmethod
    def validate_expense_split(total_amount: Decimal, split_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate expense splitting data

        Args:
            total_amount: Total expense amount
            split_data: Split configuration data

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            split_method = split_data.get('method', 'equal')

            if split_method == 'equal':
                participants = split_data.get('participants', [])
                if not participants:
                    return False, "No participants specified for equal split"
                if len(participants) == 0:
                    return False, "At least one participant required"

            elif split_method == 'exact':
                amounts = split_data.get('amounts', {})
                if not amounts:
                    return False, "No amounts specified for exact split"

                total_specified = sum(Decimal(str(amt)) for amt in amounts.values())
                if abs(total_specified - total_amount) > Decimal('0.01'):
                    return False, f"Amounts sum to ${total_specified}, expected ${total_amount}"

            elif split_method == 'percentage':
                percentages = split_data.get('percentages', {})
                if not percentages:
                    return False, "No percentages specified for percentage split"

                total_percentage = sum(Decimal(str(pct)) for pct in percentages.values())
                if abs(total_percentage - 100) > Decimal('0.01'):
                    return False, f"Percentages sum to {total_percentage}%, expected 100%"

            else:
                return False, f"Invalid split method: {split_method}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def calculate_group_statistics(expenses: List[Dict], participants: List[int]) -> Dict:
        """
        Calculate comprehensive group statistics

        Args:
            expenses: List of expense dictionaries
            participants: List of participant user IDs

        Returns:
            Dict with various statistics
        """
        if not expenses:
            return {
                'total_expenses': Decimal('0'),
                'expense_count': 0,
                'average_expense': Decimal('0'),
                'largest_expense': Decimal('0'),
                'smallest_expense': Decimal('0'),
                'most_active_payer': None,
                'category_breakdown': {},
                'monthly_trends': {}
            }

        active_expenses = [exp for exp in expenses if exp.get('is_active', True)]

        if not active_expenses:
            return BillCalculator.calculate_group_statistics([], participants)

        # Basic statistics
        amounts = [Decimal(str(exp['amount'])) for exp in active_expenses]
        total_expenses = sum(amounts)
        expense_count = len(active_expenses)
        average_expense = total_expenses / expense_count if expense_count > 0 else Decimal('0')

        # Payer statistics
        payer_counts = defaultdict(int)
        payer_amounts = defaultdict(Decimal)

        for expense in active_expenses:
            payer_id = expense['paid_by_id']
            payer_counts[payer_id] += 1
            payer_amounts[payer_id] += Decimal(str(expense['amount']))

        most_active_payer = max(payer_counts.items(), key=lambda x: x[1])[0] if payer_counts else None

        # Category breakdown
        category_breakdown = defaultdict(lambda: {'count': 0, 'amount': Decimal('0')})

        for expense in active_expenses:
            category = expense.get('category', 'general')
            category_breakdown[category]['count'] += 1
            category_breakdown[category]['amount'] += Decimal(str(expense['amount']))

        return {
            'total_expenses': total_expenses,
            'expense_count': expense_count,
            'average_expense': average_expense,
            'largest_expense': max(amounts),
            'smallest_expense': min(amounts),
            'most_active_payer': most_active_payer,
            'payer_statistics': dict(payer_amounts),
            'category_breakdown': dict(category_breakdown),
        }
