# -*- coding:utf-8 -*-
import urllib
import httplib
import re
import string
import datetime
import json
from StringIO import StringIO
import gzip

keys = ('审计', '造价', '第三方', '评估', '投资', '咨询', '中介','安装','公告','SJ','ZJ')
ndaysago = 5

endtime = datetime.datetime.now().strftime("%Y-%m-%d")
begintime = (datetime.datetime.now() - datetime.timedelta(days=ndaysago)).strftime("%Y-%m-%d")


def write_html(filehandler,prjName, urlstr):
    filehandler.write('<a href="' + urlstr + '" target="_blank" title="">')
    filehandler.write('<font size="5">' + prjName + '</font></a><p></p>\n')

def write_jump(filehandler,sitename,hostname):
    filehandler.write('<a href="#'+ hostname +'">'+ u'跳转到'.encode('gbk') + sitename + u'招标公告列表'.encode('gbk') + '</a><p></p>')

def write_returnheader(filehandler):
    filehandler.write('<a href="#header">'+ u'跳转到页首'.encode('gbk') + '</a><p></p>')

def write_header(filehandler,sitename,hostname):
    filehandler.write('<a name="'+ hostname + '"></a>')
    filehandler.write(
        '<p>=========================================<font color="red" size="5">'+ sitename +'  '+ hostname + '</font>=============================================</p>\n')
    print '\n========================================='+ sitename +'  '+ hostname + '=============================================\n'

class CCGP_HUBEI:
    def __init__(self, filehandler):
        self.sitename = u'中国政府采购。湖北'
        self.fh = filehandler
        self.pagesize = 50       # 15,25,50,100
        self.hostname = 'www.ccgp-hubei.gov.cn'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   # 'Accept-Encoding': 'gzip, deflate',
                   'Referer': 'http://www.ccgp-hubei.gov.cn/fnoticeAction!listFNoticeInfos.action',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        self.RegionIDs = [('420001',u'省级公告'),('420100',u'武汉市'),('420200',u'黄石市'),('420600',u'襄阳市'),('421000',u'荆州市'),
                            ('420500',u'宜昌市'),('420300',u'十堰市'),('420900',u'孝感市'),('420800',u'荆门市'),('420700',u'鄂州市'),
                            ('421100',u'黄冈市'),('421200',u'咸宁市'),('421300',u'随州市'),('422800',u'恩施州'),('421400',u'仙桃市'),
                            ('421500',u'潜江市'),('421600',u'天门市'),('421700',u'神龙架林区')]
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self, pageindex,cid):
        values = {'rank': '$rank', 'queryInfo.curPage': pageindex, 'queryInfo.pageSize': self.pagesize,
                  'queryInfo.TITLE': '',
                  'queryInfo.FBRMC': '', 'queryInfo.GGLX': '招标公告', 'queryInfo.CGLX': '',
                  'queryInfo.CGFS': '', 'queryInfo.BEGINTIME1': begintime, 'queryInfo.ENDTIME1': endtime,
                  'queryInfo.QYBM': cid, 'queryInfo.JHHH': ''}

        httpClient = None
        page = ''
        params = urllib.urlencode(values)
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', '/fnoticeAction!listFNoticeInfos.action', params, self.headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            # print response.getheaders()
            page = response.read()
            #print page.decode('utf-8').encode('gbk', 'ignore')
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        return page

    def get_prj_name(self,urlpath):     #有些公告条目不全（以...结尾)，需从公告的正文里取标题
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', urlpath, None, self.headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            # print response.getheaders()
            page = response.read()
            # print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()

        report_iframe_p = re.compile('<iframe(.*?)</iframe>', re.S)
        report_iframe = re.search(report_iframe_p, page)
        report_url_p = re.compile('src="(.*?)"')
        report_url = re.search(report_url_p,report_iframe.group()).group().replace('src="', '').replace('"', '')  # 取出报告url

        try:    #读取报告
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', report_url, None, self.headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            # print response.getheaders()
            page = response.read()
            # print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        project_name_p =  re.compile('<h1>(.*?)</h1>', re.S)
        project_name =  re.search(project_name_p, page).group().replace('<h1>','').replace('</h1>','')
        return project_name


    def get_one_page_context(self, page):
        p1 = re.compile('<div class="news_content ">(.*?)</div>', re.S)
        r1 = re.search(p1, page)  # 取出所有项目
        if r1:
            p2 = re.compile('<li>(.*?)</li>', re.S)
            r2 = re.findall(p2, r1.group())  # 按条取出项目
            release_time_p = re.compile('(\d+)-(\d+)-(\d+)', re.S)  # 取发布时间正则
            url_p = re.compile('href=\"(.*?)\"', re.S)  # 取URL正则
            projectname_p = re.compile('target=\"_blank\">(.*?)</a>', re.S)  # 取项目名称正则
            for item in r2:
                release_time = re.search(release_time_p, item)
                projectname = re.search(projectname_p, item)
                url = re.search(url_p, item)

                timestr = release_time.group()
                prjName = projectname.group().replace('target="_blank">', '').replace('</a>', '').strip()
                urlstr = 'http://' + self.hostname + url.group().replace('href="', '').replace('"', '')
                if prjName[-3:] == '...':
                    prjName = self.get_prj_name(urlstr)
                for key in keys:
                    if prjName.find(key) >= 0:
                        w_prjName = timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                        write_html(self.fh,w_prjName,urlstr)
                        print w_prjName
                        break

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        for cid in self.RegionIDs:
            self.fh.write('<p>-----------------<font color="red" size="5">' + cid[1].encode('gbk') + '</font>------------------</p>\n')
            print '-----------------' + cid[1].encode('gbk') + '------------------\n'
            first_page = self.getpage(0,cid[0])
            itemnum_p = re.compile('共(\d+)条记录', re.S)
            itemnum = string.atoi(re.search(itemnum_p, first_page).group().replace('共', '').replace('条记录', ''))
            if itemnum == 0:
                print cid[1].encode('gbk')+u'没有符合时间段要求的公告'.encode('gbk')
                continue
            pagenum = itemnum / self.pagesize + 1
            curpage = 2
            self.get_one_page_context(first_page)
            while curpage <= pagenum:
                self.get_one_page_context(self.getpage(curpage,cid[0]))
                curpage += 1
        write_returnheader(self.fh)

