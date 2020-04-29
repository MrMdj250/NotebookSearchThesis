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

# argument handeling
try:
    folder = str(sys.argv[1])
except:
    print('please give the folder name of the folder as an argument, example:"bb2733859v_3_1"')
    sys.exit()

# global vars
INDEX="notebookindex"
TYPE= "notebook"
COLUMNS = ['nb_id', 'html_url', 'name', 'language', 'markdown', 'comments', 'code']

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
    # raw = nbzip.read('nb_' + str(nb_id) + '.ipynb')
    with nbzip.open('nb_' + str(nb_id) + '.ipynb') as raw:
        try:
            data = nbformat.read(raw, nbformat.NO_CONVERT)
            #data = json.load(fp)
        except:
            return None, None, None, None
    if 'cells' in data:
        cells = data['cells']
        if 'metadata' in data:
            if 'kernelspec' in data['metadata']:
                if 'language' in data['metadata']['kernelspec']:
                    language = data['metadata']['kernelspec']['language']
                else:
                    language = None
            else:
                language = None
        else:
            language = None
        try:
            md_cells = [c for c in cells if c['cell_type'] == 'markdown']
            code_cells = [c for c in cells if c['cell_type'] == 'code']
        except:
            return None, None, None, None
        if 'source' in md_cells:
            for cell in md_cells:
                markdown.append(cell['source'])

        # find comments '# ' for R and Python
        if 'source' in code_cells:
            for cell in code_cells:
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
for i in range(len(ids)):
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
n = folder + '.pkl'
final_df.to_pickle(n)
endtime = time.time()
print(endtime - starttime)
final_df.head()
