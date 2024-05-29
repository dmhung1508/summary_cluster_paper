import numpy as np
from database import Database

def ranking_clustering(cluster, database, time_now):
    db = Database(time_now)
    scores = db.get_all_source_fromdb()

    clusters = {}
    for id in cluster:
        sum = 0
        score_cluster = {}
        score_cluster["id"] = str(id)
        score_article = {}
        list_article = []
        for idx in cluster[id]:
            if database[idx]["sourceId"] is not None and database[idx]["sourceId"] in scores.keys():
                score_article[idx] = [scores[database[idx]["sourceId"]], database[idx]["type"], database[idx]["sourceId"]]
            else:
                score_article[idx] = [0, database[idx]["type"], database[idx]["sourceId"]]
        list_time_articles = []
        for idx in cluster[id]:
            list_time_articles.append([database[idx]["createdAt"], idx])


        list_time_articles = sorted(list_time_articles, key=lambda x: x[0], reverse=True)
        max_index = list_time_articles[0][1]
        score_article.pop(max_index)


        sorted_dict = dict(sorted(score_article.items(), key=lambda x: -x[1][0]))
        if len(sorted_dict) <= 4:
            list_article.append(max_index)
            for idx in list(sorted_dict):
                list_article.append(idx)
        else:
            list_check_source = []
            list_article = []
            list_article.append(max_index)

            type_post = [value[1] for value in sorted_dict.values()]
            sourceId = [value[2] for value in sorted_dict.values()]
            

            if "WEBSITE_POST" in type_post and "FB_POST" in type_post and "YOUTUBE" in type_post:
                list_check_post = []
                for key in sorted_dict:
                    if sorted_dict[key][1] not in list_check_post and sorted_dict[key][2] not in list_check_source:
                        list_check_post.append(sorted_dict[key][1])
                        list_check_source.append(sorted_dict[key][2])
                        list_article.append(key)

                for key in sorted_dict:
                    if key not in list_article:
                        list_article.append(key)
            elif "WEBSITE_POST" in type_post and  "FB_POST" in type_post:
                    if type_post.count("WEBSITE_POST") >= type_post.count("FB_POST"):
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "WEBSITE_POST" and len(list_article) < 4 and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "FB_POST" and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                                break
                        for key in sorted_dict:
                            if key not in list_article:
                                list_article.append(key)
                    else:
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "WEBSITE_POST" and len(list_article) < 4 and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "FB_POST" and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                                break
                        for key in sorted_dict:
                            if key not in list_article:
                                list_article.append(key) 
            elif "WEBSITE_POST" in type_post and  "YOUTUBE" in type_post:
                    if type_post.count("WEBSITE_POST") >= type_post.count("YOUTUBE"):
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "WEBSITE_POST" and len(list_article) < 4 and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "YOUTUBE" and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                                break
                        for key in sorted_dict:
                            if key not in list_article:
                                list_article.append(key)
                    else:
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "WEBSITE_POST" and len(list_article) < 4 and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                        for key in sorted_dict:
                            if sorted_dict[key][1] == "YOUTUBE" and sorted_dict[key][2] not in list_check_source:
                                list_article.append(key)
                                list_check_source.append(sorted_dict[key][2])
                                break
                        for key in sorted_dict:
                            if key not in list_article:
                                list_article.append(key) 

            elif "FB_POST" in type_post and  "YOUTUBE" in type_post:
                for key in sorted_dict:
                    if sorted_dict[key][1] == "FB_POST" and sorted_dict[key][2] not in list_check_source:
                        list_article.append(key)
                        list_check_source.append(sorted_dict[key][2])
                        break
                for key in sorted_dict:
                    if sorted_dict[key][1] == "YOUTUBE" and sorted_dict[key][2] not in list_check_source:
                        list_article.append(key)
                        list_check_source.append(sorted_dict[key][2])
                        break
                for key in sorted_dict:
                    if key not in list_article:
                        list_article.append(key)
            else:
                for key in sorted_dict:
                    if key not in list_article and sorted_dict[key][2] not in list_check_source:
                        list_check_source.append(sorted_dict[key][2])
                        list_article.append(key)
                for key in sorted_dict:
                    if key not in list_article:
                        list_article.append(key)
        for idx in cluster[id]:
            if database[idx]["sourceId"] in scores.keys():
                sum += scores[database[idx]["sourceId"]]
            else:
                sum += 0
        score_cluster["ids"] = list_article
        score_cluster["score"] = sum
        

        clusters[id] = score_cluster

    return clusters


def distance_euclidean(a_point, b_point):
    return np.linalg.norm(a_point - b_point)

def ranking_algorithm(cluster_outputs, posts, clean_data, time, model, config):
    model = model.get_model()
    db = Database(config, time)
    scores = db.get_all_source_fromdb()

    clusters = {}
    

    for cluster in cluster_outputs:
        article_scores = {}
        outputs = {}
        article_orders = []
        vecs = []
        indexs = []
        sumOfScore = 0
        for indexInCluster in cluster_outputs[cluster]:
            vec = model.encode(clean_data[indexInCluster][2])
            vecs.append(vec)
            indexs.append(indexInCluster)
        
        for indexInVec in range(len(vecs)):
            if indexInVec == 0:
                first_index = indexInVec
                continue
            distance = distance_euclidean(vecs[indexInVec], vecs[0])
            article_scores[indexs[indexInVec]] = distance
        
        sorted_dict = dict(sorted(article_scores.items(), key = lambda item: item[1], reverse=True))


        article_orders.append(indexs[first_index])
        for k,v in sorted_dict.items():
            article_orders.append(k)


        for indexInCluster in cluster_outputs[cluster]:
            if posts[indexInCluster]['sourceId'] in scores.keys():
                sumOfScore += scores[posts[indexInCluster]["sourceId"]]
            else:
                sumOfScore += 0
        
        outputs['ids'] = article_orders
        outputs['score'] = sumOfScore
        clusters[cluster] = outputs

    return clusters
        