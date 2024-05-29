import numpy as np
import time
import openai
from tqdm import tqdm
from collections import Counter
from database import Database
from pymongo import MongoClient
from generate_openai import generate_new_paper, generate_title_paper, generate_keyword, generate_summary_paper, generate_keyword_of_cluster,generate_keyword_ver2
from ranking import ranking_clustering, ranking_algorithm
from audio import getAudio, generate_audio

def most_frequent(List):
    counter = 0
    num = List[0]
     
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i
 
    return num

def update_clusters(config, clusters_outputs, posts, list_data_clean, embeddings, time_now, esp, model):
    # score_cluster = ranking_clustering(clusters_outputs, posts, time_now)
    score_cluster = ranking_algorithm(clusters_outputs, posts, list_data_clean, time_now, model, config)
    db = Database(config, time_now)

    clusters_outputs = dict(sorted(score_cluster.items(), key=lambda item: item[1]['score'], reverse=True))
    new_cluster_outputs = {}
    for idx in clusters_outputs:
        new_cluster_outputs[idx] = clusters_outputs[idx]["ids"]

    list_cluster = []
    count_cluster = 0
    listTitles = []
    listSummary = []
    listImageContent = []

    for ids in new_cluster_outputs:
        new_post = {}
        titlePaper = str(ids)
        new_post["name"] = str(ids)
        newPaper = ""
        summaryPaper = ""

        try:
            newPaper = generate_new_paper(new_cluster_outputs[ids], list_data_clean, config)
            #print("newPaper:",newPaper)
        except:
            print("error generate new paper")
            newPaper = list_data_clean[ids][1]  # content of first paper
            newPaper = ""


        try:
            titlePaper = generate_title_paper(new_cluster_outputs[ids], list_data_clean, config)
            print("titlePaper:", titlePaper)
        except Exception as e:
            titlePaper = ""
            print("Error generating title paper:", e)

        try:
            if count_cluster < config.CLUSTER_TO_DAY:
                summaryPaper = generate_summary_paper(new_cluster_outputs[ids], list_data_clean, config)
        except:
            summaryPaper = ""

        new_post["sumaryCluster"] = titlePaper
        # new_post["keywords"] = keyword
        new_post["createdAt"] = time_now
        new_post["updatedAt"] = time_now
        new_post["newPaper"] = newPaper
        new_post["ids"] = score_cluster[ids]['ids']
        new_post["score"] = score_cluster[ids]["score"]
        list_cluster.append(new_post)

        if count_cluster < config.CLUSTER_TO_DAY:
            listTitles.append(titlePaper)
            listSummary.append(summaryPaper)
            listImageContent.append(posts[score_cluster[ids]['ids'][0]]["imageContents"])
        count_cluster += 1

    if count_cluster >= config.CLUSTER_TO_DAY:
        try:
            keyword = generate_keyword_ver2(listTitles, config)
        except:
            keyword = ""
            print("error apikey title keyword")

        # insert 8amToDay
        try:
            generate_audio(keyword, "audio/audio.mp3", config)
        except:
            print("lõi voice")
            pass

        todayNews = {}
        todayNews["keywords"] = keyword
        todayNews["createdAt"] = time_now
        todayNews["news"] = []

        for idx in range(len(listTitles)):
            news = {}
            news["title"] = listTitles[idx]
            news["summary"] = listSummary[idx]
            if idx == 0:
                first = "tin thứ nhất: "
            elif idx == 1:
                first = "tin thứ hai: "
            elif idx == 2:
                first = "tin thứ ba: "
            elif idx == 3:
                first = "tin thứ tư: "
            elif idx == 4:
                first = "tin thứ năm: "
            elif idx == 5:
                first = "tin thứ sáu: "
            elif idx == 6:
                first = "tin thứ bảy: "
            elif idx == 7:
                first = "tin thứ tám: "

            text_audio = first + listTitles[idx] + ". " + listSummary[idx]
            news["createdAt"] = time_now
            news["imageContents"] = listImageContent[idx]
            file_audio_save = "audio" + "/" + str(idx) + ".mp3"

            try:
                generate_audio(text_audio, file_audio_save, config)
                # getAudio(text_audio, "audio.mp3", db)
            except:
                pass



            with open(file_audio_save, 'rb') as mp3_file:
                mp3_content = mp3_file.read()

            news["audio"] = mp3_content
            todayNews["news"].append(news)

        db.delete_todaynews()
        time.sleep(1)
        print("delete successfull")

        db.vn_newflow["todaynews"].insert_one(todayNews)

    db.delete_db()

    #insert database
    for cluster in list_cluster:
        id_post = cluster["ids"].copy()
        cluster_insert = cluster.copy()
        cluster_categori = cluster.copy()

        listCategories = []

        for ids in id_post:
            if "sourceCategoryId" in posts[ids] and "newPaper" not in posts[ids]:
                listCategories.append(posts[ids]["sourceCategoryId"])

        maxFrequently_category = most_frequent(listCategories)

        list_time = [posts[idx]["createdAt"] for idx in id_post]
        list_imageContents = [posts[idx]["imageContents"] for idx in id_post]

        sorted_time = sorted(list_time, key=lambda x: x.timestamp(), reverse=True)
        cluster_insert["updatedAt"] = sorted_time[0]
        keyword_cluster = ""
        try:
            keyword_cluster = generate_keyword_of_cluster(cluster_insert["sumaryCluster"], config)
        except:
            keyword_cluster = "None"
            pass
    
        cluster_insert["keywords"] = keyword_cluster
        cluster_insert["categoryId"] = maxFrequently_category
        cluster_insert["createdDate"] = time_now.strftime("%Y-%m-%d %H")

        # cluster_insert["createdDate"] = sorted_time[0].strftime("%Y-%m-%d %H")
        cluster_insert["createdDate"] = time_now.strftime("%Y-%m-%d %H")
        cluster_insert["imageContents"] = list_imageContents

        clusterInsert = db.vn_newflow["clusters"].insert_one(cluster_insert)
        # clusterCategori = db.vn_newflow["clusters"].insert_one(cluster_categori)

        id_cluster = clusterInsert.inserted_id
        # id_clusterCategori = clusterCategori.inserted_id
        count_index = 0

        first_article = {}
        first_article["title"] = cluster_insert["sumaryCluster"]

        first_article["description"] = ""
        for idxs in id_post:
            first_article["sourceId"] = posts[idxs]["sourceId"]
            first_article["imageContents"] = list_imageContents
            first_article["videoContents"] = posts[idxs]["videoContents"]
            first_article["createdAt"] = posts[idxs]["createdAt"]
            first_article["postedAt"] = posts[idx]["postedAt"]
            first_article["link"] = posts[idxs]["link"]
            first_article["renderedContent"] = posts[idxs]["renderedContent"]
            first_article["updatedAt"] = cluster_insert["updatedAt"]
            break
        first_article["textContent"] = cluster_insert["newPaper"]
        first_article["likes"] = 0
        first_article["shares"] = 0
        first_article["type"] = "AI"
        first_article["comments"] = 0
        first_article["totalReactions"] = 0
        first_article["editedTextContent"] = 0
        first_article["isPositive"] = False
        first_article["isNegative"] = False
        first_article["clusterId"] = id_cluster
        first_article["index"] = 0
        first_article["sourceCategoryId"] = maxFrequently_category
        result = db.vn_newflow["articles"].insert_one(first_article)

        for idx in id_post:
            count_index += 1
            new_article = {}
            if posts[idx]["type"] == "FB_POST":
                new_article["title"] = posts[idx]["title"]
                new_article["sourceId"] = posts[idx]["sourceId"]
                new_article["description"] = "string"
                new_article["imageContents"] = posts[idx]["imageContents"]
                new_article["videoContents"] = posts[idx]["videoContents"]
                new_article["link"] = posts[idx]["link"]
                new_article["type"] = posts[idx]["type"]
                new_article["likes"] = posts[idx]["likes"]
                new_article["shares"] = posts[idx]["shares"]
                new_article["comments"] = posts[idx]["comments"]
                new_article["totalReactions"] = posts[idx]["totalReactions"]
                new_article["editedTextContent"] = posts[idx]["editedTextContent"]
                new_article["isPositive"] = False
                new_article["isNegative"] = False
                new_article["clusterId"] = id_cluster
                new_article["createdAt"] = posts[idx]["createdAt"]
                new_article["renderedContent"] = posts[idx]["renderedContent"]
                new_article["updatedAt"] = time_now
                new_article["index"] = count_index
                new_article["postedAt"] = posts[idx]["postedAt"]
                if "sourceName" in posts[idx]:
                    new_article["sourceName"] = posts[idx]["sourceName"]
                else:
                    new_article["sourceName"] = "Null"
                try:
                    new_article["sourceCategoryId"] = posts[idx]["sourceCategoryId"]
                    new_article["sourceLink"] = posts[idx]["sourceLink"]
                    new_article["sourceType"] = posts[idx]["sourceType"]
                    new_article["sourceAvatar"] = posts[idx]["sourceAvatar"]
                except:
                    new_article["sourceCategoryId"] = "Null"
                    new_article["sourceLink"] = "Null"
                    new_article["sourceType"] = "Null"
                    new_article["sourceAvatar"] = "Null"
                # new_article["score"] = cluster_insert["score"][cnt-1]
                if "TopicsOnContents" in posts[idx]:
                    new_article["TopicsOnContents"] = posts[idx]["TopicsOnContents"]
                result = db.vn_newflow["articles"].insert_one(new_article)
            else:
                new_article["title"] = posts[idx]["title"]
                new_article["textContent"] = posts[idx]["textContent"]
                new_article["sourceId"] = posts[idx]["sourceId"]
                new_article["description"] = "string"
                new_article["imageContents"] = posts[idx]["imageContents"]
                new_article["videoContents"] = posts[idx]["videoContents"]
                new_article["link"] = posts[idx]["link"]
                new_article["type"] = posts[idx]["type"]
                new_article["likes"] = posts[idx]["likes"]
                new_article["shares"] = posts[idx]["shares"]
                new_article["comments"] = posts[idx]["comments"]
                new_article["totalReactions"] = posts[idx]["totalReactions"]
                new_article["editedTextContent"] = posts[idx]["editedTextContent"]
                new_article["renderedContent"] = posts[idx]["renderedContent"]
                new_article["postedAt"] = posts[idx]["postedAt"]
                new_article["isPositive"] = False
                new_article["isNegative"] = False
                new_article["clusterId"] = id_cluster
                new_article["createdAt"] = posts[idx]["createdAt"]
                new_article["updatedAt"] = time_now
                if "sourceName" in posts[idx]:
                    new_article["sourceName"] = posts[idx]["sourceName"]
                else:
                    new_article["sourceName"] = "Null"
                try:
                    new_article["sourceCategoryId"] = posts[idx]["sourceCategoryId"]
                    new_article["sourceLink"] = posts[idx]["sourceLink"]
                    new_article["sourceType"] = posts[idx]["sourceType"]
                    new_article["sourceAvatar"] = posts[idx]["sourceAvatar"]
                except:
                    new_article["sourceCategoryId"] = "Null"
                    new_article["sourceLink"] = "Null"
                    new_article["sourceType"] = "Null"
                    new_article["sourceAvatar"] = "Null"
                # new_article["score"] = cluster_insert["score"][cnt-1]
                new_article["index"] = count_index
                if "TopicsOnContents" in posts[idx]:
                    new_article["TopicsOnContents"] = posts[idx]["TopicsOnContents"]
                result = db.vn_newflow["articles"].insert_one(new_article)

    # getAudio(text_audio, "audio.mp3", db)
