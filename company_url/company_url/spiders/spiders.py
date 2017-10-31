#! coding: utf-8

import requests
import os
import pymongo
from pymongo import MongoClient
import datetime
import logging
import scrapy
import re
import time
import traceback
from scrapy import log
import sys
from scrapy.conf import settings
from company_url.items import CompanyUrlItem
from scrapy.selector import Selector
from lxml import etree
from ipdb import set_trace


reload(sys)
sys.setdefaultencoding('utf-8')

class CompanyUrlSpider(scrapy.Spider):
    name = "spider"

    def __init__(self, settings, *args, **kwargs):
        super(CompanyUrlSpider, self).__init__(*args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def start_requests(self):
        try:
            start_url = 'http://cn.made-in-china.com/gongsi/'
            meta = {'dont_redirect': True, 'dont_retry': True}
            yield scrapy.Request(url=start_url, meta=meta, callback=self.parse, dont_filter=True)
        except:
            self.log('start_request error! (%s)' % (str(traceback.format_exc())), level=log.INFO)

    ##按行业找公司
    def parse(self, response):
        sel = Selector(response)

        if response.status != 200:
            self.log('fetch industry failed! status=%d' % (response.status), level=log.WARNING)

        xpath_handles = sel.xpath("//div[@class='floor']//dd/a")# 只返回每个行业的第一页: '/directory/Warmer-Appliance-1.html'
        for xpath_handle in xpath_handles:
            industry_href = xpath_handle.xpath("@href")[0].extract()
            industry_url = ''.join(['http://cn.made-in-china.com' + industry_href])

            meta = {'dont_redirect': True, 'item': industry_href, 'dont_retry': True}
            yield scrapy.Request(url=industry_url, meta = meta, callback=self.parse_company_page, dont_filter=True)

            
            # re_href = re.findall(u"/.*?(?=\d+)", industry_href)[0]#正则找'/directory/Warmer-Appliance-'
            # for page in range(1, 301):
                # industry_url = 'http://cn.made-in-china.com%s%d.html' % (re_href, page)
                # meta = {'dont_redirect': True, 'dont_retry': True}
                # self.log('industry_url=%s, ' % (industry_url), level=log.INFO)
                # yield scrapy.Request(url=industry_url, meta = meta, callback=self.parse_company_page, dont_filter=True)

    def parse_company_page(self, response):
        sel = Selector(response)

        # i = CompanyUrlItem()
        # if response.status != 200:
            # self.log('fetch company_page failed! status=%d' % (response.status), level=log.WARNING)

        # xpath_handles = sel.xpath("//label[@class='co-name']/a")
        # for xpath_handle in xpath_handles:
            # company_url = xpath_handle.xpath("@href")[0].extract()
            # if 'http' not in company_url:
                # company_url = ''.join(['http://cn.made-in-china.com' + company_url])
                # i['company_url'] = company_url
            # i['company_url'] = company_url

            # self.log('fetch succsed! , company_url=%s' % (i['company_url']), level=log.INFO)
            # yield i

        i = CompanyUrlItem()
        href = response.meta['item']
        if response.status != 200:
            self.log('fetch company_page failed! status=%d' % (response.status), level=log.WARNING)

        xpath_handles = sel.xpath("//label[@class='co-name']/a")
        for xpath_handle in xpath_handles:
            company_url = xpath_handle.xpath("@href")[0].extract()
            if 'http' not in company_url:
                company_url = ''.join(['http://cn.made-in-china.com' + company_url])
                i['company_url'] = company_url
            i['company_url'] = company_url

            yield i
            self.log('fetch succsed! , company_url=%s' % (i['company_url']), level=log.INFO)

        if sel.xpath("//a[@class='page-next']/text()").extract():
            re_href = re.findall(r"/.*?(?=\d+)", href) if href else ''     #正则找'/directory/Warmer-Appliance-'
            re_href = '' if not re_href else re_href[0]
            page = int(re.findall("\d+", href)[0]) + 1
            next_page_url = 'http://cn.made-in-china.com%s%d.html' % (re_href, page)
            next_href = re.findall(r"(?<=com)/.*?.html",next_page_url)
            next_href = '' if not next_href else next_href[0]
            self.log('next_url! , next_page_url=%s' % (next_page_url), level=log.INFO)
            meta = {'dont_redirect': True, 'item': next_href, 'dont_retry': True}
            yield scrapy.Request(url=next_page_url, meta=meta, callback=self.parse_company_page, dont_filter=True)

