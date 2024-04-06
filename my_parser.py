import feedparser
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import re

# Parse the RSS feed
feed_url = "https://www.p2p-kredite.com/diskussion/sm/forum"
feed = feedparser.parse(feed_url)

# Function to extract postbody from HTML page
def extract_postbody(link):
    url_components = urlparse(link)
    post_id = url_components.fragment
    if post_id:
        post_url = f"{url_components.scheme}://{url_components.netloc}{url_components.path}"
        
        # Define the session and set the session cookie
        session = requests.Session()
        session.cookies.set("p2pkredites_sid", "6bbf6d038ea0dd4c1d9e12c9cfea3a83")  # Replace COOKIE_NAME and COOKIE_VALUE with your session cookie
        
        # Make the request with the session
        response = session.get(post_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            post_link = soup.find_all('a', {'name': post_id})
            if post_link:
                postbody_element = post_link[0].find_next(class_='postbody')
                if postbody_element.get_text():
                    postbody = postbody_element.get_text()
                    #return postbody
                else:
                    next_postbody_element = postbody_element.find_next(class_='postbody')
                    heading_quotetable_before_postbody_element = next_postbody_element.find_previous('span', class_='genmed').get_text().strip()
                    quote_tabledata_before_postbody_element = next_postbody_element.find_previous('td', class_='quote').get_text().strip()
                    postbody = "<b>" + heading_quotetable_before_postbody_element + "</b><br>\n" + "<i>" + quote_tabledata_before_postbody_element + "</i><br>\n" + next_postbody_element.get_text().strip()
                #Remove signature from end of post
                last_index = postbody.rfind('_________________')
                if last_index != -1:
                    postbody = postbody[:last_index]
                #Reduce multiple line breaks to single line breaks
                postbody = re.sub(r'\n{2,}', '\n', postbody)
                return "<![CDATA[" + postbody + "]]>"
    return "Postbody not found"


# Function to update feed items with postbody content
def update_feed_with_postbody(feed):
    for item in feed.entries:
        link = item.link
        postbody = extract_postbody(link)
        item['postbody'] = postbody
    return feed

# Update feed with postbody content
updated_feed = update_feed_with_postbody(feed)

# Function to generate new feed XML with postbody content
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

# Generate new feed XML with postbody content
new_feed_xml = generate_new_feed_xml(updated_feed)

# Save new feed XML to a file
with open('new_feed.xml', 'w', encoding='utf-8') as f:
    f.write(new_feed_xml)
