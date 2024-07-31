import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.action_chains import ActionChains
import requests
import os
from datetime import datetime
import yaml
import re
import shutil


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)  # Wait for the page to loa


def extract_img_urls(image_elements):
    image_urls = [image.get_attribute('src') for image in image_elements]
    image_urls = [url for url in image_urls if url]
    return image_urls


def download_image(data, data_folder, log_data, chapter_num):
    i, url = data
    response = requests.get(url, stream=True)
    ext = url.split('.')[-1] if '.' in url else 'jpg'
    if response.status_code == 200:
        filename = f"{str(chapter_num).zfill(4)}_image_{str(i+1).zfill(3)}.{ext}"
        log_data['items'][-1].setdefault('images',
                                         []).append({'image': filename, 'url': url})

        filepath = os.path.join(data_folder, filename)
        with open(filepath, 'wb') as file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, file)


def scrape(driver, url, chapter_num=1):
    driver.get(url)
    data_folder = 'data/'
    log_data = {'items': []}
    os.makedirs(data_folder, exist_ok=True)

    while True:
        image_elements = driver.find_elements(By.CSS_SELECTOR, '#images>img')
        total_images_of_chapter = driver.find_elements(
            By.CSS_SELECTOR, "#images p.img_info:last-child")
        if len(total_images_of_chapter) == 1:
            total_images_of_chapter = total_images_of_chapter[0].text
            match = re.search(r'\((\d+)/(\d+)\)', total_images_of_chapter)
            if match:
                total_images_of_chapter = int(match.group(2))
            else:
                total_images_of_chapter = len(image_elements)

        title = driver.find_elements(By.CSS_SELECTOR, ".head_title>h2")
        if len(title) > 0:
            title = title[0].text
        else:
            title = ''
        log_data['items'].append(
            {'chapter': title, 'chapter_num': chapter_num, 'chapter_url': url, 'chapter_done': ''})
        max_check_time = 100
        check_time = 0
        all_done = True
        while len(image_elements) < total_images_of_chapter:
            scroll_to_bottom(driver)
            image_elements = driver.find_elements(
                By.CSS_SELECTOR, '#images>img')
            check_time += 1
            if check_time > max_check_time:
                all_done = False
                print(
                    f"Failed to load all images for {title}: `{url}`. Please check the website and try again.")
                break
        image_urls = extract_img_urls(image_elements)
        succeeded = 0
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(
                download_image, (i, url), data_folder, log_data, chapter_num) for i, url in enumerate(image_urls)]

            for future in as_completed(futures):
                try:
                    future.result()
                    succeeded += 1
                except Exception as e:
                    print(f"An error occurred: {e}")

        all_done_text = 'yes' if all_done else 'no'
        log_data[
            'items'][-1]['chapter_done'] = f'{all_done_text},{succeeded}/{len(image_urls)}'
        btn_to_next_chapter_css = "a.btm_chapter_btn.fr"
        btn_to_next_chapter = driver.find_element(
            By.CSS_SELECTOR, btn_to_next_chapter_css)
        actions = ActionChains(driver)
        actions.move_to_element(btn_to_next_chapter)
        actions.click(btn_to_next_chapter)
        try:
            actions.perform()
            time.sleep(1)
            alert = driver.switch_to.alert
            alert_text = alert.text
            if "已经是最后一章了" in alert_text:
                print(alert_text)
                alert.accept()
                break
        except:
            url = driver.current_url
            print(f'{chapter_num}) next: {url}')

        chapter_num += 1
    return log_data


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    start_url = 'http://www.92mh.com/manhua/199/81591.html'

    driver.get(start_url)
    driver.execute_script(
        "window.localStorage.setItem('chapterScroll', '\"scroll\"');")
    driver.refresh()
    print(f'0) start: {start_url}')
    
    data = scrape(
        driver, start_url, chapter_num=1)
    for item in data['items']:
        if 'images' in item:
            item['images'].sort(key=lambda x: x['image'])

    with open(datetime.now().strftime("data-%Y-%m-%d-%H-%M-%S.yaml"), 'w', encoding='utf-8') as data_file:
        yaml.dump(data, data_file, allow_unicode=True)
