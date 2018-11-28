# -*- coding: utf-8 -*-

import configparser
import os
import xlrd


config = configparser.ConfigParser()
configFileName = "config.ini"


# ip 转换： int 转 str
def int2ip(x):
    return ".".join([str(int(x / (256 ** i) % 256)) for i in range(3, -1, -1)])


# ip 转换： str 转 int
def ip2int(x):
    return sum([256 ** j * int(i) for j, i in enumerate(x.split(".")[::-1])])


# ip 字符串 10.10.10.10/32 转成数组: ip/mask/ip_start/ip_end
def ipParse(ipStr):
    if ipStr == "":
        return [None, None, None, None]
    maskLen = 32
    if "/" in ipStr:
        ipStr, maskLen = ipStr.split("/")
    print(ipStr, maskLen)
    mask = 0xFFFFFFFF << (32 - int(maskLen))
    print("mask:", mask)
    ipInt = ip2int(ipStr)
    ipStart = ipInt & mask & 0xFFFFFFFF
    ipEnd = ipInt | ~mask & 0xFFFFFFFF
    return [ipInt, mask, ipStart, ipEnd]


# ip, mask 转成 字符串 10.10.10.10/32
def ipImport(ipInt, mask):
    pass


# 检查配置格式是否正确
def checkConfig(configFileName):
    global config
    config.read(configFileName)
    sections = config.sections()
    sectionLens = len(sections)
    if sectionLens < 4:
        return False
    # 每个 section 中的 options 的个数必须是相同的
    for i in range(1, sectionLens):
        if i < sectionLens - 1:
            n1 = len(config.options(sections[i]))
            n2 = len(config.options(sections[i + 1]))
            if n1 == 0 | n1 != n2:
                return False
    # 可进一步判断 options 名是否一致
    pass
    return True


# 释放默认配置
def writeConfig(configFileName):
    global config
    config.add_section("对比文件名")
    config.set("对比文件名", "省内资管", "IP地址.")
    config.set("对比文件名", "集团", "-IP地址-")
    config.set("对比文件名", "工信部备案", "fpxxList")
    config.add_section("省内资管")
    config.set("省内资管", "ip", "IP地址")
    config.set("省内资管", "field2", "联系人姓名(客户侧)")
    config.set("省内资管", "field3", "联系电话(客户侧)")
    config.set("省内资管", "field4", "分配使用时间")
    config.set("省内资管", "field5", "单位详细地址")
    config.set("省内资管", "field6", "联系人邮箱(客户侧)")
    config.set("省内资管", "field7", "单位名称/具体业务信息")
    config.add_section("集团")
    config.set("集团", "ip", "网段名称")
    config.set("集团", "field2", "联系人姓名(客户侧)")
    config.set("集团", "field3", "联系人电话(客户侧)")
    config.set("集团", "field4", "分配使用时间")
    config.set("集团", "field5", "单位详细地址")
    config.set("集团", "field6", "联系人邮箱(客户侧)")
    config.set("集团", "field7", "单位名称/具体业务信息")
    config.add_section("工信部备案")
    config.set("工信部备案", "ip", "起始IP;终止IP")
    config.set("工信部备案", "field2", "联系人姓名")
    config.set("工信部备案", "field3", "联系人电话")
    config.set("工信部备案", "field4", "分配日期")
    config.set("工信部备案", "field5", "单位详细地址")
    config.set("工信部备案", "field6", "联系人电子邮件")
    config.set("工信部备案", "field7", "使用单位名称")
    with open(configFileName, "w") as configFile:
        configFile.write(
            "# Author: Xianda\n\n# 本配置为一致性检查工具的配置\n# 如删除本配置文件，重新生成的配置文件即为默认配置\n# 如需修改配置，修改本文件后直接保存即可\n\n######\n\n# 若 IP 地址字段分为起始IP、终止IP的，`ip` 字段中用“;”(英文分号)隔开\n# 程序会依次对 field 字段进行对比并输出对比结果\n# field 字段有变化可直接在此增删改，满足一一对应即可\n\n\n\n"
        )
        config.write(configFile)


