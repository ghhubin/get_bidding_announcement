# -*- coding:utf-8 -*-
import urllib
import httplib
import re
import string
import datetime
import json
from StringIO import StringIO
import gzip

keys = ('审计', '造价', '第三方', '评估', '投资', '咨询', '中介','安装','来源')
ndaysago = 5

endtime = datetime.datetime.now().strftime("%Y-%m-%d")
begintime = (datetime.datetime.now() - datetime.timedelta(days=ndaysago)).strftime("%Y-%m-%d")


class CCGP_HUBEI:
    def __init__(self, filehandler):
        self.fh = filehandler
        self.pagesize = 50  # 15,25,50,100
        self.hostname = 'www.ccgp-hubei.gov.cn'

    def write_html(self,prjName,urlstr):
        self.fh.write('<a href="'+urlstr+'" target="_blank" title="">')
        self.fh.write('<font size="5">'+prjName+'</font></a><p></p>\n')

    def getpage(self, curpage):
        values = {'rank': '$rank', 'queryInfo.curPage': curpage, 'queryInfo.pageSize': self.pagesize,
                  'queryInfo.TITLE': '',
                  'queryInfo.FBRMC': '', 'queryInfo.GGLX': '招标公告', 'queryInfo.CGLX': '',
                  'queryInfo.CGFS': '', 'queryInfo.BEGINTIME1': begintime, 'queryInfo.ENDTIME1': endtime,
                  'queryInfo.QYBM': '', 'queryInfo.JHHH': ''}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   # 'Accept-Encoding': 'gzip, deflate',
                   'Referer': 'http://www.ccgp-hubei.gov.cn/fnoticeAction!listFNoticeInfos.action',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        httpClient = None
        params = urllib.urlencode(values)
        try:
            httpClient = httplib.HTTPConnection(self.hostname, 80, timeout=10)
            httpClient.request('POST', '/fnoticeAction!listFNoticeInfos.action', params, headers)
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
        return page

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
                for key in keys:
                    if prjName.find(key) >= 0:
                        w_prjName = timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                        self.write_html(w_prjName,urlstr)
                        print w_prjName
                        break

    def get_all_context(self):
        first_page = self.getpage(0)
        itemnum_p = re.compile('共(\d+)条记录', re.S)
        itemnum = string.atoi(re.search(itemnum_p, first_page).group().replace('共', '').replace('条记录', ''))
        self.fh.write(
            '<p>=============================================='+self.hostname+'==================================================</p>\n')
        print '\n=============================================='+self.hostname+'==================================================\n'
        if itemnum == 0:
            print '没有发现招标公告'
            return 0
        pagenum = itemnum / self.pagesize + 1
        curpage = 2
        self.get_one_page_context(first_page)
        while curpage <= pagenum:
            self.get_one_page_context(self.getpage(curpage))
            curpage += 1


class JY_WHZBTB:
    def __init__(self, filehandler):
        self.hostname = 'www.jy.whzbtb.com'
        self.fh = filehandler
        self.keys = [k.decode('utf-8') for k in keys]

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
        self.fh.write(
            '<p>=============================================='+self.hostname+'==================================================</p>\n')
        print '\n=============================================='+self.hostname+'==================================================\n'
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
                        self.write_html(w_prjName,w_url )
                        print w_prjName
                        break


class HBGGZY:
    def __init__(self, filehandler):
        self.hostname = 'www.hbggzy.cn'
        self.fh = filehandler
        self.ViewState = ''
        self.curpage = 1
        self.cookie = ''
        self.keys = [k.decode('utf-8').encode('gbk') for k in keys]
        self.CategoryIDs = [('004001006001', u'房建市政工程'), ('004001006002', u'交通工程'), ('004001006003', u'水利工程'),
                            ('004001006004', u'国土整治'), ('004001006005', u'其他项目'), ('004001006006', u'铁路工程')]

    def write_html(self,prjName,urlstr):
        self.fh.write('<a href="'+urlstr+'" target="_blank" title="">')
        self.fh.write('<font size="5">'+prjName+'</font></a><p></p>\n')

    def getpage(self, CategoryID):

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
            self.fh.close()
        finally:
            if httpClient:
                httpClient.close()
        for header_item in headers:
            if header_item[0] == 'set-cookie':
                self.cookie += (header_item[1] + ';')
        # print self.cookie
        return page

    def get_one_page_context(self, page):
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
                        self.write_html(timestr + '  ' + prjName,urlstr)
                        print timestr + '  ' + prjName
                        break
        return 0

    def get_all_context(self):
        self.fh.write(
            '<p>=============================================='+self.hostname+'==================================================</p>\n')
        print '\n=============================================='+self.hostname+'==================================================\n'
        for cid in self.CategoryIDs:
            self.fh.write('<p>-----------------' + cid[1].encode('gbk') + '------------------</p>\n')
            print '-----------------' + cid[1].encode('gbk') + '------------------\n'
            self.ViewState = ''
            self.curpage = 1
            self.cookie = ''
            page = self.getpage(cid[0])
            while self.get_one_page_context(page) != -1:
                self.curpage += 1
                page = self.getpage(cid[0])

class HBBIDDING:
    def __init__(self, filehandler):
        self.hostname = 'www.hbbidding.com.cn'
        self.fh = filehandler
        self.curpage = 1
        self.overtime_count = 0

    def write_html(self,prjName,urlstr):
        self.fh.write('<a href="'+urlstr+'" target="_blank" title="">')
        self.fh.write('<font size="5">'+prjName+'</font></a><p></p>\n')


    def getpage(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
             #  'Accept-Encoding': 'gzip, deflate',
               'Referer': 'http://www.hbbidding.com.cn/zbgg.html'
               }

        url_path = '/zbgg/&FrontNews_list01-1355994659966_pageNo='+str(self.curpage)+'&FrontNews_list01-1355994659966_pageSize=20.html'
        httpClient = None
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
                        self.write_html(timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore'),urlstr)
                        print timestr + '  ' + prjName.decode('utf-8').encode('gbk', 'ignore')
                        break
        return 0

    def get_all_context(self):
        self.fh.write(
            '<p>==============================================' + self.hostname + '==================================================</p>\n')
        print '\n==============================================' + self.hostname + '==================================================\n'
        while self.curpage < 50:
            page = self.getpage()
            if self.get_one_page_context(page) == -1:
                break
            self.curpage += 1
            print self.curpage

CurTime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filehandler = file('bidding' + CurTime + '.html', 'a')

ccgp = CCGP_HUBEI(filehandler)
ccgp.get_all_context()

whzbtb = JY_WHZBTB(filehandler)
whzbtb.getcontext()

hbggzy = HBGGZY(filehandler)
hbggzy.get_all_context()

hbbidding = HBBIDDING(filehandler)
hbbidding.get_all_context()

filehandler.close()

