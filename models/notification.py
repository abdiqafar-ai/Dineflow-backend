from datetime import datetime, timedelta
from . import db

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    action_url = db.Column(db.String(255), nullable=True)

     # Define relationships without backrefs to avoid conflicts
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender.full_name if self.sender else "System",
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "priority": self.priority,
            "action_url": self.action_url
        }

    # Add this helper method to the model
    def send_email(self, recipient_email):
        """Send email notification using SMTP"""
        from flask import current_app
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # Get email config from app settings
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            from_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'notifications@yourapp.com')
            
            if not all([smtp_server, smtp_user, smtp_password]):
                current_app.logger.error("Email configuration incomplete")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Notification: {self.title}"
            
            # Create HTML content
            html = f"""
            <html>
                <body>
                    <h2>{self.title}</h2>
                    <p>{self.message}</p>
                    {f'<p><a href="{self.action_url}">View in app</a></p>' if self.action_url else ''}
                    <p>Sent at: {self.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                
            current_app.logger.info(f"Notification email sent to {recipient_email}")
            return True
        
        except Exception as e:
            current_app.logger.error(f"Failed to send notification email: {str(e)}")
            return False