# 初始化配置
def initConfig():
    global configFileName
    if os.path.exists(configFileName):
        if checkConfig(configFileName):
            # 配置检查通过，开始对比数据
            contrast()
        else:
            print("配置中 field 字段的个数不一致，请核对！")
            os.system("pause")
    else:
        # 释放默认配置，开始对比数据
        writeConfig(configFileName)
        contrast()


# 读取配置
def readConfig(section, option):
    global config
    global configFileName
    config.read(configFileName)
    value = config.get(section, option)
    return value


# 匹配导出数据文件名
def matchedFileName():
    global config
    global configFileName
    fileName = {}
    config.read(configFileName)
    for option in config.options("对比文件名"):
        value = config.get("对比文件名", option)
        for f in os.listdir():
            if value in f:
                fileName[option] = f
    return fileName


# 生成中间文件，转换导出数据为每一行一个 ip
def generateTemp(fileName):
    global config
    # print(list(fileName.keys())[0])
    # print(config.options(list(fileName.keys())[0]))
    colNames = {}
    ipCols = {}
    for k, v in fileName.items():
        xls = xlrd.open_workbook(v)
        # 获取最后一个 sheet
        sheet = xls.sheet_by_index(len(xls.sheet_names()) - 1)
        # 默认将第一行做为列名所在的行
        colsName = sheet.row_values(0)
        colNames[k] = {}
        ipCols[k] = []
        fields = config.options(k)
        # 遍历配置文件中要对比的列名 记录要对比的字段所在的列
        for field in fields:
            # 遍历导出数据的第一行单元格
            for i in range(0, len(colsName)):
                configValue = config.get(k, field)
                # 配置的列名包含导出数据的列名时（为了匹配ip列为多列的情况）
                if str(colsName[i].strip()) in configValue:
                    if "field" in field:
                        # 记录要对比的字段所在的列
                        colNames[k][field] = i
                    elif "ip" == field:
                        # 记录 ip 所在的列
                        ipCols[k].append(i)
    print("colNames", colNames)
    print("ipCols", ipCols)
    # 基于 ip 列 生成中间文件，并补充 ipStart、ipEnd 列
    # todo
    # os.mkdir('\\_temp')
    pdatadir = os.environ.get('ALLUSERSPROFILE') # C:\\ProgramData
    if os.path.exists(pdatadir):
        os.mkdir('%s\\ipContrast' %(pdatadir))


def contrast():
    # 获取导出文件的文件名
    fileName = matchedFileName()
    print("fileName", fileName)
    generateTemp(fileName)
    return
    # 根据配置，第一个字段为查询索引，对比其余字段是否一致

    # 打开文件
    zgg = xlrd.open_workbook("demo.xlsx")
    # jt = xlrd.open_workbook(r'ip-jt.xlsx')
    # print zgg.name

    print(zgg.sheet_names())
    sheet2 = zgg.sheet_by_index(0)  # sheet索引从0开始
    # sheet2 = zg.sheet_by_name('sheet2')
    # sheet的名称，行数，列数
    print(sheet2.name, sheet2.nrows, sheet2.ncols)
    # 获取整行和整列的值（数组）
    rows = sheet2.row_values(3)  # 获取第四行内容
    # cols = sheet2.col_values(2) # 获取第三列内容
    print(rows)
    # print cols
    # 获取单元格内容
    print(str(sheet2.cell(1, 0).value))
    print(int(sheet2.cell_value(1, 0)))
    print(sheet2.row(1)[0].value)


# @测试 configparser
def _test_configparser():
    global config
    config.read("config.ini")
    sections = config.sections()
    for x in sections:
        options = config.options(x)
        for y in options:
            print(config.get(x, y))


if __name__ == "__main__":
    initConfig()
    # print("aaa",readConfig('集团','field2'))
