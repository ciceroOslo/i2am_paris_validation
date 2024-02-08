import pandas as pd

def check_vetting(df):
    # create empty vetting check column
    df['vetting_check'] = ''

    # create empty vettings list where the vetting results are stored as Series with index the original index of the entry and value the result of the vetting check
    vettings_results = []

    # list of dictionaries with the basic vettings
    vetting_list = [{'variable': 'Emissions|CO2|Energy and Industrial Processes', 'low': 30116.8, 'high': 45175.2, 'year': 2020, 'error': 'Vetting error: CO2 EIP emissions'},
                    {'variable': 'Emissions|CH4', 'low': 303.2, 'high': 454.8, 'year': 2020, 'error': 'Vetting error: CH4 emissions'},
                    {'variable': 'Primary Energy', 'low': 462.4, 'high': 693.6, 'year': 2020, 'error': 'Vetting error: Primary Energy'},
                    {'variable': 'Secondary Energy|Electricity|Nuclear', 'low': 6.839, 'high': 12.701, 'year': 2020, 'error': 'Vetting error: Electricity Nuclear'},
                    {'variable': 'Emissions|CO2', 'low': 0, 'high': 1000000, 'year': 2030, 'error': 'Vetting warning: No net negative CO2 emissions before 2030'},
                    {'variable': 'Secondary Energy|Electricity|Nuclear', 'low': 0, 'high': 20, 'year': 2030, 'error': 'Vetting warning: Electricity from Nuclear in 2030'},
                    {'variable': 'Emissions|CH4', 'low': 100, 'high': 1000, 'year': 2040, 'error': 'Vetting warning: CH4 emissions in 2040'}]


    def check_vetting_range(x):
        if x[vetting['year']] < vetting['low'] or x[vetting['year']] > vetting['high']:
            return f"{vetting['error']} for year {vetting['year']}. Range must be between {vetting['low']} and {vetting['high']}." 
        else:
            return ''

    # creating Series objects with index the index of the error or warning and value the vetting error or warning if exists and appending them to the vetting_results
    for vetting in vetting_list:
        # basic vetting checks
        vcheck = df[(df['Variable'] == vetting['variable']) & (df['Region'] == 'World')]

        if not vcheck.empty:
            vettings_results.append(vcheck.apply(check_vetting_range, axis=1))

    # list of dictionaries with the sum vettings
    vettings_list = [{'variable1': 'Emissions|CO2|AFOLU', 'variable2': 'Emissions|CO2|Energy and Industrial Processes', 'low': 26550.6, 'high': 61951.4, 'year': 2020, 'error': 'Vetting error: CO2 total emissions (EIP + AFOLU)'},
                     {'variable1': 'Carbon Sequestration|CCS|Biomass|Energy', 'variable2': 'Carbon Sequestration|CCS|Fossil|Energy', 'low': 0, 'high': 250, 'year': 2020, 'error': 'Vetting error: CCS from Energy 2020 '},
                     {'variable1': 'Secondary Energy|Electricity|Wind', 'variable2': 'Secondary Energy|Electricity|Solar', 'low': 4.255, 'high': 12.765, 'year': 2020, 'error': 'Vetting error: Electricity Solar & Wind'},
                     {'variable1': 'Carbon Sequestration|CCS|Biomass|Energy', 'variable2': 'Carbon Sequestration|CCS|Fossil|Energy', 'low': 0, 'high': 2000, 'year': 2030, 'error': 'Vetting warning: CCS from Energy in 2030'}]

    for vetting in vettings_list:
        # vetting sums checks
        vetting_group = df[((df['Variable'] == vetting['variable1']) | (df['Variable'] == vetting['variable2']))
                        & (df['Region'] == 'World')].groupby(['Model', 'Scenario']).sum()[vetting['year']]
        
        # get indexes with sum out of bounds
        indexes = vetting_group[(vetting_group < vetting['low']) | (vetting_group > vetting['high'])].index
        for index in indexes:
            # append Series object with index the index of the error or warning and value the vetting error or warning
            vettings_results.append(pd.Series({df[(df['Model'] == index[0]) & (df['Scenario'] == index[1]) & (df['Variable'] == vetting['variable1']) & (df['Region'] == 'World')].index[0]: f"{vetting['error']} for year {vetting['year']}. Sum range must be between {vetting['low']} and {vetting['high']}."}))
            vettings_results.append(pd.Series({df[(df['Model'] == index[0]) & (df['Scenario'] == index[1]) & (df['Variable'] == vetting['variable2']) & (df['Region'] == 'World')].index[0]: f"{vetting['error']} for year {vetting['year']}. Sum range must be between {vetting['low']} and {vetting['high']}."}))

    # percent change between 2010-2020 vetting check 
    vettings_results.append(df[(df['Variable'] == 'Emissions|CO2|Energy and Industrial Processes') 
            & (df['Region'] == 'World')].apply(lambda x: 'Vetting error: CO2 emissions EIP 2010-2020 - % change' if abs((x[2020]-x[2010])/x[2010]) > 0.5 else '', axis=1))

    # write vetting results to the original dfframe's vetting_check column
    for vetting in vettings_results:
        for key, value in vetting.to_dict().items():
            df['vetting_check'][key] = value

    return df
