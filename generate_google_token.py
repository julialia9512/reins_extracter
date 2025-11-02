"""
Helper script to generate Google OAuth token for Google Sheets integration.
Run this once to authenticate with your Google account.

Prerequisites:
1. Create OAuth credentials in Google Cloud Console
2. Enable Google Sheets API
3. Download credentials.json file
4. Place credentials.json in the same directory as this script

Usage:
    python generate_google_token.py

This will:
1. Open your browser to log in with Google
2. Generate token.json file
3. Copy token.json contents to Streamlit Secrets as GOOGLE_CREDENTIALS
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

# Scopes needed for Google Sheets access
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def main():
    # Try to find credentials file
    creds_file = None
    
    # First, try credentials.json
    if os.path.exists('credentials.json'):
        creds_file = 'credentials.json'
    else:
        # Search for Google OAuth credentials files
        for file in os.listdir('.'):
            if file.startswith('client_secret_') and file.endswith('.json'):
                creds_file = file
                break
        
        # Also try client_secret.json
        if not creds_file and os.path.exists('client_secret.json'):
            creds_file = 'client_secret.json'
    
    if not creds_file:
        print("Error: OAuth credentials file not found!")
        print("\nPlease:")
        print("1. Go to Google Cloud Console")
        print("2. Create OAuth 2.0 Client ID credentials")
        print("3. Download the JSON file")
        print("4. Place it in the same directory as this script")
        print("   (Should be named credentials.json, client_secret.json, or client_secret_*.json)")
        return
    
    print(f"Found credentials file: {creds_file}")
    print("Starting Google OAuth flow...")
    print("This will open your browser to log in with Google.")
    print()
    
    try:
        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            creds_file,
            SCOPES
        )
        
        # Run the flow (opens browser)
        # Using port 8080 - make sure this EXACT URI is in authorized redirect URIs:
        # http://localhost:8080/  (with trailing slash!)
        # For web application OAuth clients, the redirect URI must match exactly
        try:
            creds = flow.run_local_server(port=8080)
        except Exception as e:
            print(f"\nError during OAuth flow: {str(e)}")
            print("\nTroubleshooting:")
            print("1. Make sure you added EXACTLY this redirect URI in Google Cloud Console:")
            print("   http://localhost:8080/  (with trailing slash)")
            print("2. If using 'Web application' type, the redirect URI must match exactly")
            print("3. Make sure you clicked SAVE after adding the redirect URI")
            print("4. Wait 1-2 minutes after saving for changes to propagate")
            print("\nTo fix:")
            print("- Go to Google Cloud Console → APIs & Services → Credentials")
            print("- Edit your OAuth 2.0 Client ID")
            print("- Under 'Authorized redirect URIs', add: http://localhost:8080/")
            print("- Click SAVE and wait 1-2 minutes")
            raise
        
        # Convert to JSON format
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        # Save to file
        with open('token.json', 'w') as token_file:
            json.dump(token_data, token_file, indent=2)
        
        print()
        print("Success! token.json has been created.")
        print()
        print("Next steps:")
        print("1. Open token.json")
        print("2. Copy the entire JSON content")
        print("3. Go to Streamlit Cloud → Your App → Settings → Secrets")
        print("4. Add: GOOGLE_CREDENTIALS = {paste the JSON content here}")
        print()
        print("Now you can use Google Sheets upload in the app!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nMake sure:")
        print("- credentials.json is valid OAuth 2.0 credentials")
        print("- Google Sheets API is enabled in your project")
        print("- You have internet connection")

if __name__ == '__main__':
    main()

