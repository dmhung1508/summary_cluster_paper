from datetime import datetime
from pymongo import MongoClient
from datetime import timezone, timedelta
from utils import clean_text

def check_time_in_day(time_now):
    time_now = time_now.strftime("%H:%M")
    time_slots = [
        "00:00", "06:00", "12:00", "18:00", "23:59"
    ]

    for index, slot in enumerate(time_slots[:-1], start=1):
        if slot <= time_now < time_slots[index]:
            return index
    return 4


def check_time_out_day(time_now):
    time_now = time_now.strftime("%H:%M")
    time_slots = [
        "00:00", "06:00", "12:00", "18:00", "23:59"
    ]

    if (time_slots[0] <= time_now < time_slots[1]) or (time_slots[3] <= time_now < time_slots[4]):
        return 1
    for index in range(1, len(time_slots) - 1):
        if time_slots[index] <= time_now < time_slots[index + 1]:
            return index + 1
    return 1


def check_out_day(time, time_now):
    time, time_now = time.strftime("%H:%M"), time_now.strftime("%H:%M")
    time_slots_a, time_slots_b, time_slots_c, time_slots_d = [
        "18:00", "23:59"
    ], ["00:00", "06:00"], ["06:00", "12:00"], ["12:00", "18:00"]

    if (time_slots_a[0] <= time <= time_slots_a[1]) and (time_slots_c[0] <= time_now <= time_slots_d[1]):
        return True
    return False


