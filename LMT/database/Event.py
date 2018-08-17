'''
Created on 6 sept. 2017

@author: Fab
'''
import sqlite3
import unittest
from time import *
from database.Chronometer import Chronometer

import matplotlib.pyplot as plt
import numpy as np
from turtledemo.penrose import start
from database.Measure import *

class Event:
    '''
    an event represent the interval of frame where the event is
    '''    
    def __init__(self , startFrame, endFrame ):
        
        self.startFrame = startFrame
        self.endFrame = endFrame
        
    def duration(self):
        return self.endFrame-self.startFrame+1
    
    def contain(self , frameNumber ):
        return ( frameNumber >= self.startFrame and frameNumber <= self.endFrame )
    
    def overlapInT(self , start , end ):
        '''
        XXXX
          XXXX
        
         YYYY
        YYYYYY
        '''
        if ( start <= self.endFrame and end >= self.startFrame ):
            return True
        #if ( end <= self.endFrame and end >= self.startFrame ):
        #    return True
        #if ( start <= self.endFrame and start >= self.startFrame ):
        #    return True
        ## case where the start and end are over boundaries of event
        #if ( start <= self.startFrame and end >= self.endFrame ):
        #    return True
        #return False
    
    def overlapEvent(self , eventCandidate ):    
        result = self.overlapInT( eventCandidate.startFrame , eventCandidate.endFrame )
        #print ( "Overlap debug: ( {} , {} ) - ( {} , {} ) : {}".format( self.startFrame, self.endFrame , eventCandidate.startFrame, eventCandidate.endFrame, result )  );
        return result
    
    def shift(self, nbFrame):
        '''
        Shifts event of nbFrame
        '''
        self.startFrame += nbFrame
        self.endFrame += nbFrame
    
