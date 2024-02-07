'''
Created on 26.01.2024

@author: lucas
'''

import sqlite3
from lmtanalysis.FileUtil import getFilesToProcess
from lmtanalysis.Animal import AnimalPool
from lmtanalysis.Measure import oneSecond, oneMinute, oneHour, oneDay

if __name__ == '__main__':
    
    #ask the user for database to process
    files = getFilesToProcess()
    
    for file in files:
        
        connection = sqlite3.connect(file)
        
        animalPool = AnimalPool()
        
        animalPool.loadAnimals(connection) 
        
        # load all detection (positions) of all animals for the first hour
        animalPool.loadDetection( start = 0, end = oneDay , lightLoad = True )

        animalPool.plotSpeedProfiles(title="Testprofile", upperSpeedThreshold=50, tmax= oneHour, tFactor= oneMinute)
        
        print("Done")