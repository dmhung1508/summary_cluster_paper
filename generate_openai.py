import torch
import time
import openai,re
from tqdm import tqdm
from database import Database
from pymongo import MongoClient
import config
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1/',

    # required but ignored
    api_key='ollama',
)

def generate_keyword(text, config):
    text = "\n".join(text)
    print(text)
    prompt = text + "\n" + config.PROMPT_GENERATE_KEYWORD
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.PROMPT_GENERATE_KEYWORD
            },
            {
                'role': 'user',
                'content': text
            }
        ],
        temperature=0,
        max_tokens = 256,
        
        #request_timeout=config.REQUEST_TIMEOUT,
        model='gpt-3.5-turboz',
    )
    keyword = chat_completion.choices[0].message.content
    return keyword
def generate_keyword_ver2(text, config):
    key = []
    for t in text:

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    'role': 'system',
                    'content': "Hãy tóm tắt tiêu đề trên chỉ còn 6 từ, không dài dòng lan man, giữ được đúng ý của nó. Giúp người đọc có thể hiểu luôn được tiêu đề đó,Chỉ trả lời bằng tiếng Việt Nam, ngôn ngữ Việt Nam"
                },
                {
                    'role': 'user',
                    'content': 'Cháy nhà trọ ở Hà Nội, nhiều người thương vong',
                },
                {
                    'role': 'assistant',
                    'content': "Cháy nhà trọ Hà Nội"
                },
                {
                    'role': 'user',
                    'content': "Quan chức cấp cao của Nga bị bắt trong cuộc đàn áp tham nhũng",
                },
                {
                    'role': 'assistant',
                    'content': "Quan chức Nga tham nhũng"
                },
                {
                    'role': 'user',
                    'content': "28 Người Bị Chấn Thương Não, Cột Sống Sau Sự Cố Của Singapore Airlines",
                },
                {
                    'role': 'assistant',
                    'content': "28 chấn thương Singapore Airlines",
                },
                {
                    'role': 'user',
                    'content': "Ngôi sao Ngoại Hạng Anh đối mặt án phạt cấm thi đấu 10 năm vì dàn xếp tỷ số",
                },
                {
                    'role': 'assistant',
                    'content': "Ngôi sao Anh bị cấm",
                },
                {
                    'role': 'user',
                    'content': t
                }
            ],
            temperature=0,
            max_tokens = 15,
            
            #request_timeout=config.REQUEST_TIMEOUT,
            model='gpt-3.5-turbo',
        )
        paper =  chat_completion.choices[0].message.content
        print(paper)
        key.append(paper)
    key = ";".join(key)
    return key

def generate_title_paper(clusters, list_text, config):
    num_token_input = 0
    text_full = []
    step = 0
    for idx in tqdm(clusters):
        if step == 0 and len(list_text[idx][2]) > config.MIN_OF_TOKEN:
            continue
        step += 1
        num_token_input += len(list_text[idx][2])
        if num_token_input >= config.MIN_OF_TOKEN:
            break
        text_full.append(list_text[idx][2] + "\n")
    
    merge_text = " ".join(text_full)

    prompt = merge_text + "\n" + config.PROMPT_GENERATE_TITLE
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.PROMPT_GENERATE_TITLE
            },
            {
                'role': 'user',
                'content': merge_text
            }
        ],
        temperature=0,
        max_tokens=256,
        model='gpt-3.5-turbo',
    )
    
    quick_link = chat_completion.choices[0].message.content
    items = re.findall(r'\s*(?:\d+\.\s*)?[\'"]?([^\'"\n]+?)[\'"]?(?=\s*(?:\d+\.|\Z))', quick_link)
    first_item = items[0] if items else None
    
    if first_item:
        num_words = len(first_item.split())
        print(num_words)
    else:
        num_words = 0
    
    while num_words > 30 or num_words < 3:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": config.PROMPT_GENERATE_TITLE
                },
                {
                    'role': 'user',
                    'content': merge_text
                }
            ],
            temperature=0.1,
            max_tokens=256,
            model='gpt-3.5-turbo',
        )
        quick_link = chat_completion.choices[0].message.content
        print(quick_link)
        items = re.findall(r'\s*(?:\d+\.\s*)?[\'"]?([^\'"\n]+?)[\'"]?(?=\s*(?:\d+\.|\Z))', quick_link)
        first_item = items[0] if items else None
        
        if first_item:
            num_words = len(first_item.split())
        else:
            num_words = 0
        print(num_words)
    return first_item



def generate_new_paper(clusters, list_text, config):
    num_token_input = 0
    text_full = []
    step = 0
    for id in tqdm(clusters):
        if step == 0 and len(list_text[id][1]) > config.MIN_OF_TOKEN:
            continue
        step+=1
        num_token_input +=  len(list_text[id][1])
        if num_token_input >= config.MIN_OF_TOKEN:
            break
        text_full.append(list_text[id][1]+"\n")
    merge_text = " ".join(text_full)

    prompt = merge_text+ "/n"+ config.PROMT_GENERATE_PAPER
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.PROMT_GENERATE_PAPER
            },
            {
                'role': 'user',
                'content': merge_text
            }
        ],
        temperature=0,
        max_tokens = 2048,
        
        #request_timeout=config.REQUEST_TIMEOUT,
        model='gpt-3.5-turbo',
    )
    paper =  chat_completion.choices[0].message.content
    return paper

def generate_one_paper(text, config):
    num_token_input +=  len(text)
    
    text_full = []
    if num_token_input >= config.MIN_OF_TOKEN:
        return False
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.PROMT_GENERATE_PAPER
            },
            {
                'role': 'user',
                'content': text
            }
        ],
        temperature=0,
        max_tokens = 2048,
        
        #request_timeout=config.REQUEST_TIMEOUT,
        model='gpt-3.5-turbo',
    )
    paper =  chat_completion.choices[0].message.content
    return paper

def generate_summary_paper(clusters, list_text, config):
    num_token_input = 0
    text_full = []
    step = 0
    for id in tqdm(clusters):
        if step == 0 and len(list_text[id][1]) > config.MIN_OF_TOKEN:
            continue
        step+=1
        num_token_input +=  len(list_text[id][1])
        if num_token_input >= config.MIN_OF_TOKEN:
            break
        text_full.append(list_text[id][1]+"\n")
    new_text = " ".join(text_full)


    prompt = new_text+ "/n"+ config.PROMPT_GENERATE_SUMMARY
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.PROMPT_GENERATE_SUMMARY
            },
            {
                'role': 'user',
                'content': new_text
            }
        ],
        temperature=0,
        max_tokens = 2048,
        
        #request_timeout=config.REQUEST_TIMEOUT,
        model='gpt-3.5-turbo',
    )
    title =  chat_completion.choices[0].message.content
    return title


def generate_keyword_of_cluster(text, config):
    prompt = text + "/n"+ config.PROMPT_GENERATE_KEYWORD_CLUSTER
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.PROMPT_GENERATE_KEYWORD_CLUSTER
            },
            {
                'role': 'user',
                'content': text
            }
        ],
        temperature=0,
        max_tokens = 256,
        
        #request_timeout=config.REQUEST_TIMEOUT,
        model='gpt-3.5-turbo',
    )
    hashtag =  chat_completion.choices[0].message.content
    items = re.findall(r'\s*(?:\d+\.\s*)?[\'"]?([^\'"\n]+?)[\'"]?(?=\s*(?:\d+\.|\Z))', hashtag)
    first_item = items[0]
    return hashtag