class HBGGZY:
    def __init__(self, filehandler):
        self.sitename = u'湖北省公共资源交易中心'
        self.hostname = 'www.hbggzy.cn'
        self.fh = filehandler
        self.ViewState = ''
        self.curpage = 1
        self.cookie = ''
        self.keys = [k.decode('utf-8').encode('gbk') for k in keys]
        self.CategoryIDs = [('004001006001', u'房建市政工程'), ('004001006002', u'交通工程'), ('004001006003', u'水利工程'),
                            ('004001006004', u'国土整治'), ('004001006005', u'其他项目'), ('004001006006', u'铁路工程')]
        self.RegionIDs = [('023017',u'武汉市'),('023008',u'黄石市'),('023004',u'襄阳市'),('023002',u'荆州市'),
                            ('023001',u'宜昌市'),('023013',u'十堰市'),('023010',u'孝感市'),('023009',u'荆门市'),('023006',u'鄂州市'),
                            ('023007',u'黄冈市'),('023005',u'咸宁市'),('023014',u'随州市'),('023003',u'恩施州'),('023016',u'仙桃市'),
                            ('023011',u'潜江市'),('023015',u'天门市'),('023012',u'神龙架林区')]
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage_sj(self, CategoryID):    #取省级页面
        values = {'__VIEWSTATE': self.ViewState, '__EVENTTARGET': 'MoreInfoList1$Pager',
                  '__EVENTARGUMENT': '%d' % self.curpage}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate',
                   'Cookie': self.cookie,
                   'Content-Type': 'application/x-www-form-urlencoded'}

        url_path = '/hubeizxwz/jyxx/004001/004001006/' + CategoryID + '/MoreInfo.aspx?CategoryNum=' + CategoryID
        params = urllib.urlencode(values)
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', url_path, params, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            headers = response.getheaders()
            page = response.read()
            #print page
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()
            for header_item in headers:
                if header_item[0] == 'set-cookie':
                    self.cookie += (header_item[1] + ';')
            return page

    def getpage_sz(self, RegionID):    #取市州页面
        values = {'__VIEWSTATE': self.ViewState, '__EVENTTARGET': 'MoreInfoList1$Pager',
                  '__EVENTARGUMENT': '%d' % self.curpage}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate',
                   'Cookie': self.cookie,
                   'Content-Type': 'application/x-www-form-urlencoded'}

        url_path = '/hubeizxwz/tyjyxxpt/' + RegionID + '/'+ RegionID + '001/MoreInfo.aspx?CategoryNum=' + RegionID + '001'
        params = urllib.urlencode(values)
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', url_path, params, headers)
            response = httpClient.getresponse()
            #print response.status
            #print response.reason
            headers = response.getheaders()
            page = response.read()
            #print page
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()
            for header_item in headers:
                if header_item[0] == 'set-cookie':
                    self.cookie += (header_item[1] + ';')
        # print self.cookie
            return page

    def get_prj_name(self,urlpath):     #从公告的正文里取标题
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate',
                   'Cookie': self.cookie,
                   'Content-Type': 'application/x-www-form-urlencoded'}
        httpClient = None
        page = ''
        try:    #读取报告
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', urlpath, None, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            # print response.getheaders()
            page = response.read()
            # print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()

        pp_p =  re.compile('<td id="tdTitle"(.*?)</td>', re.S)
        pp =  re.search(pp_p, page)

        project_name_p = re.compile('<b>(.*?)</b>', re.S)
        project_name = re.search(project_name_p,pp.group())
        return project_name.group().replace('<b>','').replace('</b>','').strip()

    def get_one_page_context(self, page):
        if page == '':
            return -1
        viewstat_p = re.compile('<input type="hidden" name="__VIEWSTATE"(.*?)/>', re.S)
        viewstat = re.search(viewstat_p, page)  # __VIEWSTATE
        if viewstat:
            self.ViewState = viewstat.group().replace('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE"',
                                                      '').replace('value="', '').replace('" />', '').strip()
        # print self.ViewState

        table_p = re.compile('id="MoreInfoList1_DataGrid1"(.*?)</table>', re.S)
        table = re.search(table_p, page)
        # print table.group()
        if table:
            items_p = re.compile('<tr valign="(.*?)</tr>', re.S)
            items = re.findall(items_p, table.group())  # 按条取出项目

            release_time_p = re.compile('\d\d\d\d-\d\d-\d\d', re.S)  # 取发布时间正则
            url_p = re.compile('href=\"(.*?)\"', re.S)  # 取URL正则
            #projectname_p = re.compile('title="(.*?)">', re.S)  # 取项目名称正则

            for item in items:
                release_time = re.search(release_time_p, item)
                url = re.search(url_p, item)

                timestr = release_time.group()
                if timestr < begintime:
                    return -1
                urlstr =  url.group().replace('href="', '').replace('"', '')
                prjName = self.get_prj_name(urlstr)      #读取报告页面，并从报告里取项目名称
                urlstr = 'http://'+ self.hostname + urlstr
                for key in self.keys:
                    if prjName.find(key) >= 0:
                        write_html(self.fh,timestr + '  ' + prjName,urlstr)
                        print timestr + '  ' + prjName
                        break
        return 0

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        for cid in self.CategoryIDs:   #遍历省级
            self.fh.write('<p>-----------------' + cid[1].encode('gbk') + '------------------</p>\n')
            print '-----------------' + cid[1].encode('gbk') + '------------------\n'
            self.ViewState = ''
            self.curpage = 1
            self.cookie = ''
            page = self.getpage_sj(cid[0])
            while self.get_one_page_context(page) != -1:
                self.curpage += 1
                page = self.getpage_sj(cid[0])
        for rid in self.RegionIDs:  #遍历市州
            self.ViewState = ''
            self.curpage = 1
            self.cookie = ''
            self.fh.write('<p>-----------------' + rid[1].encode('gbk') + '------------------</p>\n')
            print '-----------------' + rid[1].encode('gbk') + '------------------\n'
            page = self.getpage_sz(rid[0])
            while self.get_one_page_context(page) != -1:
                self.curpage += 1
                page = self.getpage_sz(rid[0])
        write_returnheader(self.fh)


