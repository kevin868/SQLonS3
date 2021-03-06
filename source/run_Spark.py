from pyspark.sql.types import *  
from pyspark.sql.functions import *
from datetime import datetime
import subprocess

#from time_op import *
import time
def timeOp(dataframeOp):
    t0 = time.time()
    output = eval(dataframeOp)
    t1 = time.time()
    print(output)
    print('*Query time: ' + str((t1 - t0))+'*')
    return (t1 - t0)

def getTimeString(utcTime):
    return datetime.fromtimestamp(int(utcTime)).strftime('%Y-%m-%d,%H:%M:%S')
#def mapQuery(queryNum):
mapQuery = {
    1 : "SELECT count(1) AS numPosts from SparkTempTable",
    2 : "SELECT author, avg(score) as avgScore from SparkTempTable GROUP BY author ORDER BY avgScore DESC limit 10",
    3 : "SELECT count(1) from SparkTempTable WHERE body like '%San Francisco%'",
    4 : "SELECT a.author, a.parent_id, a.score, b.author, b.parent_id, b.subreddit, b.name, b.score,\
            b.link_id from SparkTempTable AS a, SparkTempTable AS b WHERE a.year =b.year AND  a.score > 1000 AND\
            a.parent_id LIKE 't3%' AND a.name = b.parent_id AND b.score > a.score ORDER BY b.score DESC LIMIT 10",
    5 : "SELECT count(1) FROM (SELECT a.parent_id, a.score, b.author, b.parent_id, b.score from SparkTempTable AS a,\
        (select month, parent_id, score, author from SparkTempTable) AS\
    b WHERE a.score > 1000 AND a.parent_id LIKE 't3%' AND a.name = b.parent_id AND\
    b.score > a.score ORDER BY b.score DESC) AS best",
    6 : ""
}

### Return string of table location, given year

def getDataLocation(year):
    return ("s3n://kevin-de2016a/Parquet/f" + str(year)[2:])

# Return the first query result and start time, and time taken
def runTimeQuery(dbPath, queryString):
    df = sqlContext.read.parquet(dbPath)
    df.registerTempTable("SparkTempTable")
    queryDF = sqlContext.sql(queryString)
    t0 = time.time()
    result = queryDF.collect()
    delta_t = time.time() - t0
    if (len(result) == 0):
        return ("Null", t0, delta_t)
    else:
        return (str(result[0]), t0, delta_t)

query = 1
queryStr = mapQuery[query]
#Write to file
#with open("test.txt", "a") as myfile:
#        myfile.write(getTimeString(t0) + "," + str(query) + "," + str(result[0]) + "\n")

##Result is a 2-tuple, with time taken and 
def appendResultToFile(filename, startTime, queryID, year, timeTaken, result):
    outString = "{},{},{},{:.2f},{},{}\n".format(getTimeString(time.time()), queryID, year, timeTaken, result, "Spark6")
    with open(filename, "a") as myfile:
        myfile.write(outString)
    print(outString)


#Runs (approx) Count Distinct on Authors, given approxTrue boolean
def runApproxQuery(dbPath, approxTrue):
    df = sqlContext.read.parquet(dbPath)
    t0 = time.time()
    #Edit df.subreddit to use other fields
    if (approxTrue):
        result = df.agg(approxCountDistinct(df.subreddit)).collect()
    else: result = df.agg(countDistinct(df.subreddit)).collect()
    delta_t = time.time() - t0
    return (str(result[0]), t0, delta_t)

for year in [2007, 2009, 2012]:
    path = getDataLocation(year)
    #4 queries right now
    for queryID in range(1,6):
        #Repeat 2 times
        for i in range(1,5):
            queryString = mapQuery[queryID]
            result, t0, time_taken = runTimeQuery(path, queryString)
            appendResultToFile("queries.txt", t0, queryID, year, time_taken, result)
    
    #Run Count/ApproxCount
    for approxTrue in [0,1]:
        #Repeat 2 times
        for i in range(1,5):
            result, t0, time_taken = runApproxQuery(path, approxTrue)
            appendResultToFile("queries.txt", t0, "C" + str(approxTrue), year, time_taken, result)

"""Calling querying functions over range of years"""
for i in range(1,3):
    for year in [2014, 2015]:
        path = getDataLocation(year)
    #4 queries right now
        for queryID in range(1,5):
            #Repeat 2 times
            queryString = mapQuery[queryID]
            result, t0, time_taken = runTimeQuery(path, queryString)
            appendResultToFile("queries.txt", t0, queryID, year, time_taken, result)

        #Run Count/ApproxCount
        for approxTrue in [0,1]:
            #Repeat 2 times
            for i in range(1,4):
                result, t0, time_taken = runApproxQuery(path, approxTrue)
                appendResultToFile("queries.txt", t0, "C" + str(approxTrue), year, time_taken, result)
