import datetime
from datetime import *
from datetime import datetime
import calendar
from datetime import date
import numpy as np
import pandas as pd


# dca_project_dt() function includes downtime
# Added support for a third water computation method based on an exponential water-cut:
#   WCT = a * exp(b * Np)
# where Np is cumulative oil production (volume), including historical cumulative oil.
# The resulting water rate is computed as:
#   water_rate = oil_rate * (WCT / (1 - WCT))
# (with WCT capped to [0, 0.999999] to avoid division by zero).
def dca_project_dt(qoi, di, prod_start_date, fore_end_date, dip, proj_start_date, project_active_well, gor, wcut, dt, water_mode='liquid_rate', wct_a=None, wct_b=None, historical_oil_cum=0):
    '''import calendar
    from datetime import *'''
    #Inputs
    prod_start_date = datetime.strptime(prod_start_date, "%Y-%m-%d")
    proj_start_date = datetime.strptime(proj_start_date, "%Y-%m-%d")
    forecast_end_date = datetime.strptime(fore_end_date, "%Y-%m-%d")
    
    #Generate range dates list
    forecast_start_date = prod_start_date.replace(day=1)
    date1 = forecast_start_date
    date2 = forecast_end_date
    
    #create list to store dates
    range_dates_list = [] 
    
    # Loop
    while date1 < date2:
        month = date1.month
        year  = date1.year
        day  = date1.day
        # Append forecast start date
        range_dates_list.append(date1)
        # Generate range dates
        next_month = month + 1 if month != 12 else 1
        next_year = year + 1 if next_month == 1 else year
        next_day = 1
        date1 = date1.replace(month = next_month, year = next_year, day=next_day)
    
    # Append forecast end date
    month = date2.month
    year  = date2.year
    day  = date2.day
    range_dates_list.append(date2)
    # Print list
    range_dates_list
    
    # Compute effective production days per well
    # Create empty list to store prod. days
    days_prod=[]
    #Compute first days prod
    non_effective_prod_days=prod_start_date-forecast_start_date
    first_days_prod=range_dates_list[1]-range_dates_list[0]-non_effective_prod_days
    rest_of_days_prod = [range_dates_list[i+2]-range_dates_list[i+1] for i in range(len(range_dates_list)-2)]
    days_prod=np.append(first_days_prod,rest_of_days_prod).tolist()
    
    #Calculate total days available per month in order to compute Update time
    days_month=[range_dates_list[i+1]-range_dates_list[i] for i in range(len(range_dates_list)-1)]
       
    # Create dataframe
    df=pd.DataFrame()
    df['Dates']=pd.Series(range_dates_list)
    df['Days_prod']=pd.Series(days_prod).dt.days
    df['Cum_days_prod']=pd.Series(days_prod).dt.days.cumsum().shift().fillna(0)
    df['Days_month']=pd.Series(days_month).dt.days
    df['Uptime']=(df['Days_prod']/df['Days_month']).fillna(0)-dt   
    
    # Compute oil rate (qo)   
    project_active_well = project_active_well
    qo_list = []
    if project_active_well == True:
        for x, y, z in zip(df['Cum_days_prod'].to_list(), df['Uptime'].to_list(), range_dates_list):
            if z <= proj_start_date:
                q1 =qoi*np.exp((-di/365)*x)
                if q1 >= 50:
                    qo_list.append(q1)
                else:
                    qo_list.append(0)
            else:
                qoi_=q1
                #print((z-proj_start_date))
                #print(z)
                q2 =qoi_*np.exp((-dip/365)*(z-proj_start_date).days)
                if q2 >= 50:
                    qo_list.append(q2)
                else:
                    qo_list.append(0)
    if project_active_well == False:
        for x, y, z in zip(df['Cum_days_prod'].to_list(), df['Uptime'].to_list(), range_dates_list):
            q1 =qoi*np.exp((-di/365)*x)
            if q1 >= 50:
                qo_list.append(q1)
            else:
                qo_list.append(0)
    
    # Rates Oil, Gas, Water
    #Oil
    df['oil_rate']=pd.Series(qo_list)*df['Uptime'].to_list()
    #Gas
    df['gas_rate']=df['oil_rate']*gor/1000

    # Volumes/Cum Oil, Gas (needed for exponential water cut calculation)
    df['oil_volume']=(df['oil_rate']*df['Days_month']).fillna(0)
    df['oil_cum']=(df['oil_rate']*df['Days_month']).cumsum().shift().fillna(0)
    df['gas_volume']=(df['gas_rate']*df['Days_month']).fillna(0)
    df['gas_cum']=(df['gas_rate']*df['Days_month']).cumsum().shift().fillna(0)

    # Water
    # Three supported water computation modes:
    # - 'liquid_rate' (default): keep existing behaviour (based on initial qoi balance)
    # - 'constant_wc': compute water rate as oil_rate * (wcut / (1 - wcut)) (constant water cut)
    # - 'wcut_exp': compute water rate using an exponential water-cut curve WCT = a * exp(b * Np)
    #     where Np is cumulative oil production (historical + future oil_cum)

    if water_mode == 'constant_wc':
        # water rate proportional to oil_rate using water cut (wcut)
        # wcut is fraction of water in liquids; water_rate = oil_rate * (wcut / (1 - wcut))
        df['water_rate'] = df['oil_rate'] * (wcut / (1 - wcut))
        # If oil_rate is zero (or negative), ensure water_rate is zero
        df.loc[df['oil_rate'] <= 0, 'water_rate'] = 0
    elif water_mode == 'wcut_exp':
        # Ensure parameters are set
        if wct_a is None:
            wct_a = wcut
        if wct_b is None:
            wct_b = 0

        # Compute water cut (WCT) using exponential curve based on cumulative oil (Np = historical + future)
        # Cap WCT in [0, 0.999999] to avoid division by zero
        wct_dynamic = wct_a * np.exp(wct_b * (historical_oil_cum + df['oil_cum']))
        wct_dynamic = np.clip(wct_dynamic, 0, 0.999999)

        # Water rate computed from oil rate and the water cut
        df['water_rate'] = df['oil_rate'] * (wct_dynamic / (1 - wct_dynamic))
        df.loc[df['oil_rate'] <= 0, 'water_rate'] = 0
    else:
        water_list = []
        for q in qo_list:
            if q>0:
                # original behaviour: a balance where initial water + initial oil - current oil
                w = qoi + qoi * (wcut / (1 - wcut)) - q
            else:
                w = 0
            water_list.append(w)
        df['water_rate'] = pd.Series(water_list)

    #Liquid
    df['liquid_rate']=df['oil_rate']+df['water_rate']
    
    # GOR, Wcut
    df['gor']=gor
    if water_mode == 'wcut_exp':
        df['wcut'] = wct_dynamic
    else:
        df['wcut'] = wcut
    
    # Water Volumes/Cum Water
    df['water_volume']=(df['water_rate']*df['Days_month']).fillna(0)
    df['water_cum']=(df['water_rate']*df['Days_month']).cumsum().shift().fillna(0)
    
    # Historical cumulative oil + future cumulative oil (used for exponential water cut calculation and for display)
    df['oil_cum_total'] = historical_oil_cum + df['oil_cum']
    
    return df
  
