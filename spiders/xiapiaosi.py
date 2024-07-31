import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import os
from datetime import datetime
import yaml


def scrape(out_file_name, driver, url, chapter_num=1):
    driver.get(url)
    data_folder = 'data/'
    log_data = {'items': []}
    os.makedirs(data_folder, exist_ok=True)
    filepath = os.path.join(data_folder, f'out-{out_file_name}')

    with open(filepath, 'w', encoding='utf-8') as file:
        while True:
            print(f'{chapter_num}) {url}')
            title_elements = driver.find_elements(
                By.CSS_SELECTOR, 'div.text-head>h1')

            if len(title_elements) > 0:
                chapter_title = title_elements[0].text
            else:
                chapter_title = str(chapter_num)

            content_elements = driver.find_elements(
                By.CSS_SELECTOR, 'div#content-text pre p')
            text_array = [element.text.strip() for element in content_elements]
            log_data['items'].append({'chapter': chapter_title, 'chapter_num': chapter_num,
                                     'chapter_url': url, 'paragraph_count': len(text_array)})
            file.write(os.linesep + "# " + chapter_title + os.linesep)
            for text in text_array:
                file.write(text + os.linesep)

            btn_to_next_chapter_css = "div.turn-page a"
            btn_to_next_chapter = driver.find_elements(
                By.CSS_SELECTOR, btn_to_next_chapter_css)
            has_next_chapter = False
            for c in btn_to_next_chapter:
                # '下一章' means 'next chapter' in Chinese, this text comes from the target website, indicating the next chapter.
                if c.text.strip() == '下一章':
                    btn_to_next_chapter = c
                    has_next_chapter = True
                    break

            if not has_next_chapter:
                break
            url = btn_to_next_chapter.get_attribute('href')
            actions = ActionChains(driver)
            actions.move_to_element(btn_to_next_chapter)
            actions.click(btn_to_next_chapter)

            actions.perform()

            chapter_num += 1
    return log_data


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    start_url = 'https://www.xiaopiaosi.com/book/1086425/1/'

    print(f'0) start: {start_url}')
    name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    data = scrape(f'{name}.md',
                  driver, start_url, chapter_num=1)
    for item in data['items']:
        if 'images' in item:
            item['images'].sort(key=lambda x: x['image'])

    with open(datetime.now().strftime(f"data-{name}.yaml"), 'w', encoding='utf-8') as data_file:
        yaml.dump(data, data_file, allow_unicode=True)
