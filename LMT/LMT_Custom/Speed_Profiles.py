'''
Created on 26.01.2024

@author: lucas
'''

import sqlite3
from lmtanalysis.FileUtil import getFilesToProcess
from lmtanalysis.Animal import AnimalPool
from lmtanalysis.Measure import oneSecond, oneMinute, oneHour, oneDay
from datetime import datetime

if __name__ == '__main__':
    
    #ask the user for database to process
    files = getFilesToProcess()
    
    print("Starting: Speed Profiles")
    
    for file in files:
        
        connection = sqlite3.connect(file)
        
        animalPool = AnimalPool()
        
        animalPool.loadAnimals(connection) 
        
        # load all detection (positions) of all animals for the first hour
        animalPool.loadDetection( start = 0, end = oneDay , lightLoad = True )

        animalPool.plotSpeedProfiles(title=input("Enter Mouse ID and Day: "), upperSpeedThreshold=30, tmax= oneDay, tFactor= oneMinute)
        
        print("Done: Speed Profiles")