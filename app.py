import streamlit as st
import pandas as pd
import numpy as np
import xlsxwriter
from io import BytesIO
from datetime import *
import datetime
from datetime import datetime
from functions import dca_project_dt, run_res_scenario_dt, rr_summary

# Application Name
st.title("Reserve Calculator")

# Load excel file
file = st.file_uploader("Load Input data (MS Excel file)", type=["xlsx"])

if file is not None:
    # Read excel file
    inputs = pd.read_excel(file)
    #st.write("Load data:")
    #st.write(inputs)

    # Fix: Ensure Comments column is string type for Arrow compatibility
    if 'Comments' in inputs.columns:
        inputs['Comments'] = inputs['Comments'].astype(str)
    st.write("Load data:")
    st.write(inputs)
       
    # ------------------------------------------
    
    # Inputs with defaults for missing columns
    well_list = inputs['Well_Name'].to_list()
    reserve_cat_list = inputs['Category'].to_list()
    activity_list = inputs['Activity'].to_list()
    psd_list = [str(date.strftime("%Y-%m-%d")) for date in inputs['Start Date'].to_list()]
    prosd_list = [str(date.strftime("%Y-%m-%d")) if pd.notnull(date) and hasattr(date, "strftime") else "" for date in inputs['Project Start Date'].to_list()] ## Project Start Date
    di1p_list = inputs['Di_1p'].to_list()
    di2p_list = inputs['Di_2p'].to_list()
    di3p_list = inputs['Di_3p'].to_list()
    qi1p_list = inputs['Qo_1p'].to_list()
    qi2p_list = inputs['Qo_2p'].to_list()
    qi3p_list = inputs['Qo_3p'].to_list()
    di1p_pro_list = inputs['Di_1p_pro'].to_list()
    di2p_pro_list = inputs['Di_2p_pro'].to_list()
    di3p_pro_list = inputs['Di_3p_pro'].to_list()
    project_active_wells = inputs['Project'].to_list()
    gor_list = inputs['GOR'].to_list()
    wcut_list = inputs['wcut'].tolist() if 'wcut' in inputs.columns else (inputs['wcut'].tolist() if 'wcut' in inputs.columns else [0]*len(inputs))
    b_list = inputs['b'].to_list()
    dt_list = inputs['Downtime'].to_list()
    water_mode_list = inputs['Water_Mode'].tolist() if 'Water_Mode' in inputs.columns else ['wcut_exp']*len(inputs)
    #st.write("Water Mode List:", water_mode_list)  # Debug: mostrar los modos de agua

    # Allow both 'wct_a'/'wct_b' and legacy 'wcut_a'/'wcut_b' column names.
    wct_a_raw = inputs['wct_a'] if 'wct_a' in inputs.columns else (inputs['wcut_a'] if 'wcut_a' in inputs.columns else pd.Series([np.nan]*len(inputs)))
    wct_b_raw = inputs['wct_b'] if 'wct_b' in inputs.columns else (inputs['wcut_b'] if 'wcut_b' in inputs.columns else pd.Series([np.nan]*len(inputs)))

    # Coerce to numeric and validate
    wct_a_numeric = pd.to_numeric(wct_a_raw, errors='coerce')
    wct_b_numeric = pd.to_numeric(wct_b_raw, errors='coerce')
    invalid_mask = wct_a_numeric.isna() | wct_b_numeric.isna()
    if invalid_mask.any():
        invalid_wells = [
            f"{well}: wct_a={wct_a_raw.iloc[i]!r}, wct_b={wct_b_raw.iloc[i]!r}"
            for i, well in enumerate(well_list)
            if invalid_mask.iloc[i]
        ]
        st.error(
            "Invalid wct_a/wct_b values detected for the following wells (must be numeric):\n" + "\n".join(invalid_wells)
        )
        st.stop()

    wct_a_list = wct_a_numeric.tolist()
    wct_b_list = wct_b_numeric.tolist()

    historical_oil_cum_list = inputs['Historical_Oil_Cum'].tolist() if 'Historical_Oil_Cum' in inputs.columns else [0]*len(inputs)
    rate_limit = 50
       
    # ------------------------------------------
    
    # Set start forecast
    start_forecast_date = st.date_input(
        "Choose Start forecast:",
        min(inputs['Start Date'])
    )
    start_forecast_date = start_forecast_date.strftime("%Y-%m-%d")
    
    # Set Project Start Date
    #proj_start_date = st.date_input(
    #    "Choose Project Start Date:",
    #    min(inputs['Project Start Date'])
    #)
    #proj_start_date = proj_start_date.strftime("%Y-%m-%d")
      
    # Set End Forecast Date
    forecast_end_date = st.date_input(
        "Choose End Forecast Date:",
        min(inputs['Start Date']) + pd.DateOffset(years=20)
    )
    forecast_end_date = forecast_end_date.strftime("%Y-%m-%d")
    
    # Set End Date list
    # If End Date is not provided, use forecast_end_date
    end_date_list = [
        str(date.strftime("%Y-%m-%d")) if pd.notnull(date) and hasattr(date, "strftime") else forecast_end_date
        for date in inputs['End Date'].to_list()
    ]

    # Show choosen dates
    st.write("Start forecast:", start_forecast_date)
    #st.write("Project Start Date:", proj_start_date)
    st.write("End Forecast Date:", forecast_end_date)

    # -----------------------------------------
    # Reserve 1P scenario
    result_1p= run_res_scenario_dt('1P', qi1p_list, di1p_list, psd_list, well_list, reserve_cat_list, activity_list, di1p_pro_list, project_active_wells, gor_list, wcut_list, forecast_end_date, prosd_list, dt_list, end_date_list, water_mode_list, wct_a_list, wct_b_list, historical_oil_cum_list)
    # Reserve 2P scenario
    result_2p= run_res_scenario_dt('2P', qi2p_list, di2p_list, psd_list, well_list, reserve_cat_list, activity_list, di2p_pro_list, project_active_wells, gor_list, wcut_list, forecast_end_date, prosd_list, dt_list, end_date_list, water_mode_list, wct_a_list, wct_b_list, historical_oil_cum_list)
    # Reserve 3P scenario
    result_3p= run_res_scenario_dt('3P', qi3p_list, di3p_list, psd_list, well_list, reserve_cat_list, activity_list, di3p_pro_list, project_active_wells, gor_list, wcut_list, forecast_end_date, prosd_list, dt_list, end_date_list, water_mode_list, wct_a_list, wct_b_list, historical_oil_cum_list)
    # Concatenate reserve scenario
    df = pd.concat([result_1p, result_2p, result_3p], axis=0)

    # Pivot table 1P scenario (guard against empty / missing columns)
    if result_1p is None or result_1p.empty or 'oil_volume' not in result_1p.columns:
        pv_rc_year_1p = pd.DataFrame()
    else:
        pv_rc_year_1p = pd.pivot_table(result_1p, values=['oil_volume'], index=['reserve_cat'],
                       columns=['Year'], aggfunc="sum", sort=False)
    # Pivot table 2P scenario
    if result_2p is None or result_2p.empty or 'oil_volume' not in result_2p.columns:
        pv_rc_year_2p = pd.DataFrame()
    else:
        pv_rc_year_2p = pd.pivot_table(result_2p, values=['oil_volume'], index=['reserve_cat'],
                       columns=['Year'], aggfunc="sum", sort=False)
    # Pivot table 3P scenario
    if result_3p is None or result_3p.empty or 'oil_volume' not in result_3p.columns:
        pv_rc_year_3p = pd.DataFrame()
    else:
        pv_rc_year_3p = pd.pivot_table(result_3p, values=['oil_volume'], index=['reserve_cat'],
                       columns=['Year'], aggfunc="sum", sort=False)
    # Reserve & Resource Summary
    reserve_summary, resource_summary = rr_summary(pv_rc_year_1p, pv_rc_year_2p, pv_rc_year_3p)
    
    # Button to run calcs
    if st.button("Run"):
        # Compute
        st.write(df)
    
    # Button to gnerate Reserve & Resource Summary
    if st.button("Generate Reserve Summary"):
        st.write(reserve_summary)
        
    # Button to gnerate Reserve & Resource Summary
    if st.button("Generate Resource Summary"):
        st.write(resource_summary)
        
    # -----------------------------------------
    # Buttom to export results
    # Create a BytesIO buffer
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # use to_excel function and specify the sheet_name and index 
        # to store the dataframe in specified sheet
        #Schedule
        inputs.to_excel(writer, sheet_name='Schedule')
        #Total Dataframe
        df.to_excel(writer, sheet_name='Forecast_by_well')
        reserve_summary.to_excel(writer, sheet_name='Reserve_Summary')
        resource_summary.to_excel(writer, sheet_name='Resource_Summary')
    
    # Get the in-memory string
    file_name="results"+'_'+datetime.now().strftime('%d%m%Y_%H%M%S')+".xlsx"
    excel_data = output.getvalue()
    st.download_button(
        label="Download Results",
        data=excel_data,
       file_name=file_name,
    )