# --- Update: Support end date by well in run_res_scenario_dt ---    
def run_res_scenario_dt(
    reserve_scenario, qi_list, di_list, psd_list, well_list, reserve_cat_list, activity_list,
    di_pro_list, project_active_wells, gor_list, wcut_list, forecast_end_date, proj_start_date, dt_list, end_date_list=None,
    water_mode='liquid_rate', wct_a_list=None, wct_b_list=None, historical_oil_cum_list=None
):
    import pandas as pd
    df_list = []
    for idx, (qi, di, psd, w, c, a, di_pro, paw, gor, wcut, dt) in enumerate(
        zip(qi_list, di_list, psd_list, well_list, reserve_cat_list, activity_list, di_pro_list, project_active_wells, gor_list, wcut_list, dt_list)
    ):
        # Use per-well end date if provided, else use global forecast_end_date
        if end_date_list is not None:
            well_end_date = end_date_list[idx]
            # If NaT or NaN, fallback to global
            if pd.isnull(well_end_date):
                well_end_date = forecast_end_date
            # If it's a Timestamp, convert to string
            if not isinstance(well_end_date, str):
                well_end_date = str(well_end_date.date())
        else:
            well_end_date = forecast_end_date
        # Determine per-well project start date (support both a global string or a per-well list)
        try:
            # Determine per-well project start date (support both a global string or a per-well list)
            if isinstance(proj_start_date, (list, tuple, pd.Series)):
                # If element is missing or empty, fall back to the production start date for the well
                proj_start_candidate = proj_start_date[idx]
                if pd.isnull(proj_start_candidate) or proj_start_candidate == "":
                    proj_start_candidate = psd
            else:
                proj_start_candidate = proj_start_date

            # Determine water mode for the well (default to 'liquid_rate' if not provided)
            # Support both a single string or a per-well list/series
            water_mode_candidate = 'liquid_rate'
            # If caller provided a variable named 'water_mode' (via kwargs), it will be processed below
            # NOTE: Backwards-compatible: no change unless caller passes water_mode into this function
            if 'water_mode' in locals():
                water_mode_candidate = locals()['water_mode']

            # Determine per-well water_mode (support single string or list)
            if isinstance(water_mode, (list, tuple, pd.Series)):
                water_mode_candidate = water_mode[idx]
                if pd.isnull(water_mode_candidate) or water_mode_candidate == "":
                    water_mode_candidate = 'liquid_rate'
            else:
                water_mode_candidate = water_mode or 'liquid_rate'

            # Determine per-well exponential water cut parameters
            wct_a_candidate = None
            wct_b_candidate = None
            if isinstance(wct_a_list, (list, tuple, pd.Series)):
                wct_a_candidate = wct_a_list[idx]
            else:
                wct_a_candidate = wct_a_list
            if isinstance(wct_b_list, (list, tuple, pd.Series)):
                wct_b_candidate = wct_b_list[idx]
            else:
                wct_b_candidate = wct_b_list

            # Determine per-well historical oil cumulative
            historical_oil_cum_candidate = 0
            if isinstance(historical_oil_cum_list, (list, tuple, pd.Series)):
                historical_oil_cum_candidate = historical_oil_cum_list[idx]
                if pd.isnull(historical_oil_cum_candidate):
                    historical_oil_cum_candidate = 0
            else:
                historical_oil_cum_candidate = historical_oil_cum_list or 0

            df_well = dca_project_dt(qi, di, psd, well_end_date, di_pro, proj_start_candidate, paw, gor, wcut, dt,
                                     water_mode=water_mode_candidate, wct_a=wct_a_candidate, wct_b=wct_b_candidate, historical_oil_cum=historical_oil_cum_candidate)
            df_well = df_well.reset_index()
            df_well['Year'] = pd.to_datetime(df_well['Dates']).dt.year
            df_well['well_name'] = w
            df_well['reserve_cat'] = c
            df_well['activity'] = a
            df_well = df_well[[
                'Dates', 'Year', 'well_name', 'reserve_cat', 'activity',
                'Days_prod', 'Cum_days_prod', 'Days_month', 'Uptime',
                'oil_rate', 'oil_volume', 'oil_cum', 'oil_cum_total',
                'gor', 'gas_rate', 'gas_volume', 'gas_cum',
                'wcut', 'water_rate', 'water_volume', 'water_cum'
            ]]
            df_well['Dates'] = pd.to_datetime(df_well['Dates']).dt.strftime('%Y-%m-%d')
            df_list.append(df_well)
        except Exception as e:
            print(f"Error processing well {w}: {e}")
            continue
    if df_list:
        result = pd.concat(df_list).fillna(0)
        result['Reserve_scenario'] = reserve_scenario
        return result
    else:
        return pd.DataFrame()  # Return empty DataFrame if all fail


