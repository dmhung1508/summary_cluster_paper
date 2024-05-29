import time
import config
import numpy as np
from tqdm import tqdm
import os
from datetime import datetime
from database import Database
from model import SentenceEmbedding
from update import update_clusters
from message_kafka import send_message
from cluster_algorithm import DBSCAN_algorithm
import argparse
import warnings
warnings.filterwarnings("ignore")

def countdown_timer(seconds):
    """
    Hàm đếm thời gian từ giá trị giây được cung cấp.

    Args:
        seconds (int): Số giây để đếm ngược.
    """
    while seconds > 0:
        mins, secs = divmod(seconds, 60)
        time_format = '{:02d}:{:02d}'.format(mins, secs)
        print(time_format, end='\r')
        time.sleep(1)
        seconds -= 1
    print("Time's up!")

def ConfigCluster(numPost):
    min_sample = 4 if numPost >= 1550 else 3
    esp = (
        6 if numPost <= 900 else
        5.75 if numPost <= 1200 else
        5.5 if numPost <= 1500 else 5
    )
    return min_sample, esp

def Merge(dict1, dict2):

    return {**dict1, **dict2}

def check_time_used_little(time_now):
    time_now = time_now.strftime('%H:%M')
    time_slots = [
        datetime.strptime("00:00", "%H:%M").strftime('%H:%M'),
        datetime.strptime("07:00", "%H:%M").strftime('%H:%M'),
        datetime.strptime("20:00", "%H:%M").strftime('%H:%M'),
        datetime.strptime("23:59", "%H:%M").strftime('%H:%M')
    ]

    return (time_slots[0] <= time_now < time_slots[1]) or (time_slots[2] <= time_now < time_slots[3])

def update_none_activate(posts, list_index, DB):
    DB.delete_datanotincluster()
    time.sleep(5)
    for idx in tqdm(range(len(posts))):
        if idx not in list_index:
            DB.vn_newflow["datanotinclusters"].insert_one(posts[idx])


def main():
    print("hello")

    #load model sentence embedding folder model
    model_path = config.MODEL_PATH
    model = SentenceEmbedding(model_path)
    print("jkkk")
    while True:
        
        #get time now
        timeSystem = datetime.now()
        #timeSystem = datetime(year=2024, month=5, day=24, hour=11, minute=45)
        print(timeSystem)

        #call Class DB
        DB = Database(config, timeSystem)
        print("hel")

        #get data from database:
        dataCluster, dataArticle = DB.get_all_article()
        print("num post:", len(dataCluster))

        if len(dataCluster) <= 0:
            print("ko có data")
            continue
        dataClear = [[text[0], text[1], text[2]] for text in dataCluster]
        id_articles, embeddings, titlePapers = model.get_embedding(dataClear)

        min_sample, esp = ConfigCluster(len(dataCluster))

        cluster = DBSCAN_algorithm(esp=esp, min_sample=min_sample, vector_embedding=embeddings)

        if len(cluster) <= 0:
            print("None cluster")
            continue

        uniqueCluster, counts = np.unique(cluster, return_counts=True)
        uniqueCluster = [idx for idx in uniqueCluster if idx != -1]

        clusters_outputs = {}
        list_index_not_activate = []
        for idx in uniqueCluster:
            clusters_outputs[idx] = []
            for id in range(len(cluster)):
                if cluster[id] == idx:
                    clusters_outputs[idx].append(id)
                    list_index_not_activate.append(id)

        try:
            update_none_activate(dataArticle, list_index_not_activate, DB)
        except Exception as e:
            print("Error update none activate paper:", e)


        length_cluster_oputputs = len(clusters_outputs)

        new_cluster_outputs = {}
        list_idx_remove = []

        for idx in clusters_outputs:
            if len(clusters_outputs[idx]) >= config.NUM_CLUSTER_FOR_RECLUSTER:
                newEmbedding = []
                for ids in clusters_outputs[idx]:
                    newEmbedding.append(embeddings[ids])
                new_clusters = DBSCAN_algorithm(esp=esp-1.25, min_sample=min_sample, vector_embedding=newEmbedding)
                unique_new, counts_new = np.unique(new_clusters, return_counts=True)
                unique_new = [i for i in unique_new if i != -1]

                for idn in unique_new:
                    if list(new_clusters).count(idn) >= config.MIN_PAPER_IN_CLUSTER:
                        if idx not in list_idx_remove:
                            list_idx_remove.append(idx)
                        new_cluster_outputs[length_cluster_oputputs] = []
                        for idw in range(len(clusters_outputs[idx])):
                            if new_clusters[idw] == idn:
                                new_cluster_outputs[length_cluster_oputputs].append(clusters_outputs[idx][idw])
                        length_cluster_oputputs += 1

                esp_plus = config.ESP_PLUS

                while np.max(counts_new) <= config.MIN_PAPER_IN_CLUSTER:
                    new_clusters = DBSCAN_algorithm(esp=esp-esp_plus, min_sample=min_sample, vector_embedding=newEmbedding)
                    unique_new, counts_new = np.unique(new_clusters, return_counts=True)
                    for idn in unique_new:
                        if list(new_clusters).count(idn) >= config.MIN_PAPER_IN_CLUSTER:
                            if idx not in list_idx_remove:
                                list_idx_remove.append(idx)
                            new_cluster_outputs[length_cluster_oputputs] = []
                            for idw in range(len(clusters_outputs[idx])):
                                if new_clusters[idw] == idn:
                                    new_cluster_outputs[length_cluster_oputputs].append(clusters_outputs[idx][idw])
                            length_cluster_oputputs += 1
                    esp_plus += 0.1
                    if esp_plus > 1.0:
                        break
            elif len(clusters_outputs[idx]) >= config.MIN_PAPER_IN_CLUSTER:
                newEmbedding = []
                for ids in clusters_outputs[idx]:
                    newEmbedding.append(embeddings[ids])
                new_clusters = DBSCAN_algorithm(esp=esp-1, min_sample=min_sample, vector_embedding=newEmbedding)
                unique_new, counts_new = np.unique(new_clusters, return_counts=True)
                unique_new = [i for i in unique_new if i != -1]
                for idn in unique_new:
                    if list(new_clusters).count(idn) >= config.MIN_PAPER_IN_CLUSTER:
                        if idx not in list_idx_remove:
                            list_idx_remove.append(idx)
                        new_cluster_outputs[length_cluster_oputputs] = []
                        for idw in range(len(clusters_outputs[idx])):
                            if new_clusters[idw] == idn:
                                new_cluster_outputs[length_cluster_oputputs].append(clusters_outputs[idx][idw])
                        length_cluster_oputputs += 1

        for idx in list_idx_remove:
            clusters_outputs.pop(idx)
        clusters_outputs_merge = Merge(clusters_outputs, new_cluster_outputs)

        print("NEW CLUSTER:")
        print(clusters_outputs_merge)

        update_clusters(config, clusters_outputs_merge, dataArticle, dataClear, embeddings, timeSystem, esp, model)
        send_message()

        if check_time_used_little(timeSystem):
            countdown_timer(config.TIME_SLEEP)
        else:
            countdown_timer(config.TIME_WAIT)


if __name__ == "__main__":
    main()
