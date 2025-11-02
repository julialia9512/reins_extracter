# REINS Extractor

A Streamlit web application for extracting real estate data from HTML tables and exporting to Excel.

## Features

- **Apartment/Mansion Parsing**: Extract apartment listings with detailed information
- **Villa/Standalone House Parsing**: Extract villa/house listings with building and land area
- **Automatic Calculations**: 
  - Price per ㎡ for apartments and villas
  - Price per tsubo (坪) for apartments
  - Automatic data normalization
- **Data Export**: Export to Excel format with separate sheets
- **Date Tracking**: Automatically adds input date (YYYYMMDD) to each record

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/reins_extracter.git
cd reins_extracter
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Local Development

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. The app will open in your browser. You can:
   - Paste HTML content in the appropriate tab (Apartment or Villa)
   - Preview the extracted data
   - Download as Excel file

### Hosting Online (Streamlit Community Cloud)

To host this app online so you can access it without running locally:

1. **Go to Streamlit Community Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)

2. **Sign in with GitHub**: Click "Sign in" and authorize with your GitHub account

3. **Deploy your app**:
   - Click "New app"
   - Select your repository: `github account name/reins_extracter`
   - Set Main file path to: `app.py`
   - Click "Deploy"

4. **Access your app**: Once deployed, you'll get a URL like:
   ```
   https://reins-extracter.streamlit.app
   ```
   You can access this URL from anywhere, anytime!

5. **Set a password** (Recommended for privacy):
   - After deployment, go to your app's Settings
   - Click "Secrets"
   - Add: `APP_PASSWORD = "your_secure_password"`
   - Or edit `app.py` and change `PASSWORD = "change_this_password"` to your desired password


**Note**: Your app will automatically update whenever you push changes to the `main` branch on GitHub.

### Google Sheets Integration

The app supports direct upload to Google Sheets. For **personal use**, OAuth (User Login) is the simplest method:

#### OAuth (User Login) - **Recommended for personal use**

This method uses your Google account login - you authenticate once, and it works with any spreadsheet you have access to.

**Note**: You need to create OAuth credentials in Google Cloud Console once (it's required by Google APIs), but after that you just use your Google account login - no need to share spreadsheets or manage service accounts.

1. **One-time setup - Create OAuth credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Choose **"Desktop app"** (recommended) or "Web application"
   - **IMPORTANT**: For the token generation script (one-time local use), add ALL these redirect URIs:
     - `http://localhost:8080` (without trailing slash)
     - `http://localhost:8080/` (with trailing slash - this is what the script uses)
     - `http://localhost` (general use)
     - `http://127.0.0.1:8080` (IP address version)
     - `http://127.0.0.1:8080/` (IP address with trailing slash)
   - Download the JSON file (contains `client_id`, `client_secret`, etc.)
   
   **Note**: The `localhost` redirect URIs are ONLY for generating the token on your computer. Once you have the token and deploy to Streamlit Cloud, the app uses the stored token - no redirect URIs needed for the deployed app!

2. **Generate access token** (one-time):
   - Place the downloaded `credentials.json` in your project folder
   - Run the helper script: `python generate_google_token.py`
   - This will open your browser - log in with your Google account and authorize
   - The `token.json` file will be created automatically
   - Or manually run the script code (see `generate_google_token.py` for reference)

3. **Configure in Streamlit**:
   - Copy the contents of `token.json` 
   - Go to your app's Settings → Secrets
   - Add: `GOOGLE_CREDENTIALS = {paste the token.json content here}`

4. **Upload data**:
   - After extracting data, use the "📊 Google Sheets にアップロード" section
   - Enter your Spreadsheet ID (from the URL: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`)
   - Enter the sheet name
   - Click upload!

**✅ Advantages**: Works with your own Google account, no need to share spreadsheets, access to all your sheets automatically.

---

#### (Optional) Service Account - Only if you need automation/shared access

**You can skip this if you're using it personally!** 

**Key difference**: 
- **OAuth**: Uses YOUR Google account → automatically access all your spreadsheets (no sharing needed)
- **Service Account**: Uses a "robot" account → you must manually share EACH spreadsheet with the service account email

Service Account is only needed for:
- Automated scripts that run without user interaction
- Shared access where multiple people need the same credentials
- Services that need to access sheets without a user login

If you still want to use Service Account:

1. **Create a Google Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Sheets API
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Download the JSON key file

2. **Share your Google Spreadsheet**:
   - Open your Google Spreadsheet
   - Click "Share" button
   - Add the service account email (from the JSON file, looks like `xxx@xxx.iam.gserviceaccount.com`)
   - Give it "Editor" permissions

3. **Configure in Streamlit**:
   - Go to your app's Settings → Secrets
   - Add: `GOOGLE_CREDENTIALS = {paste the entire service account JSON here}`

4. **Upload data** (same as Method 1)

**✅ Advantages**: No user interaction needed, good for automation.

## Features by Property Type

### Apartments (マンション/区分)
- Number, Property ID, Property Type
- Private Area (㎡)
- Location, Transaction Type
- Price (万円), Usage Zone
- Price per ㎡, Building Name, Floor
- Layout, Transaction Status
- Management Fee, Price per Tsubo
- Station, Walking Time
- Company Name, Build Date, Phone Number
- Input Date

### Villas (戸建/ヴィラ)
- Number, Property ID, Property Type
- Land Area (㎡)
- Location, Transaction Type
- Price (万円), Usage Zone
- Building Area (㎡), Price per ㎡
- Layout, Transaction Status
- Road Access Status
- Station, Walking Time, Road Access 1
- Company Name, Build Date, Phone Number
- Input Date

## Requirements

- Python 3.8+
- streamlit
- pandas
- beautifulsoup4
- lxml
- xlsxwriter
- gspread (for Google Sheets integration - optional)
- google-auth (for Google Sheets integration - optional)

## License

MIT

