from urllib.request import urlopen
from bs4 import BeautifulSoup


import ssl
# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def sep_print(optional_msg=''):
    print(f'{optional_msg} \n-------------------------------------------------------------------------------------------------------------------------------------------------------------------')


sep_print('\nLINK EXTRACTOR')

while True:
    inp = input("\nEnter URL: ").strip()

    if inp == '':
        sep_print("\nInput can't be empty :| \n")
        continue

    if inp.startswith('https://'):
        home_link = inp
    else:
        home_link = 'https://' + inp

    print(f"\nLinks from '{home_link}' are being extracted... \n")

    links_set = set()  # used set for unique links! :)
    links_contents_list = list()
    try:
        for anchor_tag in BeautifulSoup(urlopen(home_link), 'html.parser')('a'):
            links_set.add(anchor_tag.get('href', None))
            links_contents_list.append(anchor_tag.contents[0])
    except Exception as e:
        sep_print(f"Error occurred : {e}\n")
        continue

    # print(links_set, '\n\n', len(links_set), '\n\n', links_contents_list, '\n\n', len(links_contents_list)); sep_print(); continue # checking

    count = 0
    for sub_link, content in zip(links_set, links_contents_list):  # zip is a method used to iterate over two lists simultaneously!
        if content == '\n':  # (for ok.xyz)
            content = 'N/A'
        if sub_link.startswith(home_link):
            print('Link:', sub_link, '\nContent:', content, '\n')
            count += 1
        if sub_link.startswith('/'):
            print('Link:', home_link + sub_link, '\nContent:', content, '\n')
            count += 1

    if count != 0:
        print(f"{count} links found! Now you can copy them all and share or do whatever you wanna do with them! Enjoy! :D")
    else:
        print('No link found.')
    sep_print()
