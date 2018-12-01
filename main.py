# -*- coding: utf-8 -*-
#  python 3

import json
import time
import datetime
import random
import os
import re
import requests  
Proxies_POOLs =[]
count = 0  # 记录下载的图片数量

def init_proxiesPOOLs():
    #初始化IP代理池
    global Proxies_POOLs
    with open('./prxies_pools.csv','r') as f:
        contents = f.readlines()
        f.close()
    num = len(contents)
    for i in range(num):
        details = contents[i].split(',')
        proxy= {details[2].strip('\n') :"%s:%s"%(details[0],details[1])}
        Proxies_POOLs.append(proxy)     
    print ( Proxies_POOLs[32])

def get_OneProxy(): #返回一个 代理
    global Proxies_POOLs
    proxy_pools_length  = len(Proxies_POOLs)
    return Proxies_POOLs[random.randint(0,proxy_pools_length-1)]


#定义页面打开函数
def use_proxy(url):
    data = ''
    response = requests.get(url)
    if response.status_code == 200:
        data = response.content
    return data

#获取微博主页的containerid，爬取微博内容时需要此id
def get_containerid(url):
    data=use_proxy(url)
    content=json.loads(data).get('data')
    tabs = content.get('tabsInfo').get('tabs')
    for data in tabs:
        if(data.get('tab_type')=='weibo'):
            containerid=data.get('containerid')
    return containerid

def get_detailContent(detail_url):
    try:
        data=use_proxy(detail_url) 
        if not data.find('微博正文 - 微博HTML5版'):
            return '[该条已经被和谐咯] '
        content = json.loads(data).get('data')
        longTextContent=content.get('longTextContent')
        return longTextContent
    except Exception as e:
        print(e)
        return '[该条已经被和谐咯]'

def save_imgs_description(filename,content):
    if content.strip() != "":
        with open(filename,'a',encoding="utf-8") as fn:
            fn.write(content)
            fn.close()
            
def filter_Non_BMP_Characters(target):    
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
    name=target.translate(non_bmp_map)
    return name

def update_someDirs_Include_Hourses(parentdirname,new_parts):
    #判断是非有必要重命名更新 过去下载的包含 "**前" 的文件夹名为具体日期
    dp = os.listdir(parentdirname)
    for x in dp:
            #target = filter_Non_BMP_Characters(x)
            if target.find('小时前')!= -1 :
                    tempname_0 = target[0:target.find('小时前')-1]
                    tempname_1 = target[target.find('小时前')-1 :]
                    newdirname = parentdirname + '/' + new_parts + tempname_1
                    src = parentdirname + '/'+ x
                    os.rename(src,newdirname)
    
def download_pictures(data,dirName):
    global count
    try:
        try:
            curWeiboId = data["id"]
            img_text = ""                    
            pics = []
            pics = data.get("pics")
            pic_count = len(pics)
        except Exception as e:
            print(e)
            return
        
        print("发现微博中有 %s 图片------"%pic_count)
        create_at   = data["created_at"]
        if create_at.find("小时前") != -1 :
            before_hours = int( create_at.split("小")[0] )
            create_at = (datetime.datetime.now()+datetime.timedelta(hours= -before_hours )).strftime("%Y-%m-%d")
        else:
            year = time.strftime('%Y',time.localtime(time.time()))
            create_at = "%s-%s"%(year,create_at)
            
        for picIndex in range(pic_count):
            isLongText = bool(data.get('isLongText'))
            if (not isLongText):
                text=data.get('text')
            else:
                idstr = data.get('idstr')
                detail_url = 'https://m.weibo.cn/statuses/extend?id='+str(idstr)
                text = get_detailContent(detail_url)
            picDirShort = ""
            if len(text)<1:
                text = " "
                img_text = text
            if len(text) > 20:
                img_text = text  
                text = text[0:20].strip()                                
            picDirShort = re.sub('[\/:*?"<>|]','_',text).replace(" ","")                            
            picDirName = u"%s/%s_%s"%(dirName,create_at,picDirShort) 
            #创建次级目录用于保存 该条微薄中所有图片
            if not os.path.exists(picDirName):
                os.mkdir(picDirName)
            
            pic_descriptions = "%s/描述.txt"%picDirName
            save_imgs_description(pic_descriptions,img_text)
            
            cur_pid = pics[picIndex]["pid"]
            cur_pic_large_url = pics[picIndex].get("large")["url"]
            cur_pic_extensionName = cur_pic_large_url.split(".")[-1]
            cur_pic_Name = cur_pic_large_url.split("/")[-1]
            picName = u"%s/%s.%s"%(picDirName,cur_pid,cur_pic_extensionName)
            if os.path.exists(picName):
                print("当前文件已存在!")
                continue
            
            print(u"开始下载 %s    :  第%s张图片"%(picDirShort,picIndex+1))
            stime = time.perf_counter()
            print(u"%s downloading ......"% datetime.datetime.now().strftime('[%H:%M:%S]'))
    ##                            print(u"%s"%picName)
            print("%s"%cur_pic_large_url)                            
            response = requests.get(cur_pic_large_url)
            if response.status_code == 200:
                fn = picName
                with open( fn , 'wb') as f:  # 以二进制写入到本地
                    f.write(response.content)
                    f.close()              
            etime = time.perf_counter()
            times = etime - stime
            print(u"%s downloaded  耗时: %.2f 秒\n"% (datetime.datetime.now().strftime('[%H:%M:%S]'),times))
            count = count + 1    #下载总数
            
    except Exception as e:
        print(e)
            
    
def get_weiboAllPictureByUID(id):
    global count
    i=1
    while True:
        url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id
        weibo_url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id+'&containerid=' + get_containerid(url) + '&page='+str(i)
        print(url)
        print( weibo_url)
        #return
        try:
            data=use_proxy(weibo_url)
            content = json.loads(data).get('data')            
            cards=content.get('cards')
            cards_len = len(cards)
            print("cards_len=%s"%cards_len)
 
            if(cards_len>0):
                #创建 目录
                mblog0 = cards[0].get("mblog")
                user = mblog0.get("user")
                screen_name = user["screen_name"].strip().replace(" ","")
                description = re.sub('[\/:*?"<>|，：、“”]','_',user["description"]).replace(" ","")
                dirName =  u"%s/%s_%s"%(os.curdir,id,screen_name)
                print ("dirName=%s"%dirName)
                if not os.path.exists(dirName):
                    os.mkdir(dirName)
                
                for j in range(cards_len):                     
                    print("\n-----正在探测第"+str(i)+"页，第"+str(j+1)+"条微博中图片信息------")
                    card_type=cards[j].get('card_type')
                    if(card_type==9):
                        mblog=cards[j].get('mblog')                        
                        if "pics" not in mblog:
                            print("-----当前微博中没有  原创图片")
                            if "retweeted_status" in mblog:
                                print("发现  转载图片")
                                download_pictures(mblog.get("retweeted_status"),dirName)
                                print(">    >>     >>>     >>>>  ")
                            else:
                                continue
                        else:                          
                            download_pictures(mblog,dirName)                        
                            print("+  ++  +++   ++++")
            else:
                pass
            
            i+=1
            if( i%12 == 0):
                sleeptime = random.randint(1,5)
                time.sleep(sleeptime)
                
        except Exception as e:
            print(e)
            pass

    print('>>>>>>>>>>>>>>>>>>>')
    print('共计：%s'%count)

def main():
    init_proxiesPOOLs()
    uid_list = ['3942238643']
    for uid in id_list: 
        get_weiboAllPictureByUID(uid)

    
if __name__=="__main__":
    main()



    