class HONGSHAN:
    def __init__(self, filehandler):
        self.sitename = u'武汉市洪山区政府'
        self.hostname = 'www.hongshan.gov.cn'
        self.fh = filehandler
        self.pageindex = 1
        self.cookie = ''
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        values = {'method': 'Data', 'cid': '175','currentPage': '%d' % self.pageindex, 'pageSize':'12', 'ids': '0'}

        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                        # 'Accept-Encoding': 'gzip, deflate',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': 'http://www.hongshan.gov.cn/nav.shtml'}

        url_path = '/hs/PageHandler'
        params = urllib.urlencode(values)
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', url_path, params, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            headers = response.getheaders()
            page = response.read()
                        # print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        for header_item in headers:
            if header_item[0] == 'set-cookie':
                self.cookie += (header_item[1] + ';')
        return page

    def get_one_page_context(self, page):
        items_p = re.compile('<tr>(.*?)</tr>', re.S)
        items = re.findall(items_p, page)  # 按条取出项目

        release_time_p = re.compile('\d\d\d\d-\d\d-\d\d', re.S)  # 取发布时间正则
        url_p = re.compile('href=\"(.*?)\"', re.S)  # 取URL正则
        projectname_p = re.compile('title=\'(.*?)\'', re.S)  # 取项目名称正则

        for item in items:
            release_time = re.search(release_time_p, item)
            projectname = re.search(projectname_p, item)
            url = re.search(url_p, item)

            timestr = release_time.group()
            if timestr < begintime:
                return -1
            prjName = projectname.group().replace('title=\'', '').replace('\'','').strip()
            urlstr = 'http://' + self.hostname + '/' + url.group().replace('href="', '').replace('"', '')
            for key in keys:
                if prjName.find(key) >= 0:
                    write_html(self.fh, timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'), urlstr)
                    print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                    break
        return 0

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        page = self.getpage()
        while self.get_one_page_context(page) != -1:
            self.pageindex += 1
            page = self.getpage()
        write_returnheader(self.fh)

class XINZHOU:
    def __init__(self, filehandler):
        self.sitename = u'武汉市新洲政府采购网'
        self.hostname = 'www.whxinzhou.gov.cn'
        self.fh = filehandler
        self.page_suffix = ('','_1','_2','_3','_4','_5','_6','_7','_8','_9','_10','_11','_12','_13','_14')
        self.pageindex = 0
        self.cookie = ''
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                     # 'Accept-Encoding': 'gzip, deflate',
                   'Referer': 'http://www.whxinzhou.gov.cn/bmdw/cgzx/cgxw/cggg/index.shtml'}

        url_path = '/bmdw/cgzx/cgxw/cggg/index' + self.page_suffix[self.pageindex] + '.shtml'
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', url_path, None, headers)
            response = httpClient.getresponse()
                    # print response.status
                    # print response.reason
            headers = response.getheaders()
            page = response.read()
            #print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        for header_item in headers:
            if header_item[0] == 'set-cookie':
                self.cookie += (header_item[1] + ';')
        return page

    def get_one_page_context(self, page):
        items_p = re.compile('<div class="work_list">(.*?)</div>', re.S)
        items = re.findall(items_p, page)  # 按条取出项目

        release_time_p = re.compile('\d\d\d\d年\d\d月\d\d', re.S)  # 取发布时间正则
        url_p = re.compile('href="(.*?)"', re.S)  # 取URL正则
        projectname_p = re.compile('target="_blank">(.*?)</a>', re.S)  # 取项目名称正则

        for item in items:
            release_time = re.search(release_time_p, item)
            projectname = re.search(projectname_p, item)
            url = re.search(url_p, item)

            timestr = release_time.group().replace('年','-').replace('月','-')
            if timestr < begintime:
                return -1
            prjName = projectname.group().replace('target="_blank">', '').replace('</a>', '').strip()
            urlstr = 'http://' + self.hostname + '/bmdw/cgzx/cgxw/cggg/' + url.group().replace('href="', '').replace('"', '')
            for key in keys:
                if prjName.find(key) >= 0:
                    write_html(self.fh, timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'),urlstr)
                    print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                    break
        return 0

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        MaxPageNum = len(self.page_suffix)
        page = self.getpage()
        while self.get_one_page_context(page) != -1:
            self.pageindex += 1
            if self.pageindex >= MaxPageNum:
                break
            page = self.getpage()
        write_returnheader(self.fh)

class WEHDZ:
    def __init__(self, filehandler):
        self.sitename = u'武汉东湖新技术开发区'
        self.hostname = 'www.wehdz.gov.cn'
        self.fh = filehandler
        self.pageindex = 0
        self.cookie = ''
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                           # 'Accept-Encoding': 'gzip, deflate',
                   'Referer': 'http://www.wehdz.gov.cn/info/iList.jsp?isSd=false&node_id=GKwehdz&cat_id=3855'}

        url_path = '/info/iList.jsp?node_id=GKwehdz&site_id=HIWCMwehdz&cat_id=3855&cur_page=%d' %self.pageindex
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', url_path, None, headers)
            response = httpClient.getresponse()
                    # print response.status
                    # print response.reason
            headers = response.getheaders()
            page = response.read()
                    # print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
           if httpClient:
               httpClient.close()
        for header_item in headers:
           if header_item[0] == 'set-cookie':
              self.cookie += (header_item[1] + ';')
        return page

    def get_one_page_context(self, page):
        table_p = re.compile('<table class="info-list">(.*?)<td colspan="4" class="c">', re.S)
        table = re.search(table_p, page)
        # print table.group().decode('utf-8').encode('gbk', 'ignore')
        if table:
           items_p = re.compile('<td><a (.*?)<th>所属主题</th>', re.S)
           items = re.findall(items_p, table.group())  # 按条取出项目

           release_time_p = re.compile('<td>\d\d\d\d-\d\d-\d\d</td>', re.S)  # 取发布时间正则
           url_p = re.compile('href="(.*?)"', re.S)  # 取URL正则
           projectname_p = re.compile('<th>标(.*?)</td>', re.S)  # 取项目名称正则

        for item in items:
            release_time = re.search(release_time_p, item)
            projectname = re.search(projectname_p, item)
            url = re.search(url_p, item)

            timestr = release_time.group().replace('<td>', '').replace('</td>', '')
            if timestr < begintime:
                return -1
            prjName = projectname.group().replace('<th>标', '').replace(urllib.unquote('%e3%80%80'),'').replace('题</th>','').replace('<td colspan="3">', '').replace('</td>','').strip()
            urlstr = 'http://' + self.hostname + url.group().replace('href="','').replace('"','')
            for key in keys:
                if prjName.find(key) >= 0:
                    write_html(self.fh, timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'), urlstr)
                    print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                    break
        return 0

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        page = self.getpage()
        while self.get_one_page_context(page) != -1:
            self.pageindex += 1
            page = self.getpage()
        write_returnheader(self.fh)

class WEDZ:
    def __init__(self, filehandler):
        self.sitename = u'武汉经济开发区'
        self.hostname = 'www.wedz.com.cn'
        self.fh = filehandler
        self.page_suffix = ('', '_1', '_2', '_3', '_4', '_5', '_6', '_7', '_8', '_9', '_10', '_11', '_12', '_13', '_14')
        self.pageindex = 0
        self.cookie = ''
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   # 'Accept-Encoding': 'gzip, deflate',
                   'Cookie': self.cookie,
                   'Referer': 'http://www.wedz.com.cn/cggg/index.jhtml'}
        url_path = '/cggg/index'+ self.page_suffix[self.pageindex] + '.jhtml'
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', url_path, None, headers)
            response = httpClient.getresponse()
                    # print response.status
                    # print response.reason
            headers = response.getheaders()
            page = response.read()
                    # print page
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()
            for header_item in headers:
                if header_item[0] == 'set-cookie':
                    self.cookie += (header_item[1] + ';')
            return page

    def get_prj_name(self,urlpath):     #有些公告条目不全（以...结尾)，需从公告的正文里取标题
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   # 'Accept-Encoding': 'gzip, deflate',
                   'Cookie': self.cookie,
                   'Referer': 'http://www.wedz.com.cn/cggg/index.jhtml'}
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', urlpath, None, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            # print response.getheaders()
            page = response.read()
            # print page
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()

        project_name_p =  re.compile('<h1>(.*?)</h1>', re.S)
        project_name =  re.search(project_name_p, page).group().replace('<h1>','').replace('</h1>','')
        return project_name

    def get_one_page_context(self, page):
        table_p = re.compile('<div class="wei_rcgg">(.*?)</div>', re.S)
        table = re.search(table_p, page)
                # print table.group().decode('utf-8').encode('gbk', 'ignore')
        if table:
            items_p = re.compile('<li>(.*?)</li>', re.S)
            items = re.findall(items_p, table.group())  # 按条取出项目

            release_time_p = re.compile('\d\d\d\d-\d\d-\d\d', re.S)  # 取发布时间正则
            url_p = re.compile('href="(.*?)"', re.S)  # 取URL正则
            projectname_p = re.compile('</span>(.*?)</a>', re.S)  # 取项目名称正则

            for item in items:
                release_time = re.search(release_time_p, item)
                projectname = re.search(projectname_p, item)
                url = re.search(url_p, item)

                timestr = release_time.group().replace('<td>', '').replace('</td>', '')
                if timestr < begintime:
                    return -1
                prjName = projectname.group().replace('</span>', '').replace('</a>', '').strip()
                urlstr = url.group().replace('href="', '').replace('"', '')
                if prjName[-3:] == '...':
                    prjName = self.get_prj_name(urlstr)
                for key in keys:
                    if prjName.find(key) >= 0:
                        write_html(self.fh, timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'),urlstr)
                        print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                        break
            return 0
        else:
            return -1

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        page = self.getpage()
        while self.get_one_page_context(page) != -1:
            self.pageindex += 1
            page = self.getpage()
        write_returnheader(self.fh)

#=====================================================================================================================
class JY_WHZBTB:
    def __init__(self, filehandler):
        self.sitename = u'武汉市建设工程交易中心'
        self.hostname = 'www.jy.whzbtb.com'
        self.fh = filehandler
        self.keys = [k.decode('utf-8') for k in keys]
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)

    def write_html(self,prjName,urlstr):
        self.fh.write('<a href="'+urlstr+'" target="_blank" title="">')
        self.fh.write('<font size="5">'+ prjName + '</font></a><p></p>\n')


    def getpage(self, pageno):
        values = {'page': pageno, 'rows': '10', 'prjName': '', 'evaluationMethod': '', 'prjbuildCorpName': '',
                  'registrationId': '',
                  'noticeStartDate': begintime, 'noticeEndDate': ''}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'application/json, text/javascript, */*; q=0.01',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   'Accept-Encoding': 'gzip,deflate',
                   'Referer': 'http://www.jy.whzbtb.com/V2PRTS/TendererNoticeInfoListInit.do',
                   'X-Requested-With': 'XMLHttpRequest',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        url = '/V2PRTS/TendererNoticeInfoList.do'
        httpClient = None
        params = urllib.urlencode(values)
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', url, params, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            headers = response.getheaders()
            # print headers
            page = ''
            for i in headers:
                if i == ('content-encoding', 'gzip'):
                    buf = StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    page = f.read()
                    break
            else:
                page = response.read()
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        return page

    def getcontext(self):
        p = 0
        while True:
            p += 1
            jdata = json.loads(self.getpage(p))
            rows_num = len(jdata['rows'])
            if rows_num == 0:
                break
            for i in range(rows_num):
                for key in self.keys:
                    prjName = jdata['rows'][i]['tenderPrjName']
                    if prjName.find(key) >= 0:
                        w_prjName = jdata['rows'][i]['noticeStartDate'].encode('gbk') + '  ' + prjName.encode('gbk')
                        w_url = 'http://www.jy.whzbtb.com/V2PRTS/TendererNoticeInfoDetail.do?id=' + jdata['rows'][i]['id']
                        write_html(self.fh,w_prjName,w_url )
                        print w_prjName
                        break

