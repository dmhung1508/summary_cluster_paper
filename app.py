import json
import time
from tqdm import tqdm
from fastapi import FastAPI
from pymongo import MongoClient
from bson import json_util
import uvicorn

app = FastAPI()

def get_all():
    connect_string = (
        "mongodb://rootUser:hometag121@178.128.19.31:27017/test"
        "?authSource=test&readPreference=primary&directConnection=true&ssl=false"
    )
    client = MongoClient(connect_string)
    mm_newflow = client["vn-newsflow"]
    mm_cluster = mm_newflow["clusters"]
    mm_articles = mm_newflow["articles"]

    outputs = {}

    for cluster in tqdm(mm_cluster.find()):
        ids, name_cluster = cluster["_id"], cluster["name"]
        outputs[name_cluster] = {
            "avgStd": cluster["avgStd"],
            "zscore": cluster["score"],
            "articles": [article for article in mm_articles.find({"clusterId": ids})]
        }

    return outputs

@app.get("/all_cluster")
async def get_all_items():
    time_start = time.time()
    data = get_all()
    data = json.loads(json_util.dumps(data))
    time_end = time.time()
    print(time_end - time_start)
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4502)