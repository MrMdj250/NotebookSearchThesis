from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from bs4 import BeautifulSoup
import markdown

def search(name="", language="All", index="info_clone"):
    es = Elasticsearch()
    name = '*'+ name + '*'
    if language != 'All':
        q = Q("bool", should=[Q("wildcard", name=name),
        Q("match", language=language)], minimum_should_match=2)
    else:
        q = Q("wildcard", name=name)
    print(q)
    s = Search(using=es, index=index).query(q)[0:20]
    response = s.execute()
    search = get_results(es, response)
    return search

# check if a file exists in info_clone, where no checkpoint files exist
def check_checkpoint(es, notebook_id):
    if es.exists(index='info_clone2', id=notebook_id):
        return True
    else:
        return False

def ranking(es, q):
    n = 20
    s0 = Search(using=es, index='info_clone2').query(q)[0:n]
    s1 = Search(using=es, index='markdown').query(q)[0:n]
    s2 = Search(using=es, index='comments2').query(q)[0:n]
    s3 = Search(using=es, index='code').query(q)[0:n]
    # # TODO:

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
        test = ''.join(BeautifulSoup(html).findAll(text=True))

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
