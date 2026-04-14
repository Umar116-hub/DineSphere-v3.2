import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dinesphere.settings')
django.setup()

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def test_django_email():
    print("--- Django Email Context Diagnostic ---")
    
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    subject = "DineSphere Django Test"
    text_content = "This is a test email sent using Django's email backend."
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [settings.DEFAULT_FROM_EMAIL] # Send to self
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    
    try:
        print("\nAttempting to send via Django backend...")
        msg.send(fail_silently=False)
        print("\n[SUCCESS] Django email sent successfully!")
    except Exception as e:
        print(f"\n[ERROR] Django failed to send email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_django_email()
