# Imports:
from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4.element import Tag


# Attributes:
title = 'LINK EXTRACTOR'


# Functions:
def sep_print(*msgs):
    """Print Decorator."""
    print(*msgs)
    print('--' * len(title))


# Main:
sep_print(f'\n{title}')

while True:

    # Input:

    url = input('\nEnter URL: ').strip()
    if not url:  # nothing entered
        exit('Exiting...')
    if not url.startswith('https://'):
        url = 'https://' + url

    print(f'\nLinks from {url} are being extracted... \n')  # loading message

    # Parsing:

    try:
        anchor_tags = BeautifulSoup(urlopen(url), 'html.parser')('a')  # try to open url and parse all the anchor tags
    except Exception as e:  # perhaps because of invalid URL
        sep_print('ERROR OCCURRED:', e)
        continue  # asking URL again

    data = {}  # link: content_type pair
    for anchor_tag in anchor_tags:
        link, content = anchor_tag.get('href'), anchor_tag.contents[0]
        if link:  # checking if link got is not of NoneType
            if isinstance(content, Tag):  # content is some HTML itself instead of text
                content = content.text
            data[link.strip()] = content.strip()

    # sep_print(data, len(data)); continue  # debugging

    # Output:

    count = 0
    for link, content in data.items():
        if link.startswith('/'):  # relative link
            link = url + link
        if not content:
            content = 'n/a'
        print('Link:', link, '\nContent Type:', content, '\n')
        count += 1

    sep_print(count, 'links found!')
