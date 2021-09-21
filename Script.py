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
anti_ddos = ('https://ddos-guard.net',
             'https://deflect.ca',
             'https://jigsaw.google.com',
             'https://kemptechnologies.com',
             'https://www.akamai.com',
             'https://www.blockdos.net',
             'https://www.cloudflare.com',
             'https://www.f5.com',
             'https://www.fastly.com',
             'https://www.imperva.com',
             'https://www.netscout.com',
             'https://www.radware.com',
             'https://www.stackpath.com',
             'https://www.verisign.com')  # URLs of DDoS (distributed denial-of-service) mitigation companies


# FUNCTIONS:

def sep_print(*msgs):
    """Print Decorator."""
    if msgs:
        print(*msgs)
    print('-' * len(TITLE))


def get_file_name(s: str):
    """"""
    name = ''
    for char in s:
        name += char if char not in ('\\', '/', ':', '*', '?', '"', '<', '>', '|') else ' '  # a file name can't contain any of these characters
    return name


def download(lnk: str, cont: str, i_str: str, smart: bool = True):
    """"""

    print(i_str+') Link:', lnk)
    print('Content Name:', cont)

    # Fetching Details:

    try:
        response = get_request(url=lnk, stream=True)
        # print(response.headers, '\n')  # debugging
    except RequestException as re:
        print('ERROR:', re.__doc__, '\n')
        return 0  # skipping this link for any other further processing

    content_type = response.headers.get('Content-Type', NA)
    size = response.headers.get('Content-Length', NA)  # in B
    print('Content Type:', content_type)
    print('Size (bytes):', size)

    # Download Process:

    if 'html' not in content_type:  # downloading if content is not html

        # Extracting filename:

        filename = response.headers.get('Content-Disposition', NA)
        f_index = filename.find('filename=')
        if f_index != -1:
            filename = filename[f_index+9:].split(sep='"', maxsplit=2)[1]  # 'attachment;filename="example.ext"' -> 'example.ext'
        else:
            name = lnk.rsplit(sep='/', maxsplit=1)[1]  # last component of link
            if name.startswith(('?', '&')):  # URL's parameters starting
                name = lnk.rsplit(sep='/', maxsplit=2)[1]
            else:
                name = name.split(sep='&', maxsplit=1)[0]  # excluding extra parameters
            name += '.' + content_type.split(sep='/', maxsplit=1)[1].split(sep=';', maxsplit=1)[0]  # extension
            filename = get_file_name(s=name)
        # print(filename, '\n'); return 0  # debugging

        # Main Downloading:

        try:

            # with open(filename, 'wb') as fd:  # without progressbar
            with tqdm.wrapattr(open(filename, 'wb'), 'write', miniters=1, desc=f'"{filename}"', total=int(size) if size != NA else 0) as fd:  # with progressbar
                for chunk in response.iter_content(chunk_size=1024):  # iterating over 1 KB at a time
                    fd.write(chunk)

        except Exception as ex:  # any non-exit exception
            print('ERROR OCCURRED:', ex, '\n')
            response.close()
            return 0

        print('Download: Completed \n')

        if smart and lnk not in downloaded:  # uniqueness
            insort_right(a=downloaded, x=lnk)

        response.close()
        return 1

    else:
        print('Download: Skipped \n')

        if smart and lnk not in skipped:  # uniqueness
            insort_right(a=skipped, x=(lnk, cont))

        response.close()
        return 0


