from splinter import Browser
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import time
import re


def scrape_all():
    # initate headless driver for deployment
    browser = Browser("chrome", executable_path="chromedriver", headless=True)
    news_title, news_paragraph = mars_news(browser)

    # Run all scraping functions and store in dictionary
    data = {
        "news_title": news_title,
        "news_paragraph": news_paragraph,
        "featured_image": featured_image(browser),
        "hemispheres": hemispheres(browser),
        "weather": twitter_weather(browser),
        "facts": mars_facts(),
        "last_modified": dt.datetime.now()
    }

    # Stop webdriver and return data
    browser.quit()
    return data


def mars_news(browser):
    url = "https://mars.nasa.gov/news/"
    browser.visit(url)

    # Get first list item and wait half a second
    browser.is_element_present_by_css("ul.item_list li.slide", wait_time=1)

    # Convert browser html to a soup object and then quit the browser
    html = browser.html
    news_soup = BeautifulSoup(html, 'html.parser')

    try:
        slide_elem = news_soup.select_one('ul.item_list li.slide')
        news_title = slide_elem.find("div", class_='content_title').get_text()
        news_p = slide_elem.find(
            'div', class_='article_teaser_body').get_text()

    except AttributeError:
        return None, None

    return news_title, news_p


def featured_image(browser):
    url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"
    browser.visit(url)

    # Find and click the full image button
    full_image_elem = browser.find_by_id("full_image")
    full_image_elem.click()

    # Find the more info button and click that
    browser.is_element_present_by_text("more info", wait_time=1)
    more_info_elem = browser.find_link_by_partial_text("more info")
    more_info_elem.click()

    # Parse the results with html with soup
    html = browser.html
    img_soup = BeautifulSoup(html, "html.parser")

    # Find the relative image URL
    img = img_soup.select_one("figure.lede a img")

    try:
        img_url_rel = img.get("src")

    except AttributeError:
        return None

    # Use the base url to create a new absolue url
    img_url = f"https://www.jpl.nasa.gov{img_url_rel}"

    return img_url


def hemispheres(browser):

    # A way to break up long strings
    url = ("https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars"
    )

    browser.visit(url)

    # Click the link, and find the sample anchor, return the href
    hemisphere_image_urls = []
    for i in range(4):

        # Find the elements on each loop to avoid stale elements
        browser.find_by_css("a.product-item h3")[i].click()

        hemi_data = scrape_hemisphere(browser.html)

        # Append hemisphere object to list
        hemisphere_image_urls.append(hemi_data)

        # Navigate back one page
        browser.back()

    return hemisphere_image_urls


def twitter_weather(browser):
    url = "https://twitter.com/marswxreport?lang=en"
    browser.visit(url)

    # Pause for 5sec to let the page load completely
    time.sleep(5)

    html = browser.html
    weather_soup = BeautifulSoup(html, "html.parser")

    # First, find a tweet withth e data-name "Mars Weather"
    tweet_attrs = {"class": "tweet", "data-name": "Mars Weather"}
    mars_weather_tweet = weather_soup.find("div", attrs=tweet_attrs)

    # Due to twitter changes try searching within the tweet for the ptag or span tag
    # containgn the tweet text.f
    # text using a regular exptression pattern that includes the string 'sol'
    # if there is no p tag with a class of 'tweet-text'

    try:
        mars_weather = mars_weather_tweet.find("p", "tweet-text").get_text()

    except AttributeError:
        pattern = re.compile(r'sol')
        mars_weather = weather_soup.find('span', text=pattern).text

    return mars_weather


def scrape_hemisphere(html_text):
    # Soupify the html text
    hemi_soup = BeautifulSoup(html_text, "html.parser")

    # Try to get href and text except if error.
    try:
        title_elem = hemi_soup.find("h2", class_="title").get_text()
        sample_elem = hemi_soup.find("a", text="Sample").get("href") #May be an issue

    except AttributeError:

        # Image error returns none for  better front-end handling
        title_elem = None
        sample_elem = None

    hemisphere = {
        "title": title_elem,
        "img_url": sample_elem
    }

    return hemisphere


def mars_facts():
    try:
        df = pd.read_html("https://space-facts.com/mars/")[0]
    except BaseException:
        return None

    df.columns = ["description", "value"]
    df.set_index("description", inplace=True)

    # Add some bootstrap action to the table
    return "Scraping Success - kind of"

if __name__ == "__main__":

    # If running as script, print scraped data
    print(scrape_all())
