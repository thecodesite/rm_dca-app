import streamlit as st
import pandas as pd
import numpy as np
import xlsxwriter
from io import BytesIO
from datetime import *
import datetime
from datetime import datetime
from functions import dca_project, dca_project_dt, run_res_scenario, run_res_scenario_dt, rr_summary

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
    
    # Inputs
    well_list = inputs['Well_Name'].to_list()
    reserve_cat_list = inputs['Category'].to_list()
    activity_list = inputs['Activity'].to_list()
    psd_list = [str(date.strftime("%Y-%m-%d")) for date in inputs['Start Date'].to_list()]
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
    bsw_list = inputs['bsw'].to_list()
    b_list = inputs['b'].to_list()
    dt_list = inputs['Downtime'].to_list()
    rate_limit = 50
    #td = date(2049,4,17)
    
    # -----------------------------------
    
    # Set start forecast
    start_forecast_date = st.date_input(
        "Choose Start forecast:",
        min(inputs['Start Date'])
    )
    start_forecast_date = start_forecast_date.strftime("%Y-%m-%d")
    
    # Set Project Start Date
    proj_start_date = st.date_input(
        "Choose Project Start Date:",
        min(inputs['Start Date']) + pd.DateOffset(years=1)
    )
    proj_start_date = proj_start_date.strftime("%Y-%m-%d")
    
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
    st.write("Project Start Date:", proj_start_date)
    st.write("End Forecast Date:", forecast_end_date)

    # -----------------------------------------
    # Reserve 1P scenario
    result_1p= run_res_scenario_dt('1P', qi1p_list, di1p_list, psd_list, well_list, reserve_cat_list, activity_list, di1p_pro_list, project_active_wells, gor_list, bsw_list, forecast_end_date, proj_start_date, dt_list, end_date_list)
    # Reserve 2P scenario
    result_2p= run_res_scenario_dt('2P', qi2p_list, di2p_list, psd_list, well_list, reserve_cat_list, activity_list, di2p_pro_list, project_active_wells, gor_list, bsw_list, forecast_end_date, proj_start_date, dt_list, end_date_list)
    # Reserve 3P scenario
    result_3p= run_res_scenario_dt('3P', qi3p_list, di3p_list, psd_list, well_list, reserve_cat_list, activity_list, di3p_pro_list, project_active_wells, gor_list, bsw_list, forecast_end_date, proj_start_date, dt_list, end_date_list)
    # Concatenate reserve scenario
    df = pd.concat([result_1p, result_2p, result_3p], axis=0)

    # Pivot table 1P scenario
    pv_rc_year_1p=pd.pivot_table(result_1p, values=['oil_volume'], index=['reserve_cat'],
                   columns=['Year'], aggfunc="sum", sort=False)
    # Pivot table 2P scenario
    pv_rc_year_2p=pd.pivot_table(result_2p, values=['oil_volume'], index=['reserve_cat'],
                   columns=['Year'], aggfunc="sum", sort=False)
    # Pivot table 3P scenario
    pv_rc_year_3p=pd.pivot_table(result_3p, values=['oil_volume'], index=['reserve_cat'],
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