class EventTimeLine:
    '''
    classdocs
    ''' 
    def __init__(self, conn, eventName, idA=None , idB=None ,idC=None , idD=None , loadEvent=True, minFrame = None, maxFrame=None, inverseEvent = False ):
        '''
        load events 
            where t>=minFrame and t<=maxFrame if applicable
            inverseEvent: inverse all timeline (used to make stop becomes move for instance) 
        '''
        self.idA = idA
        self.idB = idB
        self.idC = idC
        self.idD = idD
        self.eventName = eventName
        self.eventNameWithId = "{} idA:{} idB:{} idC:{} idD:{}".format( eventName , idA , idB, idC, idD )
        # build events
        self.eventList = []
                
        if ( loadEvent == False ):
            print( "Event " + eventName + " created. eventNameWithId = " +  self.eventNameWithId )
            return;
                    
        chrono = Chronometer( "Load event " + self.eventName )
        c = conn.cursor()        
        
        query = "SELECT * FROM EVENT WHERE NAME='{0}'".format( self.eventName );
        if ( idA != None ):
            query += " AND IDANIMALA={0}".format( idA )

        if ( idB != None ):
            query += " AND IDANIMALB={0}".format( idB )

        if ( idC != None ):
            query += " AND IDANIMALC={0}".format( idC )

        if ( idD != None ):
            query += " AND IDANIMALD={0}".format( idD )
        
        '''
        if ( minFrame != None ):
            query += " AND STARTFRAME>={0}".format( minFrame )

        if ( maxFrame != None ):
            query += " AND ENDFRAME<={0}".format( maxFrame )
        '''

        if ( minFrame != None ):
            query += " AND ENDFRAME>={0}".format( minFrame )

        if ( maxFrame != None ):
            query += " AND STARTFRAME<={0}".format( maxFrame )            
        
        ''' print( query ) '''
        c.execute( query )
        all_rows = c.fetchall()
                
        eventBool = {}

        for row in all_rows:
            start = row[3]
            end = row[4]
            for t in range( start, end+1 ):
                
                if ( minFrame != None ):
                    if ( t < minFrame ):
                        continue
                    
                if ( maxFrame != None ):
                    if ( t > maxFrame ):
                        continue
                                
                eventBool[t] = True

        if ( inverseEvent == True ):
            
            if ( minFrame == None ):
                print("To inverse event, need a minFrame")
                return
            if ( maxFrame == None ):
                print("To inverse event, need a maxFrame")
                return
            
            for t in range( minFrame , maxFrame +1 ):
                if ( t in eventBool ):
                    eventBool.pop( t )
                else:
                    eventBool[t] = True 
        
        self.reBuildWithDictionnary(eventBool)
        
        #keyList = sorted(eventBool.keys())
        
        #start = -1        
        #for key in keyList:
            
        #    if ( start == -1 ):
        #        start = key
                
        #    if ( eventBool.get( key+1 ) == None ):
        #        self.eventList.append( Event( start, key ) )
        #        start = -1
        
        print ( eventName , " Id(",idA ,",", idB, ",", idC, "," , idD , ") Loaded (" , len( self.eventList ) , " records loaded in ", chrono.getTimeInS() , "S )")

    def saveTimeLine(self , conn ):
        c = conn.cursor()   
        for event in self.eventList:
            query = "INSERT INTO EVENT (NAME, DESCRIPTION, STARTFRAME, ENDFRAME, IDANIMALA, IDANIMALB, IDANIMALC, IDANIMALD ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}');".format( self.eventName, self.eventNameWithId, event.startFrame, event.endFrame , self.idA, self.idB, self.idC, self.idD )
            #print( query )
            c.execute( query )
        conn.commit()


    def addEvent(self , eventToAdd ):
        self.eventList.append ( eventToAdd )
        self.checkEventHole( eventToAdd.startFrame-1 )
        self.checkEventHole( eventToAdd.endFrame )
        
        # check merge with existing events
        for event in self.eventList[:]:
            if ( event == eventToAdd ):
                continue
            if ( event.overlapEvent( eventToAdd ) ):                
                self.mergeEvent( event, eventToAdd )
        
        #TODO: should also check if the new event overlap with existing events.
    
    def addPunctualEvent(self , frameNumber ):
        '''
        Adds an event at frame frameNumber. If an event exists beside, extends it, else creates it.
        '''
        #check if event exists
        if ( self.getEventAt( frameNumber ) != None ):
            return;
        
        for event in self.eventList[:]:
            if ( event.endFrame == frameNumber-1 ):                
                event.endFrame = frameNumber
                self.checkEventHole( frameNumber )
                return
            
        for event in self.eventList[:]:
            if ( event.startFrame == frameNumber + 1 ):
                event.startFrame = frameNumber
                self.checkEventHole( frameNumber -1 )
                return
        
        #create the event
        
        event = Event( frameNumber , frameNumber )
        self.eventList.append( event )
    
    def getEventAt(self , frameNumber ):
        for event in self.eventList:
            if ( event.contain( frameNumber ) ):
                return event
        return None
        
    def hasEvent(self , frameNumber):
        if ( self.getEventAt(frameNumber) != None ):
            return True
        return False    
    
    def getNumberOfEvent(self , minFrame=None, maxFrame=None ):
        nbEvent = 0
        
        for event in self.eventList:
            takeEvent = True
            
            if ( minFrame != None ):                
                if ( event.endFrame < minFrame ):
                    takeEvent = False

            if ( maxFrame != None ):                
                if ( event.startFrame > maxFrame ):
                    takeEvent = False
            
            if (takeEvent):
                nbEvent+=1
                
        return nbEvent
            
    def getDurationEventInTimeBin(self, tmin=0, tmax=None, binSize=1*oneMinute):
        '''
        compute the proportion of frames within an event within a given time bin, to calculate the density
        '''
        if ( tmax == None ):
            tmax = self.getMaxT()
           
        dicEvent = self.getDictionnary()
           
        durationEventInBinProportionList = []
       
        frame = tmin
       
        while (frame < tmax):
       
            durationEventInBin = 0
           
            for t in range(frame, frame + binSize):
                if (t in dicEvent.keys()):
                    durationEventInBin = durationEventInBin + 1
               
            durationEventInBinProportion = durationEventInBin/binSize
           
            durationEventInBinProportionList.append(durationEventInBinProportion)
               
            frame = frame + binSize
               
        return durationEventInBinProportionList
    
    def getDictionnary(self , minFrame=None, maxFrame=None ):
        frameDico = {}
        for event in self.eventList:
            for t in range( event.startFrame, event.endFrame +1):
                frameDico[t] = True;
        
        if ( minFrame !=None ):
            for key in dict ( frameDico ).keys() :
                if ( key < minFrame ):
                    frameDico.pop( key )
                    
        if ( maxFrame !=None ):
            for key in dict ( frameDico ).keys():
                if ( key > maxFrame ):
                    frameDico.pop( key )
                    
        
        return frameDico
    
    def reBuildWithDictionnary(self, eventBool ):
        
        self.eventList.clear()
        
        keyList = sorted(eventBool.keys())
        
        start = -1        
        for key in keyList:
            
            if ( start == -1 ):
                start = key
                
            if ( eventBool.get( key+1 ) == None ):
                self.eventList.append( Event( start, key ) )
                start = -1
        
    
    def checkEventHole( self, frameNumber ):
        '''
        Checks if an event end at a givenFrame, and if another one starts just after. Merge event if found.
        XXX
          T
           XXX
           ==> merge
        '''
        eventA = self.getEventAt( frameNumber )
        eventB = self.getEventAt( frameNumber +1)
        if ( eventA == None or eventB == None ):
            return
        if ( eventA != eventB ):
            self.mergeEvent( eventA, eventB )
        
    def mergeEvent( self , eventA, eventB ):
        '''
        if events are next to another, merge it. (test A before B and B before A )
        '''
        if( eventA.endFrame == eventB.startFrame-1 ):
            mergedEvent = Event( eventA.startFrame , eventB.endFrame )
            self.eventList.remove( eventA )
            self.eventList.remove( eventB )
            self.eventList.append( mergedEvent )
            return

        if( eventB.endFrame == eventA.startFrame-1 ):
            mergedEvent = Event( eventB.startFrame , eventA.endFrame )
            self.eventList.remove( eventA )
            self.eventList.remove( eventB )
            self.eventList.append( mergedEvent )
            return
        
        if ( eventA.overlapEvent( eventB ) ):
            mini = min( eventA.startFrame , eventB.startFrame )
            maxi = max( eventA.endFrame , eventB.endFrame )
            #print ( "mini: " , mini )
            #print ( "maxi: " , maxi )
            mergedEvent = Event( mini , maxi )
            try:
                self.eventList.remove( eventA )
            except:
                pass
            try:
                self.eventList.remove( eventB )
            except:
                pass
            
            self.eventList.append( mergedEvent )
            return
        
    def getEventList(self):
        return self.eventList
    
    def removeEventsOverT(self , maxT ):
        for event in self.eventList[:]:
            if ( event.startFrame > maxT ):
                self.eventList.remove( event )
    
    def removeEventOfTimeLine(self , timeLineToRemove ):
        '''
        remove events that match timeLineToRemove
        '''
        dico = self.getDictionnary()
        removeDico = timeLineToRemove.getDictionnary()
        
        for k in removeDico:
            dico.pop( k , None )
            
        self.reBuildWithDictionnary( dico )
    
    
    def removeEventsBelowLength(self , maxLen ):
        for event in self.eventList[:]:
            if ( event.duration() < maxLen ):
                self.eventList.remove( event )
     
    def printEventList(self):
        print( "Event list of {} / {} / nbEvent: {}".format( self.eventName , self.eventNameWithId, len( self.eventList ) ) )
        i = 0
        for event in self.eventList:
            print ( "[{}] Event ({},{})".format( i, event.startFrame, event.endFrame ) )
            i+=1
    
    def getMaxT(self):
        maxT = None
        for event in self.eventList:
            if maxT == None:
                maxT = event.endFrame
            maxT = max( maxT , event.endFrame )
        return maxT

    def getMinT(self):
        minT = None
        for event in self.eventList:
            if minT == None:
                minT = event.startFrame
            minT = min( minT , event.startFrame )
        return minT
    
    def getNbEvent(self):
        nb=0
        
        for event in self.eventList:
            nb = nb+1
        
        return nb
        
    def getMeanEventLength(self):
        nb=0
        sum=0
        for event in self.eventList:
            nb = nb+1
            sum+= event.duration()
            
        if (nb == 0):
            return NaN
        else:
            return sum/nb
        
    def getMaxEventLength(self):
        maxi=0
        for event in self.eventList:
            maxi=max(maxi,event.duration())
        return maxi
    
    def getMinEventLength(self):
        mini=3*oneDay
        for event in self.eventList:
            mini=min(mini,event.duration())
        return mini
    
    def getTotalLength(self):
        sum = 0
        for event in self.eventList:
            sum+= event.duration()
        return sum
    
    def plotEventDurationDistributionHist(self , nbBin = 10 ):        
        data =[]        
        for event in self.eventList:
            data.append( event.duration() )
        #ax = plt.subplots()
        plt.hist( data , nbBin )
        plt.xlabel( "Event duration" )
        plt.ylabel( "Number of events" )
        plt.title( "Hist. of duration of event {}".format( self.eventName ) )        
        plt.figtext(.5,.85,"Number of bin: {}".format(nbBin) ,fontsize=10,ha='center')        
        plt.show()
    
    def plotEventDurationDistributionBar(self ,minDuration = None, maxDuration = None ):        
        data =[]
        
        for event in self.eventList:
            if ( minDuration != None):
                if ( event.duration() < minDuration ):
                    continue
            if ( maxDuration != None):
                if ( event.duration() > maxDuration ):
                    continue                
            data.append( event.duration() )
        
        data= sorted( data )
        fig, ax = plt.subplots()        
        indexes = np.arange( len(data) )
        plt.bar( indexes,data,1 )        
        #plt.bar( 3,11,1 )        

        plt.xlabel( "Events (sorted by duration)" )
        plt.ylabel( "Duration" )
        plt.title( "Duration of events" )         
        plt.figtext(.5,.85,"Number of events: {} (minDuration={}, maxDuration={})".format( len( data), minDuration,maxDuration ) ,fontsize=10,ha='center')        
        plt.show()
        
    def plotTimeLine(self):

        y =[]
        start =[]
        end=[]
        
        longestEvent = None
        
        for event in self.eventList:
            y.append( 1 )
            start.append( event.startFrame )
            end.append( event.endFrame )
            
            if ( longestEvent == None ):
                longestEvent = event
                
            if ( event.duration() > longestEvent.duration() ):
                longestEvent = event
                    
        plt.hlines( y, start, end, 'b', lw=4)
        plt.text( 0 ,1.01,"TimeLine of {}".format( self.eventName ) ,fontsize=10,ha='left')
        plt.annotate('Longest event ({})'.format( longestEvent.duration()), xy=( longestEvent.startFrame, 1), xytext=(longestEvent.startFrame, 0.95), arrowprops=dict(facecolor='black', shrink=0.05))
        plt.show()
        
    
    def endRebuildEventTimeLine( self, connection ):
        '''
        delete the old event timeline and save the new calculated one in the database
        '''
        if (len( self.eventList) == 0):
            print("no event")
        else:
            print ( "Number of event: " , len( self.eventList ) )
            print ( "Mean length of event: " , self.getMeanEventLength() )
            print ( "first event frame: " , self.eventList[0].startFrame )
        

        print ( "Delete old entry in base: " + self.eventName )
        deleteEventTimeLineInBase(connection, self.eventName, self.idA, self.idB, self.idC, self.idD )
        print ( "Saving timeLine: " + self.eventName + " ( " + str(len( self.eventList)) + " events )")
        self.saveTimeLine(connection)
        #trainTimeLine.plotEventDurationDistributionBar(0, 2*oneHour)
        #trainTimeLine.plotTimeLine()
    
        
    def getDensityEventInTimeBin(self, tmin=0, tmax=None, binSize=1*oneMinute):
        '''
        compute the proportion of frames within the time bin that are included in one event type
        '''
        if ( tmax == None ):
            tmax = self.getMaxT()
            
        dicEvent = self.getDictionnary()
            
        densityEventInBinList = []
        
        frame = tmin
        
        while (frame <= tmax):
        
            durationEventInBin = 0
            
            for t in range(frame, frame + binSize ):
                if (t in dicEvent.keys()):
                    durationEventInBin = durationEventInBin + 1
                
            densityEventInBin = durationEventInBin/binSize
            
            densityEventInBinList.append(densityEventInBin)
                
            frame = frame + binSize
                
        return densityEventInBinList
            
      
    def shiftInTime( self, nbFrame ):
        '''
        Shifts all events of nbFrames
        '''
        for event in self.eventList:
            event.shift( nbFrame )
    
    
    def correlateWithTimeLine( self, timeLineCandidate ):
        
        ''' 
        provides correlation of current event considering overlap with candidate event.
        '''
        
        foundEventList = []
        
        print("correlation started")
        chrono = Chronometer( "correlateWithTimeLine " + timeLineCandidate.eventName )
        
        maxT = self.getMaxT( )
        dico = self.getDictionnary( 0 , maxT )
        dicoCandidate = timeLineCandidate.getDictionnary( 0 , maxT )

        mergedDico = {}

        for k in dico.keys():
            if ( k in dicoCandidate ):
                mergedDico[k] = True
                
        mergedTimeLine = EventTimeLine( None, eventName="Merged" , loadEvent=False )
        mergedTimeLine.reBuildWithDictionnary( mergedDico )
            
        nbEvent = len( self.getEventList() )
        #nbMatch = len( newEvent.getEventList() )
        
        relativityDico = {} # relativity provide an histogram of the relative location of the even compared to the candidate. 0 is beginning, 1 is end
        for i in range(100): # zero fill
            relativityDico[i] = 0
            
        nbMatch = 0
        for event in self.eventList:
            
            for eventCandidate in mergedTimeLine.eventList:
                
                if event.overlapEvent( eventCandidate ):
                    
                    nbMatch +=1
                    meanEventT = event.startFrame + (event.endFrame - event.startFrame )/2
                    foundEvent = timeLineCandidate.getEventAt( meanEventT )
                    if ( foundEvent != None ):
                        foundEventList.append( foundEvent )
                        
                        if ( foundEvent.duration() > event.duration() * 2 ):
                            
                            try:
                                a = ( meanEventT - foundEvent.startFrame ) / foundEvent.duration()
                                a = int( a * 100 )  
                                if ( a in relativityDico ):
                                    relativityDico[a]+=1
                                else:
                                    relativityDico[a]=1
                                    
                            except:
                                pass
                            
                    
                    break
        
        print ( "NB match with " + timeLineCandidate.eventName + " " + str(nbMatch) + " / " + str(nbEvent) + " time to compute: " + str(chrono.getTimeInMS()) )
        
        ratio=0
        
        if nbMatch!=0:
            ratio = nbMatch / nbEvent
            
        
        
            
        
            
        return [ratio, foundEventList,relativityDico]    

