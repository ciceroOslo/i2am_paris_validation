import streamlit as st
import pandas as pd
import os
import re
import tempfile
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


from streamlit_extras.switch_page_button import switch_page

from validation.data_structure import *
from validation.vetting import *


pd.options.mode.chained_assignment = None  # default='warn'

st.set_page_config(layout="wide")


def main():
    st.header('Validate modelling results')

    st.sidebar.header("Instructions")

    st.sidebar.markdown("The following validation checks are available:")

    st.sidebar.markdown("*Consistency of model, variable, and region names*: \
        Check if the models, variables, or regions of the uploaded file exist in the I2AM PARIS database.")

    st.sidebar.markdown("*Vetting checks*: \
        Check whether the values of key variables fall within reasonable ranges based on \
        past measurements or future estimations. Vetting is based on the \
        IPCC AR6 vetting rules found in the IPCC AR6 Working Group III report, Annex III, Table 11\
        ([link](https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Annex-III.pdf)).")

    st.sidebar.markdown("*Consistency between disaggregated and aggregated variables*: \
        Check whether the values of aggregated variables correspond to the sum of their respective \
            disaggregated variables (an error margin of 2\% is accepted).")


    df = st.session_state.get('clean_df', pd.DataFrame())
    cleaning_error = st.session_state.get('cleaning_error')
    validated_df = st.session_state.get('validated_data', pd.DataFrame())

    placeholder = st.empty()
    if not df.empty and not cleaning_error:
        if validated_df.empty:
            with placeholder.container():
                st.markdown('Please select the validation check(s) you want to perform:')
                indices_check = st.checkbox('Consistency of model, variable, and region names', value=True)
                vetting_check = st.checkbox('Vetting checks', value=True)
                basic_sums_check = st.checkbox('Consistency between disaggregated and aggregated variables', value=False)

                validate_button_disable = False
                if not (indices_check or vetting_check or basic_sums_check):
                    validate_button_disable = True
                    st.info('Please select at least one check.')

                validate_button = st.button('Start validation', on_click=validate, args=(df, indices_check, vetting_check, basic_sums_check),
                        disabled=validate_button_disable)
        else:
            with placeholder.container():
                with st.spinner('Validating...'):
                    df_styled = validated_df.style.applymap(lambda x: f'background-color: red' if 'not found' in str(x) or 'Duplicate' in str(x) or 'Vetting error' in str(x) else (f'background-color: yellow' if str(x) == 'nan' or 'Vetting warning' in str(x) or 'sum check error' in str(x) else f'background-color: white'))

                    with tempfile.NamedTemporaryFile() as temp:
                        temp_filename = os.path.join(os.getcwd(),'temp', f'{temp.name}.xlsx')

                        convert_df(df_styled, temp_filename)
                        
                        with open(temp_filename, 'rb') as template_file:
                            template_byte = template_file.read()


                    if st.session_state.get('duplicates_count'):
                        st.error(f"Found {st.session_state.get('duplicates_count')} duplicate entries.", icon="🚨")

                    if st.session_state.get('vetting_errors'):
                        st.error(f"Found {st.session_state.get('vetting_errors')} vetting errors.", icon="🚨")

                    if st.session_state.get('model_errors'):
                        st.warning(f"Found {st.session_state.get('model_errors')} instances of model names that are not in the database.", icon="⚠️")

                    if st.session_state.get('region_errors'):
                        st.warning(f"Found {st.session_state.get('region_errors')} instances of region names that are not in the database.", icon="⚠️")

                    if st.session_state.get('variable_errors'):
                        st.warning(f"Found {st.session_state.get('variable_errors')} instances of variable names that are not in the database.", icon="⚠️")

                    if st.session_state.get('unit_errors'):
                        st.warning(f"Found {st.session_state.get('variable_errors')} instances of unit names that are not in the database.", icon="⚠️")

                    if st.session_state.get('basic_sum_check_errors'):
                        st.warning(f"Found {st.session_state.get('basic_sum_check_errors')} consistency issues between disaggregated and aggregated variables.", icon="⚠️")

                    st.markdown('Scroll the dataframe to the right to see all errors and warnings in detail. You can also download validation results in an Excel file, \
                        fix potential errors, and re-upload them.')
                    st.dataframe(df)
                    st.download_button(label="Download validation results",
                        data=template_byte,
                        file_name="validated.xlsx",
                        mime='application/octet-stream')

                    # st.session_state['validation_ended'] = True

                    # validate_data_btn = st.button('Go back to data upload')
                    
                    # if validate_data_btn:
                    #     switch_page("Upload data") 

    else: 
        with placeholder.container():
            st.info('No data for validation. Please upload a results dataset with a correct format.', icon="ℹ️")

            validate_data_btn = st.button('Upload data')
            
            if validate_data_btn:
                switch_page("Upload data") 


def validate(df, indices_check, vetting_check, basic_sums_check):
    with st.spinner('Validating...'):

        # fix missing values to do a better check
        df = check_value_format(df)
        st.session_state['missing_values_count'] = df.isna().sum().values.sum()

        df = check_duplicates(df)
        st.session_state['duplicates_count'] = count_errors(df,'duplicates_check')

        if indices_check:
            df = check_indices(df)
            st.session_state['model_errors'] = count_errors(df,'model_check')
            st.session_state['region_errors'] = count_errors(df,'region_check')
            st.session_state['variable_errors'] = count_errors(df,'variable_check')
            st.session_state['unit_errors'] = count_errors(df,'unit_check')

        if vetting_check:
            df = check_vetting(df)
            st.session_state['vetting_errors'] = count_errors(df,'vetting_check')

        if basic_sums_check:
            df = check_basic_sums(df)               
            st.session_state['basic_sum_check_errors'] = df.basic_sum_check.str.count('year').sum()

        st.session_state['validated_data'] = df


def count_errors(df, column):
    return (df[column] != '').sum()


@st.cache_data
def convert_df(_df,filename):
    return _df.to_excel(filename,index=None)

    
if __name__ == "__main__":
    main()
