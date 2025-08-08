
import os
import sys
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class WebsiteExpiryMiddleware(MiddlewareMixin):
    """
    Single-file middleware that automatically disables website after 15 days
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.expiry_file = os.path.join(settings.BASE_DIR, '.website_start_date')
        self.lock_file = os.path.join(settings.BASE_DIR, '.website_expired_lock')
        
        # Check expiry on startup
        self.check_and_handle_expiry()

    def check_and_handle_expiry(self):
        """Check if website has expired and handle accordingly"""
        try:
            # If already expired and locked, exit immediately
            if os.path.exists(self.lock_file):
                self.show_expired_message()
                sys.exit("Website expired - Application terminated")
            
            # Create start date file if it doesn't exist
            if not os.path.exists(self.expiry_file):
                with open(self.expiry_file, 'w') as f:
                    f.write(datetime.now().isoformat())
                print("🟢 Website expiry timer started - Will expire in 15 days")
                return
            
            # Read start date and check expiry
            with open(self.expiry_file, 'r') as f:
                start_date = datetime.fromisoformat(f.read().strip())
            
            current_date = datetime.now()
            expiry_date = start_date + timedelta(days=15)
            days_remaining = (expiry_date - current_date).days
            
            if current_date > expiry_date:
                # Website has expired
                self.create_lock_file(current_date)
                self.show_expired_message()
                sys.exit("Website expired after 15 days - Application terminated")
            else:
                # Still active
                print(f"⏰ Website expires in {days_remaining} days ({expiry_date.strftime('%Y-%m-%d %H:%M:%S')})")
                
        except Exception as e:
            print(f"❌ Expiry check error: {e}")

    def create_lock_file(self, expired_date):
        """Create lock file to prevent restart"""
        with open(self.lock_file, 'w') as f:
            f.write(f"Website expired on: {expired_date.isoformat()}\n")
            f.write("To reset: Delete both .website_start_date and .website_expired_lock files\n")

    def show_expired_message(self):
        """Display expiry message"""
        print("=" * 60)
        print("🚨 WEBSITE EXPIRED! 🚨")
        print("This website has been automatically disabled after 15 days.")
        print("To reset the timer:")
        print("1. Delete .website_start_date file")
        print("2. Delete .website_expired_lock file") 
        print("3. Restart the server")
        print("=" * 60)

    def process_request(self, request):
        """Block all requests if website is expired"""
        if os.path.exists(self.lock_file):
            return HttpResponse(
                """
                <html>
                <head><title>Website Expired</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #d32f2f;">🚨 Website Expired</h1>
                    <p>This website has been automatically disabled after 15 days.</p>
                    <p>Contact the administrator to reactivate.</p>
                </body>
                </html>
                """,
                status=503
            )
        return None

    def __call__(self, request):
        # Check for expiry on each request
        response = self.process_request(request)
        if response:
            return response
        
        response = self.get_response(request)
        return response


# Auto-run expiry check when module is imported
try:
    if hasattr(settings, 'BASE_DIR'):
        middleware = WebsiteExpiryMiddleware(lambda x: x)
except Exception as e:
    print(f"Failed to initialize expiry check: {e}")
