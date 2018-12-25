#!/usr/bin/env python
# -*- coding:utf-8 -*-

#./autobuild.py -p youproject.xcodeproj -s schemename
#./autobuild.py -w youproject.xcworkspace -s schemename

import argparse
import subprocess
import requests
import os

SCHEMENAME = "AskDoctor"
#configuration for iOS build setting
CONFIGURATION = "Debug"
# method:打包方式值：app-store, ad-hoc, enterprise, development
EXPORT_OPTIONS_PLIST = "exportOptions.plist"
#会在桌面创建输出ipa文件的目录
EXPORT_MAIN_DIRECTORY = "~/Desktop/"

#上传蒲公英或者Appstore
POSTPGY = True
# configuration for pgyer
PGYER_UPLOAD_URL = "http://www.pgyer.com/apiv1/app/upload"
DOWNLOAD_BASE_URL = "http://www.pgyer.com"
USER_KEY = "15d6xxxxxxxxxxxxxxxxxx"
API_KEY = "efxxxxxxxxxxxxxxxxxxxx"
#设置从蒲公英下载应用时的密码
PYGER_PASSWORD = "" 
# 蒲公英更新描述
PGYDESC = ""
#appstore用户名
APPSOTREUSERID = ''
#appstore密码
APPSOTREPASSWORD = ''

#上传到App Store
#参考官网 https://help.apple.com/itc/apploader/#/apdATD1E53-D1E1A1303-D1E53A1126
def uploadAppstore(ipaPath):
    print("ipaPath:",ipaPath)
    ipaPath = os.path.expanduser(ipaPath)
    print('正在验证ipa文件,请稍后...')
    r1 = os.system('{} -v -f {} -u {} -p {} -t ios [--output-format xml]'%(altool_path, ipaPath, APPSOTREUSERID, APPSOTREPASSWORD))
    print("验证的结果是:")
    print(r1)
    if r1 == noError:
        print('正在上传ipa文件,请稍后...')
        r2 = os.system('{} --upload-app -f {} -t ios -u {} -p {} [--output-format xml]'%(altool_path, ipaPath, APPSOTREUSERID, APPSOTREPASSWORD))
        print(r2)
        return r2
    else:
        return 1



def cleanArchiveFile(archiveFile):
    cleanCmd = 'rm -r {}'.format(archiveFile)
    process = subprocess.Popen(cleanCmd,shell=True)
    process.wait()
    print("cleaned archiveFile: {}".format(archiveFile))


def parserUploadResult(jsonResult):
	resultCode = jsonResult['code']
	if resultCode == 0:
		downUrl = DOWNLOAD_BASE_URL +"/"+jsonResult['data']['appShortcutUrl']
		print("Upload Success")
		print("DownUrl is:", downUrl)
	else:
		print("Upload Fail!")
		print("Reason:",jsonResult['message'])

def uploadIpaToPgyer(ipaPath):
    print("ipaPath:",ipaPath)
    ipaPath = os.path.expanduser(ipaPath)
    files = {'file': open(ipaPath, 'rb')}
    headers = {'enctype':'multipart/form-data'}
    payload = {'uKey':USER_KEY,'_api_key':API_KEY,'publishRange':'2','isPublishToPublic':'2', 'password':PYGER_PASSWORD, 'updateDescription':PGYDESC}
    print("update desc：" , PGYDESC)
    print("uploading....")
    r = requests.post(PGYER_UPLOAD_URL, data = payload ,files=files,headers=headers)
    if r.status_code == requests.codes.ok:
        result = r.json()
        parserUploadResult(result)
    else:
        print('HTTPError,Code:', r.status_code)

#创建输出ipa文件路径: ~/Desktop/{scheme}{2016-12-28_08-08-10}
def buildExportDirectory(scheme):
    dateCmd = 'date"+%Y-%m-%d_%H-%M-%S"'
    process = subprocess.Popen(dateCmd, stdout=subprocess.PIPE, shell=True)
    (stdoutdata, stderrdata) = process.communicate()
    exportDirectory = "{}{}{}".format(EXPORT_MAIN_DIRECTORY, scheme,stdoutdata.strip())
    return exportDirectory