def deleteEventTimeLineInBase( connection, eventName, idA=None, idB=None, idC=None, idD=None ):
    '''
    delete an event in dataBase
    '''
    cursor = connection.cursor()
    print ( "Deleting event {} (idA:{},idB:{},idC:{},idD:{}) from base...".format( eventName , idA, idB, idC, idD ) )
    query = "DELETE FROM EVENT WHERE NAME=\"{0}\"".format( eventName )
    if ( idA != None ):
        query += " AND IDANIMALA={0}".format( idA )

    if ( idB != None ):
        query += " AND IDANIMALB={0}".format( idB )

    if ( idC != None ):
        query += " AND IDANIMALC={0}".format( idC )
    
    if ( idD != None ):
        query += " AND IDANIMALD={0}".format( idD )
    
    #print(query)
    
    cursor.execute( query )
    connection.commit()
    print ( "Number of event deleted: {} ".format ( cursor.rowcount ) )

def plotMultipleTimeLine( timeLineList , colorList=None , show=True , minValue=0 ):
    '''
    Plot multiple timeLine
    '''
    
    yOffset = len( timeLineList ) -1
    maxX = 0;

    plt.figure( figsize=(10, yOffset/2 ) )

    for timeLine in timeLineList:
        start = []
        end = []
        y = []
        if timeLine != None:
            
            for event in timeLine.eventList:
                y.append( 1 + yOffset )
                start.append( event.startFrame )
                end.append( event.endFrame )
                plt.Rectangle( ( event.startFrame, 1+yOffset )  , event.duration( ) , 1 )
                if ( event.endFrame > maxX ):
                    maxX = event.endFrame      
            color = "k"
            if( colorList!= None):
                color = colorList[ timeLineList.index( timeLine ) ]
                
            plt.hlines( y, start, end, color, lw=20)
            plt.text( minValue ,1.0 + yOffset,"{}   ".format( timeLine.eventName ) ,fontsize=9,ha='right',va='center',label='test')
        
        yOffset-=1

        #plt.annotate('Longest event ({})'.format( longestEvent.duration()), xy=( longestEvent.startFrame, 1), xytext=(longestEvent.startFrame, 0.95), arrowprops=dict(facecolor='black', shrink=0.05))
            
        #ax = plt.gca()
        #ax.relim()
    plt.grid( True , axis='x' )
    marginTop = 0.3
    plt.ylim( (0+marginTop , len( timeLineList ) +1-marginTop ) )    
    plt.axes().get_yaxis().set_visible( False )
    plt.subplots_adjust( left=0.2 )

    plt.legend()    
    
    if ( show ):
        plt.show()
      


