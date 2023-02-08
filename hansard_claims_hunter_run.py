## streamlit run "C:\Users\Jack\Documents\Python_projects\Fact Check\hansard_claim_hunter\hansard_claims_hunter_run.py"

import numpy as np
import pandas as pd
import re
import streamlit as st
from st_aggrid import AgGrid
    
import scrapingTools
import hansard_claims_hunter_functions

######

def runScript():
    
    dfLATESTLINKS = hansard_claims_hunter_functions.getLatestLinks()
    
    st.dataframe(dfLATESTLINKS[['date', 'house']])
    
    selected_row = st.number_input('Choose by row number: ', step = 1, min_value = 1, max_value = dfLATESTLINKS.shape[0])
    proceed = st.radio('Start claim hunting?', ['no', 'yes'], horizontal=True)
    if proceed == 'yes':
        dfSPEECHES = hansard_claims_hunter_functions.getSpeeches(dfLATESTLINKS, selected_row)    
        dfCLAIMS = hansard_claims_hunter_functions.filterSpeeches(dfSPEECHES)
    
        st.dataframe(dfCLAIMS[['claim', 'name']], width=1000)
    
        return dfCLAIMS

########################

st.write('Constituent Investigative Analytics Studio')

st.write('# HANSARD CLAIMS HUNTER #####')

st.write('Searches the latest Hansards for claims that can be analysed by fact checker.') 

runScript()


st.write('')
st.write('')
st.write('&#11041; More tools at www.constituent.au')