class Database():
    def __init__(self, config, time):
        self.config = config
        self.connect_string = self.config.DB_PATH
        self.client = MongoClient(self.connect_string)
        self.vn_newflow = self.client["vn-newsflow"]
        self.time = time

    def add_hours_to_time(self, time_str, hours):
        time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        updated_time_obj = time_obj + timedelta(hours=hours)
        # Format the updated time
        updated_time_str = updated_time_obj.strftime("%Y-%m-%d")
        return updated_time_obj, updated_time_str

    def add_days_to_time(self, time_str, day):
        # time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        # time_obj = time_str.strptime("%Y-%m-%d %H:%M")
        updated_time_obj = time_str + timedelta(days=day)
        updated_time_str = updated_time_obj.strftime("%Y-%m-%d")
        return updated_time_obj, updated_time_str

    def get_all_article(self):
        unprocessedarticles = self.vn_newflow["unprocessedarticles"]
        print(unprocessedarticles.find())
        dataCluster, dataArticle = [], []
        timeToday = self.time.strftime("%Y-%m-%d")
        blackList = ["xổ số", "Xổ số"]
        total_paper_count = 0
        for article in unprocessedarticles.find():
            if article["postedAt"] is not None:
                timePostAt = article["postedAt"].strftime("%Y-%m-%d %H:%M")

                # GMT+0 to GMT+7
                timePostAtPlus, timeToDayPost = self.add_hours_to_time(timePostAt, 7)

                # add 1 day
                timeYesterdayPlus, timeYesterdayPost = self.add_days_to_time(timePostAtPlus, day=1)

                # check time in day
                if (timeToDayPost == timeToday) and check_time_in_day(timePostAtPlus) == check_time_in_day(self.time):
                    if article["type"] == "FB_POST":
                        text = article["textContent"]
                        total_paper_count += 1
                        if len(text.split(" ")) >= self.config.MAX_INPUT_LENGTH:
                            text = text[:self.config.MAX_INPUT_LENGTH]
                            text = " ".join(text)
                        title = article["textContent"]
                    elif article["type"] == "YOUTUBE":
                        text = article["title"]
                        title = article["title"]
                        total_paper_count += 1
                    else:
                        content = article["textContent"].split(" ")
                        if len(content) <= self.config.MIN_INPUT_LENGTH:
                            continue
                        content_of_page = content[:self.config.MAX_INPUT_LENGTH]
                        content_of_page = " ".join(content_of_page)

                        text = article["title"] + " " + article["editedTextContent"] + " " + content_of_page
                        title = article["title"]
                    flag = False
                    for backtext in blackList:
                        if backtext in text:
                            flag = True
                    if flag == True:
                        continue
                    id_article = article["_id"]
                    dataCluster.append([id_article, clean_text(text), clean_text(title)])
                    dataArticle.append(article)
                else:
                    if (check_out_day(timeYesterdayPlus, self.time) == True and timeToday == timeYesterdayPost):
                        if (check_time_out_day(timePostAtPlus) == check_time_out_day(self.time)):
                            if article["type"] == "FB_POST":
                                text = article["textContent"]
                                total_paper_count += 1
                                if len(text.split(" ")) >= self.config.MAX_INPUT_LENGTH:
                                    text = text[:self.config.MAX_INPUT_LENGTH]
                                    text = " ".join(text)
                                title = article["textContent"]
                            elif article["type"] == "YOUTUBE":

                                text = article["title"]
                                title = article["title"]
                                total_paper_count += 1
                            else:
                                content = article["textContent"].split(" ")
                                if len(content) <= self.config.MIN_INPUT_LENGTH:
                                    continue
                                content_of_page = content[:self.config.MAX_INPUT_LENGTH]
                                content_of_page = " ".join(content_of_page)

                                text = article["title"] + " " + article["editedTextContent"] + content_of_page
                                title = article["title"]

                            flag = False
                            for backtext in blackList:
                                if backtext in text:
                                    flag = True
                            if flag == True:
                                continue

                            id_article = article["_id"]
                            dataCluster.append([id_article, clean_text(text), clean_text(title)])
                            dataArticle.append(article)
        print("total paper:", total_paper_count)
        return dataCluster, dataArticle

    def get_all_source_fromdb(self):
        sources = self.vn_newflow["sources"]
        scores = {}
        for data in sources.find():
            if data["ranking"] is not None:
                scores[data["sourceId"]] = data["ranking"]
        return scores

    def get_all_category_fromdb(self):
        category = self.vn_newflow["category"]
        categorys = {}
        for cate in category.find():
            categorys[cate["categoryId"]] = cate["name"]
        return categorys

    def delete_db(self):
        clusters_table = self.vn_newflow["clusters"]
        articles_table = self.vn_newflow["articles"]
        time_today = self.time.strftime("%Y-%m-%d")
        id_clusters_del = []
        for data in clusters_table.find():
            # time_cluters = datetime.datetime.strptime(data["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
            time_cluters = data["createdAt"].strftime("%Y-%m-%d")
            time_cluster_plus, time_cluster_plus_str = self.add_days_to_time(data["createdAt"], day=1)
            time_slot_check = check_time_out_day(self.time)
            time_cluster_check = check_time_out_day(data["createdAt"])
            if time_cluters == time_today and time_slot_check == time_cluster_check:
                id_clusters_del.append(data["_id"])
                clusters_table.delete_one({"_id": data["_id"]})
            else:
                time_slot_c = datetime.strptime("18:00", "%H:%M")
                time_slot_c = time_slot_c.strftime("%H:%M")

                time_slot_d = datetime.strptime("23:59", "%H:%M")
                time_slot_d = time_slot_d.strftime("%H:%M")
                time_now = data["createdAt"].strftime("%H:%M")

                if time_today == time_cluster_plus_str and time_slot_check == time_cluster_check and time_slot_c <= time_now <= time_slot_d:
                    id_clusters_del.append(data["_id"])
                    clusters_table.delete_one({"_id": data["_id"]})

        for data in articles_table.find():
            if data["clusterId"] in id_clusters_del:
                articles_table.delete_one({"_id": data["_id"]})

    def delete_todaynews(self):
        clusters_table = self.vn_newflow["todaynews"]
        clusters_table.drop()

    def delete_datanotincluster(self):
        # datanotinclusters = self.vn_newflow["datanotinclusters"]
        # datanotinclusters.drop()
        clusters_table = self.vn_newflow["datanotinclusters"]
        time_today = self.time.strftime("%Y-%m-%d")
        count_paper = 0
        print("start delete:")
        for data in clusters_table.find():
            # time_cluters = datetime.datetime.strptime(data["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
            time_cluters = data["postedAt"].strftime("%Y-%m-%d")
            time_cluster_plus, time_cluster_plus_str = self.add_days_to_time(data["postedAt"], 1)
            time_slot_check = check_time_out_day(self.time)
            timePostAt = data["postedAt"].strftime("%Y-%m-%d %H:%M")
            timePostAtPlus, timeToDayPost = self.add_hours_to_time(timePostAt, 7)
            time_cluster_check = check_time_out_day(timePostAtPlus)
            if time_cluters == time_today and time_slot_check == time_cluster_check:
                count_paper += 1
                clusters_table.delete_one(data)
            else:
                time_slot_c = datetime.strptime("18:00", "%H:%M")
                time_slot_c = time_slot_c.strftime("%H:%M")

                time_slot_d = datetime.strptime("23:59", "%H:%M")
                time_slot_d = time_slot_d.strftime("%H:%M")
                time_now = data["createdAt"].strftime("%H:%M")

                if time_today == time_cluster_plus_str and time_slot_check == time_cluster_check and time_slot_c <= time_now <= time_slot_d:
                    clusters_table.delete_one(data)
        print("succesfull delete:"+ str(count_paper) + " paper.")
