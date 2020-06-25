import numpy as np
import pandas as pd
import markdown
import pickle
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

def search(name="", language="All", index="title"):
    n = 20
    es = Elasticsearch()
    qname = '*'+ name + '*'
    if index == 'title':
        index = 'info_clone2'
        if language != 'All':
            q = Q('bool', should=[Q('wildcard', name=qname),
            Q('match', language=language)], minimum_should_match=2)
        else:
            q = Q('wildcard', name=qname)
        print(q)
        s = Search(using=es, index=index).query(q)[0:n]
        response = s.execute()
        search = get_results(es, response)
    elif index == 'all':
        search = ranking(es, name, language, n)
    else:
        search = []

    return search

# check if a file exists in info_clone2, where no checkpoint files etc exist
def check_checkpoint(es, notebook_id):
    if es.exists(index='info_clone2', id=notebook_id):
        return True
    else:
        return False

# predict the type of query using a code/text LogisticRegression classifier
def predict(name):
    # load the model and feature transformer from disk
    clf = pickle.load(open('model.pkl', 'rb'))
    feat_trans = pickle.load(open('transformer.pkl', 'rb'))

    qfeat = feat_trans.transform([name])
    pred = clf.predict(qfeat)
    return pred[0]

def sum_to_one(list):
    factor = 1 / float(sum(list))
    return [x * factor for x in list]

# determines which index to base the search on
def ranking(es, name, language, n):
    if language != 'All':
        q1 = Q('match', should=[Q('match', markdown=name),
        Q('match', language=language)], minimum_should_match=2)
        q2 = Q('match', should=[Q('match', comments=name),
        Q('match', language=language)], minimum_should_match=2)
        q3 = Q('match', should=[Q('multi_match', query=name,
        fields=['imports', 'classes', 'functions', 'code']),
        Q('match', language=language)], minimum_should_match=2)
    else:
        q0 = Q('match', name=name)
        q1 = Q('match', markdown=name)
        q2 = Q('match', comments=name)
        q3 = Q('multi_match', query=name,
        fields=['imports', 'classes', 'functions', 'code'])
    s1 = Search(using=es, index='markdown').query(q1)[0:n].execute()
    s2 = Search(using=es, index='comments2').query(q2)[0:n].execute()
    s3 = Search(using=es, index='code').query(q3)[0:n].execute()

    # get the ids
    s1ids = [hit.meta.id for hit in s1]
    s2ids = [hit.meta.id for hit in s2]
    s3idss = [hit.meta.id for hit in s2]

    # get the scores
    s1scores = [hit.meta.score for hit in s1]
    s2scores = [hit.meta.score for hit in s2]
    s3scores = [hit.meta.score for hit in s2]
    print('markdown:', s1scores)
    print('comments2:', s2scores)
    print('code:', s3scores)

    # get prediction
    pred = predict(name)
    print('prediction:', pred)
    # # TODO:
    f = 1 # factor to increase weights with
    weights = sum_to_one(list) # normalize([1,1,1], norm='l2')

    if pred == 'code':
        weights[3] = weights[3] + f
        weights = sum_to_one(list)
    elif pred == 'markdown':
        weights[3] = weights[3] + f
        weights = sum_to_one(list)
    s1scores = [x*weights[0] for x in s1scores]
    s2scores = [x*weights[1] for x in s2scores]
    s3scores = [x*weights[2] for x in s3scores]
    tup1 = list(zip(s1ids, s1scores))
    tup2 = list(zip(s2ids, s2scores))
    tup3 = list(zip(s2ids, s2scores))
    tupt = tup1 + tup2 + tup3
    tupsorted = sorted(tupt, key=lambda x:x[1])
    tupsorted = [nid for nid in tupsorted[0] if check_checkpoint(es, nid)]
    tupsorted = tupsorted[0:20]
    final_ids = [x[0] for x in tupsorted]
    # score = [s1,s2,s3]
    # dot weights query en ding
    # cosine similarity vector
    # cosine_similarity()
    # cosine similarity new gewogen score
    # Lineaire combinatie
    return elasticsearch_dsl.mget(final_ids, using=es, index='info_clone2')

# creates a text snippit for a search results
def snippit(es, notebook_id):
    test = []
    mkdn = es.get(index='markdown', id=notebook_id)
    cmts = es.get(index='comments2', id=notebook_id)
    cmtslist = cmts['_source']['comments']
    mkdnlist = mkdn['_source']['markdown']
    if mkdnlist != []:
        markdownstr = ''.join(mkdnlist) # from list to one string
        markdownstr = markdownstr[:200] + '...'

        # convert to html, then to text
        html = markdown.markdown(markdownstr)
        test = ''.join(BeautifulSoup(html,'lxml').findAll(text=True))

    # if there is no markdown, use comment snippit
    elif cmtslist != []:
        commentstr = ''.join(cmtslist) # from list to one string
        test = commentstr[:200] + '...'
    else:
        # if there is no comment, use code snippit
        code = es.get(index='code', id=notebook_id)
        test = code['_source']['functions']
        if test == []:
            test = code['_source']['classes']
        if test == []:
            test = ''.join(code['_source']['code'])[:200] + '...'
    return test

def get_results(es, response):
    results = []
    for hit in response:
        nid = hit.meta.id
        print('HIT:', hit.name, nid)
        if check_checkpoint(es, nid):
            result_tuple = (hit.name, hit.html_url, hit.language, snippit(es, nid))
            results.append(result_tuple)
    return results

# DEBUG:
# if __name__ == '__main__':
#     print("TEST:\n", search(name = "titanic"))
#     print("the first 20 python language details:\n", search(language = "python"))
