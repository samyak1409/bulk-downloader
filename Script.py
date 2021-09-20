# IMPORTS:

from requests import get as get_request
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from bs4.element import Tag
from os import mkdir, chdir, rmdir
from datetime import datetime
from tqdm import tqdm
from bisect import insort_right
from copy import deepcopy


# ATTRIBUTES:

TITLE = 'BULK DOWNLOADER (USING WEB SCRAPING)'
HTTPS, HTTP = 'https://', 'http://'
NA = 'n/a'
DL_DIR = 'Downloads'  # download dir


# FUNCTIONS:

def sep_print(*msgs):
    """Print Decorator."""
    if msgs:
        print(*msgs)
    print('-' * len(TITLE))


def download(lnk: str, cont: str, i_str: str, smart: bool = True):
    """"""

    print(i_str+') Link:', lnk)
    print('Content Name:', cont)

    # Fetching Details:

    try:
        response = get_request(url=lnk, stream=True)
        # print(response.headers, '\n'); continue  # debugging
    except RequestException as re:
        print('ERROR:', re.__doc__, '\n')
        return 0  # skipping this link for any other further processing

    content_type = response.headers.get('Content-Type', NA)
    size = response.headers.get('Content-Length', NA)  # in B
    print('Content Type:', content_type)
    print('Size (bytes):', size)

    filename = response.headers.get('Content-Disposition')

    # Download Process:

    if filename:  # downloading only if filename is there

        filename = filename[filename.find('filename=') + 9:].split(sep='"', maxsplit=2)[1]  # extracting filename
        # print(filename); continue  # debugging

        # Main Downloading:

        try:

            # with open(filename, 'wb') as fd:  # without progressbar
            with tqdm.wrapattr(open(filename, 'wb'), 'write', miniters=1, desc=f'"{filename}"', total=int(size) if size != NA else 0) as fd:  # with progressbar
                for chunk in response.iter_content(chunk_size=1024):  # iterating over 1 KB at a time
                    fd.write(chunk)

        except Exception as ex:  # any non-exit exception
            print('ERROR OCCURRED:', ex, '\n')
            return 0

        print('Download: Completed \n')

        if smart and lnk not in downloaded:  # uniqueness
            insort_right(a=downloaded, x=lnk)

        return 1

    else:
        print('Download: Skipped \n')

        if smart and lnk not in skipped:  # uniqueness
            insort_right(a=skipped, x=(lnk, cont))

        return 0


# MAIN:

sep_print(f'\n{TITLE}')
sep_print('NOTE- Use a fast Wi-Fi connection for best experience.')

try:
    chdir(DL_DIR)
except FileNotFoundError:
    mkdir(DL_DIR)
    chdir(DL_DIR)

