import os
import requests #Used to service API connection
from lxml import html #Used to parse XML
from bs4 import BeautifulSoup #Used to read XML table on webpage
import pandas as pd
from pandas.io.json import json_normalize
# from tabula import read_pdf

def makeURL(myUrl, myKey, myParameter):
    # myUrl = "http://192.168.1.120/index.php?"
    url = myUrl + myKey + "&" + myParameter

    url = url.rstrip('&')
    return url

def xmlProcess(url):
    response = requests.get(url)
    # Check if page is up
    if response.status_code == 200:
        # Convert webpage to %Data
        Data = BeautifulSoup(response.text, 'lxml-xml')
        result = []
        rows = 0
        columnName = []
        # search Item all item tag
        iterData = Data.find_all('item')
        for item in iterData:
            item_list = []
            # Fill the value in one row
            for tag in item.find_all():
                try:
                    tagname = tag.name
                    if rows == 0:
                        columnName.append(tagname)
                    item_list.append(item.find(tagname).text)
                except Exception as e:
                    print("This row will be ignored. ", item_list)
            rows = rows + 1
            result.append(item_list)
    finalResult = pd.DataFrame(result)
    finalResult.columns = columnName
    print(finalResult)
    return finalResult


def jsonProcess(url):

    # 정상 여부 확인 (200 정상)
    response = requests.get(url)
    # JSON 데이터 획득
    json = response.json()
    # PandasDataframe변환
    df = json_normalize(json)
    return df

def csvProcess(url):

    # 정상 여부 확인 (200 정상)
    response = requests.get(url)

    df = pd.read_csv(url, encoding="ms949")
    return df

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

def pdfProcess(url):

    # 정상 여부 확인 (200 정상)
    response = requests.get(url)

    df = read_pdf("../../data/inbound/190402_금융시장동향.pdf", multiple_tables=True, pages="all")
    return df

