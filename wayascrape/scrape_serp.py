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


def get_url(url, search_engine='google'):
    if search_engine is 'google':
        if not url or not url.startswith('/imgres?imgurl='):
            return
        return urllib.parse.unquote(url.split('/imgres?imgurl=')[1].split('&imgrefurl=')[0])
    if search_engine is 'yandex':
        if not url or not url.startswith('/images/search?'):
            return
        return urllib.parse.unquote(url.split('img_url=')[1].split('&')[0])
    if search_engine is 'baidu':
        if not url or not url.startswith('https://image.baidu.com/search/'):
            if not url.startswith('/search/detail'):
                return
        return urllib.parse.unquote(url.split('objurl=')[1].split('&')[0])
    if search_engine is 'bing':
        url = ast.literal_eval(url).get('murl')
        if url:
            return url


def results_extract_urls(driver, search_engine='google'):
    time.sleep(10)
    for _ in range(5):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2.5)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    urls = []

    get = 'href'
    if search_engine is 'google':
        it = soup.find_all('a')
    elif search_engine is 'yandex':
        it = soup.find_all('a', class_='serp-item__link')
    elif search_engine is 'baidu':
        it = soup.find_all('div', class_='imgbox')
        it = list(map(lambda x: x.a, it))
    elif search_engine is 'bing':
        it = soup.find_all('a', class_='iusc')
        get = 'm'
    else:
        assert False

    for link in it:
        url = link.get(get)
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
    keywords = advanced_search_options.get('keywords').replace(' ', '+')

    if search_engine is 'google':
        # results must NOT include any words in this string
        as_eq = advanced_search_options.get('as_eq', '').replace(' ', '+')
        keywords = '{}&as_eq={}'.format(keywords, as_eq)
    elif search_engine is 'yandex':
        keywords = advanced_search_options.get('keywords')
        n = advanced_search_options.get('as_eq').replace(' ', ' -')  # still need spaces
        keywords = urllib.parse.quote_plus('{} -{}'.format(keywords, n))  # need ~~ on the first excluded keyword
    elif search_engine is 'baidu':
        q4 = advanced_search_options.get('as_eq', '').replace(' ', '+')
        keywords = '{}&q4={}'.format(keywords, q4)
    elif search_engine is 'bing':
        n = advanced_search_options.get('as_eq', '').replace(' ', '+-')
        keywords = '{}+-{}'.format(keywords, n)

    search_url = '{}={}'.format(IMAGE_SEARCH_BASE_URLS.get(search_engine), keywords)
    driver.get(search_url)
    return results_extract_urls(driver, search_engine=search_engine)
