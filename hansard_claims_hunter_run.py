## streamlit run "C:\Users\Jack\Documents\Python_projects\Fact Check\hansard_claim_hunter\hansard_claims_hunter_run.py"

import numpy as np
import pandas as pd
import re
import streamlit as st

from requests import get
from bs4 import BeautifulSoup
import requests

### 

def getSoup(url):

    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14'
    headers = {'User-Agent': user_agent,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    response = get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    return soup

#####

#############################

def getTables(soup, print_on):

    tables = soup.find_all('table')
    
    if print_on == True:
        for table in tables:
            attrs = list(table.attrs)
            print(f'\n--- {tables.index(table)}/{len(tables)} --- {attrs}')
            for attr in ['summary', 'title']:
                if attr in attrs:
                    print(attr, ' ' * (10 - len(str(attr))), table[attr])
                    
    return tables

#############################

def getTableHead(table):
    
    import pandas as pd
    import bs4
    from bs4 import BeautifulSoup
    
    df = pd.DataFrame()

    thead = table.find('thead')
            
    if thead != None:
        thead_trs = thead.find_all('tr')
                
        if len(thead_trs) > 0:       
            for tr in thead_trs:
                                    
                n = thead_trs.index(tr)
                                                    
                row_vals = [x for x in tr if x != '\n' and type(x) != bs4.element.Comment]
                row_vals = [x.text.strip() if type(x) == bs4.element.Tag else x for x in row_vals]
                #print(row_vals)
                       
                for val in row_vals:                        
                    df.loc[n, row_vals.index(val)] = val
              
    return df

#############################

def getTableBody(table):
    
    columns = None
    df = pd.DataFrame(columns=columns)   
    
    tbody = table.find('tbody')
    if tbody==None:
        tbody = table
    
    rows = tbody.find_all('tr')
                
    for row in rows:
    
        nr = df.shape[0]
                    
        headers = [x.text.strip() for x in row.find_all('th')]
        data = [x.text.strip() for x in row.find_all('td')]
        full_row = headers + data
                
        if df.shape[1] != len(full_row):  
            if len(row.text.strip()) == 0:    ### blank rows
                full_row = ['' for x in range(0,df.shape[1])] 
                            
        row_cols = [x for x in range(0, len(full_row))]
        df.loc[nr, row_cols] = full_row
          
    
    table_title = table['title'] if 'title' in table.attrs else table['summary'] if 'summary' in table.attrs else None
    
    return df.values, table_title

#############################

def getTable(url, tableNumber):
    
    ### A script to get the table data from any table in the HTML  of a website
    ### It also has the capability to show you what tables are in the page and then select the one you want.
    ### To do this, make the second criteria None. Else, put the number of the wanted table there.
    ### It returns a faithful representation of the table that can then be refined.
        
    soup = getSoup(url)

    displayTables = True if tableNumber == None else False
    tables = getTables(soup, displayTables)
    
    if tableNumber == None:
        tableNumber = int(input('Which table? '))
            
    table = tables[tableNumber]

    headers = getTableHead(table)
    values, table_title = getTableBody(table)

    if len(headers.values) == 0:  ### no header

        cols = None

    elif len(headers.values) == 1:  # normal header

        cols = headers.values[0]

    elif len(headers.values) > 1:   # multiindex header

        if headers.shape[1] == values.shape[1]:  # ... that follows pattern

            cols = []
            for i in range(0,headers.shape[0]):    
                cols.append(headers.loc[i].values)

        else:   # that does not

            cols = None
            print('\n\t!!! columns headers must be done manually !!!\n')   

    df = pd.DataFrame(columns=cols, data=values)
    df['table_title'] = table_title

    return df

######################

def getLatestLinks():
    
    '''
    Finds the most recent transcipts that have been posted. 
    User then selects which one they would like to have searched.
    '''
    
    df = pd.DataFrame(columns=['date', 'house', 'url'])
    
    url = 'https://www.aph.gov.au/Parliamentary_Business/Hansard'
    table = getTables(getSoup(url), False)[0]
    trs = table.find_all('tr')
    
    for tr in trs:
        
        date = tr.find('td', {'class': 'date'})
        if date != None:
            
            date = date.text
            house = [td.find('a')['aria-label'] for td in tr.find_all('td') if bool(td.find('a')) and 'aria-label' in td.find('a').attrs][0]
                            
            tds = [td for td in table.find_all('td')]
            for td in tds:    
                if bool(td.find_all('a')):
                    a = [x for x in td.find_all('a') if 'title' in x.attrs and x['title'] == 'XML format']
                    url = 'https://www.aph.gov.au' + a[0]['href'] if len(a) == 1 else None
                                                
            df.loc[df.shape[0]+1] = date, house, url
                        
    return df

######

def getSpeeches(dfLATESTLINKS, row):
    
    '''
    Converts all speeches (essentially, a few pars of a statement made in the chamber) from the XML into a dataframe with speaker name, state and party.
    Is unfiltered beyond some basic clean-up.
    '''
    
    df = pd.DataFrame()
    
    soup = getSoup(dfLATESTLINKS.loc[row, 'url'])

    speeches = soup.find_all('speech')
    for speech in speeches:
            
        dfx = pd.read_xml(str(speech), xpath=".//talker")
        
        talk_text = speech.find('talk.text').text 
        talk_text = ''.join(c for c in talk_text if c.isprintable())
        talk_text = re.sub('The PRESIDENT \(\d+:\d+\):', '', talk_text)
        talk_text = re.sub('^.+\(\d+:\d+\):', '', talk_text) ### ?????????????
        
        dfx['talk_text'] = talk_text
        
        
        df = pd.concat([df,dfx])
    
    df = df.drop_duplicates().reset_index(drop=True)
    df = df[[x for x in df.columns if x not in ['time.stamp', 'in.gov', 'first.speech']]] ## these are unused columns
    df = df.loc[~df['name'].str.contains('interjecting')] ### injecteors are also shown up as having given the speech. this removes their row
    df = df.loc[~df['name'].str.contains('CHAIR')] 
    df = df.loc[~df['name'].str.contains('PRESIDENT')] 

    return df

##### 

def filterSpeeches(df):
    
    '''
    Looks through each speech in the main dataframe for claims. 
    Breaks each speech into sentences, then filters out certain phrases and gives a score to sentences that contain certain other phrases that are often used in claims.
    Return a new dataframe that is sorted by score of potential claim.
    '''
    
    dfCLAIMS = pd.DataFrame(columns=df.columns)
    
    claim = None
        
    for index, row in df.iterrows():
        talk_text = row['talk_text']
        
        if bool(re.search('\d{2,10}', talk_text)):
            sentences = talk_text.split('. ')

            for sentence in sentences:
                
                ### This excludes - from the regex search = a number of phrases that may produce meaningless results. 
                ### For example, 'Section 24' or '42-years-old'
                ### This does not affect it picking up other numbers of 2 or more digits that may be in a sentence
                ### But it makes it so those terms will not be the trigger for being included
                
                pre_filtered_sentence = sentence.replace(',','').lower()  ## so no 1,435 for example
                pre_filtered_sentence = re.sub('(20\d\d)', '', pre_filtered_sentence)  ## no years
                pre_filtered_sentence = re.sub('(19\d\d)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(\d+ recommendations)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(\d+ of the recommendations)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(\d+ month)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(24-{0,1} {0,1}hour)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(standing order \d+)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(subclass \d+)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(section \d+)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(bill \d+)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(at the age of \d+)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(\d{1}0 or \d{1}0 year)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(\d+-year)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(\d+ year)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('(my \dos)', '', pre_filtered_sentence)
                pre_filtered_sentence = re.sub('covid-19', '', pre_filtered_sentence)
                
                if bool(re.search('\d{2,10}', pre_filtered_sentence)):  
                    
                    nr = dfCLAIMS.shape[0]+1
                    dfCLAIMS.loc[nr, row.keys()] = row.values
                    dfCLAIMS.loc[nr, 'claim'] = sentence
                    
                    contains_percent = 0
                    if 'percent' in sentence or 'per cent' in sentence:
                        contains_percent = 1
                        
                    contains_dollar = 0
                    if '$' in sentence or 'dollar' in sentence:
                        contains_dollar = 1
                        
                    contains_record = 0
                    if 'record' in sentence:
                        contains_record = 1
                        
                    contains_about = 0
                    if bool(re.search('about \d+', pre_filtered_sentence)):
                        contains_about = 1
                        
                    contains_there_are = 0
                    if bool(re.search('there are \d+', pre_filtered_sentence)):
                        contains_there_are = 1
                        
                    contains_funding = 0
                    if bool(re.search('funding \d+', pre_filtered_sentence.replace('$',''))):
                        contains_funding = 1
                        
                    contains_large_number = 0
                    if bool(re.search('\d,\d{3}', sentence)):  ### needs the unfiltered version
                        contains_large_number = 1
                        
                    contains_decimal = 0
                    if bool(re.search('\d\.\d+', pre_filtered_sentence)):
                        contains_decimal = 1
                        
                    contains_promise = 0
                    if 'promise' in sentence:
                        contains_promise = 1
                        
                    contains_times = 0
                    if bool(re.search('\d+ times', pre_filtered_sentence)):
                        contains_times = 1
                                                 
                    dfCLAIMS.loc[nr, 'contains_percent'] = contains_percent
                    dfCLAIMS.loc[nr, 'contains_dollar'] = contains_dollar
                    dfCLAIMS.loc[nr, 'contains_record'] = contains_record
                    dfCLAIMS.loc[nr, 'contains_about'] = contains_about
                    dfCLAIMS.loc[nr, 'contains_there_are'] = contains_about
                    dfCLAIMS.loc[nr, 'contains_funding'] = contains_funding
                    dfCLAIMS.loc[nr, 'contains_large_number'] = contains_large_number
                    dfCLAIMS.loc[nr, 'contains_decimal'] = contains_decimal
                    dfCLAIMS.loc[nr, 'contains_promise'] = contains_promise
                    dfCLAIMS.loc[nr, 'contains_times'] = contains_times
                    
    contain_columns = [x for x in dfCLAIMS.columns if 'contain' in x]
    dfCLAIMS['score'] = dfCLAIMS[contain_columns].sum(axis=1)
    dfCLAIMS = dfCLAIMS.sort_values(by=['score'], ascending=False)
        
    return dfCLAIMS

######

def runScript():
    
    dfLATESTLINKS = getLatestLinks()
    
    st.dataframe(dfLATESTLINKS[['date', 'house']])
    
    selected_row = st.number_input('Choose by row number: ', step = 1, min_value = 1, max_value = dfLATESTLINKS.shape[0])
    proceed = st.radio('Start claim hunting?', ['no', 'yes'], horizontal=True)
    if proceed == 'yes':
        dfSPEECHES = getSpeeches(dfLATESTLINKS, selected_row)    
        dfCLAIMS = filterSpeeches(dfSPEECHES)
    
        st.dataframe(dfCLAIMS[['claim', 'name']], width=1000)
    
        return dfCLAIMS

    
    
    
def runScript2():
    
    url = 'https://www.aph.gov.au/Parliamentary_Business/Hansard'
    
    response = get(url, headers=None)
    #soup = BeautifulSoup(response.text, 'lxml')

    return response
    
########################

st.write('Constituent Investigative Analytics Studio')

st.write('# HANSARD CLAIMS HUNTER #####')

st.write('Searches the latest Hansards for claims that can be analysed by fact checker.') 

runScript2()


st.write('')
st.write('')
st.write('&#11041; More tools at www.constituent.au')