def atypical_xml_process(url):
    response = requests.get(url)
    if response.status_code == 200:
        Data = BeautifulSoup(response.text, 'lxml-xml')
        allData = Data.find_all()
        
        tagLevelUp = 0
        tagLevelDown = 0
        
        # 태그의 레벨을 기록할 딕셔너리 생성
        recordDict = {}
        
        
        ### xml 데이터의 모든 태그를 검색하여 각 태그의 단계를 기록
        ## xml 데이터에 존재하는 모든 태그에 대해 반복
        for findTagIndex in range(0, len(allData)):
            # 찾을 태그명
            findTagName = allData[findTagIndex].name
            
            ## 이미 검색된 태그인지 검사
            alreadySearched = False
            for eachDictKeyIndex in range(0, len(recordDict)):
                eachDictValues = recordDict[eachDictKeyIndex]
                for eachDictValueIndex in range(0, len(eachDictValues)):
                    if (findTagName == eachDictValues[eachDictValueIndex]):
                        break
                if (findTagName == eachDictValues[eachDictValueIndex]):
                    alreadySearched = True
                    break
            
            ## 이미 검색된 태그에 대해서 상위태그 검색 생략
            if alreadySearched == True:
                continue
            
            ## 찾을 태그의 차상위 단계 부터 최상위 단계 까지 반복
            for upperTagIndex in range((findTagIndex - 1), -1, -1):
                # 데이터의 상위태그명
                upperTag = allData[upperTagIndex]
                upperTagName = upperTag.name
                # 상위 태그에 존재하는 모든 하위태그
                findLowerTag = upperTag.find_all()

                # 하위태그의 수만큼 반복
                for lowerTagIndex in range(0, len(findLowerTag)):
                    # 각 하위태그명
                    lowerTagName = findLowerTag[lowerTagIndex].name
                    # 찾을 값이 어느 상위태그 아래에 있는지 검색
                    if (findTagName == lowerTagName):
                        break
                # 상위태그보다 1단계 위의 레벨 기록
                if (findTagName == lowerTagName):
                    tagLevelUp = upperTagIndex + 1
                    break

            # 태그가 속한 레벨
            tagLevel = tagLevelUp - tagLevelDown

            ## 차상위 태그가 존재하는지 검색 (예외적인 태그 구성에 대한 조치)
            try:
                # 차상위 태그가 없을 경우 KeyError 발생
                checkError = recordDict[tagLevel - 1]
            except:
                # 현재까지 만들어진 딕셔너리의 값
                for currentEachValueIndex in range(0, len(recordDict)):
                    eachDictValues = recordDict[currentEachValueIndex]
                    # 차상위 태그가 위치한 레벨을 검색
                    for eachDictValueIndex in range(0, len(eachDictValues)):
                        eachDictValue = eachDictValues[eachDictValueIndex]
                        if eachDictValue == upperTagName:
                            break
                    if (eachDictValue == upperTagName):
                        tagLevelDown = tagLevelUp - (currentEachValueIndex + 1)
                        break
                # 올바른 태그 레벨 반환
                tagLevel = tagLevelUp - tagLevelDown

            try:
                # 딕셔너리의 해당 태그 레벨에 값 추가
                recordDict[tagLevel].append(findTagName)
            except:
                # 해당 태그 레벨에 값이 없을 경우 값 넣기
                recordDict[tagLevel] = [findTagName]
        
        if (len(recordDict) == 0):
            print("No Tag Searched")
            return None
        
        ### 생성된 딕셔너리에서 itemList와 separatorTag 검색
        findMaxItemList = []
        for eachDictKeyIndex in range(0, len(recordDict)):
            # 딕셔너리의 각 값의 길이를 리스트에 추가
            findMaxItemList.append(len(recordDict[eachDictKeyIndex]))
            
        # 길이가 가장 긴 item 기록
        maxItemKinds = max(findMaxItemList)
        
        if len(recordDict) > 1:
            for eachDictKeyIndex in range(1, len(recordDict)):
                # 딕셔너리의 상위레벨부터 max값과 비교
                if (maxItemKinds == len(recordDict[eachDictKeyIndex])):
                    # 해당 값들을 itemList에 기록
                    itemList = recordDict[eachDictKeyIndex]
                    # 해당 값들을 포함하는 차상위 태그를 separatorTag에 선언
                    for upperKeyIndex in range((eachDictKeyIndex - 1), -1, -1):
                        if (len(recordDict[upperKeyIndex]) == 1):
                            upperTagValue = recordDict[upperKeyIndex]
                            break
                        else:
                            continue
                    try:
                        separatorTag = upperTagValue[0]
                    except:
                        separatorTag = recordDict[0][0]
                    break
        else:
            print('Item Level is Only One')
            iterData = Data.find_all(recordDict[0][0])
            for dataRow in range(0, len(iterData)):
                columnName = iterData[0].name
                resultData = iterData[dataRow].text
            finalResult = pd.DataFrame(data = [resultData], columns = [columnName])
            return finalResult
        
        
        ### 데이터 프레임을 만들 최종 딕셔너리 생성
        # 값을 담을 딕셔너리 공간 생성
        resultDict = {}
        # 딕셔너리의 각 키를 itemList로 생성하며, 각 값을 넣을 공간을 리스트로 생성
        for eachItem in itemList:
            resultDict[eachItem] = []
        iterData = Data.find_all(separatorTag)
        # 데이터의 길이만큼 반복(row)
        for dataRow in range(0, len(iterData)):
            # itemList만큼 반복(column)
            for dataColumn in range(0, len(itemList)):
                eachData = iterData[dataRow].find_all(itemList[dataColumn])
                # 각 값을 담을 리스트 생성 후 값 담기
                eachItemList = []
                for eachText in range(0, len(eachData)):
                    tag = eachData[eachText]
                    eachItemList.append(tag.text)
                
                # 결측값 조치
                if (len(eachItemList) == 0):
                    resultDict[itemList[dataColumn]].append('')
                # 값이 있을 경우 추가
                elif (len(eachItemList) == 1):
                    resultDict[itemList[dataColumn]] += eachItemList
                # 값이 2개 이상 있을 경우 리스트로 묶어서 추가
                else:
                    resultDict[itemList[dataColumn]].append(eachItemList)
        ### 데이터 프레임을 만들고 return
        finalResult = pd.DataFrame(resultDict, columns = itemList)
        return finalResult
    
    else:
        print('Bad Response', response.status_code)
        return None