#coding=utf-8
import re
import requests
import urllib
#编码相关库chardet
import chardet
import jieba.analyse
import time

#判断一个unicode是否是英文字母
def is_alphabet(uchar):
    if(uchar >= u'\u0041' and uchar<= u'\u005a') or (uchar >= u'\u0061' and uchar<= u'\u007a'):
        return True 
    else: 
        return False 


#获取淘宝商品页面的交易成功额（淘宝只保留30天内的交易额）
def count_sold(url,headers):
    req = requests.get(url)
    #print req.text
    #找到sibUrl，因为淘宝上的价格、累计评论、交易成功等面板数据是由js获取的，是根据这个地址get到的
    pattern = 'sibUrl\s+:\s\'(.*?)\','
    jsurl = re.findall(pattern,req.text,re.S)
    #print jsurl[0]
    jsdata = requests.get('https:'+jsurl[0]+'&callback=onSibRequestsSuccess',headers=headers)
    #print jsdata.text
    pattern = r'"soldQuantity":\{"confirmGoodsCount":\d+,"soldTotalCount":(\d+)\}'
    soldTotalCount_30 = re.findall(pattern,jsdata.text,re.S)
    print u'该店铺30天内交易额为:' + soldTotalCount_30[0]


#百度的图片搜索
'''
百度上传图片时，会根据图片的名字拼接网址，然后往该网址上POST图片
抓包时发现其后面的参数lastModifiedDate和size不影响获取，故不管
'''
url = 'https://sp1.baidu.com/70cHazva2gU2pMbgoY3K/n/image?fr=psindex&target=pcSearchImage&needJson=true&id=WU_FILE_0&name=card100001499_1.jpg&type=image/jpeg'
files = {
    'image':('card100001499_1.jpg',open('card100001499_1.jpg','rb'),'image/jpeg')
    }
r = requests.post(url,files=files)
#该网址会返回该图片搜索页的地址，其中queryImageUrl为上传的图片资源的地址
#print r.text
pattern = r'"pageUrl":"(.*?)"}'
reurl = re.findall(pattern,r.text,re.S)
#print reurl[0]
#处理转义字符'\'
reurl[0] = reurl[0].replace('\\','')
#print reurl[0]
#转换url编码（%3A,%2F）
surl = urllib.unquote(reurl[0])
print surl
k = requests.get(surl)
#print k.text

'''
#图片来源的地址关键字为source-card-topic-same-image
#根据图片来源页面的title来获取关键字
pattern = r'<a href="(http://.*?)" target="_blank" class="source-card-topic-same-image"'
rpurl = re.findall(pattern,k.text,re.S)
print rpurl

tkeyword = ''
for i in rpurl:
    pattern = r'<title>(.*?)</title>'
    
    #此处如果用requests库来获取源码的话，输出的title会出现乱码
    #并且用chardet库获取字符串的编码方式时会报错，故用urllib库来获取
    
    #j = requests.get(i)
    #page = j.text
    page = urllib.urlopen(i).read()
    keyword = re.findall(pattern,page,re.S)
    print keyword[0]
    charset = chardet.detect(keyword[0])
    print charset
    if charset['encoding'] == 'GB2312':
        keyword[0] = keyword[0].decode('gb2312').encode('utf-8')
    tkeyword = tkeyword + keyword[0]
list = jieba.analyse.extract_tags(tkeyword,topK=20,withWeight=False,allowPOS=())
tbkeyword = ''
for j in range(0,3):
    print list[j]
    tbkeyword = tbkeyword + list[j]+' '
print tbkeyword
'''

#根据图片搜索页的title来获取关键字（但同一张图片上传结果可能不一样）
tkeyword = ''
pattern = r'<a class="source-card-topic-title-link".*? target="_blank" >(.*?)</a>'
keyword = re.findall(pattern,k.text,re.S)
for i in keyword:
    #print i
    #<strong> </strong>间的内容为百度图片搜索后根据"对该图片的最佳猜测"所加红的内容
    i = i.replace('<strong>','')
    i = i.replace('</strong>','')
    print i
    tkeyword = tkeyword + i
#print tkeyword
#jieba分词，且按词频由高到低排序
list = jieba.analyse.extract_tags(tkeyword,topK=20,withWeight=False,allowPOS=())

'''
for i in list:
    print i
'''

