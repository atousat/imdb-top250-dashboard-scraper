
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# user agent
my_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.170 Safari/537.36"
options = Options()
options.add_argument("--headless")
options.add_argument(f"--user-agent={my_user_agent}")

browser = webdriver.Chrome(options=options)
browser.get("https://www.imdb.com/chart/top/")

time.sleep(3)

# header for beautifulsoup
headers = {'User-Agent': my_user_agent,
            "Accept-Language": "en-US,en;q=0.9"}

# find page link
page_link = browser.find_elements(By.CLASS_NAME, "ipc-title-link-wrapper")
# add all links to list
page_links_list =[]
for link in page_link:
    href = link.get_attribute("href")
    # print(href)
    page_links_list.append(href)


browser.quit()

# --------- Directors Names ------------
def get_directors_names(link):
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        # get director in same page
        movie_directores = soup.find("span", string="Director").find_parent("li")
        director = [directors.get_text() for directors in movie_directores.find_all("a")]
    except:
        try:
            # get directors in same page
            movie_directores = soup.find("span", string="Directors").find_parent("li")
            director = [directors.get_text() for directors in movie_directores.find_all("a")]
        except:
            # get director in another page
            movie_directores = soup.find("a", string="Directors").find_parent("li")
            url_href = movie_directores.find("a")["href"]
            url_site = "https://www.imdb.com"
            url = url_site + url_href

            response = requests.get(url, headers=headers) 
            soup = BeautifulSoup(response.text, "html.parser")

            movie_director = soup.find("span", string="Directors").find_parent("section")
            class_item = "ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big"
            director = [stars.get_text() for stars in movie_director.find_all("a", class_=class_item)]


    return director


# --------- Stars Names ---------------
def get_stars_name(link):
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # go to stasr name page
    movie_stars = soup.find("a", string="Stars").find_parent("li")
    url_href = movie_stars.find("a")["href"]
    url_site = "https://www.imdb.com"
    url = url_site + url_href
    
    response = requests.get(url, headers=headers) 
    soup = BeautifulSoup(response.text, "html.parser")
    
    # get star name
    movie_stars = soup.find("span", string="Cast").find_parent("section")
    class_item = "ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big"
    star = [stars.get_text() for stars in movie_stars.find_all("a", class_=class_item)]

    return star


# --------- Writesrs names --------------
def get_writers_name(link):
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        # writers in same page
        movie_writer = soup.find("span", string="Writers").find_parent("li")
        writer = [writers.get_text() for writers in movie_writer.find_all("a")]

    except:
        try:
            # writer in same page
            movie_writer = soup.find("span", string="Writer").find_parent("li")
            writer = [writers.get_text() for writers in movie_writer.find_all("a")]

        except:
            # writers in another page
            url_href = soup.find(class_= "ipc-metadata-list-item__icon-link")["href"]
            url_site = "https://www.imdb.com"
            url_needed = url_site + url_href

            response = requests.get(url_needed, headers=headers) 
            soup = BeautifulSoup(response.text, "html.parser")

            movie_writer = soup.find("span", string="Writers").find_parent("section")
            class_item = "ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big"
            writer = [writer.get_text() for writer in movie_writer.find_all("a", class_= class_item)]

    return writer


# ----- to minutes -----
def to_minutes(movie_time): 
    # find number in movie time
    time = str(movie_time)
    time_numbers = re.findall(r"\d+", time)

    if len(time_numbers) == 2:
        # hour and minutes
        hours, minutes = time_numbers
        runtime = int(hours) * 60 + int(minutes)
    elif len(time_numbers) == 1:
        # just hours
        hours = time_numbers[0]
        runtime = int(hours) * 60

    return runtime



# --------- Get data from each page -------------
def data_per_page(link):
    # get data with beautifulsoup
    headers = {'User-Agent': my_user_agent,
               "Accept-Language": "en-US,en;q=0.9"}
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 0 - Movie ID
    link_id = re.search(r"tt\d+", link).group()
    movie_id = re.findall(r"\d+", link_id)
    movie_id = movie_id[0] # list to str

    # 1 - title
    title = soup.find(class_ = "hero__primary-text").string


    # 2- year, 3- parental_guide, 4- runtime
    row2 = soup.find(class_ = "ipc-inline-list ipc-inline-list--show-dividers sc-b41e510f-3 ggypaO baseAlt baseAlt")
    items = [item.string for item in row2]
    if len(items) == 3:
        year, parental_guide, movie_time = items
        runtime = to_minutes(movie_time)
    else:
        # parental guide not found
        year, movie_time = items
        parental_guide = 'Unknown'
        runtime = to_minutes(movie_time)
         
    # 5 - genrs
    movie_genres = soup.find(class_ = "ipc-chip-list__scroller")
    genre = [genre.string for genre in movie_genres]

    # 6 - directors
    director = get_directors_names(link)

    # 7 - writers
    writer = get_writers_name(link)

    # 8 - stars
    star = get_stars_name(link)

    # 9 - sales in the us and canada
    movie_sales = soup.find("span", string="Gross US & Canada")
    if movie_sales:
        movie_sales = movie_sales.find_parent("li")
        gross_us_canada = movie_sales.find("li").get_text()
    else:
        # gross us canada not found
        gross_us_canada = 0


    # --- OutPut ----
    return(
        movie_id,
        title,
        year,
        parental_guide,
        runtime,
        genre,
        director,
        writer,
        star,
        gross_us_canada
    )


# ------ Inser data to the list -------
data = []
for url in page_links_list:
    print(url)
    result = data_per_page(url)
    data.append(result)


# --------- To DataFrame ------------
df = pd.DataFrame(data, 
                  columns=["movie_id",
                            "title",
                            "year",
                            "parental_guide",
                            "runtime",
                            "genre",
                            "directore",
                            "writer",
                            "star",
                            "gross_us_canada"])

# df.head()


# --------- Clean Data -----------
"""
conver columns list to string 
"""
def list_to_str(dataframe, columns_name):
    dataframe[columns_name] = dataframe[columns_name].apply(lambda x: ",".join(x))
    return dataframe

columns_to_change = ["genre", "director", "writer", "star"] 
for col in columns_to_change:
    list_to_str(df, col)


# --------- To Excel -------------
df.to_excel("imdb_Top250Movies.xlsx")






    



