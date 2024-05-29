from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
#DBSCAN
def DBSCAN_algorithm(esp, min_sample, vector_embedding):
    clustering = DBSCAN(eps=esp, min_samples=min_sample).fit(vector_embedding)
    labels = clustering.labels_
    # labels = [label for label in labels if label !=-1]
    return labels

def custom_algorithm(vector_embedding):
    cluster = {}
    check_list_id = []
    for idx in range(len(vector_embedding)):
        cluster[idx] = []
        for id in range(len(vector_embedding)):
            if idx != id:
                score = cosine_similarity(vector_embedding[idx].reshape(1,-1), vector_embedding[id].reshape(1,-1))[0]
                if score > 0.8:
                    if id not in check_list_id:
                        cluster[idx].append(id)
                        check_list_id.append(id)
        if idx not in check_list_id:
            cluster[idx].append(idx)
            check_list_id.append(idx)
    return cluster