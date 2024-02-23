'''
Created on 22.02.2024

@author: lucas
'''

import sqlite3
from lmtanalysis.FileUtil import getFilesToProcess
from lmtanalysis.Animal import AnimalPool
from lmtanalysis.Measure import oneDay
import pandas as pd
from tkinter.filedialog import askdirectory
import ntpath

if __name__ == '__main__':
    
    #Maximum detection time
    tMax = oneDay
    #Headers for table
    Cols = {"Frame":[], "Seconds":[], "X": [], "Y": []}
    
    
    #ask the user for database to process
    files = getFilesToProcess()
    print("Select output file")
    output = askdirectory()
    if not output:
        raise ValueError("No output selected")
    
    print("Starting: Extract 2D Coordinates")
    
    for file in files:
        
        filename = ntpath.basename(file)[:-7]
        
        connection = sqlite3.connect(file)
        
        animalPool = AnimalPool()
        
        animalPool.loadAnimals(connection)
        
        animalPool.loadDetection(0,tMax,True)
        
        for Animal in animalPool.getAnimalList():
            
            for frame, detection in Animal.detectionDictionary.items():
                Cols["Frame"].append(frame)
                Cols["Seconds"].append(frame/30)
                Cols["X"].append(detection.massX)
                Cols["Y"].append(detection.massY)
            
            df = pd.DataFrame.from_dict(Cols)
            
            print(df)
            
            df.to_csv(path_or_buf=output + f"\\{filename}_{Animal.RFID}.csv", index=False)
            
            print(f"File was saved as {filename}_{Animal.RFID}.csv to {output}")
            print("Finished.")
            