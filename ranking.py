MAXGENERATIONS = 1300

def fitness():
    pass

def mutate(gene):
    return gene + np.random.normal() * exp(np.random.standard_cauchy())

def es_rank(trainingset):
    # query document pairs
    # set genes to 0
    M = [0,0,0,0] # len features
    function = 0
    good = False
    offspring = parent
    R = 0
    mutation_indices = []
    for gen in MAXGENERATIONS:
        if good:
            pass
        else:
            R = np.random(1,M)
            for j in range(R):
                # take one from M
                i = M[j] # todo random
                mutation_indices.append(i)
                offspring[i] = mutate(offspring[i])
        if fitness(parent) < fitness(offspring):
            parent = offspring
            good = True
        else:
            offspring = parent
            good = False
    return function
