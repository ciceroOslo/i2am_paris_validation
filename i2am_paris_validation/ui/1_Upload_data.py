import streamlit as st
import pandas as pd
import os
import re

from streamlit_extras.switch_page_button import switch_page


pd.options.mode.chained_assignment = None  # default='warn'

st.set_page_config(layout="wide")


def main():

    st.header("Upload modelling results for validation")

    st.sidebar.header("Instructions")

    st.sidebar.markdown("The file should include five columns named Model, Scenario, Region, Variable, and Unit and \
        a number of columns with years for column names (e.g., 2010, 2015, 2020, etc.).")

    st.sidebar.markdown("Timeseries data in the file should be given in a float or integer format \
        underneath the year columns. An empty cell will be interpreted as unavailable data, \
        a 0-character will be interpreted as a value of zero, while alphabetic characters \
        will throw an error.")

    st.sidebar.markdown("You can find an example of the format [here](https://pyam-iamc.readthedocs.io/en/stable/).")

    uploaded_file = st.file_uploader("Upload a spreadsheet file with modelling results in an IAMC timeseries format.", 
        type=["xlsx", "xls", "csv"],key="uploaded_file")


    if uploaded_file is not None:
        # load data
        if uploaded_file.type == 'text/csv':
            raw_data = pd.read_csv(uploaded_file)
        else:
            raw_data = pd.read_excel(uploaded_file)

        st.session_state['current_filename'] = st.session_state['uploaded_file'].name
        st.session_state['current_file_size'] = st.session_state['uploaded_file'].size

        # Refresh all variables
        st.session_state['validated_data'] = pd.DataFrame()
        st.session_state['missing_values_count'] = None
        st.session_state['duplicates_count'] = None
        st.session_state['model_errors'] = None
        st.session_state['region_errors'] = None
        st.session_state['variable_errors'] = None
        st.session_state['unit_errors'] = None
        st.session_state['vetting_errors'] = None   

        clean_results_dataset(raw_data)

    df = st.session_state.get('clean_df', pd.DataFrame())
    if not df.empty: 
        if uploaded_file is None:
            st.write(st.session_state['current_filename'],
                f", {round(st.session_state['current_file_size']/1000,1)} KB")

        st.dataframe(df)

        if st.session_state.get('cleaning_error'):
            st.info('Please fix the errors and upload a new file.', icon="ℹ️")
        else:
            st.info('The file has the correct column format! \
                Click the button below for validation.', icon="ℹ️")

            validate_data_btn = st.button('Validate data')
            
            if validate_data_btn:
                switch_page("Validate_data") 

def clean_results_dataset(df):
    error = False

    str_cols = pd.to_numeric(df.columns, errors='coerce').isna()
    numeric_cols = pd.to_numeric(df.columns, errors='coerce').notna()

    string_df = df.loc[:,str_cols].rename(columns=lambda x: re.sub('^[Mm][Oo][Dd][Ee][Ll]$', 'Model', x)) \
                            .rename(columns=lambda x: re.sub('^[Ss][Cc][Ee][Nn][Aa][Rr][Ii][Oo]$', 'Scenario', x)) \
                            .rename(columns=lambda x: re.sub('^[Rr][Ee][Gg][Ii][Oo][Nn]$', 'Region', x)) \
                            .rename(columns=lambda x: re.sub('^[Vv][Aa][Rr][Ii][Aa][Bb][Ll][Ee]$', 'Variable', x)) \
                            .rename(columns=lambda x: re.sub('^[Uu][Nn][Ii][Tt]$', 'Unit', x))

    for column in ['Model', 'Region', 'Scenario', 'Variable', 'Unit']:
        if column not in df.columns:
            st.error(f'Column {column} is missing or has a different name!', icon="🚨")
            error = True

    if numeric_cols.sum()==0:
        st.error(f'No year columns!', icon="🚨")
        error = True

    numeric_df = df.loc[:,numeric_cols]

    numeric_df = numeric_df.apply(pd.to_numeric, axis=1, errors='coerce')
    numeric_df.columns = pd.to_numeric(numeric_df.columns, errors='coerce')

    string_df = string_df.convert_dtypes()

    df = pd.concat([string_df, numeric_df], axis=1)

    st.session_state['clean_df'] = df
    st.session_state['cleaning_error'] = error

    return df, error


if __name__ == "__main__":
    main()
