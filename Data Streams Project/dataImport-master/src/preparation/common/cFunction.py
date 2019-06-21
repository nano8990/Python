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
        
        recordDict = {}  
        
        # Search all tags in xml data for record the steps for each tag
        for findTagIndex in range(0, len(allData)):
            # tagName to Search
            findTagName = allData[findTagIndex].name
            
            alreadySearched = False
            for eachDictKeyIndex in range(0, len(recordDict)):
                eachDictValues = recordDict[eachDictKeyIndex]
                
                for eachDictValueIndex in range(0, len(eachDictValues)):
                    if (findTagName == eachDictValues[eachDictValueIndex]):
                        break
                if (findTagName == eachDictValues[eachDictValueIndex]):
                    alreadySearched = True
                    break
            
            if alreadySearched == True:
                continue
            
            for upperTagIndex in range((findTagIndex - 1), -1, -1):
                upperTag = allData[upperTagIndex]
                upperTagName = upperTag.name
                findLowerTag = upperTag.find_all()

                for lowerTagIndex in range(0, len(findLowerTag)):
                    lowerTagName = findLowerTag[lowerTagIndex].name
                    if (findTagName == lowerTagName):
                        tagLevelUp = upperTagIndex + 1
                        break
                if (findTagName == lowerTagName):
                    break

            tagLevel = tagLevelUp - tagLevelDown

            ## Search for presence of next-level tags (action on exceptional tag configuration)
            try:
                checkError = recordDict[tagLevel - 1]
                del checkError
                
            except:
                for currentEachValueIndex in range(0, len(recordDict)):
                    eachDictValues = recordDict[currentEachValueIndex]
                    for eachDictValueIndex in range(0, len(eachDictValues)):
                        eachDictValue = eachDictValues[eachDictValueIndex]
                        if eachDictValue == upperTagName:
                            tagLevelDown = tagLevelUp - (currentEachValueIndex + 1)
                            break
                    if (eachDictValue == upperTagName):
                        break
                
                tagLevel = tagLevelUp - tagLevelDown
                '''
                ### New tagLevel Calculation Equation
                tagLevelDown = tagLevelUp - (currentEachValueIndex + 1)
                tagLevel = tagLevelUp - tagLevelDown
                         = tagLevelUp - (tagLevelUp - (currentEachValueIndex + 1))
                tagLevel = currentEachValueIndex + 1
                '''

            try:
                recordDict[tagLevel].append(findTagName)
                
            except:
                recordDict[tagLevel] = [findTagName]
        
        if (len(recordDict) == 0):
            print("No Tag Searched")
            return None
        
        # Search for itemList and separatorTag in the generated Dictionary
        findMaxItemList = []
        for eachDictKeyIndex in range(0, len(recordDict)):
            findMaxItemList.append(len(recordDict[eachDictKeyIndex]))
            
        # Longest item record
        maxItemKinds = max(findMaxItemList)
        
        if len(recordDict) > 1:  
            for eachDictKeyIndex in range(1, len(recordDict)):
                if (maxItemKinds == len(recordDict[eachDictKeyIndex])):
                    itemList = recordDict[eachDictKeyIndex]
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
                    
                    finally:
                        break
        else:
            print('Item Level is Only One')
            iterData = Data.find_all(recordDict[0][0])
            for dataRow in range(0, len(iterData)):
                columnName = iterData[0].name
                resultData = iterData[dataRow].text
            finalResult = pd.DataFrame(data = [resultData], columns = [columnName])
            return finalResult
        
        
        # Create Final Dictionary to Create Data Frame
        resultDict = {}
        
        for eachItem in itemList:
            resultDict[eachItem] = []
            
        iterData = Data.find_all(separatorTag)
        
        for dataRow in range(0, len(iterData)):
            for dataColumn in range(0, len(itemList)):
                eachData = iterData[dataRow].find_all(itemList[dataColumn])
                
                eachItemList = []
                for eachText in range(0, len(eachData)):
                    tag = eachData[eachText]
                    eachItemList.append(tag.text)
                
                if (len(eachItemList) == 0):
                    resultDict[itemList[dataColumn]].append('')

                elif (len(eachItemList) == 1):
                    resultDict[itemList[dataColumn]] += eachItemList

                else:
                    resultDict[itemList[dataColumn]].append(eachItemList)

        finalResult = pd.DataFrame(resultDict, columns = itemList)
        return finalResult
    
    ### if not response.status_code == 200
    else:
        print('Bad Response', response.status_code)
        return None