# -*- coding:utf-8 -*-
from DeviceCase  import *
import MyThread,configparser,ast
from ParserResult import *

confi=configparser.ConfigParser()
confi.read("basic.ini",encoding="utf-8")
#邮箱信息
email_host=confi.get("email","smtp_server")
email_user=confi.get("email","user")
email_pwd=confi.get("email","password")
email_receivers_list=confi.get("email","receivers").split(",")

#测试信息
count=confi.get("test","count")
wait_time=confi.get("test","wait_time")
firmware_type=confi.get("test","firmware_type")
is_lock=confi.get("test","is_lock")
excute=confi.get("test","excute").split(",")
is_send_email=confi.get("test","is_send_email")
package=confi.get("apk_info","package")
apk_relative_path=confi.get("apk_info","apk_relative_path")
app_type=confi.get("apk_info","app_type")

apk_dir=os.path.dirname(os.path.abspath(__file__))+apk_relative_path
try:
    apk_path=lambda  a:(a+os.listdir(a)[0]).replace("\\","/")
except Exception as e:
    pass



class ExcuteCase(object):
    def __init__(self,id, port):
        self.dev=DeviceCase(id,app_type,port)

    def excute_test(self,*args):
         for arg in args:
             if hasattr(self.dev,arg):
                 if arg in "test_reboot_phone":
                     getattr(self.dev,arg)(int(count),int(wait_time), firmware_type,False)
                 else:
                     getattr(self.dev,arg)(int(count),int(wait_time), firmware_type,ast.literal_eval(is_lock))
         self.dev.feedback_app_log()
         self.dev.copy_local_HCI_from_device_to_computer()

        
        




def multithreadedExecution(funlist):
    threads = MyThread.MyThread()
    threads.set_thread_func_list(funlist)
    threads.start()

def excute_all_test(id,port=None):
    print(id,port)
    e=ExcuteCase(id,port).excute_test(*excute)  #excute前面不可少*，否则传入进入的是列表
   


if __name__=="__main__":
    COUNT=0
    device_list=AdbTools.get_devices_list()
    port_list=range(5555,5555+len(device_list))
    fun_decives_list=[]
    for i in range(len(device_list)):
        fun_decives_list.append({'func':excute_all_test, 'args': (device_list[i],port_list[i])})
    multithreadedExecution(fun_decives_list)
    parser_result(email_host,email_user,email_pwd,email_receivers_list,count,ast.literal_eval(is_send_email))