#将词频最高的三个词当做关键词，且筛选掉英文的关键词
tbkeyword = ''
count = 0
for i in list:
    #print i
    for k in i:
        if is_alphabet(k):
            #print u'英文结果，排除'
            break
        else:
            tbkeyword = tbkeyword + i + ' '
            #print u'中文结果'
            count = count + 1
            break
    if count == 3:
        break
print tbkeyword


#因为淘宝可以直接在网址拼接处用-进行筛选，故无需在后面用正则表达式对搜索结果进行筛选
tbkeyword = tbkeyword + u'-中文 -ZZ -高桥 -游戏王卡组 -单卡'
print tbkeyword
payload = {'q':tbkeyword}
l = requests.get('https://s.taobao.com/search',params=payload)
#print l.text


#为提高准确性，决定将图片POST往淘宝上，并将结果进行比较
files ={
    'cross':(None,'taobao'),
    'type':(None,'iframe'),
    'imgfile':('card100001499_1.jpg',open('card100001499_1.jpg','rb'),'image/jpeg'),
    }
#发送multipart/form-data请求
sk = requests.post('https://s.taobao.com/image',files=files)
#print sk.text
#该页面包含有上传的图片在淘宝上的名字，知道该名字才能向淘宝请求返回页面
pattern = '"name":"(.*?)","url"'
s = re.findall(pattern,sk.text,re.S)
tfsid = s[0]
#获取当天时间，因为'initiative_id'需要知道当天时间
date = time.strftime('%Y%m%d',time.localtime(time.time()))
payload = {
    'commend':'all',
    'ssid':'s5-e',
    'search-type':'item',
    'sourceId':'tb.index',
    'spm':'a21bo.50862.201856-taobao-item.2',
    'ie':'utf8',
    'initiative_id':'tbindexz_' + date,
    'tfsid':tfsid,
    'app':'imgsearch',
    #'cat'为88888888时即搜索结果显示的是其他类,为22时即搜索结果显示的是数码类等等
    #注：当不指明cat值时，淘宝会根据其所认为的最接近的类来显示，可能是数码类等等，然而游戏王卡归类为其他类
    'cat':'88888888'
    }
r = requests.get('https://s.taobao.com/search',params=payload)
#print r.text

#将您可能会喜欢的筛选掉，其中第一个"auctions"包含的是外观相似宝贝，第二个"auctions"包含的是您可能会喜欢
pattern = r'("title":"外观相似宝贝".*?"title":"您可能会喜欢")'
retain = re.findall(pattern,r.text,re.S)
pattern = r'"raw_title":"(.*?)","pic_url"'
tbtitle = re.findall(pattern,l.text,re.S)
for k in tbtitle:
    #print k
    if (u'zz' in k) or (u'中文' in k) or (u'高桥' in k) or (u'卡组' in k) or (u'单卡' in k):
        pass
    else:
        list = k.split()
        if len(list) == 1:
            pass
        else:
            for blank in list:
                print blank
            print '____________'
    

#注：此处获取到的网页源码和浏览器中的不尽相同，顺序也与浏览器中的不同，原因不明
'''
pattern = r'"raw_title":"(.*?)","pic_url"'
tbtitle = re.findall(pattern,l.text,re.S)
for tt in tbtitle:
    print tt
    pattern = r'"raw_title":"'+tt+'","pic_url":".*?","detail_url":"(.*?)"'
    murl = re.findall(pattern,l.text,re.S)
    print murl
'''
#需要筛选掉"根据上面的商品结果，为你推荐的相似商品"这部分的商品，不过一刀切可能有问题
#其中"auctions"包含的就是搜索到的商品，而"recommendAuctions"包含的是根据上面结果推荐的商品
pattern = r'("auctions":.*?"recommendAuctions")'
retain = re.findall(pattern,l.text,re.S)

pattern = r'"raw_title":.*?,"detail_url":"(.*?)"'
murl = re.findall(pattern,retain[0],re.S)
#print murl

headers = {
    'Referer':'https://item.taobao.com/item.htm?spm=a230r.1.14.86.t3CiML&id=41642057442&ns=1&abbucket=11',
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36'
    }
for g in murl:
    #筛选掉天猫和一些奇怪的东西
    http = 'https'
    tianmao = 'tmall'
    #用in来判断字串
    ishttp = http in g
    istmall = tianmao in g
    if ishttp or istmall:
        pass
    else:
        g = 'https:' + g
        g = g.replace('\\\\','\\')
        #将Unicode编码转换成符号
        g = g.decode('unicode-escape')
        print g
        count_sold(g,headers)