def partitioned(lnk: str):  # 'https://example.com/'
    """"""
    p = lnk.split('/')[2:]  # ['https:', '', 'example.com', ''] -> ['example.com', '']
    return p if p[-1] else p[:-1]  # ['example.com', ''] -> ['example.com']


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
        if url.endswith('/'):  # https://example.com/ -> https://example.com
            url = url[:-1]

    print(f'\nLinks from "{url}" are being extracted... \n')

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

    total_data = len(data)

    if total_data == 1:

        link_ = list(data)[0]

        # Anti-DDoS Detection:
        try:
            sep_print(f'OOPS! Entered URL is protected from bots by "{next(filter(lambda x: link_.startswith(x), anti_ddos))}". Please try entering some other website.')
        except StopIteration:
            pass
        else:
            continue

        if link_.startswith('http://enable-javascript.com'):
            sep_print("OOPS! JavaScript webpage. Sorry I can't run JavaScript webpages, please try some other website.")
            continue

    print('Total Links Found:', total_data)
    # print(); list(map(print, data.items()))  # debugging

    if not data:  # no links found
        sep_print()
        continue

    if input('\nStart trying download (y/n): ').casefold() != 'y':  # confirming
        sep_print('\n"Moved on."')
        continue

    print()  # spacing

    # OUTPUT PROCESS:

    dir_name = get_file_name(s=url[url.index('//')+2:])  # (URL without protocol)
    dir_name += f" ({str(datetime.now().time()).replace(':', ';')}) "  # appending current time to make dir_name distinct
    mkdir(dir_name)
    chdir(dir_name)
    # print(dir_name); exit()  # debugging

    homepage = '/'.join(url.split(sep='/', maxsplit=3)[:3])  # URL = 'http://www.example.com/index.html'; homepage = 'http://www.example.com'
    # print("URL's Homepage:", homepage, '\n')  # debugging
    count = 0
    downloaded, skipped = [], []  # downloaded links, skipped (link, content) tuple

    for i, (link, content) in enumerate(iterable=data.items(), start=1):  # iterating over fetched links
        count += download(homepage+link if link.startswith(('/', '#')) else link, cont=content if content else NA, i_str=f'{i}/{total_data}')

    if downloaded and skipped:  # if at least one link is downloaded and at least one link is skipped

        # SMART DOWNLOAD:

        print('SMART DOWNLOAD: \n')
        # list(map(print, downloaded)); print(); list(map(print, skipped)); print()  # debugging

        # Formatting Links:

        counts = {}

        for i, link in enumerate(downloaded):

            parts = partitioned(link)
            downloaded[i] = parts

            # Counting Lengths:
            parts_len = len(parts)
            counts[parts_len] = counts.get(parts_len, 0) + 1

        most_len = sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]  # length of most links (downloaded)
        downloaded = list(filter(lambda x: len(x) == most_len, downloaded))

        for i, (link, content) in enumerate(skipped):

            parts = partitioned(link)

            # if len(parts) < most_len:
            # len must be less than len of downloaded links by any NUMBER ✔
            # more correct but complex because we don't even know that NUMBER here,
            # e.g. skipped = 'example.com/bla' -> 'example.com/bla/free/download' = downloadable; so here NUMBER = 2
            # so to make it straight assuming NUMBER = 1 -> e.g. -> skipped = 'example.com/bla' -> 'example.com/bla/download' = downloadable
            if len(parts)+1 == most_len:
                skipped[i] = (parts, content)
            else:
                skipped[i] = []

        skipped = list(filter(None, skipped))
        # list(map(print, downloaded)); print(); list(map(print, skipped)); print()  # debugging; partitioned

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
        print('Generalized Download Link:', generalized, '\n\nTrying to match this format with the skipped links...\n')

        # Matching Generalized-Link Format:

        matched = []

        for (parts, content) in skipped:  # loop over links

            # print(parts)  # debugging
            changed = False
            not_matched = False

            for i in range(most_len):  # loop to match generalized

                try:
                    if parts[i] != generalized[i] and generalized[i] != '':

                        if not changed:
                            parts.insert(i, generalized[i])
                            changed = True  # allowing one diff

                        else:  # changes = 2
                            not_matched = True
                            break

                except IndexError:  # due to parts[i] at last iteration, that's totally fine
                    parts.append(generalized[i])

            if not not_matched and parts not in downloaded:  # ✔ if matched and link not already downloaded
                matched.append((HTTPS + '/'.join(parts), content))

        # Downloading Modified Links:
        if matched:
            total_matched = len(matched)
            for i, (link, content) in enumerate(iterable=matched, start=1):
                count += download(link, cont=content, i_str=f'{i}/{total_matched}', smart=False)
        else:
            print('No Links Matched :( \n')

    sep_print('Files Downloaded:', count)
    chdir('..')  # back to home path
    if not count:  # deleting made dir if nothing's downloaded
        rmdir(dir_name)
