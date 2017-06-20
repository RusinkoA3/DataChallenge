#----------------------------------------------------------------------------------
#	ChallengeModel.py: Build a logistic growth model for generic conversion
#			   rate data.
#
#			    A. Rusinko (5/23/17)
#----------------------------------------------------------------------------------
#
import sqlite3
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from scipy.optimize import curve_fit


global Alpha, Beta, Gamma				# model parameters

#
# 	Functions for optimization
#
# Optimize a,b,c where c is the conversion rate
def func(x, a, b, c):
    return c / (1.0 + a * np.exp(-b * x))
  
# Optimize a and b, holding c (or Gamma) constant
def func1(x, a, b):
  global Gamma
  return Gamma / (1.0 + a * np.exp(-b * x))

# Optimize c, given constant a and b
def func4(x, c):
  global Alpha, Beta
  return c / (1.0 + Alpha * np.exp(-Beta * x))

# Calculate c (conversion rate)
def Calc_c(yp, x):
  global Alpha, Beta
  return yp * (1.0+ Alpha* np.exp(-Beta*x))

# 
#	Data Retrieval
#
# From result retrieved from sqlite db, output records 
# matching Date1
def RetrieveByDate(Date1, result):
  MatchByDate = []
  for r in result:
    if Date1 == r[2]:
      rtup = (r[1],r[3],r[4])
      MatchByDate.append(rtup)
  MatchByDate.sort()
  return MatchByDate

# Add number_days to Date1 and return a new date
def AddDays(Number_Days, Date1):
  start_date = datetime.strptime(Date1, "%m/%d/%Y")
  NewDate    = start_date + relativedelta(days=Number_Days)
  end_date   = datetime.strftime(NewDate, "%m/%d/%Y")
  return  end_date

#
#		MAIN Code
#
def main(argv):
  global Alpha, Beta, Gamma
  
  
# initialize the calculations
  dpoints    = 200						# Max number of data points
  xdata      = np.linspace(0,dpoints, num=dpoints+1)		# Evenly space vector of x values
  Start_Date = '5/1/2013'					# Start date of study
  MaxDays    = 92						# Max number of points used
  Gamma0     =  0.25						# Initialize guess at conversion rate
  ConvData   = {}						# Conversion Rate Data
  Params     = {}						# Parameters

# READ in data from sqlite in gulp
  connection = sqlite3.connect("company.db")
  cursor = connection.cursor()
  cursor.execute("SELECT * FROM generic")
  result = cursor.fetchall() 
  connection.close()

# Loop until MaxDays is reached
  for i  in range(MaxDays):
    NewDate = AddDays(i, Start_Date)				# Get NEW date
    Matched = RetrieveByDate(NewDate, result)			# Retrieve data for that date
    AveConversion = Gamma0					
    NumberStudied = 1
    
    print "\nNewDate:",  NewDate

#   Loop over each data set retrieved
    for (Cohort_Number,Track,ConversionRate) in Matched:
      
#      
#      First three Track cases are ALL guesses to set up future optimizations
#
      if Track == 0:									# Initialize NEW Cohort
	Alpha = Gamma0 / ConversionRate
	print "Cohort" + str(Cohort_Number),  Track, Gamma0, 0.0, Track	
	ptup = (Alpha,0.0,Gamma0)							# Get initial value of a
	Params[Cohort_Number] = ptup
	ydata = [ConversionRate]
	ConvData[Cohort_Number] = ydata
	
      elif Track == 1:									
	ydata = ConvData[Cohort_Number]
	ydata.append(ConversionRate)
	(Alpha,Beta,Gamma) = Params[Cohort_Number]					# Calculate b using fixed a
	Btop  = (ydata[0] * (1.0 + Alpha) / ydata[1]) -1.0
	Beta  = -1.0 * np.log(Btop/Alpha)
	popt, pcov = curve_fit(func4, xdata[:2], ydata[:2])				# Get C for two points, and constant a,b
	print "Cohort" + str(Cohort_Number), Track,  popt[0], int(np.log(Alpha)/Beta)	
	Params[Cohort_Number]   =  (Alpha,Beta, popt[0])
	ConvData[Cohort_Number] = ydata
	
	
      elif Track == 2:
	ydata = ConvData[Cohort_Number]
	ydata.append(ConversionRate)
	(Alpha,Beta,Gamma) = Params[Cohort_Number]
	popt, pcov = curve_fit(func1, xdata[:3], ydata[:3])				# Get a &  b for three points
	Alpha = popt[0]
	Beta  = popt[1]
	C3pt  =  Calc_c(ydata[2],2.0)							# Calculate conversion rate
	print "Cohort" + str(Cohort_Number), Track, C3pt, int(np.log(Alpha)/Beta)
	Params[Cohort_Number]   =  (Alpha,Beta, C3pt)
	ConvData[Cohort_Number] = ydata	
	
	
      else:
	ydata = ConvData[Cohort_Number]							# more than 3 points, FIT a,b,c
	ydata.append(ConversionRate)
	(Alpha,Beta,Gamma) = Params[Cohort_Number]
	param_bounds=([Alpha-0.75,Beta-0.1,-np.inf],[Alpha+0.75,Beta+0.1,np.inf])
	popt, pcov = curve_fit(func, xdata[:Track+1], ydata[:Track+1], bounds=(param_bounds))
	Alpha = popt[0]
	Beta  = popt[1]
	Gamma = popt[2]
	print "Cohort" + str(Cohort_Number), Track, Gamma, int(np.log(Alpha)/Beta)
	Params[Cohort_Number]   =  (Alpha,Beta, Gamma)
	ConvData[Cohort_Number] = ydata	

#   Echo average conversion rate for each new day
    avesum = 0.0
    ival   = 0
    for (k,v) in Params.items():
      ival   += 1
      (a,b,c) = v
      avesum += c
    print "Average Conversion Rate = ", avesum / float(ival)

  pass	

# EXECUTE
if __name__ == "__main__":
    main(sys.argv)
      