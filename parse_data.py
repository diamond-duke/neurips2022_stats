import re
import os
import json
import time
import sqlite3
import datetime
import operator
import numpy as np
from tqdm import tqdm, trange

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# def get_item_url(panel, url_list, page_id):
#     # find all items in current page
#     item_list = panel.find_elements(By.CLASS_NAME, "note")
#     item_list_len = len(item_list)
#     for i in trange(item_list_len, desc=f"->{page_id}"):
#         # the fist <a> is the paper title and url
#         item = item_list[i].find_element(By.TAG_NAME, 'a')
#         url_list.append(item.get_attribute('href').strip()) 
        
        
# def get_url_list_for_tab(panel, tab_name):
#     # get totoal page number
#     _right_arrow = panel.find_elements(By.CLASS_NAME, 'right-arrow')[-1]
#     total_pages = int(_right_arrow.get_attribute('data-page-number'))
    
#     # loop all pages
#     url_list = []
#     for page_id in trange(total_pages):
#         get_item_url(panel, url_list, page_id)
        
#         if page_id == total_pages - 1:
#             continue
        
#         # the first item
#         flag = panel.find_element(By.CLASS_NAME, "note").text
        
#         time.sleep(1.5)
        
#         # click to jump to next page
#         next_page_btn = panel.find_element(By.CSS_SELECTOR, "li[class='  right-arrow']")
#         next_page_btn.find_element(By.TAG_NAME, 'a').click()
        
#         # jump to next page
#         jumped = False
#         num_try = 0
#         while not jumped:
#             time.sleep(1)
#             _flag = panel.find_element(By.CLASS_NAME, "note").text
#             if _flag != flag:
#                 jumped = True
#             num_try += 1
#             if num_try > 1000:
#                 break
    
#     return url_list
    
# s = Service('/opt/homebrew/bin/chromedriver')
# op = Options()
# op.add_argument('headless')
# for tab_name in ['poster']:
#     # driver = webdriver.Chrome(service=s, options=op)
#     driver = webdriver.Chrome(service=s)
#     driver.get(f'https://openreview.net/group?id=NeurIPS.cc/2022/Conference#accepted-papers')
#     time.sleep(2)
#     tabpanel = driver.find_element(By.ID, f'accepted-papers')
#     url_list = get_url_list_for_tab(tabpanel, tab_name)
    
#     # save to file
#     save_path = f"assets/{tab_name}_url_list_" \
#                 f"{datetime.datetime.now():%Y-%m-%d-%H:%M-UTC}.txt"
#     with open(save_path, 'w') as f:
#         f.write('\n'.join(url_list))  
        
#     # quit
#     driver.quit()

# read url list
url_dict = {}
text_files = os.listdir('assets/')
for text_file in text_files:
    if text_file.endswith('.txt'):
        cat = text_file.split('_')[0]
        with open(os.path.join('assets', text_file), 'r') as f:
            _urls = f.readlines()
        for _url in _urls:
            if len(_url.strip()) > 0:
                url_dict.update({_url: cat})
num_items = len(url_dict)
print(f'Total {num_items} items')

from database import DataBase
db = DataBase('assets/neurips2022.db')
# db.initialize(create=True, drop=True)
db.initialize(create=False)

s = Service('/opt/homebrew/bin/chromedriver')
op = Options()
op.add_argument('headless')
driver = webdriver.Chrome(service=s, options=op)

url_list = list(url_dict.keys())
for i in trange(num_items):
    url = url_list[i].strip()
    item_id = url.split('id=')[-1]
    cat = url_dict[url_list[i]]
    driver.get(url)
    time.sleep(1)
    loaded = False
    num_try = 0
    while not loaded:        
        # comments
        _comments = driver.find_element(By.ID, 'note_children')
        comments = _comments.find_elements(By.XPATH, "div[@class='note_with_children comment-level-odd']")
        
        if len(comments) > 0:
            loaded = True
        else:
            time.sleep(.5)
            assert num_try < 10, f'Failed to load {url} | tried: {num_try}'
            num_try += 1
    
    item = driver.find_element(By.ID, f'note_{item_id}')

    # title
    title_el = item.find_element(
        By.CSS_SELECTOR, "div[class='title_pdf_row clearfix']"
    ).find_element(By.CLASS_NAME, 'note_content_title').find_element(By.TAG_NAME, 'a')
    item_title = title_el.text.strip()

    # authors
    author_el = item.find_element(
        By.CSS_SELECTOR, "div[class='meta_row']"
    ).find_element(By.TAG_NAME, 'span').find_elements(By.TAG_NAME, 'a')
    item_authors = ", ".join([a.text for a in author_el])

    # keywords
    key_el = item.find_element(By.CLASS_NAME, 'note_contents').find_elements(By.TAG_NAME, 'span')
    if key_el[0].text == 'Keywords:':
        assert key_el[0].text == 'Keywords:', f'{url}: Keywords not found!'
        item_keywords = key_el[1].text
    else:
        item_keywords = ""
    
    # comments
    _comments = driver.find_element(By.ID, 'note_children')
    comments = _comments.find_elements(By.XPATH, "div[@class='note_with_children comment-level-odd']")
    
    item_ratings = []
    two_decision = False
    for comment in comments:
        keys = comment.find_elements(By.CLASS_NAME, 'note_content_field')
        values = comment.find_elements(By.CLASS_NAME, 'note_content_value')
        assert len(keys) == len(values), 'key not match with value for {url}'
        
        # paper decision box
        if 'Decision:' in [k.text for k in keys]:
            for _k in range(len(keys)):
                if keys[_k].text == 'Decision:':  # decesion
                    item_final_decision = values[_k].text
                    _item_final_decision = item_final_decision.split(' ')[-1].strip('(').strip(')')
                    # assert _item_final_decision.lower() == cat, f'final decision not match for {url}'
                if keys[_k].text == 'Consistency Experiment:':  # 
                    two_decision = True
                    _value = values[_k].text
                    _value_re = re.findall(r'.*This copy’s committee reached the following decision: (.*)', _value)
                    if len(_value_re) > 0:  
                        item_decision = _value_re[0]
                    else:  # both 
                        _value_re = re.findall(r'.*Both committees reached the same decision: (.*)', _value)
                        item_decision = _value_re[0]
                        
        # comemnt box
        elif 'Rating:' in [k.text for k in keys]:
            for _k in range(len(keys)):
                if keys[_k].text == 'Rating:':
                    _rating = int(values[_k].text.split(':')[0])
                    item_ratings.append(_rating)
    if two_decision:
        num_decision = 2
    else:
        num_decision = 1
        item_decision = item_final_decision
    # print(i, url, item_title, item_keywords, item_authors, item_final_decision, item_decision, item_ratings)
    db.write_item(i, url, item_title, item_keywords, item_authors, num_decision, item_final_decision, item_decision, item_ratings)

db.close()
driver.quit()