class HBBIDDING:
    def __init__(self, filehandler):
        self.sitename = u'湖北设备工程招标有限公司'
        self.hostname = 'www.hbbidding.com.cn'
        self.fh = filehandler
        self.curpage = 1
        self.overtime_count = 0
        write_jump(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
             #  'Accept-Encoding': 'gzip, deflate',
               'Referer': 'http://www.hbbidding.com.cn/zbgg.html'
               }

        url_path = '/zbgg/&FrontNews_list01-1355994659966_pageNo='+str(self.curpage)+'&FrontNews_list01-1355994659966_pageSize=20.html'
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', url_path, None, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            #headers = response.getheaders()
            page = response.read()
            #print page.decode('utf-8').encode('gbk', 'ignore')
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        return page

    def get_one_page_context(self, page):
        self.overtime_count = 0
        table_p = re.compile('<div id="FrontNews_list01-1355994659966"(.*?)<div class="pageJump">', re.S)
        table = re.search(table_p, page)
        #print table.group().decode('utf-8').encode('gbk', 'ignore')
        if table:
            items_p = re.compile('<div class="newstitle">(.*?)</div>', re.S)
            items = re.findall(items_p, table.group())  # 按条取出项目

            release_time_p = re.compile('\d\d\d\d-\d\d-\d\d', re.S)  # 取发布时间正则
            url_p = re.compile('href=\"(.*?)\"', re.S)                 # 取URL正则
            projectname_p = re.compile('title="(.*?)" target="_self">', re.S)  # 取项目名称正则
            #print len(items)
            for item in items:
                release_time = re.search(release_time_p, item)
                projectname = re.search(projectname_p, item)
                url = re.search(url_p, item)

                timestr = release_time.group()
                if timestr < begintime:
                    self.overtime_count += 1
                    if self.overtime_count < 10:
                        continue
                    else:
                        return -1
                print timestr + '************' + begintime
                prjName = projectname.group().replace('title="', '').replace('" target="_self">','').strip()
                urlstr = 'http://' + self.hostname + url.group().replace('href="', '').replace('"', '')
                for key in keys:
                    if prjName.find(key) >= 0:
                        write_html(self.fh,timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'),urlstr)
                        print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                        break
        return 0

    def get_all_context(self):
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)
        while self.curpage < 50:
            page = self.getpage()
            if self.get_one_page_context(page) == -1:
                break
            self.curpage += 1
            print self.curpage
        write_returnheader(self.fh)

