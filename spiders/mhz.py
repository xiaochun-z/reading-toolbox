import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager # chrome
#from webdriver_manager.firefox import GeckoDriverManager # firfox
#from webdriver_manager.microsoft import EdgeChromiumDriverManager # edge
import requests
# from urllib.parse import urljoin
from selenium.webdriver.chrome.options import Options
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from datetime import datetime
import yaml


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(0.8, 1.2))  # Wait for the page to load


def extract_img_urls(image_elements):
    image_urls = []
    for image in image_elements:
        src = image.get_attribute('src')
        if src:
            image_urls.append(src)
    return image_urls


def download_image(data, data_folder, log_data, chapter_num):
    i, url = data
    response = requests.get(url)
    ext = url.split('.')[-1] if '.' in url else 'jpg'
    if response.status_code == 200:
        filename = f"{str(chapter_num).zfill(4)}_image_{
            str(i+1).zfill(3)}.{ext}"
        log_data['items'][-1].setdefault('images',
                                         []).append({'image': filename, 'url': url})

        filepath = os.path.join(data_folder, filename)
        with open(filepath, 'wb') as file:
            file.write(response.content)


def scrape(driver, url, chapter_num=1):
    driver.get(url)
    data_folder = 'data/'
    log_data = {'items': []}
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    while True:
        # Find all image elements
        image_elements = driver.find_elements(By.CSS_SELECTOR, 'img.lazy')

        '''
        some other examples to find elements
        elements_by_id = driver.find_elements(By.ID, 'element_id')
        elements_by_class = driver.find_elements(By.CLASS_NAME, 'element_class')
        elements_by_css = driver.find_elements(By.CSS_SELECTOR, 'div.class > p')
        elements_by_tag = driver.find_elements(By.TAG_NAME, 'div')
        elements_by_name = driver.find_elements(By.NAME, 'element_name')
        elements_by_link_text = driver.find_elements(By.LINK_TEXT, 'Click Here')
        elements_by_partial_link_text = driver.find_elements(By.PARTIAL_LINK_TEXT, 'Click')
        elements_by_xpath = driver.find_elements(By.XPATH, '//div[@class="container"]')
        '''
        title = driver.find_elements(By.CSS_SELECTOR, "div.title")
        if len(title) > 0:
            title = title[0].text
        else:
            title = ''
        log_data['items'].append(
            {'chapter': title, 'chapter_num': chapter_num, 'chapter_url': url, 'chapter_done': ''})
        # Extract the src of each image
        image_urls = extract_img_urls(image_elements)

        # get file name, for this website it will load a lazyload.gif first, then load the actual image
        # simulate the browser to scroll to bottom to load the real images
        max_check_time = 30
        check_time = 0
        all_done = True
        while any('lazyload.gif' in url for url in image_urls):
            scroll_to_bottom(driver)
            image_urls = extract_img_urls(image_elements)
            check_time += 1
            if check_time > max_check_time:
                all_done = False
                print(
                    f"Failed to load all images for {title}: `{url}`. Please check the website and try again.")
                break

        succeeded = 0
        # Download the images concurrently
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(
                download_image, (i, url), data_folder, log_data, chapter_num) for i, url in enumerate(image_urls)]

            # Wait for all futures to complete (optional, if you want to track progress)
            for future in as_completed(futures):
                # You can check if the future completed successfully, or catch exceptions
                try:
                    future.result()  # This will raise any exceptions that occurred during execution
                    succeeded += 1
                except Exception as e:
                    print(f"An error occurred: {e}")
        all_done_text = 'yes' if all_done else 'no'
        log_data[
            'items'][-1]['chapter_done'] = f'{all_done_text},{succeeded}/{len(image_urls)}'
        btn_to_next_chapter_css = "div.chapterBtn>ul li.last>a"
        btn_to_next_chapter = driver.find_element(
            # find button to get to next chapter.
            By.CSS_SELECTOR, btn_to_next_chapter_css)
        if not btn_to_next_chapter or not btn_to_next_chapter.get_attribute('href') or btn_to_next_chapter.get_attribute('href') in ('', '#'):
            driver.quit()
            break
        url = btn_to_next_chapter.get_attribute('href')
        actions = ActionChains(driver)
        actions.move_to_element(btn_to_next_chapter)  # hover this element
        # click next chapter to go to next chapter
        actions.click(btn_to_next_chapter)
        actions.perform()  # performa these actions
        print(f'{chapter_num}) next: {url}')
        chapter_num += 1
    return log_data


if __name__ == '__main__':
    options = Options()
    options.add_argument("--headless")  # Ensure GUI is off
    options.add_argument("--no-sandbox")  # Bypass OS security model
    
    # Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Firefox
    #ervice = Service(GeckoDriverManager().install())
    #driver = webdriver.Firefox(service=service, options=options)
    
    # Edge
    #service = Service(EdgeChromiumDriverManager().install())
    #driver = webdriver.Edge(service=service, options=options)
    
    start_url = 'https://www.manhuazhan.com/chapter/255320-51671.html'
    print(f'0) start: {start_url}')

    # Navigate to the start URL
    data = scrape(
        driver, start_url, chapter_num=1)

    for item in data['items']:
        if 'images' in item:
            item['images'].sort(key=lambda x: x['image'])
    # print(data)
    with open(datetime.now().strftime("data-%Y-%m-%d-%H-%M-%S.yaml"), 'w', encoding='utf-8') as data_file:
        yaml.dump(data, data_file, allow_unicode=True)
