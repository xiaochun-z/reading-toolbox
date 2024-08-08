import yaml
import re


def split_into_paragraphs(text_file):
    """
    Reads a text file and splits it into paragraphs.

    Args:
      text_file: The path to the .txt file.

    Returns:
      A list of paragraphs.
    """

    with open(text_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # Split the text into paragraphs based on double newlines
    paragraphs = text.split('\n\n')

    return paragraphs


book_file = 'Divergent.txt'

paragraphs = split_into_paragraphs(book_file)
data = {'chapter': []}

# for different novel, the regular expression might be different
chapter_pattern = r"^(CHAPTER\s+)(.+\s*)"
chapter_index = 0

if len(paragraphs) > 0:
    data['chapter'].append({'paragraphs': [],'chapter_index': str(chapter_index).zfill(5)})

longest_paragraph = max(paragraphs, key=len)
# if paragraph is too long, it might fail when doing text to speech.
print(f'debug info: longest paragraph: \n{longest_paragraph}')

# find paragraphs which are longer than 2kb
long_paragrahs = [
    paragraph for paragraph in paragraphs if len(paragraph) > 2048]
if len(long_paragrahs) > 0:
    print(f'there are {len(longest_paragraph)} which are longer than 2kb, keep in mind long paragraph conversion might lead to failure when doing text to speech.')
    for p in long_paragrahs:
        print(p)

for i, paragraph in enumerate(paragraphs):
    p = paragraph.strip()
    if len(p) == 0:
        continue
    m = re.match(chapter_pattern, p)
    if m:
        chapter_index += 1
        data['chapter'].append(
            {'paragraphs': [], 'chapter_title': m.group(2), 'chapter_index': str(chapter_index).zfill(5)})
        print(f"Chapter {chapter_index}: {m.group(2)}")

    data['chapter'][-1]['paragraphs'].append({'index': str(i).zfill(7), 'text': p})

# save to file
# import json
# with open('data.json', 'w') as f:
#     json.dump(data, f)
with open('data.yml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True)
