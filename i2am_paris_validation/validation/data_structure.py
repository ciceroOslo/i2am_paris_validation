import streamlit as st
import pandas as pd

KNOWN_MODELS_REGIONS_VARS = 'input_data/available_models_regions_variables_units.xlsx'

@st.cache_data
def load_known_names():
    models = pd.read_excel(KNOWN_MODELS_REGIONS_VARS, sheet_name='models').Model.unique()
    regions = pd.read_excel(KNOWN_MODELS_REGIONS_VARS, sheet_name='regions').Region.unique()
    variables_units = pd.read_excel(KNOWN_MODELS_REGIONS_VARS, sheet_name='variable_units')
    variables = variables_units.Variable.unique()
    units = variables_units.Unit.unique()
    variables_units_combination = (variables_units['Variable'] + ' ' + variables_units['Unit']).unique()

    return models,regions,variables_units,variables,units,variables_units_combination


def check_value_format(df):
    numeric_columns =  df.columns[pd.to_numeric(df.columns, errors='coerce').notna()]

    # find possible mixed columns (strings and floats) and turn them to numeric columns, making the strings NaN
    for column in numeric_columns:
        # if pd.api.types.infer_dtype(df[column]) == 'mixed-integer' or pd.api.types.infer_dtype(df[column]) == 'mixed-integer-float':
        df[column] = pd.to_numeric(df[column], errors = 'coerce')

    return df


def check_duplicates(df):
    # check if there are any duplicates (we consider duplicates those entries that have same Model, Scenario, Region and Variable)
    df['duplicates_check'] = df.duplicated(['Model', 'Scenario', 'Region', 'Variable']).apply(lambda x: 'Duplicate' if x else '')

    return df


def check_indices(df):
    models,regions,variables_units,variables,units,variables_units_combination = load_known_names()

    # check if model is valid
    df['model_check'] = df.Model.dropna().apply(lambda x: 'Model ' + x + ' not found!' if x not in models else '')

    # check if region is valid
    df['region_check'] = df.Region.dropna().apply(lambda x: 'Region ' + x + ' not found!' if x not in regions else '')

    # check if variable is valid
    df['variable_check'] = df.Variable.dropna().apply(lambda x: 'Variable ' + x + ' not found!' if x not in variables else '')

    # check if unit is valid
    df['unit_check'] = df.Unit.dropna().apply(lambda x: 'Unit ' + x + ' not found!' if x not in units else '')

    # check if variable unit combination is valid
    # fix check to avoid dropping rows
    df['variable_unit_check']= df.dropna().apply(lambda x: f"Variable {x['Variable']} combined with unit {x['Unit']} not found!" if (x['Variable'] + ' ' + x['Unit']) not in variables_units_combination else '', axis=1)

    return df

def check_basic_sums(df):

    numeric_columns =  df.columns[pd.to_numeric(df.columns, errors='coerce').notna()]

    # create a list with the aggregated variables
    aggr_vars = []
    unique_vars = df.Variable.unique()
    for var in unique_vars:
        var_levels = var.count('|')

        if var_levels > 0:
            for level in range(0,var_levels):
                test_aggr_var = var.rsplit("|",level+1)[0]

                if test_aggr_var in unique_vars:
                    if test_aggr_var not in aggr_vars:
                        aggr_vars.append(test_aggr_var)
                        break

    # create dictionary with keys the aggregated variables and values the disaggregated variables
    var_tree = {}
    for var in unique_vars:
        var_levels = var.count('|')

        if var_levels > 0:
            for level in range(0,var_levels):
                test_aggr_var = var.rsplit("|",level+1)[0]

                if test_aggr_var in unique_vars:
                    if test_aggr_var not in var_tree.keys():
                        if var not in aggr_vars:
                            var_tree[test_aggr_var] = [var]
                    else:
                        if var not in aggr_vars:
                            var_tree[test_aggr_var].append(var)

    # check basic sums
    df['basic_sum_check'] = ''
    for variable in var_tree.keys():
        # get df that have the aggregated variable
        agg_results = df[df['Variable'].isin(var_tree[f'{variable}'])].groupby(['Model', 'Scenario', 'Region']).sum()[numeric_columns]

        for row in agg_results.index:
            for year in numeric_columns:
                values = df[(df['Model'] == row[0]) & (df['Scenario'] == row[1]) & (df['Region'] == row[2])  & (df['Variable'] == variable)][year].values
                if len(values) != 0:
                    # find percentage difference using the formula |x1 - x2|/((x1+x2)/2)
                    diff = (abs(values[0] - agg_results[year][row[0]][row[1]][row[2]]))/((values[0] + agg_results[year][row[0]][row[1]][row[2]])/2)
                    
                    # set difference margin at 2%
                    if diff > 0.02:
                        df.loc[(df['Model'] == row[0]) & (df['Scenario'] == row[1]) & (df['Region'] == row[2])  & (df['Variable'] == variable), 'basic_sum_check'] += f'Basic sum check error on year {year}.     \n'

    return df
