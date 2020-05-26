from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from bs4 import BeautifulSoup
import markdown

def search(name="", language=""):
    es = Elasticsearch()
    name = '*'+ name + '*'
    if language != 'All':
        q = Q("bool", should=[Q("wildcard", name=name),
        Q("match", language=language)], minimum_should_match=2)
    else:
        q = Q("wildcard", name=name)
    print(q)
    s = Search(using=es, index="info_clone").query(q)[0:20]
    # TODO add more indices to search
    # TODO ranking function
    response = s.execute()
    search = get_results(es, response)
    return search

def get_results(es, response):
    results = []
    for hit in response:
        nid = hit.meta.id
        print('HIT:', hit.name, nid)

        # add text snippit to search results
        mkdn = es.get(index='markdown', id=nid)
        mkdnlist = mkdn['_source']['markdown']
        if mkdnlist != []:
            markdownstr = ''.join(mkdnlist) # from list to one string
            markdownstr = markdownstr[:200] + '...'

            # convert to html, then to text
            html = markdown.markdown(markdownstr)
            test = ''.join(BeautifulSoup(html).findAll(text=True))
        else:
            # if there is no markdown, use code snippit
            code = es.get(index='code', id=nid)
            test = code['_source']['functions']
            if test == []:
                test = code['_source']['classes']

            # no code, then comment snippit
            if test == []:
                comments = es.get(index='comments2', id=nid)
                c = comments['_source']['comments']
                if c != []:
                    test = ''.join(c)[:200] + '...'
                else:
                    test = []
            if test == []:
                print('Empty File', nid)
                test = 'Empty File'

        result_tuple = (hit.name, hit.html_url, hit.language, test)
        results.append(result_tuple)
    return results

# DEBUG:
# if __name__ == '__main__':
#     print("TEST:\n", search(name = "titanic"))
#     print("the first 20 python language details:\n", search(language = "python"))