class TestEventTimeLine ( unittest.TestCase ):
    
    def test_PuntualEvent(self):
                
        myEventTimeLine = EventTimeLine( None, "testEvent" , 1 , 2 , loadEvent=False )
        myEventTimeLine.addPunctualEvent( 500 )
        myEventTimeLine.printEventList()
        
        result = ( myEventTimeLine.getMinT() == 500 and myEventTimeLine.getMaxT() == 500 ) 
        self.assertEqual( result, True )

    def test_PuntualEvent2(self):
                
        myEventTimeLine = EventTimeLine( None, "testEvent" , 1 , 2 , loadEvent=False )
        myEventTimeLine.addEvent( Event( 51,99 ) )
        myEventTimeLine.addPunctualEvent( 100 )
        myEventTimeLine.addPunctualEvent( 50 )
        
        myEventTimeLine.printEventList()
        result = ( myEventTimeLine.getMinT() == 50 and myEventTimeLine.getMaxT() == 100 ) 
        self.assertEqual( result, True )

    def test_PuntualEvent3(self):
                
        myEventTimeLine = EventTimeLine( None, "testEvent" , 1 , 2 , loadEvent=False )
        myEventTimeLine.addEvent( Event( 100,200 ) )
        myEventTimeLine.addEvent( Event( 50,99 ) )
        
        myEventTimeLine.printEventList()
        result = ( myEventTimeLine.getMinT() == 50 and myEventTimeLine.getMaxT() == 200 ) 
        self.assertEqual( result, True )

    def test_PuntualEvent4(self):
                
        myEventTimeLine = EventTimeLine( None, "testEvent" , 1 , 2 , loadEvent=False )
        myEventTimeLine.addEvent( Event( 100,200 ) )
        myEventTimeLine.addEvent( Event( 201,300 ) )
        
        myEventTimeLine.printEventList()
        result = ( myEventTimeLine.getMinT() == 100 and myEventTimeLine.getMaxT() == 300 ) 
        self.assertEqual( result, True )

    def test_PuntualEvent5(self):
                
        myEventTimeLine = EventTimeLine( None, "testEvent" , 1 , 2 , loadEvent=False )
        myEventTimeLine.addEvent( Event( 100,200 ) )
        #print("test overlap")
        myEventTimeLine.addEvent( Event( 150,250 ) )
        myEventTimeLine.addEvent( Event( 50,160 ) )
        myEventTimeLine.addEvent( Event( 50,400 ) )
        
        myEventTimeLine.printEventList()
        result = ( myEventTimeLine.getMinT() == 50 and myEventTimeLine.getMaxT() == 400 and len( myEventTimeLine.eventList ) == 1 ) 
        self.assertEqual( result, True )

    def test_PuntualEvent6(self):
                
        myEventTimeLine = EventTimeLine( None, "testEvent" , 1 , 2 , loadEvent=False )
        myEventTimeLine.addEvent( Event( 100,200 ) )
        #print("test overlap")
        myEventTimeLine.addEvent( Event( 202,300 ) )
        myEventTimeLine.addPunctualEvent( 201 )

        myEventTimeLine.printEventList()
        result = ( myEventTimeLine.getMinT() == 100 and myEventTimeLine.getMaxT() == 300 and len( myEventTimeLine.eventList ) == 1 ) 
        self.assertEqual( result, True )

        
if __name__ == '__main__':
    unittest.main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    