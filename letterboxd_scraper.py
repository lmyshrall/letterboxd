from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import requests
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500,502,503,504])
session.mount('https://', HTTPAdapter(max_retries=retries))

driver = webdriver.Chrome()
headers = {'User-Agent': 'Mozilla/5.0'}
base_url = 'https://letterboxd.com'

list_url = 'https://letterboxd.com/mogwai_synth/list/new-york-times-100-best-movies-of-the-21st/'
driver.get(list_url)
soup = BeautifulSoup(driver.page_source, features = 'html.parser')

urls = [
    base_url + a['href']
    for a in soup.select('a[href^="/film/"]')
]

def get_runtime(movie_soup):
    runtime_selectors = [
        'p.text-link.text-footer',
        'div.text-footer',   
        'span.runtime',
        'time'
    ]
    
    for selector in runtime_selectors:
        runtime_element = movie_soup.select_one(selector)
        if runtime_element:

            runtime_match = re.search(
                r'(\d+)\s*(?:&nbsp;|\s)*mins?',
                runtime_element.get_text()
            )
            if runtime_match:
                return f"{runtime_match.group(1)} mins"
            
            runtime_text = runtime_element.get_text(strip=True)
            if 'min' in runtime_text:
                return runtime_text.split('min')[0].strip() + ' mins'
    
    return "Unknown"



data = []
for index, url in enumerate(urls[:100], start=1):
    print(f'Scraping #{index}, {url}...')
    response = requests.get(url, headers = headers)
    movie_soup = BeautifulSoup(response.text, 'html.parser')
    
    title = movie_soup.select_one('h1.headline-1').get_text(strip=True) if movie_soup.select_one('h1.headline-1') else 'Unknown'
        
    director = movie_soup.select_one('a[href*="/director/"]').get_text(strip=True) if movie_soup.select_one('a[href*="/director/"]') else 'Unknown'

    year = movie_soup.select_one('a[href*="/year/"]').get_text(strip=True) if movie_soup.select_one('a[href*="/year/"]') else 'Unknown' 

    genres = [
            genre.get_text(strip=True)
            for genre in movie_soup.select('a[href*="/genre/"]')
        ]     if movie_soup.select('a[href*="/genre/"]') else ['Unknown']
        
    rating = movie_soup.select_one('meta[name="twitter:data2"]')['content'] if movie_soup.select_one('meta[name="twitter:data2"]') else 'Unknown'
        
    language = movie_soup.select_one('a[href*="/language/"]').get_text(strip=True) if movie_soup.select_one('a[href*="/language/"]') else 'Unknown'
    
    country_element = movie_soup.select('a[href*="/films/country/"]')   
    countries = [    
            country.get_text(strip=True)
            for country in country_element
        ] if country_element else ['Unknown']

    runtime = get_runtime(movie_soup)
    
    data.append({
        'rank': index, 
        'title': title,
        'director': director,
        'release_year': year,
        'genre': genres,
        'rating': rating,
        'language': language,
        'country': countries,
        'runtime': runtime,
        'url': url
    })
    time.sleep(2)
    
driver.quit()
    
df = pd.DataFrame(data)
df.to_csv('letterboxd.csv', index=False, encoding='utf-8')
print('Scraping complete, data saved to letterboxd.csv.')