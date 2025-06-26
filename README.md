# Reserve Calculator App

## Overview
A Streamlit web application for calculating oil & gas reserves and resources based on user-uploaded Excel input data. The app processes well data, runs decline curve analysis (DCA) scenarios, and generates summary tables with downloadable results.

## Features
- **Excel Data Upload**: Process .xlsx files with well production data
- **Interactive Date Selection**: Customizable forecast periods
- **Multi-Scenario Analysis**: 1P, 2P, and 3P reserve calculations
- **Comprehensive Summaries**: 
  - Annual production by reserve category
  - Reserve and resource classification summaries
- **One-Click Export**: Download all results as formatted Excel file

## Installation
1. Clone the repository:
   ```bash
   git clone [repository-url]
   ```
2. Install dependencies:
   ```bash
   pip install streamlit pandas numpy xlsxwriter
   ```

## Usage
### Input File Format
Your Excel file must include these columns (exact names required):

| Column          | Description                          | Example       |
|-----------------|--------------------------------------|---------------|
| Well_Name       | Well identifier                      | "Well-001"    |
| Category        | Reserve category (PDP, PDNP, PUD)    | "PDP"         |
| Activity        | Well activity type                   | "Producer"    |
| Start Date      | Production start date                | 2023-01-01    |
| End Date        | Production end date (before forecast end date)                  | 2023-01-01    |
| Di_1p/2p/3p     | Decline rates for each scenario (frac.)      | 0.15          |
| Qo_1p/2p/3p     | Initial production rates (STB/D)             | 500           |
| GOR             | Gas-Oil Ratio (scf/STB)                        | 800           |
| bsw             | Basic Sediments & Water (%)          | 20            |

### Running the App
```bash
streamlit run app.py
```

### Application Workflow
1. **Upload Data**: Click "Load Input data" and select your Excel file
2. **Set Forecast Period**:
   - Start Forecast Date (default: earliest well start)
   - Project Start Date (default: 1 year after earliest well)
   - End Forecast Date (default: 20 years after earliest well)
3. **Generate Results**:
   - Click "Run" to view detailed forecasts
   - Click summary buttons to view reserve/resource breakdowns
4. **Download**: Export all results as timestamped Excel file

## Output Files
The generated Excel file contains:
1. **Schedule**: Original input data
2. **Forecast_by_well**: Detailed production forecasts
3. **Reserve_Summary**: 1P/2P/3P reserve categorization
4. **Resource_Summary**: Contingent resource breakdown

## Dependencies
- Python 3.8+
- Streamlit (frontend)
- pandas (data processing)
- numpy (numerical calculations)
- xlsxwriter (Excel export)

## Architecture
```
/reserve-calculator/
├── app.py            # Main application
├── functions.py      # Calculation logic
├── requirements.txt  # Dependencies
└── README.md         # This file
```

## Troubleshooting
- **Date Errors**: Ensure all date columns contain valid dates or NA
- **Upload Issues**: Verify Excel file format (.xlsx) and column names
- **Calculation Errors**: Check for negative values in rate/decline parameters

## License
[MIT License](LICENSE)

---

Developed by [Jose Perez](mailto:jose.perez@example.com)  
For technical support or feature requests, please open an issue in the repository.
```