def rr_summary(pv_rc_year_1p, pv_rc_year_2p, pv_rc_year_3p):
    # Create reserve summary
    #1P
    pv_rc_year_1p_rs=pv_rc_year_1p.fillna(0)/1000000
    try:
        pv_rc_year_1p_rs.loc['PDP']
    except:
        pv_rc_year_1p_rs.loc['PDP'] = 0
    try:
        pv_rc_year_1p_rs.loc['PDNP']
    except:
        pv_rc_year_1p_rs.loc['PDNP'] = 0
    try:
        pv_rc_year_1p_rs.loc['PUD']
    except:
        pv_rc_year_1p_rs.loc['PUD'] = 0
    pv_rc_year_1p_rs.loc['PD']=pv_rc_year_1p_rs.loc['PDP']+pv_rc_year_1p_rs.loc['PDNP']
    pv_rc_year_1p_rs.loc['1P']=pv_rc_year_1p_rs.loc['PDP']+pv_rc_year_1p_rs.loc['PDNP']+pv_rc_year_1p_rs.loc['PUD']
    pv_rc_year_1p_rs.insert(0, 'Total',pv_rc_year_1p_rs.sum(1))
    onep_list_category=['PDP','PDNP','PD','PUD','1P']
    pv_rc_year_1p_rs=pv_rc_year_1p_rs.loc[pv_rc_year_1p_rs.index.intersection(onep_list_category)].reindex(onep_list_category)
    
    #2P
    pv_rc_year_2p_rs=pv_rc_year_2p.fillna(0)/1000000
    try:
        pv_rc_year_2p_rs.loc['PDP']
    except:
        pv_rc_year_2p_rs.loc['PDP'] = 0
    try:
        pv_rc_year_2p_rs.loc['PDNP']
    except:
        pv_rc_year_2p_rs.loc['PDNP'] = 0
    try:
        pv_rc_year_2p_rs.loc['PUD']
    except:
        pv_rc_year_2p_rs.loc['PUD'] = 0
    pv_rc_year_2p_rs.loc['2PD']=pv_rc_year_2p_rs.loc['PDP']+pv_rc_year_2p_rs.loc['PDNP']
    pv_rc_year_2p_rs.loc['2P']=pv_rc_year_2p_rs.loc['PDP']+pv_rc_year_2p_rs.loc['PDNP']+pv_rc_year_2p_rs.loc['PUD']
    #Compute P2D and P2UD
    pv_rc_year_2p_rs.loc['P2D']=pv_rc_year_2p_rs.loc['2PD']-pv_rc_year_1p_rs.loc['PD']
    pv_rc_year_2p_rs.loc['P2UD']=pv_rc_year_2p_rs.loc['PUD']-pv_rc_year_1p_rs.loc['PUD']
    pv_rc_year_2p_rs.loc['P2']=pv_rc_year_2p_rs.loc['P2D']+pv_rc_year_2p_rs.loc['P2UD']
    pv_rc_year_2p_rs.insert(0, 'Total',pv_rc_year_2p_rs.sum(1))
    twop_list_category=['P2D','P2UD','P2','2PD','2P']
    pv_rc_year_2p_rs_filter=pv_rc_year_2p_rs.loc[pv_rc_year_2p_rs.index.intersection(twop_list_category)].reindex(twop_list_category)
    #3P
    pv_rc_year_3p_rs=pv_rc_year_3p.fillna(0)/1000000
    try:
        pv_rc_year_3p_rs.loc['PDP']
    except:
        pv_rc_year_3p_rs.loc['PDP'] = 0
    try:
        pv_rc_year_3p_rs.loc['PDNP']
    except:
        pv_rc_year_3p_rs.loc['PDNP'] = 0
    try:
        pv_rc_year_3p_rs.loc['PUD']
    except:
        pv_rc_year_3p_rs.loc['PUD'] = 0
    pv_rc_year_3p_rs.loc['3PD']=pv_rc_year_3p_rs.loc['PDP']+pv_rc_year_3p_rs.loc['PDNP']
    pv_rc_year_3p_rs.loc['3P']=pv_rc_year_3p_rs.loc['PDP']+pv_rc_year_3p_rs.loc['PDNP']+pv_rc_year_3p_rs.loc['PUD']
    #Compute P3D and P3UD
    pv_rc_year_3p_rs.loc['P3D']=pv_rc_year_3p_rs.loc['3PD']-pv_rc_year_2p_rs.loc['2PD']
    pv_rc_year_3p_rs.loc['P3UD']=pv_rc_year_3p_rs.loc['PUD']-pv_rc_year_2p_rs.loc['PUD']
    pv_rc_year_3p_rs.loc['P3']=pv_rc_year_3p_rs.loc['P3D']+pv_rc_year_3p_rs.loc['P3UD']
    pv_rc_year_3p_rs.insert(0, 'Total',pv_rc_year_3p_rs.sum(1))
    threep_list_category=['P3D','P3UD','P3','3PD','3P']
    pv_rc_year_3p_rs=pv_rc_year_3p_rs.loc[pv_rc_year_3p_rs.index.intersection(threep_list_category)].reindex(threep_list_category)
    # Concat 1P, 2P and 3P
    reserve_summary = pd.concat([pv_rc_year_1p_rs, pv_rc_year_2p_rs_filter, pv_rc_year_3p_rs], axis=0)
    
    # Create resource summary
    #1C
    pv_rc_year_1p_cs=pv_rc_year_1p.fillna(0)/1000000
    try:
        pv_rc_year_1p_cs.loc['CUD']
    except:
        pv_rc_year_1p_cs.loc['CUD'] = 0
        
    pv_rc_year_1p_cs.loc['C1']=pv_rc_year_1p_cs.loc['CUD']
    onec_list_category=['C1']
    pv_rc_year_1p_cs_filter=pv_rc_year_1p_cs.loc[pv_rc_year_1p_cs.index.intersection(onec_list_category)].reindex(onec_list_category)
    pv_rc_year_1p_cs_filter.insert(0, 'Total',pv_rc_year_1p_cs_filter.sum(1))
    #2c
    pv_rc_year_2p_cs=pv_rc_year_2p.fillna(0)/1000000
    try:
        pv_rc_year_2p_cs.loc['CUD']
    except:
        pv_rc_year_2p_cs.loc['CUD'] = 0
    pv_rc_year_2p_cs.loc['C2']=pv_rc_year_2p_cs.loc['CUD']-pv_rc_year_1p_cs.loc['CUD']
    pv_rc_year_2p_cs.loc['2C']=pv_rc_year_2p_cs.loc['CUD']
    twoc_list_category=['C2','2C']
    pv_rc_year_2p_cs_filter=pv_rc_year_2p_cs.loc[pv_rc_year_2p_cs.index.intersection(twoc_list_category)].reindex(twoc_list_category)
    pv_rc_year_2p_cs_filter.insert(0, 'Total',pv_rc_year_2p_cs_filter.sum(1))
    
    #3C
    pv_rc_year_3p_cs=pv_rc_year_3p.fillna(0)/1000000
    try:
        pv_rc_year_3p_cs.loc['CUD']
    except:
        pv_rc_year_3p_cs.loc['CUD'] = 0
    pv_rc_year_3p_cs.loc['C3']=pv_rc_year_3p_cs.loc['CUD']-pv_rc_year_2p_cs.loc['CUD']
    pv_rc_year_3p_cs.loc['3C']=pv_rc_year_3p_cs.loc['CUD']
    threec_list_category=['C3','3C']
    pv_rc_year_3p_cs_filter=pv_rc_year_3p_cs.loc[pv_rc_year_3p_cs.index.intersection(threec_list_category)].reindex(threec_list_category)
    pv_rc_year_3p_cs_filter.insert(0, 'Total',pv_rc_year_3p_cs_filter.sum(1))
    # Concat 1C, 2C and 3C
    resource_summary = pd.concat([pv_rc_year_1p_cs_filter, pv_rc_year_2p_cs_filter, pv_rc_year_3p_cs_filter], axis=0)
    return reserve_summary, resource_summary
