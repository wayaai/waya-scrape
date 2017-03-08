import time
import urllib

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


IMAGE_SEARCH_BASE_URLS = {
    'google': 'https://images.google.com',
    'bing': 'https://www.bing.com/images',
    'baidu': 'http://image.baidu.com',
}

SEARCH_BY_IMAGE = {
    'google': (By.ID, 'qbi'),
    'bing': (By.ID, 'sbi_t'),
    # //*[@id="sttb"]/img[1]
    'baidu': '//*[@id="sttb"]',
}

UPLOAD_AN_IMAGE = {
    'google': (By.LINK_TEXT, 'Upload an image'),
    'bing': (By.LINK_TEXT, 'upload an image'),
    # //*[@id="stfile"]
    'baidu': '//*[@id="uploadImg"]',
}

CHOOSE_FILE = {
    'google': (By.ID, 'qbfile'),
    'bing': (By.CSS_SELECTOR, 'input[type="file"]'),
    'baidu': (By.CSS_SELECTOR, 'input[type="file"]'),
}

SHOW_IMAGE_RESULTS = {
    'google': (By.LINK_TEXT, 'Visually similar images'),
    'bing': (By.ID, 'mmComponent_images_4_1_1_exp'),
    'baidu': (By.XPATH, '//*[@id="imglist"]/div/div/a[@class="imglist-more"]'),
}

SHOW_MORE_RESULTS_XPATH = {
    'google': '//*[@id="smb"]',
    # //*[@id="mmComponent_images_4_1_1_exp"]/a
    'bing': '//*[@id="mmComponent_images_4_1_1_exp"]/a',
    # //*[@id="imglist"]/div/div[1]/a
    'baidu': '//*[@id="imglist"]/div/div/a[@class="imglist-more"]',
}


def get_url(url, search_engine='google'):
    if search_engine is 'google':
        if not url or not url.startswith('/imgres?imgurl='):
            return
        return urllib.parse.unquote(url.split('/imgres?imgurl=')[1].split('&imgrefurl=')[0])


def results_extract_urls(driver, search_engine='google'):
    time.sleep(10)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    urls = []
    for link in soup.find_all('a'):
        url = link.get('href')
        url = get_url(url, search_engine=search_engine)
        if url:
            urls.append(url)

    return urls


def search_by_image(driver, image_path, search_engine='google'):
    driver.get(IMAGE_SEARCH_BASE_URLS.get(search_engine))

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(SEARCH_BY_IMAGE.get(search_engine))).click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(UPLOAD_AN_IMAGE.get(search_engine))).click()

    choose_file_elem = \
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(CHOOSE_FILE.get(search_engine)))

    choose_file_elem.clear()
    choose_file_elem.send_keys(image_path)

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(SHOW_IMAGE_RESULTS.get(search_engine))).click()

    return results_extract_urls(driver, search_engine=search_engine)


def search_by_keywords(driver, advanced_search_options, search_engine='google'):
    keywords = advanced_search_options.get('keywords', '').replace(' ', '+')
    # results must include the query, in the word order displayed
    as_epq = advanced_search_options.get('as_epq', '').replace(' ', '+')
    # results must include one or more of the words in this string
    as_oq = advanced_search_options.get('as_oq', '').replace(' ', '+')
    # results must NOT include any words in this string
    as_eq = advanced_search_options.get('as_eq', '').replace(' ', '+')
    # controls the number of results shown. Must be a numeric value, and can be anything up to 100
    num = advanced_search_options.get('num', 100)

    search_url = 'http://www.google.com/search?q={}&as_epq={}&as_oq={}&as_eq={}&num={}&tbm=isch'.\
        format(keywords, as_epq, as_oq, as_eq, num)

    driver.get(search_url)
    return results_extract_urls(driver, search_engine=search_engine)
