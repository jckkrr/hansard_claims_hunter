## streamlit run "C:\Users\Jack\Documents\Python_projects\Fact Check\hansard_claim_hunter\hansard_claims_hunter_run.py"

import numpy as np
import pandas as pd
import re
import streamlit as st
    
import scrapingTools
import hansard_claims_hunter_functions

### 

def getSoup(url):
    
    from requests import get
    from bs4 import BeautifulSoup
    import requests

    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14'
    headers = {'User-Agent': user_agent,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    response = get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    return soup

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

#runScript()


st.write('')
st.write('')
st.write('&#11041; More tools at www.constituent.au')