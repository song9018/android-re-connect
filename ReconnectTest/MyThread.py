#!/usr/bin/env python
# -*- coding:utf-8 -*-
import threading


class MyThread(object):
    def __init__(self, func_list=None):
        self.func_list = func_list
        self.threads = []
        self.result_list = []

    def set_thread_func_list(self, func_list):
        self.func_list = func_list

    def start(self):
        self.threads = []
        for func_dict in self.func_list:
            if 'args' in func_dict.keys():
                new_arg_list = []
                new_arg_list.append(func_dict["func"])  # trace_func(self,func, *args,**kwargs)
                for arg in func_dict["args"]:
                    new_arg_list.append(arg)
                new_arg_tuple = tuple(new_arg_list)
                t = threading.Thread(target=self.trace_func, args=new_arg_tuple)
                self.threads.append(t)

            else:
                t = threading.Thread(target=self.trace_func, args=(func_dict["func"],))
                self.threads.append(t)
        for thread_obj in self.threads:
            thread_obj.start()

        for thread_obj in self.threads:
            thread_obj.join()

    def trace_func(self, func, *args, **kwargs):

        dis = []
        print('print trace_func:  func: %s args:  %s kwargs: %s' % (func, args, kwargs))
        ret = func(*args, **kwargs)
        dis = dict(ret=ret, func=func, args=args)
        print("over")
        self.result_list.append(dis)

    def ret_value(self):
        return self.result_list
