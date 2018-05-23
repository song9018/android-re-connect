#-*- coding: utf-8 -*-
from uiautomator import Device
from AdbTool import *
from logConfig import *
import time,json
from  collections import OrderedDict



class DeviceCase(object):
        __id=""
        def __init__(self,id,app_type,port=None):
                self.__id=id
                self.app_type=app_type
                self.tool = AdbTools(self.__id)
                try:
                        self.model = self.tool.get_device_model().split("\n")[0]
                        print(self.model)
                        self.log = WriteLog(path="log/"+self.model.replace(" ",""))
                        self.device = Device(serial=self.__id,local_port=port)
                        self.device.dump(compressed=False)#解决点击不中的问题
                        info = self.device.info  # 获取该值比较慢，不单独写
                        self.log.log_done(str(info))
                        self.width = info["displayWidth"]
                        self.height = info["displayHeight"]
                        self.get_device_info()
                        self.__switch_ime()
                except IOError as e:
                        self.log.log_error("初始化错误：{}".format(e))

        def get_device_info(self):
            """
            获取设备的android版本、sdk版本、内存情况
            :return:
            """
            try:
                info=OrderedDict()
                android_version=self.tool.get_device_android_version()
                sdk_version=self.tool.get_device_SDK_version()
                disk= self.tool.get_disk()
                resolution=self.tool.get_device_resolution()
                density=self.tool.get_wm_density()
                mac_address=self.tool.get_mac_address()

                info["android_version"]=android_version
                info["sdk_version"] = sdk_version
                info["resolution"]=resolution
                info["density"] = density
                # info["mac_address"] = mac_address
                # if disk:
                #     used, free = disk
                #     info["used_mem"] = used
                #     info["free_mem"] = free
                # else:
                #     info["used_mem"] = ""
                #     info["free_mem"] = ""

                json_object=json.dumps(info)
                with  open(self.log.get_runtime_path()+"/info.json","w") as f:
                    f.write(json_object)
            except Exception as e:
                self.log.log_error("获取设备信息错误：{}".format(e))





        def  __switch_ime(self,ime="jp.jun_nama.test.utf7ime/.Utf7ImeService"):
            """
            切换输入法，默认切换至自动化测试的输入法
            :param ime: 输入法
            :return:
            """
            result=self.tool.set_phone_ime(ime)
            self.log.log_done("切换设备输入法：{}".format(result))

        def test_reboot_phone(self,round=10,wait_sleep=300, firmware_type="pace",is_lock=False):
                """
                重启手机测试
                :param round:
                :return:
                """
                result=None
                wait_connect_time=[0]
                self.log.log_done("机型：{} 测试轮次:{} 开始测试关开手机".format( self.model,round))
                self.device.wakeup()
                for i in range(int(round)):
                        self.log.log_done("第{}轮测试 关开手机操作".format(i+1))
                        if self.is_connect_computer(wait_connect_time,sleeptime=30, round=1):
                                self.device.press.home()
                                self.tool.reboot_phone()#重启后得判断设备是否连接
                                wait_connect_time=[0]
                                if self.is_connect_computer(wait_connect_time):
                                    self.device.swipe(self.width / 2, self.height - 400, self.width / 2, 400, 15)  # 上划解锁
                                    self.log.log_done("上划解锁")
                                    if wait_connect_time[0]<wait_sleep:
                                        print(wait_connect_time[0])
                                        self.lock_and_wait_and_unlock(wait_sleep-wait_connect_time[0], is_lock)#开关机不模拟锁屏
                                    result=self.assert_connect_status_by_app(firmware_type)
                                    self.save_hci(result)
                                else:
                                    self.log.log_done("重启后，adb未连接设备状态，本轮测试结束")
                                    continue
                        else:
                                self.log.log_done("开关机测试前，adb未连接设备状态，本轮测试结束")
                                continue
                        time.sleep(10)

        def test_reset_watch(self,round=10,wait_sleep=300,firmware_type="pace",is_lock=True):
                """
                app端恢复出厂设置测试
                :param round:
                :return:
                """
                result=None
                self.log.log_done("机型：{} 测试轮次:{} 开始测试恢复出厂设置".format( self.model,round))
                self.device.wakeup()
                for i in range(int(round)):
                        self.log.log_done("第{}轮测试 恢复出厂设置操作".format(i+1))
                        self.device.swipe(self.width / 2, self.height - 400, self.width / 2, 400, 100)  # 上划解锁,每一轮解锁，避免上一轮解锁失败影响下一轮
                        time.sleep(2)
                        self.device.press.home()
                        if self.reset_watch(firmware_type):
                                self.lock_and_wait_and_unlock(wait_sleep, is_lock)
                                result=self.assert_connect_status_by_app(firmware_type)
                                self.save_hci(result)
                        time.sleep(10)



        def test_turn_on_and_off_airplane(self, round=10,wait_sleep=300,firmware_type="pace", is_lock=True):
              """
              开关飞行模式,通过启动activity的方式
              :param round:
              :return:
              """
              result = None
              self.log.log_done("机型：{} 测试轮次:{} 开始测试开关飞行模式".format(self.model, round))
              self.device.wakeup()
              for i in range(int(round)):
                     self.log.log_done("第{}轮 开关飞行模式操作".format(i + 1))
                     self.device.swipe(self.width / 2, self.height - 400, self.width / 2, 400, 100)  # 上划解锁
                     time.sleep(2)
                     self.device.press.home()
                     if self.turn_on_airplane_switch():
                            time.sleep(5)
                            self.device.press.home()
                            if self.turn_off_airplane_switch():
                                self.device.press.home()
                                self.lock_and_wait_and_unlock(wait_sleep,is_lock)
                                result =self.assert_connect_status_by_app(firmware_type)#pace \omni
                                self.save_hci(result)



        def test_turn_off_and_on_ble(self,round=10,wait_sleep=300,firmware_type="omni", is_lock=True):
                """
                借助辅助apk 开关蓝牙测试
                :param round:
                :return:
                """
                result = None
                self.log.log_done("机型：{} 测试轮次:{} 开始测试关开蓝牙".format(self.model, round))
                self.device.wakeup()
                for i in range(int(round)):
                        self.log.log_done("第{}轮 关开蓝牙操作".format(i + 1))
                        self.device.swipe(self.width / 2, self.height - 400, self.width / 2, 400, 100)  # 上划解锁
                        time.sleep(2)
                        self.device.press.home()
                        if self.turn_ble_off():
                                time.sleep(5)
                                if self.turn_ble_on():
                                        self.lock_and_wait_and_unlock(wait_sleep,is_lock)
                                        result =self.assert_connect_status_by_app(firmware_type)#pace \omni
                                        self.save_hci(result)

        def lock_and_wait_and_unlock(self, wait_sleep=300, is_lock=True):
                print('lock_and_wait_and_unlock')
                if is_lock:
                        self.device.sleep()
                        print("休眠")
                        self.log.log_done("休眠")
                        time.sleep(wait_sleep)
                        self.device.wakeup()
                        print("唤醒")
                        self.log.log_done("唤醒")
                else:
                        time.sleep(wait_sleep)
                self.device.press.home()
                time.sleep(0.5)
                find_on=2
                while True:
                    if self.tool.get_screen_status()=="ON":
                        self.log.log_done("唤醒成功")
                        self.unlock()
                        break
                    else:
                        self.log.log_done("唤醒失败，倒数:{},重试".format(find_on))
                        if find_on<=0:
                            break
                        find_on-=1
                        self.tool.input_keyevent(26)
                        time.sleep(1)

                time.sleep(2)
                print('{}  lock_and_wait_and_unlock'.format(self.model))

        def unlock(self):
            try:
                unlcok_count=3
                while True:
                    if not self.tool.get_device_lock_status():
                        self.log.log_done("屏幕处于未锁定状态")
                        return True
                       
                    else:
                        unlcok_count-=1
                        self.log.log_done("屏幕锁定，尝试解锁")
                        if unlcok_count<=0:
                            self.log.screenslot(self.device, "解锁失败")
                            self.log.log_done("解锁失败")
                            return False
                        self.device.swipe(self.width / 2, self.height -400, self.width / 2, 400, 15)  # 上划解锁
                        time.sleep(1)
            except Exception as e:
                 self.log.log_warn("解锁异常:{}".format(e))


        def copy_local_HCI_from_device_to_computer(self,source="/sdcard/AutoHCI",target=None):
                """
                从手机端复制HCI日志到电脑端，注意文件夹名称一致，且路径不能有空格
                :param source:手机端路径
                :param target:电脑端路径
                :return:
                """
                fie_dir=target
                if target is None:
                        file_list=source.split("/")
                        fie_dir = os.path.join(self.log.get_runtime_path(), source.split("/")[-1])
                        print(fie_dir)
                if not os.path.exists(fie_dir):
                        os.makedirs(fie_dir)
                self.log.log_done("copy hci,result:{}".format(self.tool.pull(source,fie_dir)))

        # define double click function
        def double_click(self,count=2,*args, **kwargs):
          # set ack timeout
          config = self.device.server.jsonrpc.getConfigurator()
          config['actionAcknowledgmentTimeout'] = 40
          self.device.server.jsonrpc.setConfigurator(config)
          # double click
          for i in range(count):
            print(i)
            self.device(*args, **kwargs).click(x=357,y=87)
          # restore previous config
          config['actionAcknowledgmentTimeout'] = 3000
          self.device.server.jsonrpc.setConfigurator(config)

        def feedback_app_log(self):
            if self.app_type=="唯乐":
                self.weile_feedback_app_log()
            else:
                 if hasattr(self,self.app_type+"_feedback_app_log"):
                        return getattr(self,self.app_type+"_feedback_app_log")()


        def COROS_feedback_app_log(self):
                """反馈日志"""
                if self.open_app():
                        if self.device(resourceId="com.yf.smart.coros.alpha:id/icon").wait.exists(timeout=3000):
                                self.device(resourceId="com.yf.smart.coros.alpha:id/icon")[2].click()
                                self.device.swipe(self.width/2,self.height-400,self.width/2,400,100)#向上滑动
                                if self.device(resourceId="com.yf.smart.coros.alpha:id/v_feedback").wait.exists(timeout=3000):
                                        self.device(resourceId="com.yf.smart.coros.alpha:id/v_feedback").click()
                                        if self.device(resourceId="com.yf.smart.coros.alpha:id/ul_et_content").wait.exists(timeout=3000):
                                            self.device(resourceId="com.yf.smart.coros.alpha:id/ul_et_content").click()
                                            self.device(resourceId="com.yf.smart.coros.alpha:id/ul_et_content").set_text("ReconnectTest")
                                            if self.device(text="Send").exists:
                                                    self.device(text="Send").click()
                                            if self.device(resourceId="com.yf.smart.coros.alpha:id/icon").wait.exists(timeout=30000):
                                                    self.log.log_done("日志发送至服务器成功")
        def weile_feedback_app_log(self):
                """反馈日志"""
                try:
                    if self.open_app():
                            if self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                    self.device(className="android.support.v7.app.ActionBar$Tab")[3].click()
                                    self.device.swipe(self.width/2,self.height-400,self.width/2,400,100)#向上滑动
                                    if self.device(text="帮助与反馈").wait.exists(timeout=3000):
                                            self.device(text="帮助与反馈").click()
                                            if self.device(text="我要反馈").wait.exists(timeout=3000):
                                                    self.device(text="我要反馈").click()
                                                    if self.device(text="问题反馈").exists:
                                                        self.device(resourceId="com.yf.smart.weloopx.alpha:id/ul_et_content").click()
                                                        self.device(resourceId="com.yf.smart.weloopx.alpha:id/ul_et_content").set_text("ReconnectTest")
                                                        self.device(text="提交反馈").click()
                                                    if self.device(text="我要反馈").wait.exists(timeout=30000):
                                                            self.log.log_done("日志发送至服务器成功")
                except Exception as e:
                    self.log.screenslot(self.device,"feedback error")
                    self.log.log_warn("weile_feedback_app_log except:{}".format( e))

        def WeLoopAlpha_feedback_app_log(self):
                """反馈日志"""
                if self.open_app():
                        if self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                self.device(className="android.support.v7.app.ActionBar$Tab")[3].click()
                                self.device.swipe(self.width/2,self.height-400,self.width/2,400,100)#向上滑动
                                if self.device(text="Feedback").wait.exists(timeout=3000):
                                        self.device(text="Feedback").click()
                                        if self.device(resourceId="com.yf.smart.weloopx.overseas.alpha:id/ul_et_content").wait.exists(timeout=3000):
                                                self.device(resourceId="com.yf.smart.weloopx.overseas.alpha:id/ul_et_content").click()
                                                self.device(resourceId="com.yf.smart.weloopx.overseas.alpha:id/ul_et_content").set_text("ReconnectTest")
                                                self.device(text="Send").click()
                                                if self.device(text="Feedback").wait.exists(timeout=30000):
                                                        self.log.log_done("日志发送至服务器成功")


        def save_hci(self, is_success):
                """
                根据每轮的测试结果，判断是否要保存HCI日志
                :param is_success:
                :return:
                """
                if is_success is None:
                        return
                else:
                        if not is_success:
                                self.log.log_done("拷贝hci日志")
                                if self.open_automator_tool():
                                        if self.device(text="HCI").wait.exists(timeout=1000):
                                                self.device(text="HCI").click()
                                                self.log.log_done("点击HCI")
                                                if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/edit_info").wait.exists(timeout=60000):
                                                        self.log.log_done(self.device(resourceId="com.example.yuanxiaowen.myapplication:id/edit_info").text)
                                        else:
                                                if self.device(text="》").wait.exists(timeout=1000):
                                                        self.device(text="》").click()
                                                        time.sleep(2)
                                                        self.device(text="HCI").click()
                                                        self.log.log_done("点击HCI")
                                                        if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/edit_info").wait.exists(timeout=60000):
                                                                self.log.log_done(self.device(resourceId="com.example.yuanxiaowen.myapplication:id/edit_info").text)

        def wait_airpline_on(self,timeout=5):
                """
                指定时间轮询飞行模式的打开状态
                :param timeout:
                :return:
                """
                timeout=timeout
                while True:
                        if timeout:
                                time.sleep(1)
                                if self.tool.get_airplane_status():
                                   return True
                                else:
                                   timeout-=1
                        else:
                                return False

        def wait_airpline_off(self,timeout=5):
                """
                指定时间轮询飞行模式的关闭状态
                :param timeout:
                :return:
                """
                timeout = timeout
                while True:
                        if timeout:
                                time.sleep(1)
                                if not self.tool.get_airplane_status():
                                   return True
                                else:
                                   timeout-=1
                        else:
                                return False



        def turn_on_airplane_switch(self):
                """
                打开飞行模式开关
                :return:
                """
                self.device.press.home()
                if self.tool.get_airplane_status():
                        self.log.log_done("飞行模式为打开状态，不做任何操作")
                        return True
                else:
                        self.tool.start_activity("android.settings.AIRPLANE_MODE_SETTINGS")
                        count=1
                        while True:
                                if self.device(text="关").wait.exists(timeout=3000):#飞行模式为开或者关
                                        self.device(text="关").click()
                                        time.sleep(5)
                                        if self.wait_airpline_on(10):
                                                self.log.log_done("打开飞行模式：成功")
                                                self.device.press.back()
                                                return True
                                else:
                                        if self.device(text="飞行模式").wait.exists(timeout=3000):#直接点击飞行模式文本就可以开关
                                                self.device(text="飞行模式").click()
                                                if self.device(text="确定").wait.exists(timeout=5000):#g3
                                                        self.device(text="确定").click()
                                                        time.sleep(5)
                                                if self.wait_airpline_on(10):
                                                         self.log.log_done("打开飞行模式：成功")
                                                         self.device.press.back()
                                                         return True
                                                else:
                                                        if self.device(resourceId="oppo:id/colorswitchWidget").exists:#oppo f5
                                                                self.log.log_done("点击 oppo f5 oppo:id/colorswitchWidget")
                                                                self.device(resourceId="oppo:id/colorswitchWidget").click()
                                                                if self.wait_airpline_on(10):
                                                                        self.log.log_done("打开飞行模式：成功")
                                                                        self.device.press.back()
                                                                        return True

                                                        if self.device(resourceId="com.android.settings:id/switchWidget").exists:#乐视2
                                                                self.log.log_done("点击 乐视2 com.android.settings:id/switchWidget")
                                                                self.device(resourceId="com.android.settings:id/switchWidget").click()
                                                                if self.wait_airpline_on(10):
                                                                        self.log.log_done("打开飞行模式：成功")
                                                                        self.device.press.back()
                                                                        return True
                                                        if self.device(resourceId="com.android.settings:id/enabledswitch").exists:#360 N4
                                                                self.log.log_done("点击360 N4 com.android.settings:id/enabledswitch")
                                                                self.device(resourceId="com.android.settings:id/enabledswitch").click()
                                                                if self.wait_airpline_on(10):
                                                                        self.log.log_done("打开飞行模式：成功")
                                                                        self.device.press.back()
                                                                        return True


                                        elif self.device(text="Airplane mode").wait.exists(timeout=1000):#英文
                                                self.device(text="Airplane mode").click()
                                                time.sleep(5)
                                                if self.wait_airpline_on(10):
                                                         self.log.log_done("打开飞行模式：成功")
                                                         self.device.press.back()
                                                         return True

                                        elif self.device(text="离线模式").wait.exists(timeout=1000):#vivo
                                                self.device(text="离线模式").click()
                                                time.sleep(5)
                                                if self.wait_airpline_on(10):
                                                        self.log.log_done("打开飞行模式：成功")
                                                        self.device.press.back()
                                                        return True
                                                else:
                                                        self.device(resourceId="com.android.settings:id/checkBox").click()
                                                        self.log.log_done("点击 com.android.settings:id/checkBox")
                                                        if self.wait_airpline_on(10):
                                                                self.log.log_done("打开飞行模式：成功")
                                                                self.device.press.back()
                                                                return True
                                        else:
                                                self.device.swipe(self.width /2,200 , self.width /2,self.height-200, 15)
                                                count+=1
                                                if count>3:
                                                         self.log.log_done("打开飞行模式：失败1")
                                                         self.log.screenslot(self.device,"打开飞行模式失败1")
                                                         self.device.press.back()
                                                         return  False
                                self.log.log_done("其他原因打开飞行模式：失败")
                                self.log.screenslot(self.device, "其他原因打开飞行模式失败2")
                                self.device.press.back()
                                return  False

        def  turn_off_airplane_switch(self):
              """
              关闭飞行模式开关
              :return:
              """
              self.device.press.home()
              if self.tool.get_airplane_status():
                     self.tool.start_activity("android.settings.AIRPLANE_MODE_SETTINGS")
                     count=1
                     while True:
                            if self.device(text="开").wait.exists(timeout=3000):
                                   self.device(text="开").click()
                                   time.sleep(5)
                                   if not self.wait_airpline_on(10):
                                          self.log.log_done("关闭飞行模式：成功")
                                          self.device.press.back()
                                          return True
                            else:
                                   if self.device(text="飞行模式").wait.exists(timeout=3000):
                                          print("关闭飞行模式")
                                          self.device(text="飞行模式").click()
                                          time.sleep(5)
                                          if not self.wait_airpline_on(10):
                                                 self.log.log_done("关闭飞行模式：成功")
                                                 self.device.press.back()
                                                 return True
                                          else:
                                                if self.device(resourceId="oppo:id/colorswitchWidget").exists:
                                                          self.log.log_done("oppo f5 点击 oppo:id/colorswitchWidget")
                                                          self.device(resourceId="oppo:id/colorswitchWidget").click()#oppo f5
                                                          if not self.wait_airpline_on(10):
                                                                  self.log.log_done("关闭飞行模式：成功")
                                                                  self.device.press.back()
                                                                  return True
                                                if self.device(resourceId="com.android.settings:id/switchWidget").exists:#乐视2
                                                  self.log.log_done("乐视2 点击 com.android.settings:id/switchWidget")
                                                  self.device(resourceId="com.android.settings:id/switchWidget").click()
                                                  if not self.wait_airpline_on(10):
                                                          self.log.log_done("关闭飞行模式：成功")
                                                          self.device.press.back()
                                                          return True

                                                if self.device(resourceId="com.android.settings:id/enabledswitch").exists:#360 N4
                                                  self.log.log_done("360 N4点击 com.android.settings:id/enabledswitch")
                                                  self.device(resourceId="com.android.settings:id/enabledswitch").click()
                                                  if not self.wait_airpline_on(10):
                                                          self.log.log_done("关闭飞行模式：成功")
                                                          self.device.press.back()
                                                          return True

                                   elif self.device(text="Airplane mode").wait.exists(timeout=1000):  # 英文
                                           self.device(text="Airplane mode").click()
                                           time.sleep(5)
                                           if not self.wait_airpline_on(10):
                                                   self.log.log_done("关闭飞行模式：成功")
                                                   self.device.press.back()
                                                   return True

                                   elif self.device(text="离线模式").wait.exists(timeout=1000):  # vivo
                                           self.device(text="离线模式").click()
                                           time.sleep(5)
                                           if not self.wait_airpline_on(10):
                                                   self.log.log_done("关闭飞行模式：成功")
                                                   self.device.press.back()
                                                   return True
                                           else:
                                                   self.device(resourceId="com.android.settings:id/checkBox").click()  # 待获取开关ui
                                                   self.log.log_done("点击 com.android.settings:id/checkBox")
                                                   if not self.wait_airpline_on(10):
                                                           self.log.log_done("关闭飞行模式：成功")
                                                           self.device.press.back()
                                                           return True

                                   else:
                                          self.device.swipe(self.width /2,200, self.width /2, self.height-200, 15)
                                          count+=1
                                          if count>3:
                                                 self.log.log_done("关闭飞行模式：失败")
                                                 self.log.screenslot(self.device, "关闭飞行模式失败1")
                                                 self.device.press.back()
                                                 return  False

                            self.log.log_done("其他原因，关闭飞行模式：失败")
                            self.log.screenslot(self.device, "其他原因关闭飞行模式失败")
                            self.device.press.back()
                            return False
              else:
                     self.log.log_done("飞行模式为关闭状态，不做任何操作")
                     return True


        def turn_ble_off(self):
              count=1
              while True:
                     if self.open_automator_tool():
                            self.log.log_done("找到自动化辅助工具")
                            if self.device(text="《").wait.exists(timeout=1000):
                                    self.device(text="《").click()

                            if self.device(text="》").wait.exists(timeout=3000):
                                   self.device(text="》").click()
                                   self.log.log_done("点击》")
                                   if  self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").wait.exists(timeout=3000):
                                          if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").text == "OFF":
                                                 self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").click()
                                                 self.log.log_done("关闭蓝牙开关")
                                                 # time.sleep(4)
                                                 #待加弹框处理
                                                 self.handler_permissions_box()
                                                 self.device.press.back()
                                                 self.log.log_done("返回上一页")
                                                 time.sleep(2)
                                                 self.device(text="》").click()
                                                 self.log.log_done("点击》")
                                                 if self.device( resourceId="com.example.yuanxiaowen.myapplication:id/but3").text == "ON":
                                                        self.log.log_done("关闭蓝牙开关:成功")
                                                        return True
                                                 else:
                                                        self.log.log_warn("关闭蓝牙开关:失败")
                                                        self.log.log_done("第{}次尝试关闭".format(count))
                                                        if count>3:
                                                               return False
                                                        count+=1
                                          else:
                                                 if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").text == "ON":
                                                        self.log.log_warn("上一次的蓝牙开关为关闭状态，不做任何操作")
                                                        return True

                                   else:
                                          self.log.log_warn("找不到打开蓝牙的开关按钮")
                                          self.log.screenslot(self.device,"找不到打开蓝牙的开关按钮")
                                          return False
                            else:
                                   self.log.log_warn("找不到下一步的按钮")
                                   self.log.screenslot(self.device, "找不到下一步的按钮")
                                   return False
                     else:
                            self.log.log_done("找不到自动化辅助工具")
                            self.log.screenslot(self.device, "找不到自动化辅助工具")
                            return False

        def turn_ble_on(self):
              count = 1
              while True:
                     if self.open_automator_tool():
                            self.log.log_done("找到自动化辅助工具")
                            if self.device(text="《").wait.exists(timeout=1000):
                                    self.device(text="《").click()

                            if self.device(text="》").wait.exists(timeout=3000):
                                   self.device(text="》").click()
                                   self.log.log_done("点击》")
                                   if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").wait.exists(timeout=3000):
                                          if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").text == "ON":
                                                 self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").click()
                                                 self.log.log_done("打开蓝牙开关")
                                                 # time.sleep(4)
                                                 # 待加弹框处理
                                                 self.handler_permissions_box()
                                                 self.device.press.back()
                                                 self.log.log_done("返回上一页")
                                                 time.sleep(2)
                                                 self.device(text="》").click()
                                                 self.log.log_done("点击》")
                                                 if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").text == "OFF":
                                                        self.log.log_done("打开蓝牙开关：成功")
                                                        return True
                                                 else:
                                                        self.log.log_done("打开蓝牙开关：失败")
                                                        self.log.log_done("第{}次尝试打开".format(count))
                                                        if count>3:
                                                               return False
                                                        count += 1
                                          else:
                                                 if self.device(resourceId="com.example.yuanxiaowen.myapplication:id/but3").text == "OFF":
                                                        self.log.log_warn("上一次的蓝牙开关为打开状态，不做任何操作")
                                                        return True
                                   else:
                                          self.log.log_warn("找不到打开蓝牙的开关按钮")
                                          self.log.screenslot(self.device, "找不到打开蓝牙的开关按钮")
                                          return False
                            else:
                                   self.log.log_warn("找不到下一步的按钮")
                                   self.log.screenslot(self.device, "找不到下一步的按钮")
                                   return False
                     else:
                            self.log.log_done("找不到自动化辅助工具")
                            self.log.screenslot(self.device, "找不到自动化辅助工具")
                            return False
              self.device.press.back()

        def handler_permissions_box(self):
                try:
                        self.log.log_done("handler_permissions_box")
                        if self.device(text="允许").wait.exists(timeout=4000):
                            self.log.log_done("点击允许")
                            self.device(text="允许").click()
                            self.log.log_done("ok")
                        if self.device(text="允许一次").exists:  # 小米
                            self.log.log_done("点击允许一次")
                            self.device(text="允许一次").click()
                            self.log.log_done("ok")
                        if self.device(text="是").exists:
                             self.log.log_done("点击是")
                             self.device(text="是").click()
                             self.log.log_done("ok")
                        if self.device(text="确认").exists:
                             self.log.log_done("点击确认")
                             self.device(text="确认").click()
                             self.log.log_done("ok")

                        if self.device(text="确定").exists:
                             self.log.log_done("点击确定")
                             self.device(text="确定").click()
                             self.log.log_done("ok")

                        time.sleep(6)
                except Exception as e:
                        self.log.log_warn("处理弹框出现异常：{}".format(e))
                        self.log.screenslot(self.device, "处理弹框出现异常")

        def reset_watch(self,witch):
              """
              恢复出厂设置
              :return:
              """
              if witch in["pace","omni"]:
                print(witch)
                if hasattr(self,"pace_reset_watch"):
                    return getattr(self,"pace_reset_watch")()
                else:
                    print("不存在 {}_reset_watch".format(witch))
              if witch in["hey3s","neo","hey3"]:
                print(witch)
                if hasattr(self,"neo_reset_watch"):
                    return getattr(self,"neo_reset_watch")()
                else:
                    print("不存在 {}_reset_watch".format(witch))


        def pace_reset_watch(self):
              """
              恢复出厂设置
              :return:
              """
              print("pace_reset_watch")
              try:
                      if self.open_app():
                             if self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                    self.device(className="android.support.v7.app.ActionBar$Tab")[3].click()
                                    self.device(resourceId="com.yf.smart.coros.alpha:id/ivArrow").click()  # 下一步
                                    if self.device(resourceId="com.yf.smart.coros.alpha:id/btnBaseSettings").wait.exists(timeout=3000):
                                           self.device(resourceId="com.yf.smart.coros.alpha:id/btnBaseSettings").click()
                                           if self.device(text="Reset").wait.exists(timeout=3000):
                                                  self.device(text="Reset").click()
                                                  if self.device(resourceId="com.yf.smart.coros.alpha:id/rv_tv_sure").wait.exists(timeout=3000):
                                                         self.device(resourceId="com.yf.smart.coros.alpha:id/rv_tv_sure").click()
                                                         if self.device(text="Add New Device").wait.exists(timeout=60000):
                                                                self.log.log_done("恢复出厂：成功")
                                                                self.device.press.back()
                                                                return True
                                                         else:
                                                                self.log.screenslot(self.device,"找不到Add New Device")
                                                                self.log.log_warn("找不到Add New Device")
                                                  else:
                                                         self.log.screenslot(self.device,"找不到弹框的确定")
                                                         self.log.log_warn("找不到弹框的确定")
                                           else:
                                                  self.log.screenslot(self.device,"找不到Reset")
                                                  self.log.log_warn("找不到Reset")
                                    else:
                                           self.log.screenslot(self.device, "找不到基础设置按钮")
                                           self.log.log_warn("找不到基础设置按钮")
                             else:
                                    self.log.screenslot(self.device,"找不到底部菜单")
                                    self.log.log_warn("找不到底部菜单")
                      else:
                             self.log.screenslot(self.device, "打开coros app失败")
                             self.log.log_warn("打开coros app失败")

                      self.device.press.back()
                      self.device.press.back()
                      self.device.press.home()
                      return False
              except Exception as e:
                      self.log.log_warn("恢复出厂出现异常：{}".format(e))
                      self.log.screenslot(self.device,"恢复出厂出现异常")

        def neo_reset_watch(self):
              """
              恢复出厂设置
              :return:
              """
              print("neo_reset_watch")
              try:
                      if self.open_app():
                             # print(self.device.watchers)
                             self.device.watchers.remove()#使用完需要注销，否则控件与监视器相同时，会出发监视器
                             # self.device.watchers.reset()#使用完需要注销，否则控件与监视器相同时，会出发监视器
                             if self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                    self.device(className="android.support.v7.app.ActionBar$Tab")[2].click()
                                    if self.app_type == "唯乐":  # 弄成字典
                                        self.device(resourceId="com.yf.smart.weloopx.alpha:id/ivSetting").click()  # 下一步
                                        self.device.swipe(self.width/2,self.height-400,self.width/2,400,14)
                                        self.device(text="恢复出厂设置").click()
                                        if self.device(text="确定").wait.exists(timeout=3000):
                                                self.device(text="确定").click()
                                                if self.device(text="已断开").wait.exists(timeout=60000):
                                                        self.log.log_done("恢复出厂：成功")
                                                        self.device.press.back()
                                                        return True
                                                else:
                                                        self.log.screenslot(self.device,"找不到已断开")
                                                        self.log.log_warn("找不到已断开")

                                    elif self.app_type == "WeLoopAlpha":
                                        self.device(resourceId="com.yf.smart.weloopx.overseas.alpha:id/option_vcard",text="Setting").click()  # 下一步
                                        self.device.swipe(self.width / 2, self.height - 400, self.width / 2, 400, 15)
                                        self.device(text="Factory Reset").click()
                                        if self.device(text="OK").wait.exists(timeout=3000):
                                            self.device(text="OK").click()
                                            if self.device(resourceId="com.yf.smart.weloopx.overseas.alpha:id/option_vcard",text="Setting").wait.gone(timeout=60000):
                                                self.log.log_done("恢复出厂：成功")
                                                self.device.press.back()
                                                return True
                                            else:
                                                self.log.screenslot(self.device, "一直存在Setting，未断开")
                                                self.log.log_warn("一直存在Setting，未断开")

                                    else:
                                           self.log.screenslot(self.device, "找不到OK")
                                           self.log.log_warn("找不到OK")
                             else:
                                        self.log.screenslot(self.device,"找不到底部菜单")
                                        self.log.log_warn("找不到底部菜单")
                      else:
                             self.log.screenslot(self.device, "打开app失败")
                             self.log.log_warn("打开app失败")

                      self.device.press.back()
                      self.device.press.back()
                      self.device.press.home()
                      return False
              except Exception as e:
                      self.log.log_warn("恢复出厂出现异常：{}".format(e))
                      self.log.screenslot(self.device,"恢复出厂出现异常")



        def open_automator_tool(self):
                try_count = 1
                while True:
                        try:
                                self.device.press.home()
                                if self.device(text="自动化辅助工具").wait.exists(timeout=3000):
                                        self.device(text="自动化辅助工具").click()
                                        return True
                                else:
                                            self.tool.start_activity("android.settings.AIRPLANE_MODE_SETTINGS")
                                            self.log.log_done("home当前界面无自动化辅助工具，进入勿扰界面")
                                            time.sleep(1)
                                            self.device.press.home()
                                            for i in range(4):  # 先向左滑动
                                                   self.device.swipe(self.width - 50, self.height / 2, 50, self.height / 2, 15)
                                                   if self.device(text="自动化辅助工具").wait.exists(timeout=3000):
                                                          self.device(text="自动化辅助工具").click()
                                                          return True

                                            for j in range(6):  # 向右滑动查找
                                                   if self.device(text="自动化辅助工具").wait.exists(timeout=3000):
                                                          self.device(text="自动化辅助工具").click()
                                                          return True
                                                   self.device.swipe(50, self.height / 2, self.width - 50, self.height / 2, 15)
                                self.log.log_done( "左右切换找不到自动化辅助工具,进入勿扰界面刷新")
                                if not try_count:
                                        return False
                                self.tool.start_activity("android.settings.AIRPLANE_MODE_SETTINGS")
                                try_count -= 1
                        except Exception as e:
                                self.log.log_warn("查找自动化辅助工具出现异常：{}".format(e))
                                self.log.screenslot(self.device,"查找自动化辅助工具出现异常")
                                return False


        def open_app(self):
                self.log.log_done("准备打开app: {}".format(self.app_type))
                try_count=1
                while True:
                        try:
                                self.device.press.home()
                                if self.device(text=self.app_type).wait.exists(timeout=3000):
                                        self.device(text=self.app_type).click()
                                        self.log.log_done("找到app")
                                        return True
                                else:
                                    # watcher,当UI找不到时才执行
                                            self.device.watcher("yes").when(text=u"用 USB 进行文件传输？").when(text=u"是").click(text=u"是")  # m8
                                            self.device.watcher("sure").when(text=u"确定").click(text=u"确定")  # m8
                                            self.device.watcher("sure1").when(text=u"确认").click(text=u"确认")  #是，访问数据
                                            self.device.watcher("allow1").when(text=u"允许").click(text=u"允许")  # s8、j7
                                            self.device.watcher("allow2").when(text=u"是，访问数据").click(text=u"是，访问数据")  # 华为
                                            self.device.watcher("OK").when(text=u"OK").click(text=u"OK")  #
                                            self.device.watcher("Yes").when(text=u"Yes").click(text=u"Yes")  #
                                            self.device.watcher("agree").when(text=u"同意").click(text=u"同意")  #
                                            self.tool.start_activity("android.settings.AIRPLANE_MODE_SETTINGS")
                                            self.log.log_done("home当前界面无{} app，进入勿扰界面刷新".format(self.app_type))
                                            time.sleep(1)
                                            self.device.press.home()
                                            self.log.log_done("向左滑动")
                                            for i in range(4):  # 先向左滑动
                                                   self.device.swipe(self.width - 50, self.height / 2, 50, self.height / 2, 15)
                                                   if self.device(text=self.app_type).wait.exists(timeout=3000):
                                                          self.device(text=self.app_type).click()
                                                          self.log.log_done("找到app")
                                                          return True
                                            self.log.log_done("向右滑动")
                                            for j in range(6):  # 向右滑动查找
                                                   if self.device(text=self.app_type).wait.exists(timeout=3000):
                                                          self.device(text=self.app_type).click()
                                                          self.log.log_done("找到app")
                                                          return True
                                                   self.device.swipe(50, self.height / 2, self.width - 50, self.height / 2, 15)

                                self.log.log_done( "左右切换找不到{}app,进入勿扰界面刷新".format(self.app_type))
                                if not try_count:
                                        return False
                                self.tool.start_activity("android.settings.AIRPLANE_MODE_SETTINGS")
                                try_count -= 1
                        except Exception as e:
                             self.log.log_warn("查找{}app出现异常：{}".format(self.app_type,e))
                             self.log.screenslot(self.device,"查找{} app出现异常".format(self.app_type))
                             return False


        def is_connect_computer(self, wait_connect_time,sleeptime=30, round=6):
                """
                检查usb是否真正连接,默认超时时间为3分钟
                :param sleeptime: 等待指定时间查看usb连接情况
                :param count: 轮询次数
                :return:
                """
                wait_connet_count=1
                while True:
                        # self.device.freeze_rotation(False)
                        time.sleep(sleeptime)  # 等待指定时间查看usb连接情况
                        device_status=self.tool.get_device_state()
                        if "device" in device_status:  # 已连接
                                self.log.log_done("等待{}s usb与电脑已连接".format(sleeptime))
                                wait_connect_time[0]=30
                                return True
                        else:
                                if wait_connet_count>round:
                                        self.log.log_warn("usb与电脑未连接")
                                        return False
                                self.log.log_warn("首次查看usb与电脑未连接后，第{}次检查 ，间隔时长：{}s 设备状态:{}".format(wait_connet_count, sleeptime,device_status))
                                wait_connet_count += 1
                                wait_connect_time[0]+=30
                return False

        def  assert_connect_status_by_app(self,witch,round=1):
                method=witch+"_assert_connect_status_by_app"
                print(method)
                if hasattr(self,method):
                        return getattr(self,method)(round)
                else:
                        print("不存在此类方法：{}".format(method))


        def pace_assert_connect_status_by_app(self, round):
                """
                进入app查看连接状态
                :param sleeptime:默认5分钟
                :param round:
                :return:
                """
                wait_round=1
                try_count=3
                try:
                        while True:
                                if self.open_app():
                                        if self.device(textContains="允许").exists:
                                          self.device(textContains="允许").click()
                                        if self.device(textContains="ok").exists:
                                          self.device(textContains="ok").click()
                                        if  self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                                try:
                                                        self.device(className="android.support.v7.app.ActionBar$Tab")[3].click()
                                                except IndexError as e:
                                                        self.log.log_done("出现底部菜单出现IndexError错误，back 重新进入:{}".format(try_count))
                                                        self.device.press.back()
                                                        time.sleep(2)
                                                        self.device.press.home()
                                                        if try_count<0:
                                                                try_count -= 1
                                                                continue
                                                        else:
                                                               pass

                                                if  self.device(resourceId="com.yf.smart.coros.alpha:id/tvTracker").wait.exists(timeout=1000):
                                                        self.log.log_done("蓝牙已连接")
                                                        return True
                                                else:
                                                        wait_round+=1
                                                        if wait_round>round:
                                                                self.log.screenslot(self.device, "not_connect")
                                                                self.log.log_error("蓝牙未连接")
                                                                return False
                                                        else:
                                                                self.log.log_warn("首次查看未连接,第{}次尝试查看".format(wait_round))
                                                                self.log.screenslot(self.device,"首次查看未连接,第{}次尝试查看".format(wait_round))
                                        else:
                                                self.log.screenslot(self.device, "app底部菜单栏不存在")
                                                self.log.log_warn("app底部菜单栏不存在")
                                                return
                                else:
                                        self.log.screenslot(self.device, "coros app不存在")
                                        self.log.log_warn("coros app不存在")
                                        return
                                return
                except Exception as e:
                        self.log.log_done("进入app 查看蓝牙连接情况出现异常：{}".format(e))
                        self.log.screenslot(self.device,"进入app 查看蓝牙连接情况出现异常")
                        return

        def omni_assert_connect_status_by_app(self, round):
                """
                进入app查看连接状态
                :param sleeptime:默认5分钟
                :param round:
                :return:
                """
                wait_round = 1
                try_count = 3
                try:
                        while True:
                                if self.open_app():
                                        if self.device(textContains="允许").exists:
                                                self.device(textContains="允许").click()
                                        if self.device(textContains="ok").exists:
                                                self.device(textContains="ok").click()
                                        if self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                                try:
                                                        self.device(className="android.support.v7.app.ActionBar$Tab")[3].click()
                                                except IndexError as e:
                                                        self.log.log_done("出现底部菜单出现IndexError错误，back 重新进入:{}".format(try_count))
                                                        self.device.press.back()
                                                        time.sleep(2)
                                                        self.device.press.home()
                                                        if try_count < 0:
                                                                try_count -= 1
                                                                continue
                                                        else:
                                                                pass
                                                if self.device(resourceId="com.yf.smart.coros.alpha:id/tvEmergence",enabled=True).wait.exists(timeout=1000):#self.device(text="Emergency Contact",enabled=True)
                                                        self.log.log_done("蓝牙已连接")
                                                        return True
                                                else:
                                                        wait_round += 1
                                                        if wait_round > round:
                                                                self.log.screenslot(self.device, "not_connect")
                                                                self.log.log_error("蓝牙未连接")
                                                                return False
                                                        else:
                                                                self.log.log_warn("首次查看未连接,第{}次尝试查看".format(wait_round))
                                                                self.log.screenslot(self.device,"首次查看未连接,第{}次尝试查看".format(wait_round))
                                        else:
                                                self.log.screenslot(self.device, "app底部菜单栏不存在")
                                                self.log.log_warn("app底部菜单栏不存在")
                                                return
                                else:
                                        self.log.screenslot(self.device, "coros app不存在")
                                        self.log.log_warn("coros app不存在")
                                        return
                                return
                except Exception as e:
                        self.log.log_done("进入app 查看蓝牙连接情况出现异常：{}".format(e))
                        self.log.screenslot(self.device, "进入app 查看蓝牙连接情况出现异常")
                        return

        def neo_assert_connect_status_by_app(self, round):
                """
                进入app查看连接状态：唯乐和weloopoverseas
                进入app查看连接状态：唯乐和weloopoverseas
                :param sleeptime:默认5分钟
                :param round:
                :return:
                """
                wait_round = 1
                try_count = 3
                try:
                        while True:
                                if self.open_app():
                                        if self.device(textContains="允许").exists:
                                                self.device(textContains="允许").click()
                                        if self.device(textContains="ok").exists:
                                                self.device(textContains="ok").click()
                                        if  self.device(text="跳过").exists:
                                                self.device(text="跳过").click()
                                        if self.device(className="android.support.v7.app.ActionBar$Tab").wait.exists(timeout=3000):
                                                try:
                                                        self.device(className="android.support.v7.app.ActionBar$Tab")[2].click()
                                                except IndexError as e:
                                                        self.log.log_done("出现底部菜单出现IndexError错误，back 重新进入:{}".format(try_count))
                                                        self.device.press.back()
                                                        time.sleep(2)
                                                        self.device.press.home()
                                                        if try_count < 0:
                                                                try_count -= 1
                                                                continue
                                                        else:
                                                                pass

                                                if self.app_type=="唯乐":
                                                    self.log.log_done("检查app的状态，time：{}".format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))))
                                                    if self.device(resourceId="com.yf.smart.weloopx.alpha:id/device_name",textContains="已连接").wait.exists(timeout=1000):#self.device(text="Emergency Contact",enabled=True)
                                                            self.log.log_done("蓝牙已连接")
                                                            return True
                                                    else:
                                                            wait_round += 1
                                                            if wait_round > round:
                                                                    self.log.screenslot(self.device, "not_connect")
                                                                    self.log.log_error("蓝牙未连接")
                                                                    return False
                                                            else:
                                                                    self.log.log_warn("首次查看未连接,第{}次尝试查看".format(wait_round))
                                                                    self.log.screenslot(self.device,"首次查看未连接,第{}次尝试查看".format(wait_round))

                                                elif self.app_type=="WeLoopAlpha":
                                                    self.log.log_done("检查app的状态，time：{}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))))
                                                    if self.device(resourceId="com.yf.smart.weloopx.overseas.alpha:id/option_vcard",textContains="Update").wait.exists(timeout=1000):#self.device(text="Emergency Contact",enabled=True)
                                                            self.log.log_done("蓝牙已连接")
                                                            return True
                                                    else:
                                                            wait_round += 1
                                                            if wait_round > round:
                                                                    self.log.screenslot(self.device, "not_connect")
                                                                    self.log.log_error("蓝牙未连接")
                                                                    return False
                                                            else:
                                                                    self.log.log_warn("首次查看未连接,第{}次尝试查看".format(wait_round))
                                                                    self.log.screenslot(self.device,"首次查看未连接,第{}次尝试查看".format(wait_round))

                                                else:
                                                    self.log.log_warn("不支持的app类型  信息:{}".format(self.app_type))
                                        else:
                                                self.log.screenslot(self.device, "app底部菜单栏不存在")
                                                self.log.log_warn("app底部菜单栏不存在")
                                                return
                                else:
                                        self.log.screenslot(self.device, "{} app不存在".format(self.app_type))
                                        self.log.log_warn( "{} app不存在".format(self.app_type))
                                        return
                                return
                except Exception as e:
                        self.log.log_done("进入app 查看蓝牙连接情况出现异常：{}".format(e))
                        self.log.screenslot(self.device, "进入app 查看蓝牙连接情况出现异常")
                        return




