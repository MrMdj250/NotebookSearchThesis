from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

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
    search = get_results(response)
    return search

def get_results(response):
    results = []
    for hit in response:
        print('HIT:', hit.name)
        result_tuple = (hit.name, hit.html_url, hit.language)
        results.append(result_tuple)
    return results

# if __name__ == '__main__':
#     print("Opal guy details:\n", search(name = "opal"))
#     print("the first 20 f language details:\n", search(language = "f"))
