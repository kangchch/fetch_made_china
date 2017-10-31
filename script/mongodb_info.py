# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient
import datetime

mongo_db_Conn = pymongo.MongoClient('192.168.60.65', 10010).made_china_info

db_made_china= mongo_db_Conn.content_tbl

db_made_china.insert({
                    'company_name': '',                   #公司名称
                    'company_url': '',                  #公司url地址

                    'introduce': '',                    #公司介绍
                    'keywords': '',                     #公司关键词
                    'operate_pattern': '',             #经营模式
                    'staffs': '',                       #员工人数
                    'turnover': '',                #年营业额

                    'renzheng': '',                     #认证情况：未认证/已认证
                    'member_level': '',                 #会员级别
                    'mainpro': '',                      #主营
                    'contactor': '',                    #联系人
                    'telephone': '',                    #电话
                    'mobilephone': '',                  #手机
                    'url': '',                          #网址
                    'address': '',                      #地址

                    'registr': '',                      #注册号
                    'legal': '',                        #法人
                    'company_type': '',                 #企业类型
                    'operate_period': '',              #经营期限
                    'operate_range': '',               #经营范围
                    'found_date': '',                   #成立日期
                    'register_office': '',              #登记机关

                })