while True:

    # INPUT:

    url = input('\nEnter URL: ').strip()  # https://unsplash.com
    if not url:  # nothing entered
        exit('Exiting.')

    if '.' not in url:  # then not a URL (hostname must have '.') so perform a google search
        url = 'https://www.google.com/search?q=' + url
    else:
        if not (url.startswith(HTTPS) or url.startswith(HTTP)):
            url = HTTPS + url
        if url.endswith('/'):  # https://unsplash.com/ -> https://unsplash.com
            url = url[:-1]

    print(f'\nLinks from "{url}" are being extracted... \n')  # loading message

    # PARSING LINKS:

    try:
        html = get_request(url=url).text  # try to open URL and read data from it
    except RequestException as e:
        sep_print('ERROR:', e.__doc__)
        continue  # asking URL again

    anchor_tags = BeautifulSoup(markup=html, features='html.parser')('a')  # parse all the anchor tags
    data = {}  # link: content pair

    for anchor_tag in anchor_tags:

        link, content = anchor_tag.get('href'), anchor_tag.contents[0] if anchor_tag.contents else ''

        if link:  # checking if link got is not of NoneType

            if isinstance(content, Tag):  # content is some HTML itself instead of text
                content = content.text

            data[link.strip()] = content.strip()

    data_len = len(data)
    print('Total Links Found:', data_len)
    # print(); list(map(print, data.items()))  # debugging

    if not data:  # no links found
        sep_print()
        continue

    if input('\nStart trying download (y/n): ').casefold() != 'y':  # confirming
        sep_print('\n"Moved on."')
        continue

    print()  # spacing

    # OUTPUT PROCESS:

    dir_name = ''
    for char in url[url.index('//')+2:]:
        dir_name += char if char not in ('\\', '/', ':', '*', '?', '"', '<', '>', '|') else ' '  # a file name can't contain any of those characters
    dir_name += f" ({str(datetime.now().time()).replace(':', ';')}) "  # appending current time to make dir_name distinct
    mkdir(dir_name)
    chdir(dir_name)
    # print(dir_name); exit()  # debugging

    homepage = '/'.join(url.split(sep='/', maxsplit=3)[:3])
    # print("URL's Homepage:", homepage, '\n')  # debugging
    count = 0
    downloaded, skipped = [], []  # downloaded links, skipped (link, content) tuple

    for i, (link, content) in enumerate(iterable=data.items(), start=1):  # iterating over fetched links

        # Formatting:

        http_i = max(link.find(HTTPS), link.find(HTTP))
        if http_i != -1 and http_i != 0:
            link = link[http_i:]  # not considering useless stuff before 'https://' (or 'http://')

        elif link.startswith('/'):  # relative link
            link = homepage + link

        if not content:
            content = NA

        count += download(lnk=link, cont=content, i_str=f'{i}/{data_len}')

    if downloaded:  # if at least one link is downloaded

        # SMART DOWNLOAD:

        print('Smart Download: \n')
        # list(map(print, downloaded)); print(); list(map(print, skipped)); print()  # raw

        # Formatting Links:

        counts = {}

        for i, link in enumerate(downloaded):

            # Partitioning:
            parts = link.split('/')[2:]  # 'https://example.com/' -> ['https:', '', 'example.com', ''] -> ['example.com', '']
            if not parts[-1]:
                parts.pop()  # ['example.com', ''] -> ['example.com']

            downloaded[i] = parts

            # Counting Lengths:
            parts_len = len(parts)
            counts[parts_len] = counts.get(parts_len, 0) + 1

        most_len = sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]  # length of most links (downloaded)
        downloaded = list(filter(lambda x: len(x) == most_len, downloaded))

        for i, (link, content) in enumerate(skipped):

            # Partitioning:
            parts = link.split('/')[2:]
            if not parts[-1]:
                parts.pop()

            if most_len-len(parts) == 1:  # TODO: this needs testing
                skipped[i] = (parts, content)
            else:
                skipped[i] = []

        skipped = list(filter(None, skipped))
        # list(map(print, downloaded)); print(); list(map(print, skipped)); print()  # processed

        # Classifying Links:

        classifs = []  # classifications; [[parts (list), occurrence (int)], ...]

        for parts in deepcopy(downloaded):  # loop over links; TODO: Why downloaded[0] is changing in this loop without deepcopy?

            # print(parts)  # debugging
            not_classified = None  # unnecessary line (added due to PyCharm's warning)

            for i, classif in enumerate(classifs):  # loop over classifications

                backup = deepcopy(classifs)  # https://stackoverflow.com/questions/2612802/list-changes-unexpectedly-after-assignment-why-is-this-and-how-can-i-prevent-it; https://stackoverflow.com/questions/2465921/how-to-copy-a-dictionary-and-only-edit-the-copy
                differed = False
                not_classified = False

                for j, (c_part, part) in enumerate(zip(classif[0], parts)):  # loop to match a classification

                    if c_part != part:

                        if not differed:

                            classifs[i][0][j] = ''  # generalizing
                            differed = True  # allowing one difference

                        else:

                            classifs = backup  # restore
                            not_classified = True
                            break  # unmatched classif as num_of_diffs > 1

                if not not_classified:

                    classifs[i][1] += 1  # link classified
                    break  # as classified ✔

            if classifs == [] or not_classified:  # if no classifs are there or num_of_diffs > 1 everytime

                classifs.append([parts, 1])  # new classif

        # list(map(print, classifs)); print()  # debugging
        generalized = sorted(classifs, key=lambda x: x[1], reverse=True)[0][0]
        print('Generalized Download Link:', generalized, '\n')  # debugging

        # Matching Generalized-Link Format:

        smart_downloaded = []

        for (parts, content) in skipped:  # loop over links

            # print(parts)  # debugging
            changed = False
            not_matched = False

            for g_part, part in zip(generalized, parts):  # loop to match generalized

                if g_part != part:

                    if not changed:
                        changed = True  # allowing one diff

                    else:
                        not_matched = True
                        break

            if not not_matched:  # matched

                parts.append(generalized[-1])  # appending that one part which will make this skipped link to a downloadable link

                if parts not in downloaded:  # ✔ link not already downloaded

                    smart_downloaded.append((HTTPS+'/'.join(parts), content))

        # Downloading Modified Links:
        if smart_downloaded:
            smart_dl_len = len(smart_downloaded)
            for i, (link, content) in enumerate(iterable=smart_downloaded, start=1):
                count += download(lnk=link, cont=content, i_str=f'{i}/{smart_dl_len}', smart=False)
        else:
            print('No Links Matched :( \n')

    sep_print('Files Downloaded:', count)
    chdir('..')  # back to home path
    if not count:  # deleting made dir if nothing's downloaded
        rmdir(dir_name)


# TODO:
#  Recursive Downloading to download requested no. of files.
