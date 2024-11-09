import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from ..database import db
from ..utils.logger import logger
from ..utils.config import get_settings

settings = get_settings()

class AlertManager:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email

    async def send_email_alert(self, to_email: str, subject: str, body: str):
        """Send email alert to user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False

    async def process_alerts(self):
        """Process all unsent alerts"""
        try:
            # Get unsent alerts
            alerts = await db.db.sentiment_alerts.find(
                {"is_sent": False}
            ).to_list(1000)

            for alert in alerts:
                # Get user details
                user = await db.db.users.find_one({"_id": alert["user_id"]})
                if not user:
                    continue

                # Get company details
                company = await db.db.companies.find_one({"_id": alert["company_id"]})
                if not company:
                    continue

                # Get recent news articles for this company
                recent_articles = await db.db.news_articles.find({
                    "company_id": alert["company_id"],
                    "created_at": {"$gte": datetime.utcnow() - timedelta(days=1)}
                }).sort("created_at", -1).limit(5).to_list(5)

                # Create email content
                subject = f"Stock Alert: {company['name']} ({company['symbol']}) - {alert['alert_type'].upper()}"
                body = self._create_alert_email_body(
                    company,
                    alert,
                    recent_articles
                )

                # Send email
                if await self.send_email_alert(user["email"], subject, body):
                    # Mark alert as sent
                    await db.db.sentiment_alerts.update_one(
                        {"_id": alert["_id"]},
                        {"$set": {"is_sent": True}}
                    )

        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")

    def _create_alert_email_body(self, company, alert, articles):
        """Create HTML email body for alert"""
        action = "SELL" if alert["alert_type"] == "sell" else "BUY"
        
        html = f"""
        <html>
            <body>
                <h2>Stock Alert: {action} Opportunity</h2>
                <p>Company: {company['name']} ({company['symbol']})</p>
                <p>Sentiment Score: {alert['sentiment_score']:.2f}</p>
                <p>Alert Type: {alert['alert_type'].upper()}</p>
                
                <h3>Recent News Articles:</h3>
                <ul>
        """

        for article in articles:
            html += f"""
                <li>
                    <p><a href="{article['url']}">{article['title']}</a></p>
                    <p>Sentiment: {article['sentiment_label']} ({article['sentiment_score']:.2f})</p>
                    <p>Published: {article['published_date'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </li>
            """

        html += """
                </ul>
                <p>This is an automated alert based on news sentiment analysis.</p>
            </body>
        </html>
        """

        return html

# Create alert manager instance
alert_manager = AlertManager()