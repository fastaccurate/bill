import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service using Twilio API for sending payment reminders"""

    def __init__(self):
        """Initialize Twilio client with credentials from environment variables"""
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_PHONE_NUMBER')

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.error("Missing Twilio credentials in environment variables")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for Twilio (E.164 format)"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))

        # Add country code if not present (assuming US/Canada +1)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif digits_only.startswith('+'):
            return phone
        else:
            return f"+{digits_only}"

    def _generate_payment_reminder_message(
        self, 
        user_name: str, 
        group_name: str, 
        amount: float, 
        sender_name: str,
        message_type: str = 'friendly',
        custom_message: Optional[str] = None
    ) -> str:
        """Generate payment reminder message based on type"""

        if custom_message:
            return custom_message

        formatted_amount = f"${amount:.2f}"

        if message_type == 'friendly':
            return (
                f"Hi {user_name}! Friendly reminder that you have an outstanding balance of "
                f"{formatted_amount} in the '{group_name}' group. "
                f"Please settle when convenient. Thanks! - {sender_name} 💰"
            )

        elif message_type == 'urgent':
            return (
                f"Hi {user_name}, you have an outstanding balance of {formatted_amount} "
                f"in '{group_name}'. Please settle this amount soon. "
                f"Contact {sender_name} if you have any questions. 🔔"
            )

        elif message_type == 'final':
            return (
                f"FINAL NOTICE: {user_name}, your outstanding balance of {formatted_amount} "
                f"in '{group_name}' needs immediate attention. "
                f"Please contact {sender_name} to resolve this matter. ⚠️"
            )

        else:
            # Default friendly message
            return (
                f"Hi {user_name}! You have a balance of {formatted_amount} "
                f"in '{group_name}'. Please settle when you can. - {sender_name}"
            )

    def send_payment_reminder(
        self,
        user_name: str,
        user_phone: str,
        group_name: str,
        amount: float,
        sender_name: str,
        message_type: str = 'friendly',
        custom_message: Optional[str] = None
    ) -> Dict:
        """
        Send payment reminder SMS

        Args:
            user_name: Name of the user to remind
            user_phone: Phone number of the user
            group_name: Name of the group
            amount: Outstanding amount
            sender_name: Name of person sending reminder
            message_type: Type of message ('friendly', 'urgent', 'final')
            custom_message: Custom message to override templates

        Returns:
            Dict with success status and details
        """
        if not self.client:
            return {
                'success': False,
                'error_message': 'SMS service not configured - missing Twilio credentials'
            }

        try:
            # Format phone number
            to_number = self._format_phone_number(user_phone)

            # Generate message
            message_body = self._generate_payment_reminder_message(
                user_name=user_name,
                group_name=group_name,
                amount=amount,
                sender_name=sender_name,
                message_type=message_type,
                custom_message=custom_message
            )

            # Ensure message is within SMS limits (160 characters for single SMS)
            if len(message_body) > 320:  # Allow for 2 SMS messages
                message_body = message_body[:317] + "..."

            # Send SMS
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"Payment reminder SMS sent successfully to {to_number}, SID: {message.sid}")

            return {
                'success': True,
                'sms_id': message.sid,
                'message_body': message_body,
                'to_number': to_number
            }

        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {user_phone}: {str(e)}")
            return {
                'success': False,
                'error_message': f"Twilio error: {str(e)}"
            }

        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {user_phone}: {str(e)}")
            return {
                'success': False,
                'error_message': f"Unexpected error: {str(e)}"
            }

    def send_settlement_confirmation(
        self,
        payer_name: str,
        payer_phone: str,
        receiver_name: str,
        amount: float,
        group_name: str
    ) -> Dict:
        """Send settlement confirmation SMS"""
        if not self.client:
            return {
                'success': False,
                'error_message': 'SMS service not configured'
            }

        try:
            to_number = self._format_phone_number(payer_phone)
            formatted_amount = f"${amount:.2f}"

            message_body = (
                f"Hi {payer_name}! Your payment of {formatted_amount} to {receiver_name} "
                f"in '{group_name}' has been recorded. Thank you for settling up! ✅"
            )

            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"Settlement confirmation SMS sent to {to_number}, SID: {message.sid}")

            return {
                'success': True,
                'sms_id': message.sid,
                'message_body': message_body
            }

        except Exception as e:
            logger.error(f"Error sending settlement confirmation SMS: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

    def send_expense_notification(
        self,
        user_name: str,
        user_phone: str,
        expense_title: str,
        amount_owed: float,
        paid_by_name: str,
        group_name: str
    ) -> Dict:
        """Send new expense notification SMS"""
        if not self.client:
            return {
                'success': False,
                'error_message': 'SMS service not configured'
            }

        try:
            to_number = self._format_phone_number(user_phone)
            formatted_amount = f"${amount_owed:.2f}"

            message_body = (
                f"New expense in '{group_name}': {expense_title}. "
                f"You owe {formatted_amount} to {paid_by_name}. "
                f"Check the app for details. 📝"
            )

            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"Expense notification SMS sent to {to_number}, SID: {message.sid}")

            return {
                'success': True,
                'sms_id': message.sid,
                'message_body': message_body
            }

        except Exception as e:
            logger.error(f"Error sending expense notification SMS: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

    def send_test_message(self, phone_number: str, message: str) -> Dict:
        """Send test SMS message"""
        if not self.client:
            return {
                'success': False,
                'error_message': 'SMS service not configured'
            }

        try:
            to_number = self._format_phone_number(phone_number)

            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"Test SMS sent to {to_number}, SID: {message.sid}")

            return {
                'success': True,
                'sms_id': message.sid,
                'message_body': message
            }

        except Exception as e:
            logger.error(f"Error sending test SMS: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

    def get_message_status(self, message_sid: str) -> Dict:
        """Get status of a sent message"""
        if not self.client:
            return {
                'success': False,
                'error_message': 'SMS service not configured'
            }

        try:
            message = self.client.messages(message_sid).fetch()

            return {
                'success': True,
                'status': message.status,
                'direction': message.direction,
                'date_sent': message.date_sent.isoformat() if message.date_sent else None,
                'date_updated': message.date_updated.isoformat() if message.date_updated else None,
                'error_code': message.error_code,
                'error_message': message.error_message
            }

        except Exception as e:
            logger.error(f"Error fetching message status: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
