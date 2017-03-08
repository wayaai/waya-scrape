import os
import pickle
import uuid

import selenium

from wayascrape import download_urls
from wayascrape import scrape_serp


#
# directories
#

path = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(path, 'data-scraped')


def scrape_urls(keyword_file_path, search_engine='google'):
    """
    Scrape a search engine page-by-page via keyword searches.

    :param keyword_file_path: A text file with the keywords for each search stored line-by-line (no commas).
    :param search_engine: The search engine to scrape (i.e. Google, Baidu, Yandex, Bing, etc ...).
    """
    # if `dataset_dir` does not exist we will create it and start the scrape from scratch
    # otherwise we will continue the scrape from where we left off
    if not os.path.isdir(dataset_dir):
        os.makedirs(dataset_dir)

    # a pickled dictionary `image_details` mapping each scraped data-points name to it's relevant meta-data
    # is stored in this file
    image_details_file_path = os.path.join(dataset_dir, 'image_details.pickle')
    image_details = {}

    # keep track of urls we've already scraped so we don't scrape duplicates
    existing_urls = []

    # continue the scrape from where we left off
    if os.path.isfile(image_details_file_path):
        with open(image_details_file_path, 'rb') as handle:
            image_details = pickle.load(handle)

        for _, value in image_details.items():
            url = value.get('image_url')

            if url:
                existing_urls.append(url)

    # use chrome as the default browser for our scrape, but another browser (i.e. firefox) can be used as well
    driver = selenium.webdriver.Chrome('/Users/mjdietzx/Downloads/chromedriver')

    advanced_search_options = {
        'keywords': '',  # keywords we are searching for
        'as_eq': 'pathology histology histopathology prognosis chart diagram graph plot figure',  # omit these results
    }

    with open(keyword_file_path, 'r') as f:
        # `keyword_file_path` must be a text file with each search term (keywords) separated line-by-line
        keywords = f.readlines()

    for keyword in keywords:
        advanced_search_options['keywords'] = keyword

        try:
            # get the resource url of each image found in search
            urls = scrape_serp.search_by_keywords(driver, advanced_search_options, search_engine=search_engine)
        except Exception as e:
            print('scrape_serp.search_by_keywords() failed for keyword: {}, with Exception: {}.'.format(keyword, e))
            continue

        # if we've already found this url discard it
        existing_url_collisions = 0
        for url in urls:
            if url not in existing_urls:
                existing_urls.append(url)
                img_uuid = '{}'.format(uuid.uuid4())
                image_details[img_uuid] = {'search_engine': search_engine, 'keywords': keyword, 'image_url': url}
            else:
                existing_url_collisions += 1

        print('Successfully scraped \'{}\' with {} total urls and {} collisions occurring with existing urls.'.
              format(keyword, len(urls), existing_url_collisions))

    # write the meta-data to disc
    with open(image_details_file_path, 'wb') as handle:
        pickle.dump(image_details, handle, protocol=pickle.HIGHEST_PROTOCOL)

    driver.quit()


def download_images():
    image_details_file_path = os.path.join(dataset_dir, 'image_details.pickle')
    with open(image_details_file_path, 'rb') as handle:
        image_details = pickle.load(handle)

    download_urls.download_and_phash_urls(image_details, dataset_dir)


if __name__ == '__main__':
    # scrape the unique urls of all images found when searching with keywords, store meta data in image_details.pickle
    scrape_urls('keywords.txt', search_engine='google')
    # download all the images from their urls and save them to dataset_dir
    download_images()
