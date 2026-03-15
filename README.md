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
Provide a single Excel workbook (.xlsx) containing a flat table (one row per well). Column names are case-sensitive and must match exactly. The app requires the columns listed below; some are mandatory while others are optional but recommended.

| Column Name | Required | Type / Format | Units / Examples | Description / Notes |
|-------------:|:--------:|:--------------|:----------------:|---------------------|
| `Well_Name` | Yes | Text | Well-001 | Unique well identifier (string). No duplicates recommended.
| `Category` | Yes | Text | PDP / PDNP / PUD / Undeveloped | Reserve classification. Use project standard codes (e.g., PDP, PDNP, PUD).
| `Activity` | Yes | Text | Producer / Injector / Other | Activity type used for filtering and scheduling.
| `Start Date` | Yes | Date (YYYY-MM-DD) | 2023-01-01 | Date when production starts. Must be a valid Excel date or ISO string.
| `End Date` | No | Date (YYYY-MM-DD) or blank | 2025-12-31 | Last actual production date before forecast begins. Leave blank if still producing.
| `Qo_1p` | Conditional* | Numeric | STB/day (e.g., 500) | Initial production rate for 1P scenario. Required when `Di_1p` is provided.
| `Qo_2p` | Conditional* | Numeric | STB/day | Initial production rate for 2P scenario.
| `Qo_3p` | Conditional* | Numeric | STB/day | Initial production rate for 3P scenario.
| `Di_1p` | Conditional* | Numeric (fraction) | e.g., 0.15 | Nominal decline rate for 1P (expressed as fraction per period). If using percent, convert to fraction (15% → 0.15).
| `Di_2p` | Conditional* | Numeric (fraction) | e.g., 0.12 | Decline rate for 2P scenario.
| `Di_3p` | Conditional* | Numeric (fraction) | e.g., 0.10 | Decline rate for 3P scenario.
| `GOR` | No | Numeric | scf/STB (e.g., 800) | Gas-to-oil ratio. Used to estimate associated gas volumes.
| `wcut` | No | Numeric (fraction 0-1) | e.g., 0.2 | Water cut (fraction of water in liquids). Use fraction (20% → 0.2). If your dataset uses percent, convert to fraction.
| `wct_a` / `wcut_a` | No | Numeric (fraction) | e.g., 0.2 | Parameter `a` for exponential water-cut (WCT = a * exp(b * Np)). `wct_a` is preferred; legacy `wcut_a` also accepted.
| `wct_b` / `wcut_b` | No | Numeric | e.g., -0.0001 | Parameter `b` for exponential water-cut. `wct_b` is preferred; legacy `wcut_b` also accepted.
| `Water_Mode` | No | Text | liquid_rate / constant_wc / wcut_exp | Per-well water computation mode. See notes for behaviour.
| `Project` | No | Boolean / 0/1 | True / False / 1 / 0 | Flag indicating whether the well is active during the project period. If True, a secondary decline (`Di_*_pro`) is applied after `Project Start Date`.
| `Project Start Date` | No | Date (YYYY-MM-DD) | 2024-01-01 | Optional per-well project start date used to switch to the `Di_*_pro` decline. If missing, global project start is used.
| `Di_1p_pro` | No | Numeric (fraction) | e.g., 0.20 | Post-project decline rate (1P) applied after `Project Start Date`.
| `Di_2p_pro` | No | Numeric (fraction) | e.g., 0.18 | Post-project decline rate (2P).
| `Di_3p_pro` | No | Numeric (fraction) | e.g., 0.15 | Post-project decline rate (3P).
| `Downtime` | No | Numeric (fraction) | e.g., 0.05 | Fraction of time the well is unavailable; used to reduce `Uptime`.
| `Historical_Oil_Cum` | No | Numeric | STB (e.g., 120000) | Historical cumulative oil produced for the well. Used when computing exponential water-cut curves.
| `Comments` | No | Text | Free text | Optional comments; the app coerces this column to string when present.
| `b` | No | Numeric | -- | (Reserved) present in inputs but not required by core DCA routines; keep if used by custom workflows.
| `Fluid_Type` | No | Text | Oil / Gas / Condensate | Optional descriptor used in reporting.
| `API` | No | Numeric | °API (e.g., 35) | Oil gravity, if available.
| `Operator` | No | Text | Operator name | Useful for grouping/filtering reports.
| `Field` | No | Text | Field name | Field or asset name where the well is located.

Notes:
- Conditional columns: provide both `Qo_*` and `Di_*` for any scenario you want calculated (e.g., `Qo_1p` + `Di_1p` for 1P). Missing scenario values will cause that scenario to be skipped for the well.
- `Project` can be boolean (`True`/`False`) or numeric (`1`/`0`). When `Project` is true for a well and a `Project Start Date` is supplied, the code applies the corresponding `Di_*_pro` decline after that date.
- Water modes:
   - `liquid_rate` (default): legacy behaviour based on initial balance.
   - `constant_wc`: water rate computed as oil_rate * (wcut / (1 - wcut)).
   - `wcut_exp`: exponential water-cut: WCT = a * exp(b * Np), where `a`=`wct_a` (defaults to `wcut` if missing), `b`=`wct_b` (defaults to 0). `Np` includes `Historical_Oil_Cum` + future cumulative oil.
- `wcut`, `wct_a`, `wct_b` should be fractions (0–1). If your data uses percent, convert to fractions (e.g., 20% → 0.2).
- `Downtime` is subtracted from uptime; supply as fraction (e.g., 0.05 → 5% downtime).
- Date formats: accept Excel date types or ISO strings (YYYY-MM-DD). Avoid ambiguous formats (MM/DD/YYYY) to prevent locale-related parsing errors.
- Units: production in stock tank barrels per day (STB/D) and GOR in standard cubic feet per stock tank barrel (scf/STB). Gas rate is computed as `gas_rate = oil_rate * GOR / 1000` (so GOR in scf/STB produces gas in Mscf/day when divided by 1000).
- Minimum rate cutoff: the model applies a 50 STB/day cutoff — rates below 50 STB/day are set to zero in forecasts.
- `wct_a`/`wct_b` vs `wcut_a`/`wcut_b`: the app accepts both new (`wct_*`) and legacy (`wcut_*`) parameter names; prefer `wct_*`.

### Running the App

```bash
streamlit run app.py
```

### Application Workflow

1. **Upload Data**: Click "Load Input data" and select your Excel file (single sheet with the table). The app validates required columns and reports any missing/invalid fields.
2. **Set Forecast Period**:
   - Start Forecast Date: default is the earliest `Start Date` in the dataset.
   - Project Start Date: default is 1 year after the earliest well start (configurable in UI).
   - End Forecast Date: default is 20 years after the earliest well (configurable).
3. **Select Scenarios**: Choose which reserve scenarios to run (1P / 2P / 3P). The app will only calculate scenarios for wells that have the corresponding `Qo_*` and `Di_*` values.
4. **Generate Results**:
   - Click "Run" to compute forecasts and reserves. The UI shows per-well forecasts and aggregated summaries.
   - Use summary buttons to view reserve/resource breakdowns by category, field, or operator.
5. **Download**: Export all results as a timestamped Excel file containing schedule, forecasts, and summary sheets.

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

Developed by [Jose Perez](mailto:perezjgg@gamail.com)  
For technical support or feature requests, please open an issue in the repository.
```
