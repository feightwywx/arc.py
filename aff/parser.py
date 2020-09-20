#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Author: .direwolf <kururinmiracle@outlook.com>
# Licensed under the MIT License.

import re
from . import note
from . import sorter


# 正则表达式
patt_offset = r'AudioOffset:(-*\d+)'
patt_tap = r'\((\d+),([1-4])\);'
patt_hold = r'hold\((\d+),(\d+),([1-4])\);'
patt_arc = r'arc\((\d+),(\d+),(-*\d+[.\d+]*),(-*\d+[.\d+]*),([a-z]{1,4}),(-*\d+[.\d+]*),(-*\d+[.\d+]*),([0-2]),' \
             r'([a-z]+),([a-z]+)\).*;'
patt_arctap = r'arctap\(([0-9]+)\)'
patt_timing = r'timing\((\d+),(-*\d+[.\d+]*),(\d+[.\d+]*)\);'
patt_camera = r'camera\((\d+),(-*\d+[.\d+]*),(-*\d+[.\d+]*),(-*\d+[.\d+]*),(-*\d+[.\d+]*),(-*\d+[.\d+]*),' \
              r'(-*\d+[.\d+]*),([a-z]+),(\d+)\);'
patt_scene = r'scenecontrol\((\d+),([a-z]+)(,(\d+[.\d+]*),(\d+))?\);'


def append(noteobj, path: str):  # TODO 向aff追加note的功能——！
    pass


def __dumpline(noteobj: note.Note):
    return str(noteobj)


def dump(notelist: list):
    notelist = sorter.sort(notelist)
    affstr = ''
    isfirsthyphen = False
    for eachline in notelist:
        if eachline:
            affstr += (str(eachline) + '\n')
        if type(eachline).__name__ == 'AudioOffset' and not isfirsthyphen:
            affstr += '-\n'
            isfirsthyphen = True
    return affstr


def dumps(notelist: list, destpath: str):
    notelist = sorter.sort(notelist)
    print(notelist)
    isfirsthyphen = False
    with open(destpath, 'w') as faff:
        for eachline in notelist:
            if eachline:
                faff.write(str(eachline) + '\n')
            if type(eachline).__name__ == 'AudioOffset' and not isfirsthyphen:
                faff.write('-\n')
                isfirsthyphen = True
    return True


def __serialgroup(notelist):
    tmpgroup = []
    currlen = len(notelist)
    for i in range(currlen - 1):
        if i < len(notelist) and notelist[i] == '_groupbegin_':
            notelist.pop(i)  # 扔掉初始标记
            # 哦我的上帝，这循环比隔壁苏珊阿姨的苹果派还要烂，让我直想穿皮靴狠狠踹你的屁股
            while True:
                try:
                    if notelist[i] == '_groupend_':
                        notelist.pop(i)  # 扔掉结束标记，
                        break  # 然后跳出死循环
                except IndexError:  # 没有找到timinggroup结束标记
                    pass
                tmpgroup.append(notelist[i])
                notelist.pop(i)
            notelist.insert(i, note.TimingGroup(tmpgroup))
            tmpgroup = []

    return notelist


def __loadline(notestr: str):
    noteobj = None
    if re.match(patt_offset, notestr):
        offset = re.findall(patt_offset, notestr)[0]
        noteobj = note.AudioOffset(int(offset))
    elif re.match(patt_tap, notestr):
        notepara = re.findall(patt_tap, notestr)[0]
        noteobj = note.Tap(time=int(notepara[0]), lane=int(notepara[1]))
    elif re.match(patt_hold, notestr):
        notepara = re.findall(patt_hold, notestr)[0]
        noteobj = note.Hold(time=int(notepara[0]), totime=int(notepara[1]), lane=int(notepara[2]))
    elif re.match(patt_arc, notestr):
        notepara = re.findall(patt_arc, notestr)[0]
        noteeasing, notecolor, notefx = None, None, None
        arctap = re.findall(patt_arctap, notestr)

        # 转换为枚举类型
        for each in note.SlideEasing:
            if each.value == notepara[4]:
                noteeasing = each
        for each in note.ArcColor:
            if each.value == int(notepara[7]):
                notecolor = each
        for each in note.FX:
            if each.value == notepara[8]:
                notefx = each

        noteobj = note.Arc(time=int(notepara[0]), totime=int(notepara[1]), fromx=float(notepara[2]),
                           fromy=float(notepara[3]), slideeasing=notepara[4], tox=float(notepara[5]),
                           toy=float(notepara[6]), color=int(notepara[7]), fx=notepara[8],
                           isskyline=bool(notepara[9]), skynote=arctap)

        # 如果不为None就设置属性
        if noteeasing:
            noteobj.slideeasing = noteeasing
        if notecolor:
            noteobj.color = notecolor
        if notefx:
            noteobj.fx = notefx
        if arctap:
            noteobj.skynote = arctap
    elif re.match(patt_timing, notestr):
        notepara = re.findall(patt_timing, notestr)[0]
        noteobj = note.Timing(time=int(notepara[0]), bpm=float(notepara[1]), bar=float(notepara[2]))
        return noteobj
    elif re.match(patt_camera, notestr):
        notepara = re.findall(patt_camera, notestr)[0]
        noteobj = note.Camera(int(notepara[0]), float(notepara[1]), float(notepara[2]), float(notepara[3]),
                              float(notepara[4]), float(notepara[5]), float(notepara[6]), str(notepara[7]),
                              int(notepara[8]))
    elif re.match(patt_scene, notestr):
        notepara = re.findall(patt_scene, notestr)[0]
        print(notepara)
        noteobj = note.SceneControl(int(notepara[0]), str(notepara[1]))
        try:
            if notepara[3]:
                noteobj.x = float(notepara[3])
            if notepara[4]:
                noteobj.y = int(notepara[4])
        except IndexError:
            pass
        return noteobj
    elif notestr == 'timinggroup(){':  # flag
        return '_groupbegin_'
    elif notestr == '};':
        return '_groupend_'

    return noteobj


def load(affstr: str):
    notestrlist = affstr.splitlines()
    notelist = []
    for eachline in notestrlist:
        notelist.append(__loadline(eachline))
    return __serialgroup(notelist)


def loads(path: str):
    notelist = []
    with open(path, mode='r') as faff:
        for eachline in faff:
            notelist.append(__loadline(eachline[:-1]))
    print(notelist)
    return __serialgroup(notelist)
