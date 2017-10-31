
# -*- coding: utf-8 -*-
##
# @file fetch_made_china.py
# @brief fetch company info
# @author kangchaochao
# @version 1.0
# @date 2017-10-27

from scrapy.http import Request
import xml.etree.ElementTree
from scrapy.selector import Selector

import scrapy
import re
from pymongo import MongoClient
from copy import copy
import traceback
import pymongo
from scrapy import log
from Made_China.items import MadeChinaItem
import time
import datetime
import sys
import logging
import random
import binascii
from scrapy.conf import settings
import json

reload(sys)
sys.setdefaultencoding('utf-8')


class MadeChinaSpider(scrapy.Spider):
    name = "made_china"

    def __init__(self, settings, *args, **kwargs):
        super(MadeChinaSpider, self).__init__(*args, **kwargs)
        self.settings = settings
        mongo_info = settings.get('MONGO_INFO', {})

        try:
            self.mongo_db = pymongo.MongoClient(mongo_info['host'], mongo_info['port']).made_china_info
        except Exception, e:
            self.log('connect mongo 192.168.60.65:10010 failed! (%s)' % (str(e)), level=log.CRITICAL)
            raise scrapy.exceptions.CloseSpider('initialization mongo error (%s)' % (str(e)))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def start_requests(self):

        try:
            records = self.mongo_db.made_china_tbl.find({'status': 0}, {'company_url': 1})
            for record in records:
                company_url = record['company_url']
                if company_url.endswith('made-in-china.com'):
                    next_mem = re.findall("(?<=http://).*?(?=.cn)", company_url)[0]#公司标识
                    next_url = 'http://cn.made-in-china.com/showroom/' + next_mem + '-companyinfo.html'
                    meta = {'dont_redirect': True, 'company_url': company_url, 'dont_retry': True}
                    self.log('fetch next_mem url=%s' % (next_url), level=log.INFO)
                    yield scrapy.Request(url = next_url, meta = meta, callback = self.parse_introduce_page, dont_filter = True)
                else:
                    show_url = company_url + '-companyinfo.html'
                    meta = {'dont_redirect': True, 'company_url': company_url, 'dont_retry': True}
                    self.log('fetch new url=%s' % (show_url), level=log.INFO)
                    yield scrapy.Request(url = show_url, meta = meta, callback = self.parse_introduce_page, dont_filter = True)
        except:
            self.log('start_request error! (%s)' % (str(traceback.format_exc())), level=log.INFO)

    # 解析公司信息
    def parse_introduce_page(self, response):
        sel = Selector(response)

        ret_item = MadeChinaItem()
        ret_item['update_item'] = {}
        i = ret_item['update_item']
        i['company_url'] = response.meta['company_url']

        if response.status != 200 or len(response.body) <= 0:
            self.log('fetch failed ! status = %d, url=%s' % (response.status, i['company_url']), level = log.WARNING)

        ## introduce 公司简介
        introduce = sel.xpath("//p[@class='companyInf js-companyInf']")
        i['introduce'] = '' if not introduce else introduce[0].xpath('string(.)').extract()[0].strip().strip('\n')

        ## keywords 公司关键词
        keywords = sel.xpath("//label/@title").extract()
        if keywords:
            for keyword in keywords:
                i['keywords'] = keyword
        else:
            i['keywords'] = ''

        ## 详细信息{经营模式','员工人数','营业额'}
        xpath_handles = sel.xpath("//tr//text()").extract()
        xpath_handles = ''.join(xpath_handles)

        ## operate_pattern 经营模式
        operate_pattern = re.findall(u"经营模式：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['operate_pattern'] = '' if not operate_pattern else operate_pattern[0].strip()

        ## turnover 营业额
        turnover = re.findall(u"营业额：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['turnover'] = '' if not turnover else turnover[0].strip()

        # 员工人数 staffs
        staffs = re.findall(u"员工人数：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['staffs'] = '' if not staffs else staffs[0].strip()

        if i['company_url'].endswith('made-in-china.com'):
            next_mem = re.findall("(?<=http://).*?(?=.cn)", i['company_url'])[0]#公司标识
            next_url = 'http://cn.made-in-china.com/showroom/' + next_mem + '-contact.html'
            meta = {'dont_redirect': True, 'item': ret_item, 'contac': next_url, 'dont_retry': True}
            yield scrapy.Request(url = next_url, meta = meta, callback = self.parse_contact_page, dont_filter = True)
        else:
            show_url = i['company_url'] + '-contact.html'
            meta = {'dont_redirect': True, 'item': ret_item, 'contac': show_url, 'dont_retry': True}
            yield scrapy.Request(url = show_url, meta = meta, callback = self.parse_contact_page, dont_filter = True)


    #解析联系我们页面
    def parse_contact_page(self, response):
        sel = Selector(response)

        ret_item = response.meta['item']
        i = ret_item['update_item']

        ## company_name 公司名称
        company_name = sel.xpath("//dl[@class='card-company-info']/dd/h3/text()").extract()
        i['company_name'] = '' if not company_name else company_name[0].strip()

        ## renzheng 认证情况
        renzheng = sel.xpath("//div[@class='cert-service']/span[@class='cert-sign']/text()").extract()
        i['renzheng'] = '' if not renzheng else renzheng[0].strip()

        ## mainpro 主营
        mainpro = sel.xpath("//dl[@class='card-company-info']/dd/p[1]").extract()
        mainpro = ''.join(mainpro)
        mainpro = re.findall(u"主营\s*：\n?\s*([^\n]+)", mainpro, re.S) if mainpro else ''
        i['mainpro'] = '' if not mainpro else mainpro[0].strip()

        ## contactor 联系人
        contactor = sel.xpath("//div[@class='card-name js-hidden4sem']/text()").extract()
        i['contactor'] = '' if not contactor else contactor[0].strip()

        ## 联系信息
        xpath_handles = sel.xpath("//div[@class='card-info-bd']//text()").extract()
        xpath_handles = ''.join(xpath_handles)

        ## telephone 电话
        telephone = re.findall(u"电话：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['telephone'] = '' if not telephone else telephone[0].strip()

        ## mobilephone 手机
        mobilephone = re.findall(u"手机：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['mobilephone'] = '' if not mobilephone else mobilephone[0].strip()

        ## url 网址
        url = re.findall(u"公司主页：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['url'] = '' if not url else url[0].strip()

        ## address 地址
        address = re.findall(u"(?<=地址：).*?(?=公)", xpath_handles, re.S) if xpath_handles else ''
        i['address'] = '' if not address else address[0].replace('\n','').strip().replace('\t','').replace('\r','').replace(' ','')

        if i['company_url'].endswith('made-in-china.com'):
            next_url = '%s/files-%s.html' % (i['company_url'], i['company_name'])
            meta = {'dont_redirect': True, 'item': ret_item, 'dont_retry': True}
            yield scrapy.Request(url = next_url, meta = meta, callback = self.parse_renzheng_page, dont_filter = True)
        else:
            yield ret_item

    #解析认证信息
    def parse_renzheng_page(self, response):
        sel = Selector(response)

        ret_item = response.meta['item']
        i = ret_item['update_item']

        ## 工商注册信息
        xpath_handles = sel.xpath("//tr//text()").extract()
        xpath_handles = ''.join(xpath_handles)

        ## 注册号 registr
        registr = re.findall(u"统一社会信用代码/注册号：\n*?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['registr'] = '' if not registr else registr[0].strip()

        ## 法人代表 legal
        legal = re.findall(u"法定代表人：\n*?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['legal'] = '' if not legal else legal[0].strip()

        ## 企业类型 company_type
        company_type = re.findall(u"企业类型：\n*?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['company_type'] = '' if not company_type else company_type[0].strip()

        ## 经营期限 operate_period
        operate_period = re.findall(u"经营期限：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['operate_period'] = '' if not operate_period else operate_period[0].strip()

        ## 经营范围 operate_range
        operate_range = re.findall(u"经营范围：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['operate_range'] = '' if not operate_range else operate_range[0].strip()

        ## 成立日期 found_date
        found_date = re.findall(u"成立日期：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['found_date'] = '' if not found_date else found_date[0].strip()

        ## 登记机关 register_office 
        office = re.findall(u"登记机关：\n?\s*([^\n]+)", xpath_handles, re.S) if xpath_handles else ''
        i['register_office'] = '' if not office else office[0].strip()

        self.log(' . company_name:%s, url=%s ' % (i['company_name'], i['company_url']), level=log.INFO)
        yield ret_item

