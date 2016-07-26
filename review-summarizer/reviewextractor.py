from bs4 import BeautifulSoup
import os
import re
import sys
if sys.version_info[0] >= 3:
    import urllib
    import urllib.request as request
    import urllib.error as urlerror
else:
    import urllib2 as request
    import urllib2 as urlerror
import socket
from contextlib import closing
from time import sleep
import codecs


domain='in'
out_folder='reviews'
args_force=False
args_maxretries,args_timeout,args_pause=3,180,1
args_captcha='skip'
args_maxreviews=100000
basepath = out_folder + os.sep + domain
counterre = re.compile('cm_cr_arp_d_paging_btm_([0-9]+)')
robotre = re.compile('images-amazon\.com/captcha/')

# File which containing the crawled reviews.
f=open('reviews.txt','w')

#Download the html page from the url passed
def download_page(url, referer, maxretries, timeout, pause):
    tries = 0
    htmlpage = None
    while tries < maxretries and htmlpage is None:
        try:
            code = 404
            req = request.Request(url)
            req.add_header('Referer', referer)
            req.add_header('User-agent',
                           'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.91 Chrome/12.0.742.91 Safari/534.30')
            with closing(request.urlopen(req, timeout=timeout)) as f:
                code = f.getcode()
                htmlpage = f.read()
                sleep(pause)
        except (urlerror.URLError, socket.timeout, socket.error):
            tries += 1
    if htmlpage:
        return htmlpage.decode('utf-8'), code
    else:
        return None, code

#Parse the html page and extract the reviews, write into a file
def parseandwrite(htmlpage):
    soup = BeautifulSoup(htmlpage,'html.parser')
    for tag in soup.find_all("span",class_="a-size-base review-text"):
        review=''
        for child in tag.children:
            if child.string is not None:
                print(child.string)
                review+=''+child.string
        f.write(review+'\n')

#Program execution starts here. Crawls the reviews for the given product ids.
for id_ in ['B01C7C143A']:
    if not os.path.exists(basepath + os.sep + id_):
        os.makedirs(basepath + os.sep + id_)

    urlPart1 = "http://www.amazon." + domain + "/product-reviews/"
    urlPart2 = "/?ie=UTF8&showViewpoints=0&pageNumber="
    urlPart3 = "&sortBy=bySubmissionDateDescending"

    referer = urlPart1 + str(id_) + urlPart2 + "1" + urlPart3

    page = 1
    lastPage = 1
    while page <= lastPage:
        if not page == 1 and not args_force and os.path.exists(basepath + os.sep + id_ + os.sep + id_ + '_' + str(
                page) + '.html'):
            print('Already got page ' + str(page) + ' for product ' + id_)
            page += 1
            continue

        url = urlPart1 + str(id_) + urlPart2 + str(page) + urlPart3
        print(url)
        htmlpage, code = download_page(url, referer, args_maxretries, args_timeout, args_pause)

        if htmlpage is None or code != 200:
            if code == 503:
                page -= 1
                args_pause += 2
                print('(' + str(code) + ') Retrying downloading the URL: ' + url)
            else:
                print('(' + str(code) + ') Done downloading the URL: ' + url)
                break
        else:
            print('Got page ' + str(page) + ' out of ' + str(lastPage) + ' for product ' + id_ + ' timeout=' + str(
                args_pause))
            if robotre.search(htmlpage):
                print('ROBOT! timeout=' + str(args_pause))
                if args_captcha or page == 1:
                    args_pause *= 2
                    continue
                else:
                    args_pause += 2
            for match in counterre.findall(htmlpage):
                try:
                    value = int(match)
                    if value > lastPage:
                        lastPage = value
                except:
                    pass
            with codecs.open(basepath + os.sep + id_ + os.sep + id_ + '_' + str(page) + '.html', mode='w',
                             encoding='utf8') as file:
                # file.write(htmlpage)
                parseandwrite(htmlpage)
            if args_pause >= 2:
                args_pause -= 1
        referer = urlPart1 + str(id_) + urlPart2 + str(page) + urlPart3
        if args_maxreviews > 0 and page * 10 >= args_maxreviews:
            break
        page += 1
f.close()







