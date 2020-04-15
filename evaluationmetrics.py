# this file contains evaluation metrics
# Michael de Jong

def precision(relevant_list):
    return relevant_list.count(1) / len(relevant_list)

def recall(relevant_list, relevant_count):
    return relevant_list.count(1) / relevant_count

def f1(relevant_list, relevant_count):
    P = precision(relevant_list)
    R = recall(relevant_list, relevant_count)
    return 2 * P * R / (P+R)

def avg_precision(relevant_list, relevant_count):
    total = 0
    for k in range(len(relevant_list)):
        if k != 0:
            total = total + (precision(relevant_list[0:k]) * relevant_list[k])
    return total / relevant_count

def map(queries_relevant_lists, relevant_count):
    total = 0
    for relevant_list in queries_relevant_lists:
        total = total + avg_precision(relevant_list, relevant_count)
    return total / len(queries_relevant_lists)

def dcg():
    return

def ndcg():
    return
