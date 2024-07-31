import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager  # chrome
# from webdriver_manager.firefox import GeckoDriverManager # firfox
# from webdriver_manager.microsoft import EdgeChromiumDriverManager # edge
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


def download_image(data, data_folder, log_data, chapter_num, chapter_page):
    i, url = data
    response = requests.get(url)
    ext = url.split('.')[-1] if '.' in url else 'jpg'
    if response.status_code == 200:
        filename = f"c{str(chapter_num).zfill(4)}_p{str(
            chapter_page).zfill(3)}_image_{str(i+1).zfill(3)}.{ext}"
        log_data['items'][-1]['pages'][-1]['images'].append(
            {'image': filename, 'url': url})

        filepath = os.path.join(data_folder, filename)
        with open(filepath, 'wb') as file:
            file.write(response.content)


def scrape(driver, url, chapter_num=1):
    driver.get(url)
    data_folder = 'data/'
    log_data = {'items': []}
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    title = driver.find_elements(By.CSS_SELECTOR, "div.head_title > h2")
    if len(title) > 0:
        title = title[0].text
    else:
        title = ''

    chapter_page = 1
    log_data['items'].append(
        {'chapter': title, 'chapter_num': chapter_num, 'pages': []})
    while True:
        # Find all image elements
        image_elements = driver.find_elements(By.CSS_SELECTOR, '#images>img')
        new_title = driver.find_elements(
            By.CSS_SELECTOR, "div.head_title > h2")
        if new_title and len(new_title) > 0:
            new_title = new_title[0].text

        if title != new_title:
            chapter_num += 1
            chapter_page = 1
            title = new_title

        # Extract the src of each image
        image_urls = extract_img_urls(image_elements)

        # get file name, for this website it will load a lazyload.gif first, then load the actual image
        # simulate the browser to scroll to bottom to load the real images
        scroll_to_bottom(driver)

        log_data['items'][-1]['pages'].append(
            {'image_done': '', 'page_url': url, 'images': []})

        succeeded = 0
        # Download the images concurrently
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(
                download_image, (i, url), data_folder, log_data, chapter_num, chapter_page) for i, url in enumerate(image_urls)]

            # Wait for all futures to complete (optional, if you want to track progress)
            for future in as_completed(futures):
                # You can check if the future completed successfully, or catch exceptions
                try:
                    future.result()  # This will raise any exceptions that occurred during execution
                    succeeded += 1
                except Exception as e:
                    print(f"An error occurred: {e}")
        log_data['items'][-1]['pages'][-1]['image_done'] = f'{succeeded}/{len(image_urls)}'

        btn_to_next_page_css = "a.img_land_next"
        try:
            # Find button to get to next chapter
            btn_to_next_page = driver.find_element(
                By.CSS_SELECTOR, btn_to_next_page_css)
            actions = ActionChains(driver)
            actions.move_to_element(btn_to_next_page)  # hover this element
            # click next chapter to go to next chapter
            actions.click(btn_to_next_page)

            try:
                actions.perform()  # perform these actions
                # Wait to see if an alert appears
                # WebDriverWait(driver, 10).until(lambda driver: driver.execute_script(
                #     'return document.readyState') == 'complete')
                time.sleep(1)

                alert = Alert(driver)
                alert_text = alert.text
                if "已经是最后一章了" in alert_text:
                    print(alert_text)
                    alert.accept()  # Accept the alert to close it
                    break
            except:
                # No alert found, continue to the next page
                print(f'{chapter_page}) next: {url}')

            url = driver.current_url
            chapter_page += 1

        except Exception as e:
            print(f"An error occurred: {e}")
            break

    return log_data


if __name__ == '__main__':
    options = Options()
    options.add_argument("--headless")  # Ensure GUI is off
    options.add_argument("--no-sandbox")  # Bypass OS security model

    # Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Firefox
    # service = Service(GeckoDriverManager().install())
    # driver = webdriver.Firefox(service=service, options=options)

    # Edge
    # service = Service(EdgeChromiumDriverManager().install())
    # driver = webdriver.Edge(service=service, options=options)

    start_url = 'http://www.92mh.com/manhua/199/76091.html'
    print(f'0) start: {start_url}')

    # Navigate to the start URL
    data = scrape(driver, start_url, chapter_num=1)

    for item in data['items']:
        if 'images' in item:
            item['images'].sort(key=lambda x: x['image'])
    # print(data)
    with open(datetime.now().strftime("data-%Y-%m-%d-%H-%M-%S.yaml"), 'w', encoding='utf-8') as data_file:
        yaml.dump(data, data_file, allow_unicode=True)
