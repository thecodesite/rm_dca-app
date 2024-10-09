# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 10:09:20 2024

@author: R115127
"""
import datetime
from datetime import *
from datetime import datetime
import calendar
from datetime import date
import numpy as np
import pandas as pd

def dca_project(qoi, di, prod_start_date, fore_end_date, dip, proj_start_date, project_active_well, gor, bsw):
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
    df['Uptime']=(df['Days_prod']/df['Days_month']).fillna(0)   
    
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
    #Water
    water_list = []
    for q in qo_list:
        if q>0:
            w=qoi+qoi*bsw-q
        else:
            w=0
        water_list.append(w)
    df['water_rate']=pd.Series(water_list)
    #Liquid
    df['liquid_rate']=df['oil_rate']+df['water_rate']
    
    # GOR, Bsw
    df['gor']=gor
    df['bsw']=bsw

    # Volumes/Cum Oil, Gas, Water
    #Oil
    df['oil_volume']=(df['oil_rate']*df['Days_month']).fillna(0)
    df['oil_cum']=(df['oil_rate']*df['Days_month']).cumsum().shift().fillna(0)
    # Gas
    df['gas_volume']=(df['gas_rate']*df['Days_month']).fillna(0)
    df['gas_cum']=(df['gas_rate']*df['Days_month']).cumsum().shift().fillna(0)
    # Water
    df['water_volume']=(df['water_rate']*df['Days_month']).fillna(0)
    df['water_cum']=(df['water_rate']*df['Days_month']).cumsum().shift().fillna(0)
    
    return df
# dca_project_dt() function includes downtime
def dca_project_dt(qoi, di, prod_start_date, fore_end_date, dip, proj_start_date, project_active_well, gor, bsw, dt):
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
    #df['oil_rate']=pd.Series(qo_list)*df['Uptime'].to_list()
    #df['oil_rate']=pd.Series(qo_list)*df['Uptime'].to_list()*(1-dt)
    df['oil_rate']=pd.Series(qo_list)*df['Uptime'].to_list()
    #Gas
    df['gas_rate']=df['oil_rate']*gor/1000
    #Water
    water_list = []
    for q in qo_list:
        if q>0:
            w=qoi+qoi*bsw-q
        else:
            w=0
        water_list.append(w)
    df['water_rate']=pd.Series(water_list)
    #Liquid
    df['liquid_rate']=df['oil_rate']+df['water_rate']
    
    # GOR, Bsw
    df['gor']=gor
    df['bsw']=bsw

    # Volumes/Cum Oil, Gas, Water
    #Oil
    df['oil_volume']=(df['oil_rate']*df['Days_month']).fillna(0)
    df['oil_cum']=(df['oil_rate']*df['Days_month']).cumsum().shift().fillna(0)
    # Gas
    df['gas_volume']=(df['gas_rate']*df['Days_month']).fillna(0)
    df['gas_cum']=(df['gas_rate']*df['Days_month']).cumsum().shift().fillna(0)
    # Water
    df['water_volume']=(df['water_rate']*df['Days_month']).fillna(0)
    df['water_cum']=(df['water_rate']*df['Days_month']).cumsum().shift().fillna(0)
    
    return df

# Create function to perfom calcs
def run_res_scenario(reserve_scenario, qi_list, di_list, psd_list, well_list, reserve_cat_list, activity_list, di_pro_list, project_active_wells, gor_list, bsw_list, forecast_end_date, proj_start_date):
    import pandas as pd
    # Compute 1P reserves 
    df_list = []
    for qi, di, psd, w, c, a, di_pro, paw, gor, bsw  in zip(qi_list, di_list, psd_list, well_list, reserve_cat_list, activity_list, di_pro_list, project_active_wells, gor_list, bsw_list):
        # Perform dca 1P forecast
        vars()[w] = dca_project(qi, di, psd, forecast_end_date, di_pro, proj_start_date, paw, gor, bsw)
        # Reset index
        vars()[w] = vars()[w].reset_index()
        # Add new columns
        vars()[w]['Year'] = vars()[w]['Dates'].dt.year
        vars()[w]['well_name'] = w
        vars()[w]['reserve_cat'] = c
        vars()[w]['activity'] = a
        # Reorder columns
        vars()[w] = vars()[w][['Dates','Year', 'well_name', 'reserve_cat','activity', 'Days_prod', 'Cum_days_prod', 'Days_month', 'Uptime',
                               'oil_rate','oil_volume', 'oil_cum', 'gor','gas_rate','gas_volume', 'gas_cum', 'bsw', 'water_rate','water_volume', 'water_cum']]
        vars()[w]['Dates'] = vars()[w]['Dates'].dt.strftime('%Y-%m-%d')
        # Append dataframes
        df_list.append(vars()[w])    
        # Concat list of dataframes
        result = pd.concat(df_list).fillna(0)
    result['Reserve_scenario'] = reserve_scenario
    
    # Units K: oil & water, M: Gas
    #result_1p=result_1p
    return result
    
# run_res_scenario_dt() function includes downtime
def run_res_scenario_dt(reserve_scenario, qi_list, di_list, psd_list, well_list, reserve_cat_list, activity_list, di_pro_list, project_active_wells, gor_list, bsw_list, forecast_end_date, proj_start_date, dt_list):
    import pandas as pd
    # Compute 1P reserves 
    df_list = []
    for qi, di, psd, w, c, a, di_pro, paw, gor, bsw, dt  in zip(qi_list, di_list, psd_list, well_list, reserve_cat_list, activity_list, di_pro_list, project_active_wells, gor_list, bsw_list, dt_list):
        # Perform dca 1P forecast
        vars()[w] = dca_project_dt(qi, di, psd, forecast_end_date, di_pro, proj_start_date, paw, gor, bsw, dt)
        # Reset index
        vars()[w] = vars()[w].reset_index()
        # Add new columns
        vars()[w]['Year'] = vars()[w]['Dates'].dt.year
        vars()[w]['well_name'] = w
        vars()[w]['reserve_cat'] = c
        vars()[w]['activity'] = a
        # Reorder columns
        vars()[w] = vars()[w][['Dates','Year', 'well_name', 'reserve_cat','activity', 'Days_prod', 'Cum_days_prod', 'Days_month', 'Uptime',
                               'oil_rate','oil_volume', 'oil_cum', 'gor','gas_rate','gas_volume', 'gas_cum', 'bsw', 'water_rate','water_volume', 'water_cum']]
        vars()[w]['Dates'] = vars()[w]['Dates'].dt.strftime('%Y-%m-%d')
        # Append dataframes
        df_list.append(vars()[w])    
        # Concat list of dataframes
        result = pd.concat(df_list).fillna(0)
    result['Reserve_scenario'] = reserve_scenario
    
    # Units K: oil & water, M: Gas
    #result_1p=result_1p
    return result

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