def buildArchivePath(tempName):
    process = subprocess.Popen("pwd", stdout=subprocess.PIPE)
    (stdoutdata, stderrdata) = process.communicate()
    archiveName = "{}.xcarchive".format(tempName)
    archivePath = (str)(stdoutdata.strip()) + '/' + archiveName
    return archivePath

def getIpaPath(exportPath):
    cmd = "ls {}".format(exportPath)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (stdoutdata, stderrdata) = process.communicate()
    ipaName = stdoutdata.strip()
    ipaPath = (str)(exportPath) + "/" + (str)(ipaName)
    return ipaPath

def exportArchive(scheme, archivePath):
    exportDirectory = buildExportDirectory(scheme)
    exportCmd = "xcodebuild -exportArchive -archivePath {} -exportPath {} -exportOptionsPlist {}".format(archivePath, exportDirectory, EXPORT_OPTIONS_PLIST)
    process = subprocess.Popen(exportCmd, shell=True)
    (stdoutdata, stderrdata) = process.communicate()

    signReturnCode = process.returncode
    if signReturnCode != 0:
        print("export {} failed".format(scheme))
        return ""
    else:
        return exportDirectory

def buildProject(project, scheme):
    archivePath = buildArchivePath(scheme)
    print("archivePath: ",archivePath)
    archiveCmd = 'xcodebuild -project {} -scheme {} -configuration {} archive -archivePath {} -destination generic/platform=iOS'.format(project, scheme, CONFIGURATION, archivePath)
    process = subprocess.Popen(archiveCmd, shell=True)
    process.wait()

    archiveReturnCode = process.returncode
    if archiveReturnCode != 0:
        print("archive workspace {} failed".format(workspace))
        cleanArchiveFile(archivePath)
    else:
        exportDirectory = exportArchive(scheme, archivePath)
        cleanArchiveFile(archivePath)
        if exportDirectory != "":
            ipaPath = getIpaPath(exportDirectory)
            if POSTPGY:
                uploadIpaToPgyer(ipaPath)
            else:
                uploadAppstore(ipaPath)

def buildWorkspace(workspace, scheme):
    archivePath = buildArchivePath(scheme)
    print("archivePath: " , archivePath)
    archiveCmd = 'xcodebuild -workspace {} -scheme {} -configuration {} archive -archivePath {} -destination generic/platform=iOS'.format(workspace, scheme, CONFIGURATION, archivePath)
    process = subprocess.Popen(archiveCmd, shell=True)
    process.wait()

    archiveReturnCode = process.returncode
    if archiveReturnCode != 0:
        print("archive workspace {} failed".format(workspace))
        cleanArchiveFile(archivePath)
    else:
        exportDirectory = exportArchive(scheme, archivePath)
        cleanArchiveFile(archivePath)
        if exportDirectory != "":
            ipaPath = getIpaPath(exportDirectory)
            if POSTPGY:
                uploadIpaToPgyer(ipaPath)
            else:
                uploadAppstore(ipaPath)

def xcbuild(options):
    project = options.project
    workspace = options.workspace
    scheme = options.scheme
    desc = options.desc

    if not workspace:
        scheme = SCHEMENAME
        workspace = '../' + SCHEMENAME + '.xcworkspace'

    global PGYDESC
    PGYDESC = desc

    if project is None and workspace is None:
        pass
    elif project is not None:
        buildProject(project, scheme)
    elif workspace is not None:
        buildWorkspace(workspace, scheme)

def main():
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-w", "--workspace", help="Build the workspace name.xcworkspace.", metavar="name.xcworkspace")
	parser.add_argument("-p", "--project", help="Build the project name.xcodeproj.", metavar="name.xcodeproj")
	parser.add_argument("-s", "--scheme", help="Build the scheme specified by schemename. Required if building a workspace.", metavar="schemename")
	parser.add_argument("-m", "--desc", help="Pgyer update description.", metavar="description")
	options = parser.parse_args()

	print("options: %s",(options))

	xcbuild(options)

if __name__ == '__main__':
	main()
