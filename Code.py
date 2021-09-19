# Imports:

from requests import get as get_request
from bs4 import BeautifulSoup
from bs4.element import Tag
from os import mkdir, chdir, rmdir
from datetime import datetime
from tqdm import tqdm


# Attributes:

TITLE = 'BULK DOWNLOADER (USING WEB SCRAPING)'
N = len(TITLE)
HTTPS, HTTP = 'https://', 'http://'
GS_BASE = 'https://www.google.com'  # google search base URL
GSQ = GS_BASE + '/search?q='  # google search query URL
NA = 'n/a'
DL_DIR = 'Downloads'  # download dir


# Functions:

def sep_print(*msgs):
    """Print Decorator."""
    if msgs:
        print(*msgs)
    print('-' * N)


# Main:

sep_print(f'\n{TITLE}')
sep_print('NOTE- Use a fast Wi-Fi connection for best experience.')

try:
    chdir(DL_DIR)
except FileNotFoundError:
    mkdir(DL_DIR)
    chdir(DL_DIR)

while True:

    # Input:

    url = input('\nEnter URL: ').strip()  # https://unsplash.com/t/
    if not url:  # nothing entered
        exit('Exiting...')

    if '.' not in url:  # then not a URL (hostname must have '.') so perform a google search
        url = GSQ + url
    elif not (url.startswith(HTTPS) or url.startswith(HTTP)):
        url = HTTPS + url

    print(f'\nLinks from "{url}" are being extracted... \n')  # loading message

    # Parsing:

    try:
        html = get_request(url=url).text  # try to open URL and read data from it
    except Exception as e:  # any exception from requests.exceptions
        sep_print('ERROR OCCURRED:', e)
        continue  # asking URL again

    anchor_tags = BeautifulSoup(markup=html, features='html.parser')('a')  # parse all the anchor tags
    data = {}  # link: content pair
    for anchor_tag in anchor_tags:
        link, content = anchor_tag.get('href'), anchor_tag.contents[0] if anchor_tag.contents else ''
        if link:  # checking if link got is not of NoneType
            if isinstance(content, Tag):  # content is some HTML itself instead of text
                content = content.text
            data[link.strip()] = content.strip()

    print('Total Links Found:', len(data))
    # sep_print(data); continue  # debugging

    if not data:  # no links found
        sep_print()
        continue

    if input('\nStart trying download (y/n): ').casefold() == 'n':  # confirming
        sep_print('\n"Moved on."')
        continue
    print()  # spacing

    # Output:

    dir_name = ''
    for char in url[url.index('//')+2:]:
        dir_name += char if char not in ('\\', '/', ':', '*', '?', '"', '<', '>', '|') else ' '  # a file name can't contain any of those characters
    dir_name += f" ({str(datetime.now().time()).replace(':', ';')}) "  # appending current time to make dir_name distinct
    mkdir(dir_name)
    chdir(dir_name)
    # print(dir_name); exit()  # debugging

    count = 0

    for i, (link, content) in enumerate(iterable=data.items(), start=1):  # iterating over fetched links

        http_i = max(link.find(HTTPS), link.find(HTTP))
        if http_i != -1 and http_i != 0:
            link = link[http_i:]  # not considering useless stuff before 'https://' (or 'http://')

        elif link.startswith('/'):  # relative link
            if url.startswith(GSQ):  # exception for google search
                link = GS_BASE + link
            else:
                link = url + link

        if not content:
            content = NA

        print(f'{i}) Link:', link)
        print('Content Name:', content)

        try:
            response = get_request(url=link, stream=True)
            # print(response.headers, '\n'); continue  # debugging
        except Exception as e:
            print('ERROR OCCURRED:', e, '\n')
            continue  # skipping this link for any other further processing

        content_type = response.headers.get('Content-Type', NA)
        size = response.headers.get('Content-Length', NA)  # in B
        print('Content Type:', content_type)
        print('Size (bytes):', size)

        filename = response.headers.get('Content-Disposition')

        if filename:  # downloading only if filename is not None
            filename = filename[filename.find('filename=')+9:].split(sep='"', maxsplit=2)[1]  # extracting filename
            # print(filename); continue  # debugging

            # with open(filename, 'wb') as fd:  # without progressbar
            with tqdm.wrapattr(open(filename, 'wb'), 'write', miniters=1, desc=f'"{filename}"', total=int(size) if size != NA else 0) as fd:  # with progressbar
                for chunk in response.iter_content(chunk_size=1024):  # iterating over 1 KB at a time
                    fd.write(chunk)

            print('Download: Completed \n')
            count += 1

        else:
            print('Download: Skipped \n')

    sep_print('Links Downloaded:', count)

    chdir('..')  # back to home path

    if not count:  # deleting made dir if nothing's downloaded
        rmdir(dir_name)
