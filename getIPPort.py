#!/usr/bin/evn python
# coding:utf-8

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import sys
import getopt

keydics = {'http':['',None],'mongod':['',None]}    #存放输出文件名,和打开文件的句柄

def open_output_files(str):
    for key in keydics:
        keydics[key][0] = xml_filename + '.' + key
        keydics[key][1] = file(keydics[key][0], 'w')

def close_output_files():
    for key in keydics:
        keydics[key][1].close()

if __name__ == "__main__":
    msg = '''
Usage: python getipport.py -x nmap-outpot.xml
'''
    if len(sys.argv) < 3:
        print msg
        sys.exit(-1)
    try:
        options, args = getopt.getopt(sys.argv[1:], "x:")
        xml_filename = ''
        for opt, arg in options:
            if opt == '-x':
                xml_filename = arg
    except Exception, e:
        print msg
        exit(-3)

    open_output_files(str)

    try:
        tree = ET.parse(xml_filename)  # 打开xml文档
        root = tree.getroot()  # 获得root节点
    except Exception, e:
        print "Error:cannot parse file:.xml."
        close_output_files()
        sys.exit(-2)
    for host in root.findall('host'):  # 找到root节点下的所有host节点
        try:
            addr = host.find('address').get('addr')  # 子节点下节点address的值
            state = host.find('status').get('state')  # 子节点下属性name的值
            if state != 'up':
                continue
            ports = host.find('ports')
        except Exception, e:
            continue
        for port in ports.findall('port'):
            try:
                p = port.get('portid')
                pstate = port.find('state').get('state')
                service = port.find('service').get('name')
            except Exception, e:
                continue
            if pstate != 'open':
                continue
            for key in keydics:
                if service.find(key) >= 0:
                    if key == 'http':
                        if service.find('https') >= 0:
                            keydics[key][1].write('https://' + addr + ':' + p + '/\n')
                        else:
                            keydics[key][1].write('http://'+addr+':'+p+'/\n')
                    elif key == 'mongod':
                        keydics[key][1].write(key+ '  ' + addr + ' ' + p + '\n')
    close_output_files()