class HSZTBZX:
    def __init__(self, filehandler):
        self.sitename = u'黄石公共资源交易中心'
        self.hostname = 'www.hsztbzx.com'
        self.fh = filehandler
        self.pageindex = 1
        self.overtime_count = 0      #公告项目发布时间晚于开始时间的条目的计数器
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   #  'Accept-Encoding': 'gzip, deflate',
                   'Referer': 'http://www.hsztbzx.com/BidNotice/zfcg/cggg?Length=7'
                   }

        url_path = '/BidNotice/zfcg/cggg?pageIndex=' + str(self.pageindex)
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('GET', url_path, None, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            # headers = response.getheaders()
            page = response.read()
            # print page.decode('utf-8').encode('gbk', 'ignore')
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        return page

    def get_one_page_context(self, page):
        table_p = re.compile('<div class="filter-content">(.*?)<nav style="text-align: center">', re.S)
        table = re.search(table_p, page)
        # print table.group().decode('utf-8').encode('gbk', 'ignore')
        if table:
            items_p = re.compile('<li>(.*?)</li>', re.S)
            items = re.findall(items_p, table.group())     # 按条取出项目

            release_time_p = re.compile('\d\d\d\d/\d\d/\d\d', re.S)  # 取发布时间正则
            url_p = re.compile('href=\"(.*?)\"', re.S)  # 取URL正则
            projectname_p = re.compile('title="(.*?)">', re.S)  # 取项目名称正则
            # print len(items)
            for item in items:
                release_time = re.search(release_time_p, item)
                projectname = re.search(projectname_p, item)
                url = re.search(url_p, item)

                timestr = release_time.group().replace('/','-')

                if  timestr < begintime:
                    if self.overtime_count < 40:   #连续40条时间小于开始时间，结束
                        self.overtime_count += 1
                        continue
                    else:
                        return -1
                else:
                    self.overtime_count = 0     #发现大于开始时间的条目，计数器复位0

                prjName = projectname.group().replace('title="', '').replace('">', '').strip()
                urlstr = 'http://' + self.hostname + url.group().replace('href="', '').replace('"', '')
                for key in keys:
                    if prjName.find(key) >= 0:
                        write_html(self.fh, timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'), urlstr)
                        print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                        break
                else:  print '   '+timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')

        return 0

    def get_all_context(self):
        while self.pageindex < 50:
            page = self.getpage()
            if self.get_one_page_context(page) == -1:
                break
            self.pageindex += 1
            print '           PageNum  '+ str(self.pageindex)

class XYSZTB:
    def __init__(self, filehandler):
        self.sitename = u'襄阳市公共资源交易中心'
        self.hostname = 'www.xysztb.gov.cn'
        self.fh = filehandler
        self.ViewState = ''
        self.pageindex = 1
        self.cookie = ''
        self.keys = [k.decode('utf-8').encode('gbk') for k in keys]
        write_header(self.fh, self.sitename.encode('gbk'), self.hostname)

    def getpage(self):
        values = {'__VIEWSTATE': self.ViewState,'__VIEWSTATEGENERATOR':'1EC70CCD', '__EVENTTARGET': 'MoreInfoList1$Pager',
                  '__EVENTARGUMENT': '%d' % self.pageindex}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   #'Accept-Encoding': 'gzip, deflate',
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Referer': 'http://www.xysztb.gov.cn/xyzbw/jyxx/002002/002002001/MoreInfo.aspx'}

        url_path = '/xyzbw/jyxx/002002/002002001/MoreInfo.aspx'
        params = urllib.urlencode(values)
        httpClient = None
        page = ''
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', url_path, params, headers)
            response = httpClient.getresponse()
            # print response.status
            # print response.reason
            #headers = response.getheaders()
            page = response.read()
            #print page
        except Exception, e:
            print e
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        return page

    def get_one_page_context(self, page):
        viewstat_p = re.compile('<input type="hidden" name="__VIEWSTATE"(.*?)/>', re.S)
        viewstat = re.search(viewstat_p, page)  # __VIEWSTATE
        if viewstat:
            self.ViewState = viewstat.group().replace('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE"',
                                                      '').replace('value="', '').replace('" />', '').strip()
        # print self.ViewState

        table_p = re.compile('<table cellspacing=(.*?)</table>', re.S)
        table = re.search(table_p, page)
        # print table.group()
        if table:
            items_p = re.compile('<tr valign="(.*?)</tr>', re.S)
            items = re.findall(items_p, table.group())  # 按条取出项目

            release_time_p = re.compile('\d\d\d\d-\d\d-\d\d', re.S)  # 取发布时间正则
            url_p = re.compile('href=\"(.*?)\"', re.S)  # 取URL正则
            projectname_p = re.compile('title="(.*?)">', re.S)  # 取项目名称正则

            for item in items:
                release_time = re.search(release_time_p, item)
                projectname = re.search(projectname_p, item)
                url = re.search(url_p, item)

                timestr = release_time.group()
                if timestr < begintime:
                    return -1
                prjName = projectname.group().replace('title="', '').replace('<font color=red>', '').replace('">',
                                                                                                             '').replace(
                    '</font>', '').strip()
                urlstr = 'http://' + self.hostname + url.group().replace('href="', '').replace('"', '')
                for key in self.keys:
                    if prjName.find(key) >= 0:
                        write_html(self.fh,timestr + '  ' + prjName,urlstr)
                        print timestr + '  ' + prjName
                        break
        return 0

    def get_all_context(self):
        page = self.getpage()
        while self.get_one_page_context(page) != -1:
            self.pageindex += 1
            page = self.getpage()


if __name__ == '__main__':
    CurTime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filehandler = file('bidding' + CurTime + '.html', 'a')
    filehandler.write('<a name="header"></a>')

    ccgp = CCGP_HUBEI(filehandler)
    hbggzy = HBGGZY(filehandler)
    hbbidding = HBBIDDING(filehandler)
    hongshan = HONGSHAN(filehandler)
    xinzhou = XINZHOU(filehandler)
    wehdz = WEHDZ(filehandler)
    wedz = WEDZ(filehandler)

    ccgp.get_all_context()

    hbggzy.get_all_context()

    hbbidding.get_all_context()

    hongshan.get_all_context()

    xinzhou.get_all_context()

    wehdz.get_all_context()

    wedz.get_all_context()

    filehandler.close()

'''
whzbtb = JY_WHZBTB(filehandler)
whzbtb.getcontext()

hsztbzx = HSZTBZX(filehandler)
hsztbzx.get_all_context()

xysztb = XYSZTB(filehandler)
xysztb.get_all_context()
'''

