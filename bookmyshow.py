"""Bookmyshow scraper."""
__author__ = "Santosh Venkatraman<santosh.venk@gmail.com>"
import sys
sys.dont_write_bytecode = True
from json import dumps

from requests import get
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout                                                                              
from lxml import html


BASE_URL = "https://in.bookmyshow.com"


def get_html_document(url):
    """
    Helper to fetch content from url and convert into a HTML document.
    :param url: URL to be scraped
    :type  url: str
    :rtype html.HtmlElement
    """
    if not url:
        raise SystemError("get_html_document(): url must not be empty")
    if not isinstance(url, str):
        raise SystemError("get_html_document(): url must be a string")

    try:
        response = get(url, timeout=10)
    except (ConnectionError, ConnectTimeout, ReadTimeout) as error:
        print(f"Error fetching content from '{url}' : '{error}'. Exiting...")
        sys.exit(1)
    return html.document_fromstring(response.content)


def fetch_xpath_data(dom_element, xpath_key):
    """
    Helper to fetch xpath data using xpath key
    :param dom_element: HTML DOM element
    :type. dom_element: html.HtmlElement
    :rtype None / html.HtmlElement
    """
    if not isinstance(dom_element, html.HtmlElement):
        return None

    xpath_value = dom_element.xpath(xpath_key)
    if not xpath_value:
        return None

    return xpath_value[0] if len(xpath_value) == 1 else xpath_value


def fetch_children(dom_element):
    """
    Helper to fetch children of DOM element
    :param dom_element: HTML DOM element
    :type. dom_element: html.HtmlElement
    """
    if dom_element is None:
        return

    children = dom_element.getchildren()
    if not children:
        return
    if len(children) == 1:
        return children[0]
    return children


def fetch_currently_showing_cards(html_document):
    """
    Helper method to fetch 'currently showing' cards.
    :param html_document: HTML document
    :type. html_document: html.HtmlElement
    """
    if not isinstance(html_document, html.HtmlElement):
        raise SystemError(
            " ".join([
                "fetch_currently_showing_cards():",
                "html_document must be of type html.HtmlElement"
            ])
        )
    return fetch_xpath_data(
        dom_element=html_document,
        xpath_key="//div[@class='card-container']"
    )

def fetch_tickets_link(card_element):
    """Helper to fetch tickets link."""
    dom_element = fetch_xpath_data(
        dom_element=card_element,
        xpath_key="div[@class='book-button']"
    )
    child = fetch_children(dom_element)
    if child is None:
        return
    if child.tag == "div":
        return
    return fetch_xpath_data(
        dom_element=child,
        xpath_key="@href"
    )


def fetch_movie_data(card_element):
    """
    Helper method to fetch title & link of movie from card.
    :param card_element: Movie card element
    :type. card_element: html.HtmlElement
    :rtype dict
    """
    if not isinstance(card_element, html.HtmlElement):
        raise SystemError(
            " ".join([
                "fetch_movie_data():",
                "card_element must be of type html.HtmlElement"
            ])
        )
    movie_data = fetch_xpath_data(
        dom_element=card_element,
        xpath_key="div[@class='detail']/div[@class='__name overflowEllipses']/a"
    )
    title = fetch_xpath_data(dom_element=movie_data, xpath_key="@title")
    title = title.strip() if isinstance(title, str) else title
    movie_link = fetch_xpath_data(dom_element=movie_data, xpath_key="@href")
    tickets_link = fetch_tickets_link(card_element=card_element)
    return {
        "title": title,
        "movie_link": movie_link if movie_link is None else \
            f"{BASE_URL}{movie_link}",
        "tickets_link": tickets_link if tickets_link is None else \
            f"{BASE_URL}{tickets_link}",
    }

def fetch_movies_data(url):
    """
    Helper to fetch 'currently showing' movies with active booking links on BMS.
    :param url: URL to scrape from
    :type  url: str
    :rtype list<dict>
    """
    html_document = get_html_document(url)
    cards = fetch_currently_showing_cards(html_document)
    data = list(
        filter(
            lambda x: x.get("tickets_link") is not None,
            map(fetch_movie_data, cards)
        )
    )
    print(dumps({"url": url, "data": data}, indent=4))

if __name__ == '__main__':
    urls = [
        "https://in.bookmyshow.com/bengaluru/movies/english",
        "https://in.bookmyshow.com/chennai/movies/english"
    ]
    list(map(fetch_movies_data, urls))
