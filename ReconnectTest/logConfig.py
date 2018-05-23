#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os,time

root_dir=os.path.dirname(__file__)
class WriteLog(object):
    path=""
    def __init__(self,path="log",filename="runtime.log"):
        self.path = os.path.join(root_dir,path) if path else root_dir
        print(self.path)
        self.runtime_file_path = os.path.join(self.path, filename)
        self.screenslot_dir = os.path.join(self.path,"screenslots")
        if not os.path.exists(self.screenslot_dir):
            os.makedirs(self.screenslot_dir)
        log_dir=os.path.join(self.path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.runtime_file = open(os.path.abspath(self.runtime_file_path), "a",encoding='utf-8')

    def get_runtime_path(self):
        return self.path

    @staticmethod
    def get_now_time():
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    @staticmethod
    def _write(write_file,log_type,msg):
        """
        给对应的日志文件写入日志
        Args：
            write_file(str): 日志文件名称, 是runtime文件还是error文件
         """
        write_file.writelines("".join([WriteLog.get_now_time(), ": [", log_type, "]",msg, '\n']))
        write_file.flush()

    def _log(self,log_type,msg):
        """
        根据日志类别判断写入对应的日志类别文件
            Args:
             log_type(str): 日志类别，error, warn, pass, done等
             msg(str): 日志信息
        """
        WriteLog._write(self.runtime_file, log_type, msg)

    def log_pass(self,msg):
        self._log("pass", msg)

    def log_done(self,msg):
           self._log("done", msg)

    def log_warn(self,msg):
        self._log("warn", msg)

    def log_error(self,msg):
        self._log("error", msg)

    def screenslot(self,device,filename=""):
        device.screenshot(os.path.join(self.screenslot_dir,WriteLog.get_now_time().replace(":","") + "_+"+filename+".jpg"))

class TestRunError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self, value):
        return str(self.value)





