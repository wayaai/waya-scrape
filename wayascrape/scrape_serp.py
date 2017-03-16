import ast
import time
import urllib

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


IMAGE_SEARCH_BASE_URLS = {
    'google': 'https://google.com/search?tbm=isch&q',
    'bing': 'https://www.bing.com/images/search?q',
    'baidu': 'http://image.baidu.com/search/index?tn=baiduimage&word',
    'yandex': 'https://yandex.com/images/search?text',
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


def get_url(url, search_engine):
    if search_engine is 'google':
        starts_with = '/imgres?imgurl='
        img_tag = '/imgres?imgurl='
    if search_engine is 'yandex':
        starts_with = '/images/search?'
        img_tag = 'img_url='
    if search_engine is 'baidu':
        starts_with = 'https://image.baidu.com/search/'
        img_tag = 'objurl='
    if search_engine is 'bing':
        url = ast.literal_eval(url).get('murl')
        return url

    if not url or not url.startswith(starts_with):
        if search_engine is not 'baidu' or not url.startswith('/search/detail'):
            return

    return urllib.parse.unquote(url.split(img_tag)[1].split('&')[0])


def results_extract_urls(driver, search_engine):
    time.sleep(6)
    # scroll to the bottom of page, TODO: click the 'more results' button if we get to it
    for _ in range(5):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    urls = []
    url_field = 'href'

    if search_engine is 'google':
        result_containers = soup.find_all('a')
    elif search_engine is 'yandex':
        result_containers = soup.find_all('a', class_='serp-item__link')
    elif search_engine is 'baidu':
        result_containers = soup.find_all('div', class_='imgbox')
        result_containers = list(map(lambda x: x.a, result_containers))
    elif search_engine is 'bing':
        result_containers = soup.find_all('a', class_='iusc')
        url_field = 'm'

    for link in result_containers:
        url = link.get(url_field)
        url = get_url(url, search_engine)
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

    return results_extract_urls(driver, search_engine)


def search_by_keywords(driver, advanced_search_options, search_engine='google'):
    keywords = advanced_search_options.get('keywords').replace(' ', '+')
    # results must not include any words in this string
    as_eq = advanced_search_options.get('as_eq', '').replace(' ', '+')

    if search_engine is 'google':
        if as_eq:
            keywords = '{}&as_eq={}'.format(keywords, as_eq)
    elif search_engine is 'yandex':
        if as_eq:
            as_eq = as_eq.replace('+', ' -')  # need spaces between words
            # undo replacing ' ' with '+' and need '-' between the last keyword and first excluded word
            keywords = urllib.parse.quote_plus('{} -{}'.format(keywords.replace('+', ' '), as_eq))
    elif search_engine is 'baidu':
        if as_eq:
            keywords = '{}&q4={}'.format(keywords, as_eq)
    elif search_engine is 'bing':
        if as_eq:
            as_eq = as_eq.replace('+', '+-')
            keywords = '{}+-{}'.format(keywords, as_eq)  # need '+-' on the first excluded word
    else:
        assert False, 'Unsupported search engine.'

    search_url = '{}={}'.format(IMAGE_SEARCH_BASE_URLS.get(search_engine), keywords)
    driver.get(search_url)
    return results_extract_urls(driver, search_engine)
