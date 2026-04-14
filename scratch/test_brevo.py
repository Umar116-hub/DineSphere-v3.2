import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email():
    print("--- Brevo SMTP Diagnostic ---")
    
    # 1. Load environment variables
    if not os.path.exists('.env'):
        print("[ERROR] .env file not found!")
        return

    load_dotenv()
    
    user = os.environ.get('EMAIL_HOST_USER')
    password = os.environ.get('EMAIL_HOST_PASSWORD')
    from_email = os.environ.get('DEFAULT_FROM_EMAIL')
    
    print(f"User: {user}")
    print(f"From Email: {from_email}")
    if not password:
        print("[ERROR] EMAIL_HOST_PASSWORD is NOT set in .env!")
        return
    else:
        print("Password: [SET]")

    # 2. Setup Message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = from_email # Send to self for testing
    msg['Subject'] = "DineSphere SMTP Test"
    body = "This is a test email from the DineSphere diagnostic script."
    msg.attach(MIMEText(body, 'plain'))

    # 3. Connect and Send
    try:
        print("\nConnecting to smtp-relay.brevo.com:587...")
        server = smtplib.SMTP('smtp-relay.brevo.com', 587, timeout=10)
        
        print("Starting TLS...")
        server.starttls()
        
        print("Logging in...")
        server.login(user, password)
        
        print("Sending email...")
        server.send_message(msg)
        
        print("\n[SUCCESS] Email sent successfully!")
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        print("\n[ERROR] Authentication Failed! Please check your Brevo API key (EMAIL_HOST_PASSWORD).")
    except smtplib.SMTPConnectError:
        print("\n[ERROR] Could not connect to the SMTP server. Check your internet/firewall.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()
