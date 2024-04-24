import os
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from playwright.sync_api import sync_playwright

# Login credentials (from environment variables)
LOGIN_URL = "https://www.p2p-kredite.com/diskussion/login.php"
USERNAME = os.environ.get("FORUM_USERNAME")
PASSWORD = os.environ.get("FORUM_PASSWORD")

def extract_postbody(my_page, link):
    url_components = urlparse(link)
    post_id = url_components.fragment
    if post_id:
        post_url = f"{url_components.scheme}://{url_components.netloc}{url_components.path}"
        my_page.goto(post_url)
        soup = BeautifulSoup(my_page.content(), 'html.parser')
        post_link = soup.find_all('a', {'name': post_id})
        author = post_link[0].find_next('b')
        if post_link:
            post_td = post_link[0].find_next('td')
            while post_td:
                if post_td.find(class_='postbody'):
                    post_td.find("tr").decompose()
                    post_td.find("tr").decompose()
                    # Wrap the text inside each "quote" element with the <i> tag
                    quote_elements = post_td.find_all(class_='quote')
                    for quote in quote_elements:
                        new_tag = soup.new_tag('i')
                        for content in quote.contents:
                            new_tag.append(content)
                        quote.clear()
                        quote.append(new_tag)
                    post_td.insert(0, author)
                    postbody = str(post_td)
                    #Remove signature from end of post
                    last_index = postbody.rfind('_________________')
                    if last_index != -1:
                        postbody = postbody[:last_index]
                        return "<![CDATA[" + postbody + "]]>"
                    return "<![CDATA[" + postbody + "]]>"
                post_td = post_td.find_next('td')
            # #Reduce multiple line breaks to single line breaks
            # postbody = re.sub(r'\n{2,}', '\n', postbody)
    return "Postbody not found"

def generate_new_feed_xml(feed):
    new_feed = '<?xml version="1.0"?>\n<rss version="2.0">\n<channel>\n<title>P2P Forum</title>\n<link>https://www.p2p-kredite.com/diskussion/</link>\n<description>All Posts in the P2P Forum</description>\n'
    for item in feed.entries:
        new_feed += '<item>\n'
        new_feed += f'<title>{item.title}</title>\n'
        new_feed += f'<description>{item.postbody}</description>\n'
        new_feed += f'<link>{item.link}</link>\n'
        new_feed += f'<guid>{item.link}</guid>\n'
        new_feed += f'<pubDate>{item.published}</pubDate>\n'
        new_feed += '</item>\n'
    new_feed += '</channel>\n</rss>'
    return new_feed

with sync_playwright() as p:
    # Log into the forum
    browser = p.firefox.launch()
    page = browser.new_page()
    page.goto(LOGIN_URL)
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[name="login"]')
    # Parse original RSS feed
    feed_url = "https://www.p2p-kredite.com/diskussion/sm/forum"
    feed = feedparser.parse(feed_url)
    # Add postbody to feed
    for item in feed.entries:
        postbody = extract_postbody(page, item.link)
        item['postbody'] = postbody
    new_feed_xml = generate_new_feed_xml(feed)
    # Save new feed XML to a file
    with open('new_feed.xml', 'w', encoding='utf-8') as f:
        f.write(new_feed_xml)