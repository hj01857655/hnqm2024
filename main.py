import requests
from loguru import logger
from bs4 import BeautifulSoup
import time
import re
import random
import configparser
import json
from urllib.parse import unquote
import hashlib
import threading
from datetime import datetime
import math
import numbers
import re
class QingMaLearningSystem:
    #初始化
    def __init__(self):
        
        self.session = requests.Session()
        #必修和选修学习情况,默认获取全部
        self.HOST = "https://hnqmgc.17el.cn"
        self.BBS_HOST = "https://qmbbs.17el.cn"
        self.lastCourseType=1
        #培训结果:未结业,已结业
        self.pptView=False
        self.navigator={
            "userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
        }
        self.player={id:"#normalModel_video","autoplay":True}
        self.loadMsg = "正在初始化视频信息，请稍候 ..."
        self.currentSelectId=None;
        self.isLearnOver=False
        self.enabledDragging=False
        self.gkyxsj=0
        self.timestamp=int(datetime.now().timestamp() * 1000)  # 转换为毫秒
        self.pathSource = []
        self.info={}
        self.pptSource = []
        self.isFirstTime=True
        self.next_id=0
        self.timeS=0
        self.timea=0
        self.currentKcId=""
        self.currentZid=""
        self.currentJid=""
        self.currentGkyxsj=0
        self.currentKczsc=0
        self.currentItem=None
        self.first=True
        self.currentTemp=0
        self.tipsGap=5
        self.ct=60
        self.timeSS=0
        self.timePP=0
        self.onlyOne=0
        self.tmpOnlyOne=0
        self.pptdz=""
        self.currentBFSJ = 0
        self.currnetPptIndex=-1
        self.currnetPptImg1=""
        self.currnetPptImg2=""
        self.isNextPlayer=False
        self.gkyxsj=0
        self.timestamp=int(datetime.now().timestamp() * 1000)  # 转换为毫秒
    
    def cydl_get_captcha(self):
        # 模拟获取验证码的过程
        number1 = ''.join(str(random.randint(0, 9)) for _ in range(4))
        color = '#' + ''.join(str(random.randint(0, 9)) for _ in range(6))
        logger.info(f"验证码: {number1}, 背景色: {color}")
        # 在实际应用中，这里可以更新页面或数据库中的验证码信息
        return number1
    #登录
    def do_login(self, username, password):
        vcode = self.cydl_get_captcha()
        if not vcode:

            logger.error("无法获取验证码，登录中止")
            return

        url = f"{self.HOST}/api/schoolHomeAction_login_index.action"
        data = {
            "yhzh": username,
            "yhmm": password,
            "vcodekey": "",  # 默认"",
            "vcode": vcode,  # 验证码从页面获取
        }

        response = self.session.post(url, data=data)
        if response.status_code == 200:
            msg = response.json()
            if 'errorNum' in msg:

                if 'msg' in msg['errorNum']:
                    msg['errorNum']['xm'] = unquote(msg['errorNum']['xm'])
                    logger.success(f"登录成功，用户名: {unquote(msg['errorNum']['xm'])}")
            #定期更新

            with open('login.json', 'w',encoding='utf-8') as f:
                json.dump(msg, f,ensure_ascii=False)
            # 更新session的cookies
            self.session.cookies.update(response.cookies)


        else:
            logger.error(f'登录失败，状态码: {response.status_code}')
    #获取个人信息和学习信息
    def load_person_info(self) -> tuple:
        url = f"{self.BBS_HOST}/personalData.shtml?param=125,1"
        try:
            response = self.session.get(url, cookies=self.session.cookies)
            if response.status_code == 200:
                result = response.json()
                if 'resultData' in result:
                    data = result['resultData']
                    courses_num = data.get('CoursesNum', '0/0')
                    course_xx_num = data.get('courseXXNum', '0/0')

                    logger.info(f"必修课程进度: {courses_num}, 选修课程进度: {course_xx_num}")
                else:
                    logger.warning("响应中缺少预期的字段")
            else:
                logger.error(f"获取(个人信息)失败,状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"获取(个人信息)过程出错:{e}")

        return courses_num,course_xx_num
        # 返回默认值以防止错误
    #切换课程类型

    def init(self):
        while True:
            courses_num, course_xx_num = self.load_person_info()
            
            # 检查必修和选修课程是否全部完成
            if courses_num == '20/20' and course_xx_num == '20/20':
                logger.info("必修和选修课程已全部完成，退出")
                break
            
            # 加载未完成的课程信息
            course_type = 1 if courses_num != '20/20' else 2
            unlearn_courses = self.load_learn_info_data(course_type)
            for course in unlearn_courses:
                self.goPlayCourse(course['id'])

    

    def timeHandler(self,player):
        if(self.currentItem)!=None:
            self.currentGkyxsj=self.currentItem['gkyxsj']
        else:
            self.currentGkyxsj=0
        self.currentKczsc=self.currentItem['spzsj']
        currentTime=player['currentTime']
        if(currentTime!=self.timePP):
            self.timePP=currentTime
            self.checkChangePpt()
        self.onlyOne=self.tmpOnlyOne
        if(self.first):
            player['currentTime']=self.currentGkyxsj//1000
            self.currentTemp=self.currentGkyxsj//1000
            self.first=False
        else:
            if(self.currentItem!=self.currentKczsc and self.currentKczsc>self.currentGkyxsj):
                if(self.currentItem['process']!=100 and self.currentTemp+5<=currentTime):
                    player['currentTime']=self.currentTemp
                    return
            else:
                if(self.currentItem['process']!=100 ):
                    player['currentTime']=self.currentTemp
                    return
                self.currentTemp=currentTime
                if(currentTime%self.ct==0 and currentTime!=0 and currentTime!=int(self.currentGkyxsj//1000)):
                    if(currentTime!=self.timea):
                        self.start_video_heartbeat(self.currentKcId,self.currentZid,self.currentJid,self.currentGkyxsj-self.ct,currentTime,self.currentKczsc)
                        self.timea=currentTime
                if(currentTime!=self.timeSS):
                    self.timeS=currentTime
                    currentTotal=int(self.currentGkyxsj//1000)
                    if(currentTime==currentTotal):
                        self.start_video_heartbeat(self.currentKcId,self.currentZid,self.currentJid,self.currentGkyxsj-self.ct,self.currentKczsc)
                        self.currentFinish()
                        self.timea=currentTime
        if(currentTime['process']>=100):
            self.onlyOne=1
        if(self.onlyOne==0):
            if(currentTime!=self.timeSS and currentTime%self.tipsGap==0):
                self.timeSS=currentTime
                self.get_tips(self.currentJid,'125')
    #加载学习信息数据
    def load_learn_info_data(self, course_type: int):
        url = f"{self.BBS_HOST}/learnInfoData.shtml"
        data = {
            "type": course_type,
            "name": ""  # 假设课程名称为空，或根据需要设置
        }
        unlearn_course_list = []
        try:
            response = self.session.post(url, data=data)
            if response.status_code == 200:
                result = response.json()
                if 'resultList' in result:
                    data = result['resultList']
                    for item in data:
                        # 只添加未完成的课程, gkjd != "100%" 表示未完成
                        if item['gkjd'] != "100%":
                            unlearn_course_list.append(item)
                    logger.info(f"未完成课程: {unlearn_course_list}")
                    return unlearn_course_list
                else:
                    logger.warning("响应中缺少预期的字段")
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"请求出错: {e}")
        return unlearn_course_list

    
    #获取在线课程信息
    def load_online_course_data(self, courseType: int):
        page = 1
        courses_info = []
        while True:
            url = f"{self.BBS_HOST}/onlineCourse=125_-1___0_{courseType}_{page}.shtml"
            try:
                response = self.session.get(url, cookies=self.session.cookies)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    courses_div = soup.find('div', class_='clear', id='courses')
                    if courses_div:
                        course_list = courses_div.find_all('div', class_='kclist')
                        course_details = courses_div.find_all('div', class_='kcxx')

                        if not course_list:
                            logger.info("没有更多课程信息")
                            break

                        for course, detail in zip(course_list, course_details):
                            # 提取课程名称
                            kcmc = course.find('div', class_='kcmc')
                            course_name = kcmc.get_text(strip=True) if kcmc else '未知课程'

                            # 提取课程类别
                            category_div = detail.find('div', title=True)
                            course_category = category_div.get('title', '未知类别').replace('-', '').strip() if category_div else '未知类别'

                            # 找到.xx并提取onclick属性中的课程ID
                            xx = course.find('div', class_='xx')
                            if xx:
                                input_tag = xx.find('input')
                                if input_tag:
                                    onclick = input_tag.get('onclick', '')
                                    course_id_match = re.search(r"detail\('(\d+)'", onclick)
                                    course_id = course_id_match.group(1) if course_id_match else '未知ID'
                                else:
                                    course_id = '未知ID'
                            else:
                                course_id = '未知ID'
                            courses_info.append({
                                "课程名称": course_name,
                                "类别": course_category,
                                "课程ID": course_id,

                            })
                            return courses_info

                            logger.info(f"课程名称: {course_name}, 类别: {course_category}, 课程ID: {course_id}")


                    else:
                        logger.warning("未找到课程信息的div")
                        break
                else:
                    logger.error(f"请求失败，状态码: {response.status_code}")
                    break

                page += 1  # 增加页码以请求下一页
            except Exception as e:
                logger.error(f"load_online_course_data请求出错: {e}")
                break

        # 将所有课程信息写入JSON文件
        with open('online_courses.json', 'w', encoding='utf-8') as f:
            json.dump(courses_info, f, ensure_ascii=False, indent=4)
    
    #进入课程学习页面
    def goPlayCourse(self, kcid: str):
        url = f"{self.BBS_HOST}/coursePlay_125_{kcid}.shtml"
        logger.info(f"进入课程播放页面: {url}")
        try:
            response = self.session.get(url, cookies=self.session.cookies)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                iframe = soup.find('iframe', id='learnIframe')
                if iframe:
                    iframe_src = iframe.get('src')
                    logger.info(f"课程 {kcid} 的 iframe src: {iframe_src}")
                    
                    # 视频类型
                    if "play_125" in iframe_src:
                        logger.info(f"视频类型的课程src: {self.BBS_HOST+iframe_src}")
                        response = self.session.get(self.BBS_HOST+iframe_src, cookies=self.session.cookies)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            player = soup.find('div', id='PPTModel_video')
                            if player:
                                logger.info("正常进入视频页面")
                                item_list, info = self.getCourseInfo(kcid)
                                self.pathSource=item_list
                                self.info=info
                                for item in self.pathSource:
                                    self.currentItem=item
                                    #已学完的小节不要学习
                                    if item['gkyxsj'] == item['spzsj']:
                                        logger.info(f"小节: {item['mc']} 已完成，跳过")
                                        continue
                                    else:
                                        logger.info(f"开始学习小节: {item['mc']} (ID: {item['id']})")
                                        
                                        #简短写法,如果node['gkyxsj']为空,self.gkyxsj=0,否则self.gkyxsj=node['gkyxsj']
                                        self.gkyxsj = 0 if item['gkyxsj'] == "" else item['gkyxsj']
                                        #将gkyxsj转为秒提交
                                        self.start_video_heartbeat(self.info['kcid'], item['fid'], item['id'], self.gkyxsj//1000 , item['spzsj'])
                                        break  # 只学习第一个未完成的小节
                                    
                            else:
                                logger.warning("视频通道被占用，稍后重试")
                                for i in range(10, 0, -1):
                                    logger.info(f"倒计时: {i}秒")
                                    time.sleep(1)
                                self.goPlayCourse(kcid)
                else:
                    logger.warning(f"找到一个提示通道被占用的div，稍后重试")
                    #倒计时
                    for i in range(10, 0, -1):
                        logger.info(f"倒计时: {i}秒")
                        time.sleep(1)
                    self.goPlayCourse(kcid)
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"请求出错: {e}")

    
        def get_article_course_info(self, kcid: str, y: str):
        url = f"https://qmbbs.17el.cn/hnlgbAction_getCourseInfo.action"
        params = {
            "kcid": kcid,
            "y": y,
            "isAddDjl": "1"
        }
        
        try:
            response = self.session.get(url, params=params, cookies=self.session.cookies)
            if response.status_code == 200:
                result = response.json()
                if 'map' in result:
                    info = result['map'].get('info', {})
                    currnetChilds = result['map'].get('currnetChilds', [])
                    
                    # 处理课程信息
                    logger.info(f"课程信息: {info}")
                    
                    # 检查当前子节点
                    if currnetChilds:
                        zid = currnetChilds[0].get('fid')
                        jid = currnetChilds[0].get('id')
                        return zid, jid
                    
                    # 检查学习进度
                    if info.get('gkjd') == '100%':
                        logger.info("课程已完成")
                    else:
                        logger.info("课程未完成")

                else:
                    logger.warning("响应中缺少预期的字段")
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"get_article_course_info请求出错: {e}")
    
    #如果是文章类型,直接提交
    def post_article_progress(self, kcid: str, y: str, zid: str, jid: str):
        url = f"https://qmbbs.17el.cn/hnlgbAction_postProgress.action"


        params = {
            "kcid": kcid,
            "y": y,
            "xtid": "12",
            "zid": zid,
            "jid": jid
        }
        
        try:
            response = self.session.get(url, params=params, cookies=self.session.cookies)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    logger.success("提交成功")
                    # 如果有需要隐藏的按钮或其他操作，可以在这里处理
                else:
                    logger.error("提交失败")
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"post_article_progress请求出错: {e}")
    
    '''
    获取课程信息
    请求方式:POST
    参数:#kcId:课程ID
    {
        "kcId": kcId 
    }
    响应:#nodeList:节点列表
        
    {
        "nodeList": [
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": 900005,
            "mc": "第一节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-b5090124-70e5-47b5-9d8a-2fce8c9590d7.mp4",
            "id": 27839,
            "spzsj": 900005,
            "xgsj": 1739224907267,
            "xt_id": 12
            },
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第二节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-653fa09e-3f95-4d58-b814-82f48174c437.mp4",
            "id": 27843,
            "spzsj": 900005,
            "xt_id": 12
            },
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第三节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-feecbbe3-afea-4353-a755-35751cf39025.mp4",
            "id": 27847,
            "spzsj": 900005,
            "xt_id": 12
            },
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第四节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-0bae3c17-e995-4d08-b7fa-bd8f39ff71fb.mp4",
            "id": 27851,
            "spzsj": 900005,
            "xt_id": 12
            },
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第五节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-c06a6a8d-c859-41fc-a7d8-f190143f3580.mp4",
            "id": 27855,
            "spzsj": 900005,
            "xt_id": 12
            },
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第六节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-7ee2ae03-c0e7-4c81-bbc0-4e9cea80ab39.mp4",
            "id": 27859,
            "spzsj": 900005,
            "xt_id": 12
            },
            {
            "zsj": "00:15:00.05",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第七节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-8bb79187-f6cf-4657-96e2-e1c57cb0a935.mp4",
            "id": 27863,
            "spzsj": 900005,
            "xt_id": 12
            },
            {
            "zsj": "00:14:11.61",
            "fid": 27835,
            "gkyxsj": "",
            "mc": "第八节",
            "spdz": "http://hnqmgccdn.17el.cn/hnqmzx/media/media/qmzx_tyy/zm-6097516b-4113-49d7-a757-1511d863edce.mp4",
            "id": 27867,
            "spzsj": 851061,
            "xt_id": 12
            }
        ],
        "status": 1,
        "info": {
            "kcid": 6355,
            "pxstate": "0",
            "pfstate": "0",
            "mycourseid": 3429288,
            "byzd2": 7106096,
            "byzd1": 1406695,
            "gkjd": "14%",
            "zystate": "0",
            "xkzt": "2",
            "isVr": false,
            "kjlx": 1,
            "ztzystate": "0",
            "pcid": 127,
            "kcmc": "切实掌握马克思主义基本理论这一看家本领"
        }
    }
    '''
    #视频类型中:获取课程信息https://qmbbs.17el.cn/personal_getCourseInfo.action
    #获取当前课程信息
    def getCourseInfo(self, kcId: str):
        url = f"{self.BBS_HOST}/personal_getCourseInfo.action"
        data = {
            "kcId": kcId
        }
        try:
            response = self.session.post(url, data=data, cookies=self.session.cookies)
            if response.status_code == 200:
                result = response.json()
                if 'nodeList' in result and 'info' in result:
                    self.pathSource = result['nodeList']  # 将 nodeList 赋值给 pathSource
                    info = result['info']
                    self.isLearnOver=True
                    return self.pathSource, info
                else:
                    logger.warning("响应中缺少预期的字段")
            else:
                logger.error(f"获取课程信息失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"getCourseInfo请求出错: {e}")
    def tipsLearnInfo(self,list,isVr):
        lastLearnDate=None
        k=-1,x=0
        for i,item in enumerate(list):
            zsj=item['zsj']
            zsjArr=[]
            if zsj:
                zsjArr=zsj.split(":")
            else:
                zsjArr=[0]
            zsjNum=0
            if len(zsjArr)==1:
                zsjNum=zsjArr[0]*1000
                break
            elif len(zsjArr)==2:
                zsjNum=zsjArr[0]*60*1000+zsjArr[1]*1000
                break
            elif len(zsjArr)==3:
                miao=int(zsjArr[2][:zsjArr[2].find(".")])
                
                hm=zsjArr[2][zsjArr[2].find('.') + 1:]
                #如果hm不为空且hm长度大于0,则将hm转为int
                if hm and len(hm)>0:
                    hm=int(hm)
                zsjNum=zsjArr[0]*60*60*1000+zsjArr[1]*60*1000+miao*1000+hm
                logger.info(f"小节时长: {zsjNum}")
                break

            item['spzsj']=zsjNum
            if item['gkyxsj']=="":
                item['gkyxsj']=0
            item['process']=int(item['gkyxsj']/item['spzsj']*100)
            #如果process isNaN,则设置为0
            if math.isnan(item['process']):
                item['process']=0
            #如果process大于98,则设置为100
            if item['process']>98:
                item['process']=100
            if item['xgsj']==None:
                item['xgsj']=0
            if item['process']<100:
                self.isLearnOver=False
            if item['process']==100:
                continue
            #如果lastLearnDate为空,则设置为item['xgsj'],k设置为i
            if lastLearnDate==None:
                lastLearnDate=item['xgsj']
                k=i
            #如果lastLearnDate不为空,则比较lastLearnDate和item['xgsj']
            if lastLearnDate!=None:
                if lastLearnDate<item['xgsj']:
                    lastLearnDate=item['xgsj']
                    k=i
            else:
                if item['xgsj']>self.lastLearnDate:
                    k=i
                    self.lastLearnDate=item['xgsj']
        self.pathSource=list
        for i,item in enumerate(self.pathSource):
            percent=item['process']
        if k==-1:
            k=0
        if isVr:
            self.openVrApp(self.pathSource[k]['kcId'],self.pathSource[k]['id'])
    def openVrApp(self,kcId:str,jid:str):
        url=f"{self.BBS_HOST}/personal_yyzAppURL.action"
        data={
            "kcId":kcId,"siteId": "125","jid":jid
        }
        result=self.post(url,data=data)
        
    #视频类型中:获取当前节的播放信息
    def getPlayerInfo(self, jid: str, ocid:int=0):
        url = f"{self.BBS_HOST}/personal_getPlayerInfo.action"
        data = {
            "nodeId": jid,#节点ID
            "siteId": "125",#站点ID
            "nodeId2": ocid#节点ID2
        }
        
        try:
            response = self.session.post(url, data=data, cookies=self.session.cookies)
            if response.status_code == 200:
                result = response.json()
                if 'info' in result:
                    #拿到info
                    info = result['info']
                    # 处理 info
                    logger.info(f"课程名称: {info['kcmc']}, 节点名称: {info['mc']}, 时长: {info['zsj']}")


                    return result
                else:
                    logger.warning("响应中缺少预期的字段")
            else:
                logger.error(f"获取播放信息失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"getPlayerInfo请求出错: {e}")
    #检测视频状态
    def get_tips(self, currentJid: str,site:str="125"):
        url = f"{self.BBS_HOST}/personal_getTips.action"
        params = {
            "currentJid": currentJid,
            "site": site,
            "_":self.timestamp
        }
        try:
            response = self.session.get(url, params=params, cookies=self.session.cookies)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 2:
                    logger.warning("视频状态过期，请刷新页面！")
                    return False
            else:
                logger.error(f"获取提示信息失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"get_tips请求出错: {e}")
            return False

    def heart_beat(self, kcid: str, fid: str, jid: str, currentTime: int, spzsj: int, callback=None):
        sign = hashlib.md5(f"jdxx{kcid}{fid}{jid}1218hnjj20202920476".encode()).hexdigest()
        url = f"{self.BBS_HOST}/personal_timeGap.action"
        params = {
            "kcid": kcid,#课程ID
            "zid": fid,#站点ID
            "jid": jid,#节点ID
            "spzsj": currentTime,#当前时间
            "kczsc": spzsj,#课程时长
            "sign": sign,#签名
            "_":self.timestamp#时间戳
        }
        
        logger.info(f"心跳参数: {params}")
        try:
            response = self.session.get(url, params=params, cookies=self.session.cookies)
            logger.info("开始心跳")
            if response.status_code == 200:
                result = response.json()
                logger.info(f"心跳结果: {result}")
                if result.get('status') == 1:
                    logger.success("心跳成功")
                    logger.success("进度已提交")
                    self.currentGkyxsj+=self.ct*1000
                    self.updateProgress(jid)
                    if callable(callback):
                        callback()
                elif result.get('status') == 2:
                    logger.warning("进度未提交")
                    logger.error("心跳失败")
                    #提交失败,倒计时10秒后按刚才的进度提交
                    for i in range(40, 0, -1):
                        logger.warning(f"{i}秒后将重新提交")
                        time.sleep(1)
                    self.heart_beat(kcid, fid, jid, currentTime, spzsj, callback=callback)
                else:
                    pass
            else:
                logger.error(f"心跳请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"heart_beat请求出错: {e}")
    
    def start_video_heartbeat(self, kcid: str, zid: str, jid: str, gkyxsj: int, kczsc: int):
        logger.info(f"开始视频心跳: 课程ID {kcid}, 节点ID {jid}")

        def heartbeat_callback():
            for(i,item) in enumerate(self.pathSource):
                if item['id']==jid:
                    if(isinstance(item['process'],numbers.Number) and item['process']<99):
                        logger.info()
                        self.onlyOne=1

        # 检查当前进度
        if gkyxsj >= kczsc:
            logger.info(f"小节 {jid} 已完成，跳过心跳")
            return

        # 拿到心跳结果
        result=self.heart_beat(kcid, zid, jid, gkyxsj, kczsc, callback=heartbeat_callback)
        #如果result为1,则每隔60秒发送一次心跳请求
        if result == 1:
            # 每隔60秒发送一次心跳请求
            while gkyxsj < kczsc:
                time.sleep(60)
            gkyxsj += 60  # 增加60秒（60000毫秒）
            result = self.heart_beat(kcid, zid, jid, gkyxsj, kczsc, callback=heartbeat_callback)
            if result == 1:
                logger.info(f"进度提交成功: 节点ID {jid}")
            elif result == 2:
                logger.warning(f"进度提交失败: 节点ID {jid}")

    def updateProgress(self, jid: str):
        for item in self.pathSource:
            if item['id'] == jid:
                item['gkyxsj'] = self.gkyxsj
                logger.info(f"updateProgress: {item['gkyxsj']}")
                item['process'] = int(item['gkyxsj'] // item['spzsj'] * 100)
                if(math.isnan(item['process'])):
                    item['process'] = 0
                if item['process'] > 98:
                    item['process'] = 100
                # 更新UI或其他逻辑
                self.update_ui(jid, item['process'])
                break


    def start_tips_check(self, currentJid: str):
        def check_tips():
            while True:
                tips=self.get_tips(currentJid)
                if tips:
                    logger.info("视频状态正常")
                    return True
                else:
                    return False
        # 使用线程来运行check_tips，以便它不会阻塞主程序
        threading.Thread(target=check_tips, daemon=True).start()
    
    def update_ui(self, jid: str, process: int):
        logger.info(f"节点ID {jid}, 进度 {process}%")
    def currentFinish(self):
        for item in self.pathSource:
            if isinstance(item['process'],numbers.Number) and item['process']<99:
                self.onlyOne=1
                self.playByJid(item,self.getStartBFSJ(item))
    def playByJid(self,item,bfsj):
        if bfsj=="" or bfsj==None or math.isnan(bfsj):
            bfsj=0
            ocid=0
            if(self.currentItem):
                ocid=self.currentItem['id']
                self.currentItem=item
                node_finish = self.currentItem['process'] == 100
                logger.info(f"currentBFSJ: {bfsj},{self.currentItem}")
                jid=self.currentItem['id']
                self.currentZid=self.currentItem['fid']
                self.currentJid=jid
                self.currentBFSJ=bfsj
                result=self.getPlayerInfo(jid,ocid)
                info=result['info']
                learnLength=0
                url=info['spdz']
                ssqs=info['ssqs']
                self.pptdz=info['spdz']
                sfpbffs=info['sfpbffs']
                self.tmpOnlyOne=info['onlyOne']
                self.tipsGap = int(info.tipsGap)
                self.ct = int(info.timeGap)
                self.first=True
                self.currnetPptIndex=-1
                if(sfpbffs=="2"):
                    self.pptView=True
                    if "http" in url:
                        url = url.replace("http", "https")
                    pptjd = info['sfpsjjd']
                    pptSource=[]
                    if 'pptdz' in locals() and self.pptdz is not None and self.pptdz != "":
                        time_points = []
                        time_points_tmp = pptjd.split(",")
                        for i in range(len(time_points_tmp)):
                            time_points.append(int(time_points_tmp[i]))
                        timePoints = self.quick_sort(timePoints);
                        self.pptSource=pptSource
                        self.pptdz=url
                        self.currnetPptIndex=0
                        for i, time in enumerate(time_points):
                            item = {}
                            item['url'] = f"{self.pptdz}sm{i}.jpg"
                            item['imgIndex'] = i
                            item['time'] = time
                            pptSource.append(item)
                        self.checkChangePpt()
                else:
                    self.pptView=False
                
        else:
            self.onlyOne=0

        if item['process']==100:
            return False
        return True
    def checkChangePpt(self):
        if not self.pptView or 'pptdz' not in locals() or self.pptdz is None or self.pptdz == "":
            return
        findIndex = 0
        for i,item in enumerate(self.pptSource):
            strTime=str(item['time'])
            time=self.getTimeByStr(strTime)
            time-=2000
            if(self.isNextPlayer):
                vt=self.currentBFSJ+int(self.player['currentTime'])*1000
            else:
                vt=int(self.player['currentTime'])*1000
            if int(vt)>time:
                findIndex=item['imgIndex']
        if(self.currnetPptIndex!=findIndex):
            ppturl=self.pptdz+f"{findIndex}.jpg"
            self.currnetPptIndex = findIndex;
            if(self.currnetPptIndex%2==0):
                self.currnetPptImg1=ppturl
            else:
                self.currnetPptImg2=ppturl
    def getTimeByStr(self,value):
        value = str(value)  # 确保输入是字符串
        # 使用正则表达式替换所有类型的冒号为点
        
        str_value = re.sub(r'[：:。]', '.', value)
        times = str_value.split('.')
        
        time = 0
        for i, part in enumerate(times):
            # 计算每部分时间的毫秒数，注意Python中索引从0开始
            t = int(part) * 1000 * (60 ** (len(times) - i - 1))
            time += t
        return time        

    def quick_sort(self,arr):
        if len(arr) <= 1:
            return arr
        # 这里选择中间的元素作为pivot
        mid_index = len(arr) // 2
        pivot = arr.pop(mid_index)
        left = []
        right = []
        for item in arr:
            if item < pivot:
                left.append(item)
            else:
                right.append(item)
        return self.quick_sort(left) + [pivot] + self.quick_sort(right)
    def getStartBFSJ(self,jid):
        for item in self.pathSource:
            if item['id']==jid or str(item['id'])==jid:
                return item['gkyxsj']
            else:
                return item['spzsj']
        return 0
    # 添加 start_video_heartbeat 方法

    


if __name__ == "__main__":
    # 示例调用
    #从配置config.ini读取账号密码
    config = configparser.ConfigParser()
    config.read('config.ini')
    username = config.get('userinfo', 'username')
    password = config.get('userinfo', 'password')
    qmsystem=QingMaLearningSystem()
    qmsystem.do_login(username, password)
    #获取
    qmsystem.init()


    
