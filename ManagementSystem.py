from pprint import pprint
from typing import List
from datetime import datetime
from pandas import read_excel, DataFrame
from pathlib import Path


class ManagementSystem:
    @property
    def save_path(self):
        return Path("data") / "speak" / (self.class_name + datetime.now().strftime("-%Y-%m-%d-%H%M%S.xlsx"))

    def __init__(self):
        self.speak = {}
        self.students = self.read_students()
        self.class_name_list = self.input()
        self.class_name = "-".join(self.class_name_list)
        print("选择班级", self.class_name)
        self.class_student = list()
        for name in self.class_name_list:
            self.class_student += list(self.students[name].dropna().values)
        self.student_length: int = len(self.class_student)

    def to_speak(self, name: str, msg: str):
        """学生发言保存"""
        if name in self.class_student:
            if not self.speak.get(name, None):
                self.speak[name] = []
            self.speak[name].append(msg or "[图片]")

    def input(self) -> List[str]:
        """选择班级"""
        print("[选择班级]")
        for i, name in enumerate(self.students.columns.values):
            print(f" [{i}]\t{name}")
        class_index = input("[FAQ]\n   "
                            "单个班级输入一个数字(例如: 0)\n   "
                            "如果一堂课有多个班级可以写多个数字(例如：0 1)\n[输入数字]: ").split()
        return [self.students.columns.values[int(i)] for i in class_index if i.isdigit()]

    def search(self, users: list):
        """寻找不在直播间的用户"""
        class_student = list(self.class_student)
        for user in users:
            for student in class_student:
                if student in user:
                    class_student.remove(student)
                    break
        return class_student

    def class_student_name(self, name: str) -> str:
        """寻找学生姓名"""
        if name not in self.class_student:
            for student in self.class_student:
                if student in name:
                    return student
        return name

    @staticmethod
    def read_students() -> DataFrame:
        """读取学生"""
        return read_excel("ClassStudents.xlsx", sheet_name=0)

    def save_speak(self):
        if self.speak:
            pprint(self.speak)
            DataFrame(self.speak).to_excel(self.save_path, index=False)
            print("课堂讨论文件保存", self.save_path)



