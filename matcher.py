import re
import sys

def getResources(sql):
        #parse file and delete in line comments and contents of double quotes
        #comments could create false positives
        report = sql.split("*/") #delete header
        if len(report) > 1:
                report = report[1]
        else:
                report = report[0]
        report = '\n\n'.join(report.split("-- Results Query --"))
        delineated = report.split(sep="\n")
        commentFree = [ x.split('--')[0] for x in delineated ]
        quoteFree = [re.findall("(.*?\").*?(\".*)", x) for x in commentFree]

        #originally had a function to do this part but this works on one line.
        #for each header line it chooses the one from quoteFree if it was matched by the
        #quote removal regex and turns that object into a string. otherwise it grabs
        #from commentFree
        merged = [''.join(x[0][0]) if x[0] != [] else x[1]
                  for x in zip(quoteFree, commentFree)]
        #compile the regular expressions and use list comprehension to iterate and match
        resources = re.compile("(from|join) (\w+\.)?([_\w]+)($|\s)", flags=re.IGNORECASE)


        match1 = [resources.findall(x) for x in merged]
        match1 = [x[0][1] + x[0][2] for x in match1 if x != [] and x[0][2] != ''] #grab captured not blank table names and schema names
        match1 = list(set(match1)) #remove duplicates
        match1.sort() #alphabatize


        tempTable = re.compile("(?<=TEMP TABLE )\w+", flags=re.IGNORECASE)
        match2 = [ tempTable.findall(x) for x in merged]
        match2 = [x[0] for x in match2 if x != [] and x[0] != '']
        match2 = list(set(match2))
        match2.sort()

        sources = "Resources Used: "
        for i, x in enumerate(match1):
                if x not in match2:
                        if i:
                                sources += ", "
                        sources += x

        sources += "\n\nTemp Tables: "
        if match2 == []:
                sources += "None"
        else:
                for i, x in enumerate(match2):
                        if i:
                                sources += ", "
                        sources += x
        return sources

#getResources(sys.stdin.read())
