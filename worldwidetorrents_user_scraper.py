from bs4 import BeautifulSoup

import os
import requests
import time
import urllib2


"""
" Tool to scrape all the torrents of a specific user on worldwidetorrents
"""

# USER DEFINED VARIABLES
USERS_TORRENTS_URL = 'http://worldwidetorrents.eu/torrents-user.php?id=36&page='
USER_AGENT_STRING = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
DOWNLOAD_DIR = 'worldwidetorrents/'
SLEEP_BETWEEN_TORRENT_DOWNLOADS = 0.8
NUM_ALREADY_DOWNLOADED_BEFORE_STOP = 10


# SCRIPT-ONLY GLOBAL VARIABLES
CACHE = [] # This cache ensures already downloaded files are not re-downloaded
NUM_ALREADY_DOWNLOADED = 0 # A counter for the torrents that have already been downloaded

def main():
    # Ensure the download directory exists
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Fill the cache
    populate_cache()

    page_num = 0
    url = USERS_TORRENTS_URL + str(page_num)
    run = True
    while run:
        # Scrape the user's torrent page and download the torrent files
        print 'Getting torrent page... [URL=' + url + ']'
        response = get_url(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        run = scrape_page(soup)

        # Determine the next URL to scrape
        page_num = page_num + 1
        url = USERS_TORRENTS_URL + str(page_num)


def populate_cache():
    global CACHE

    all_files = os.listdir(DOWNLOAD_DIR)
    CACHE = [f for f in all_files if f.lower().endswith('.torrent')]
    print 'The cache has been populated, size = ' + str(len(CACHE))

def scrape_page(soup):
    rows = soup.find_all('td', 'ttable_col2')
    if rows is None or len(rows) == 0:
        return False

    if rows is not None:
        urls = [row.a.get('href') for row in rows if row is not None and row.a is not None]
        dl_urls = ['http://worldwidetorrents.eu/' + url for url in urls if url.lower().startswith('download.php')]

        for dl_url in dl_urls:
            did_download = download_file(dl_url)

            # Determine if we have downloaded the remaining torrents and abort if yes
            if not did_download and NUM_ALREADY_DOWNLOADED >= NUM_ALREADY_DOWNLOADED_BEFORE_STOP:
                return False

            time.sleep(SLEEP_BETWEEN_TORRENT_DOWNLOADS) # Avoid hammer time

    return True

def get_url(url, max_attempts = 3):
    attempt = 0
    while attempt < max_attempts:
        try:
            return requests.get(url, headers=USER_AGENT_STRING)
        except requests.ConnectionError as e:
            print 'FAILED to get the URL ' + url
            print e
            print 'Going to sleep for a lil...'
            time.sleep(4)

        attempt = attempt + 1


def download_file(url):
    print 'Downloading torrent file... [URL=' + url + ']'
    response = get_url(url)
    cd = response.headers['Content-Disposition']
    filename = parse_filename(cd)
    filename = filename.replace('[https://worldwidetorrents.eu]', '').replace('[http://worldwidetorrents.eu]', '')

    global NUM_ALREADY_DOWNLOADED
    if filename in CACHE:
        print 'SKIPPING: Already downloaded ' + filename
        NUM_ALREADY_DOWNLOADED = NUM_ALREADY_DOWNLOADED + 1
        return False

    with open(DOWNLOAD_DIR + filename, 'wb') as f:
        f.write(response.content)
        f.close()

    return True


def parse_filename(content_disposition):
    if content_disposition is None:
        return None
    else:
        return content_disposition.split('"')[1]




if __name__ == '__main__':
    main()