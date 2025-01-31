# imports
import os
import sys
import json
import numpy as np
import pandas as pd
import nbconvert
import nbformat
import zipfile
import csv
import time
from tqdm.auto import tqdm

# argument handeling
try:
    folder = str(sys.argv[1])
except:
    print('please give the folder name of the folder as an argument, example:"bb2733859v_3_1"')
    sys.exit()

# global vars
TYPE= "notebook"
COLUMNS = ['nb_id', 'html_url', 'name', 'language', 'markdown', 'comments', 'code']
VERSION = 4

def get_ids_zip(path):
    path = path + '.zip'
    print(path)
    nbzip = zipfile.ZipFile(path, 'r')
    filenames = nbzip.namelist()
    ids = []
    for i in range(len(filenames)):
        if filenames[i].startswith('nb_') and filenames[i].endswith('.ipynb'):
            current_id = int(filenames[i][3:-6])
            ids.append(current_id)
        else:
            print('miss')
    return ids, nbzip

# zip version
def get_text_zip(nb_id, nbzip):
    markdown = []
    comments = []
    code = []
    with nbzip.open('nb_' + str(nb_id) + '.ipynb') as raw:
        try:
            data = nbformat.read(raw, VERSION)
            #data = json.load(fp)
        except:
            try:
                data = nbformat.read(raw, nbformat.NO_CONVERT)
            except:
                return None, None, None, None
    if 'cells' in data.keys():
        cells = data['cells']
        if 'metadata' in data:
            if 'kernelspec' in data['metadata']:
                if 'language' in data['metadata']['kernelspec']:
                    language = data['metadata']['kernelspec']['language']
                else:
                    language = 'unknown'
            else:
                language = 'unknown'
        else:
            language = 'unknown'
        try:
            md_cells = [c for c in cells if c['cell_type'] == 'markdown']
            code_cells = [c for c in cells if c['cell_type'] == 'code']
        except:
            return None, None, None, None
        for cell in md_cells:
            if 'source' in cell:
                markdown.append(cell['source'])

        # find comments '# ' for R and Python
        for cell in code_cells:
            if 'source' in cell:
                source = cell['source']
                code.append(source)
                string = ''
                if source != None:
                    for item in source:
                        string = string + str(item)
                    if '# ' in string:
                        comments.append(string)
        return language, markdown, comments, code
    else:
        return None, None, None, None

# load the csv with all notebook information
df_nb = pd.read_csv('notebooks.csv')
df_nb = df_nb.drop(['max_filesize','min_filesize', 'path', 'query_page', 'repo_id'], axis=1)

ids, nbzip = get_ids_zip(folder)

# append all extra columns to dataframe and export to pickle, zip
starttime = time.time()
final_df = pd.DataFrame(columns = COLUMNS)
# ids = [0,1,2,3,4,5,120951,23352,73638,179265,54493]
for i in tqdm(range(len(ids))):
    language, markdown, comments, code = get_text_zip(ids[i], nbzip)
    if language != None or markdown != None or comments != None or code != None:
        row = df_nb.loc[df_nb['nb_id'] == ids[i]]
        final_df = final_df.append({COLUMNS[0]:row['nb_id'].values[0],
                                    COLUMNS[1]:row['html_url'].values[0],
                                    COLUMNS[2]:row['name'].values[0],
                                    COLUMNS[3]:language,
                                    COLUMNS[4]:markdown,
                                    COLUMNS[5]:comments,
                                    COLUMNS[6]:code},
                                   ignore_index=True)
# save the dataframe to pickle
midtime = time.time()
print(midtime - starttime)
n = folder + '_new' + '.pkl'# + 'TEST' + '.pkl'
final_df.to_pickle(n)
endtime = time.time()
print(endtime - starttime)
final_df.head()
