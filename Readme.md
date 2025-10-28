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

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. The app will open in your browser. You can:
   - Paste HTML content in the appropriate tab (Apartment or Villa)
   - Preview the extracted data
   - Download as Excel file

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

## License

MIT

