import requests
from bs4 import BeautifulSoup

def news_pars():
    url_v = "https://vc.ru/popular"
    url_r = "https://ria.ru/science"
    r_v = requests.get(url_v)
    r_r = requests.get(url_r)
    soup_v = BeautifulSoup(r_v.text, "html.parser")
    soup_r = BeautifulSoup(r_r.text, "html.parser")

    articles = []

    for i in soup_v.find_all("div", class_="content content--short"):
        article = i.find("div", class_="content-title content-title--short l-island-a")
        if article is None:
            articles.append('none')
        else:
            title = article.text.strip().replace("\n\n\nСтатьи редакции", "")
            articles.append(title)

    for i in soup_r.find_all("div", class_="section_set"):
        for article in i.find_all("div", class_="cell-list__item"):
            if article is None:
                articles.append('none')
            else:
                title = article.a["title"]
                articles.append(title)

    return articles
