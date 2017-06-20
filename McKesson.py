#----------------------------------------------------------------------------------
#
#	McKesson.py:  Code to create data set for modeling from original raw data.
#
#			    A. Rusinko (5/23/17)
#----------------------------------------------------------------------------------
#
import csv
import sqlite3
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

def AddDays(Number_Days, Date1):
  start_date = datetime.strptime(Date1, "%m/%d/%Y")
  NewDate    = start_date + relativedelta(days=Number_Days)
  end_date   = datetime.strftime(NewDate, "%m/%d/%Y")
  return  end_date

def DeltaDays(Date1, Date2):
  if Date1 == '' or Date2 == '': 		
    delta = -1							# Return -1, if Date1 or Date2 == null
    return delta
  start_date = datetime.strptime(Date1, "%m/%d/%Y")
  end_date   = datetime.strptime(Date2, "%m/%d/%Y")
  delta      = abs((end_date-start_date).days)
  return delta

def Calc_ConversionRate(xc,xl):
  xsum  = float(sum(xl))
  xcalc = []
  xval  = 0.0
  for i,x in enumerate(xl):
      xval += float(x)
      xcalc.append(xval/float(xc))
  return xcalc

def Print_Cohort(Reference_Date, Cohort_Number,  ConRate_ByDate, Number_FollowDays):
  for i in range(Number_FollowDays):
    NewDate = AddDays(i,Reference_Date)
    Cohort =  str(Cohort_Number).zfill(3)
    print NewDate,  ',', Cohort, ',',  i, ',', ConRate_ByDate[i]
  return 1


def main(argv):
  FileName = './DataScienceTakeHomev2DataSetSorted.csv'
  
  connection = sqlite3.connect("company.db")
  cursor     = connection.cursor()
  
# delete table if needed
  cursor.execute("""DROP TABLE generic;""")

# Create new generic table
  sql_command = """
  CREATE TABLE generic ( 
  Record_Count INTEGER PRIMARY KEY, 				# SQL statements
  cohort_number INTEGER,
  Tracking_Date DATE,
  Tracking INTEGER, 
  ConversionRate REAL);"""
  cursor.execute(sql_command)

  with open(FileName, 'rb') as csvfile:

    Total_Unique_Count = 0
    Cohort_Number      = 0
    Cohort_Count       = 0
    Reference_Date     = '5/1/2000'
    Conversions_ByDate = [0]*160
    Number_FollowDays  = 120

    reader = csv.reader(csvfile, delimiter=',',quotechar='"')
    for i,row in enumerate(reader):

#     Column headers in Row 1 of csvfile
      if i == 0:				
	headers = row
	continue

#     Increment total number of unique records	  
      Total_Unique_Count += 1			

#     Proccess current and then initilize new one
      if row[1] != Reference_Date:
	if Cohort_Number>0: 
	  
#	  Process current cohort	  
	  ConRate_ByDate = Calc_ConversionRate(Cohort_Count,Conversions_ByDate)	  
	  	  
	  for i in range(Number_FollowDays):
	    NewDate = AddDays(i,Reference_Date)  
	    Cohort =  str(Cohort_Number).zfill(3)
	    
#	    Print in CSV format
	    print NewDate,  ',', Cohort, ',',  i, ',', ConRate_ByDate[i]

#	    Store in db table
	    CRate = ConRate_ByDate[i]
	    format_str = """INSERT INTO generic (cohort_number,tracking_date,tracking,conversionrate) 
	    VALUES ("{Cohort_Number}", "{Tracking_Date}","{tracking}","{ConversionRate}");"""
	    sql_command = format_str.format(Cohort_Number=Cohort_Number, Tracking_Date=NewDate, tracking=i,  ConversionRate=ConRate_ByDate[i] )	                
	    print sql_command
            cursor.execute(sql_command)	  
	  
#	NEW Cohort	  
	Reference_Date = row[1]
	Conversions_ByDate = [0]*160

	Cohort_Count   = 0
	Cohort_Number += 1
#	if Cohort_Number == 2: break

      Cohort_Count    += 1					# Increment current count in cohort
      xdelta = DeltaDays(Reference_Date,row[5])
      if xdelta>=0: Conversions_ByDate[xdelta] += 1

# never forget this, if you want the changes to be saved:
  connection.commit()
  connection.close()

  pass	
	
if __name__ == "__main__":
    main(sys.argv)
      