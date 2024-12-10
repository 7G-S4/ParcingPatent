import re
import tqdm

from scrapy import Item
from scrapy.exceptions import IgnoreRequest
from w3lib.html import remove_tags
from itemloaders.processors import MapCompose, Join, TakeFirst, Compose
from scrapy.loader import ItemLoader
import scrapy
import os

class ProxyPool:
    def __init__(self, proxy_pool):
        self.proxy_pool = [(proxy_pool[i], i) for i in range(len(proxy_pool))]
        self.proxy = None
    def get_proxy(self):
        self.proxy = self.proxy_pool.pop()
        self.proxy_pool = [self.proxy] + self.proxy_pool
        return self.proxy[0]
    def get_pos(self):
        return self.proxy[1]


class PatentItem(Item):
    num = scrapy.Field()
    status = scrapy.Field()
    status_date = scrapy.Field()
    syntax = scrapy.Field()
    classification = scrapy.Field()
    country = scrapy.Field()
    req_num = scrapy.Field()
    req_date = scrapy.Field()
    reg_date = scrapy.Field()
    references = scrapy.Field()
    authors = scrapy.Field()
    patentees = scrapy.Field()
    name = scrapy.Field()
    summary = scrapy.Field()
    text = scrapy.Field()
    formula = scrapy.Field()


class PatentLoader(ItemLoader):
    default_output_processor = Join()
    num_in = MapCompose(lambda s: ''.join(re.findall(r'\d', s)))

    status_in = MapCompose(remove_tags, lambda s: s[:s.find("(")-1] if s.find("(") != -1 else s)
    status_out = TakeFirst()


    status_date_out = TakeFirst()
    status_date_in = MapCompose(lambda s: re.findall(r"\b(\d{2})\.(\d{2})\.(\d{4})\b", s),
                                lambda s: '.'.join(list(i for i in s)))

    classification_in = MapCompose(remove_tags, lambda s: ' '.join(s.split()))
    classification_out = Join(', ')

    syntax_in = MapCompose(remove_tags)

    country_in = MapCompose(remove_tags)

    req_num_in = MapCompose(remove_tags, lambda s: s.split(', ')[0] if s != "" else "")
    req_date_in = MapCompose(remove_tags, lambda s: s.split(', ')[1] if s != "" else "")

    reg_date_in = MapCompose(remove_tags)

    authors_in = MapCompose(remove_tags, lambda s: s.replace('\n', ''))
    patentees_in = MapCompose(remove_tags, lambda s: s.replace('\n', ''))

    summary_in = MapCompose(lambda s: s.replace('\n', ''))
    text_out = Compose(lambda s: ' '.join(s), lambda s: s[:s.find("Формула изобретения")].replace('\n', ''),
                       lambda s: ' '.join(s.split()))
    formula_out = Compose(lambda s: ' '.join(s), lambda s: s[s.find("Формула изобретения")+19:s.find("ИЗВЕЩЕНИЯ")].replace('\n', ''),
                          lambda s: ' '.join(s.split()))


class PatentsSpider(scrapy.Spider):
    name = "alpha"

    def start_requests(self, first=2820020, n=294737):
        proxy_pool = ProxyPool([
            "http://Q3vAK3:atozXLR9f6@95.182.125.102:1050",
            "http://Q3vAK3:atozXLR9f6@109.248.54.100:1050",
            "http://Q3vAK3:atozXLR9f6@188.130.136.67:1050",
            "http://Q3vAK3:atozXLR9f6@188.130.221.189:1050",
            "http://Q3vAK3:atozXLR9f6@46.8.110.111:1050",
            "http://Q3vAK3:atozXLR9f6@185.181.244.68:1050",
            "http://Q3vAK3:atozXLR9f6@46.8.23.118:1050",
            "http://Q3vAK3:atozXLR9f6@46.8.192.158:1050",
            "http://Q3vAK3:atozXLR9f6@46.8.22.245:1050",
            "http://Q3vAK3:atozXLR9f6@185.181.245.89:1050",
            "http://Q3vAK3:atozXLR9f6@109.248.166.53:1050",
            "http://Q3vAK3:atozXLR9f6@95.182.127.97:1050",
            "http://Q3vAK3:atozXLR9f6@109.248.205.159:1050",
            "http://Q3vAK3:atozXLR9f6@109.248.12.55:1050",
            "http://Q3vAK3:atozXLR9f6@109.248.139.104:1050"
        ])
        for num in tqdm.tqdm(range(first, first-n, -1)):
            yield scrapy.Request(url=f"https://new.fips.ru/registers-doc-view/fips_servlet?DB=RUPAT&DocNumber={num}&TypeFile=html",
                                 callback=self.parse,
                                 meta={'proxy': proxy_pool.get_proxy(),
                                       'download_slot' : proxy_pool.get_pos()})
            os.system("cls")

    def parse(self, response):
        objects = {'num': "//title",
                   "status": "(//td[@id='StatusR'])[1]",
                   "status_date": "(//td[@id='StatusR'])[1]",
                   "classification": "//ul[@class='ipc']//a",
                   "syntax": "//div[@id='top6']",
                   "country": "//div[@id='top2']",
                   "req_num": "//table[@id='bib']//p[contains(text(), '(21)')]/b",
                   "req_date": "//table[@id='bib']//p[contains(text(), '(21)')]/b",
                   "reg_date": "//table[@id='bib']//p[contains(text(), '(45)')]/b[1]",
                   "references": "//table[@id='bib']//p[@class = 'B560']/b/text()",
                   "authors": "//td[@id='bibl']/p[contains(text(), '(72)')]/b",
                   "patentees": "//td[@id='bibl']/p[contains(text(), '(73)')]/b",
                   "name": "//p[@id='B542']/b/text()",
                   "summary": "//div[@id='Abs']/p[2]/text()",
                   "text": "//div[@id='mainDoc']/child::p[not(@id='B542')]/text()",
                   "formula": "//div[@id='mainDoc']/child::p[not(@id='B542')]/text()"}
        l = PatentLoader(PatentItem(), response=response)
        flag_0 = 0
        flag_1 = False
        for name, path in objects.items():
            try:
                l.add_xpath(name, path)
            except Exception as e:
                l.add_value(name, "")
                flag_0 += 1
                with open("err_log.txt", 'a+') as f:
                    flag_1 = True
                    f.write("\n"*4 + str(e) + "\n"*2 + response.url)
            else:
                if l.get_output_value(name)=="":
                    flag_0 += 1
        print('\n\n')
        for name in ["num", "status", "country", "syntax", "classification"]:
            print(f'{name}: {l.get_output_value(name)}')
        print(f'ip: {response.request.meta.get("download_slot")}')
        if all(l.get_output_value(name)=="" or l.get_output_value(name) is None for name in objects.keys()):
            with open('skipped_urls.txt', 'a+') as f:
                f.write(response.request.url + ' ' + str(response.request.meta.get('download_slot')) + '\n')
        else:
            if flag_1:
                with open("err_log.txt", 'a+') as f:
                    f.write('\n'+ '-'*64)
            yield l.load_item()

class TimeoutMiddleware:
    def process_exception(self, request, exception, spider):
        with open('skipped_urls.txt', 'a+') as f:
            f.write(request.url + ' ' + str(request.meta.get('download_slot')) + '\n')
        raise IgnoreRequest()