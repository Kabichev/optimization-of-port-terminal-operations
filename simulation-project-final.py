import numpy as np
import random
import pandas as pd

def runSim(T):

    #####################################################################
    # Initial settings (in minutes) for all start events and activities #
    #####################################################################
    
    # Arrival regular boat
    arrivalPoissonRate = 4/24/60 
    
    # Arrival rate ext request port basin
    poissonRateServicePortBasin = 4/24/60
    portBasinMeanService = 40
    portBasinStdService = 7
    
    # Docking service Request
    dockMeanService = 4 * 60
    dockStdService = 0.5 * 60
    interArrivalTimeDock = 2 * 60
    
    # Tugboat service request
    tugMeanService = 90
    tugStdService = 10
    interArrivalTime = 55
    
    # Entering and leaving port
    lbEntLeave = 30
    ubEntLeave = 45
    
    # Tugboat service request
    tugMeanService = 90
    tugStdService = 10
    interArrivalTime = 55
    
    # Docking process
    dockingTime = 30
    undockingTime = 20
    
    # Unloading process
    lbUnloading = 4 * 60
    peakUnloading = 5 * 60
    ubUnloading = 6 *60
    
    # Customs process
    meanInspection = 1.5 * 60
    stdInspection = 0.5 * 60
    
    # Loading process
    lbLoading = 4.5 * 60
    peakLoading = 4.75 * 60
    ubLoading = 5 * 60
 
    ###############################################################################################
    # Initialize number of resources and make a list to track time at which resource is available #
    ###############################################################################################
    
    nrTugboats = 4               # To be optimized
    nextTugboatArrival = [0 for _ in range(nrTugboats)]
    tugsLiveCounter = 0          # Needed to make sure that the same tugboat can be used for multiple activities
    nrBerths = 4                 # To be optimized in later phase
    berthsLiveCounter = 0        # Needed to make sure that the same berth can be used for multiple activities
    nextBerthAvailable = [0 for _ in range(nrBerths)]
    portBasin = 2
    nextPortBasinAvailable = [0 for _ in range(portBasin)]
    dockerTeams = 4              # To be optimized
    nextDockerTeamAvailable = [0 for _ in range(dockerTeams)]
    
    portBasins = []              # Used to make sure that FIFO policy is applied (although service requests for port basins have priority)
    dockers = []                 # Used to make sure that FIFO policy is applied
    tugs = []                    # Used to make sure that FIFO policy is applied
    tugBack = []                 # Used to ensure that the number of available tugboats increases with one when a tugboat is available
     
    ##################################################################################
    # Create queue where potential start time of corresponding activity is filled in #
    ##################################################################################
    
    queueEntering = []
    
    queueDocking = []
    queueDockingTug = []         # Needed to make sure that the same tugboat can be used for multiple activities
    
    queueUnloading = []
    queueUnloadingBerth = []     # Needed to make sure that the same berth can be used for multiple activities
    
    queueInspection = []
    queueInspectionBerth = []    # Needed to make sure that the same berth can be used for multiple activities
    
    queueLoading = []
    queueLoadingBerth = []       # Needed to make sure that the same berth can be used for multiple activities
    
    queueUndocking = []
    queueUndockingBerth = []     # Needed to make sure that the same berth can be used for multiple activities
    
    queueLeaving = []
    queueLeavingTug = []         # Needed to make sure that the same tugboat can be used for multiple activities
    
    queueServiceRequestPortBasin = []
    queueServiceRequestDockTeam = []
    queueServiceRequestTug = []
    
    #############################################
    # Calculate arrival times and service times #
    #############################################
    
    # Process times and arrivals
    def regularArrival(arrivalPoissonRate):
       arrivalTimeShip = np.random.exponential(1/arrivalPoissonRate)
       return arrivalTimeShip
    
    # External service request port basin #
    def portBasinServiceRequestArrival(poissonRateServicePortBasin):
        arrivalPortBasinServiceRequest = np.random.exponential(1/poissonRateServicePortBasin)
        return arrivalPortBasinServiceRequest
    
    def portBasinServiceRequest(portBasinMeanService, portBasinStdService):
        serviceRequestTimePortBasin = np.random.normal(portBasinMeanService, portBasinStdService)
        return serviceRequestTimePortBasin
    
    def enterLeavePort(lbEntLeave, ubEntLeave):
        portManeuverTime = np.random.uniform(lbEntLeave,ubEntLeave)
        return portManeuverTime
    
    def tugboatServiceRequest(tugMeanService, tugStdService):
        serviceRequestTime = np.random.normal(tugMeanService, tugStdService) 
        return serviceRequestTime
    
    def tugboatServiceRequestarrival(interArrivalTime):
        arrivalTugServiceRequest = random.expovariate(1/interArrivalTime) 
        return arrivalTugServiceRequest
        
    def docking(dockingTime):
        dockingTime = dockingTime
        return dockingTime
    
    def unloading(lbUnloading, peakUnloading, ubUnloading):
        unloadingTime = np.random.triangular(lbUnloading, peakUnloading, ubUnloading)
        return unloadingTime
    
    def cargoInspection(meanInspection, stdInspection):
        inspectionTime = np.random.normal(meanInspection, stdInspection)
        return inspectionTime
    
    def loading(lbLoading, peakLoading, ubLoading):
        loadingTime = np.random.triangular(lbLoading, peakLoading, ubLoading)
        return loadingTime
    
    def undocking(undockingTime):
        undockingTime = undockingTime
        return undockingTime
            
    def dockTeamServiceRequestarrival(interArrivalTimeDock):
        arrivalDockTeamRequest = random.expovariate(1/interArrivalTimeDock)
        return arrivalDockTeamRequest
    
    def dockTeamServiceRequest(dockMeanService, dockStdService):
        serviceRequestTimeDock = np.random.normal(dockMeanService, dockStdService)
        return serviceRequestTimeDock
    
    ###############################################################
    # Initialize time at which temporary entity enters the system #
    ###############################################################
    
    nextArrival = 0
    nextServReqTug = 0
    busyArrivals = 0            # Used to avoid congestion in the system -> not all tugboats can be used to let ships enter the port, because then no ships can leave the port any more
    nextPortBasinReq = portBasinServiceRequestArrival(poissonRateServicePortBasin)
    nextServReqDockTeam = dockTeamServiceRequestarrival(interArrivalTimeDock)
    nextServReqTug = tugboatServiceRequestarrival(interArrivalTime)
    
    ######################################################################
    # Create lists that keeps track on where which ship is at any moment #
    ######################################################################
    
    shipEntering = []           # Enter queue 'Entering port'
    shipOTWDocking = []         # Leave previous queue, enter port, and on the way to enter the queue 'Docking'
    shipDocking = []
    shipOTWInspection = []
    shipInspection = []
    shipOTWUnloading = []
    shipUnloading = []
    shipOTWLoading = []
    shipLoading = []
    shipOTWUndocking = []
    shipUndocking = []
    shipOTWLeaving = []
    shipLeaving = []
    shipEnd = []
    
    ##############################################################################
    # Keep track of results temporary entities (identification number and times) #
    ##############################################################################
    
    shipID = 0
    extReqPBID = 0
    extReqDOID = 0
    extReqTuID = 0
    shipsPropListed = []
    extReqPBListed = []
    extReqDOListed = []
    extReqTUListed = []
    
    ################################################################################################
    # Initialize time of simulation at zero and make list to keep track of first event that occurs #
    ################################################################################################

    nextEvent = [0 for _ in range(15)]
    t = 0                       # Start simulation at time zero

    ##############
    # Simulation #
    ##############

    while t < T:                # Continue simulation until time T has been reached / passed
        
        ###########################
        # Next arrival event ship #
        ###########################
    
        if nextArrival == t:
            nextArrival = t + regularArrival(arrivalPoissonRate)
            queueEntering.append(t)
            tugs.append('A')            # FIFO
            
            # Sequencing -> ship can overtake if it arrives earlier in next queue #
            shipEntering.append(shipID)
            
            # Statistics #
            shipsPropListed.append([shipID, t, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            shipID += 1
        
        #################################################
        # Next arrival event service request port basin #
        #################################################
        
        if nextPortBasinReq == t:
            nextPortBasinReq = t + portBasinServiceRequestArrival(poissonRateServicePortBasin)
            queueServiceRequestPortBasin.append(t)
            portBasins.append('SR_PB')  # Priority
            
            # Statistics #
            extReqPBListed.append([extReqPBID, t, 0, 0, 0])
            extReqPBID += 1

        ##################################################
        # Next arrival event service request docker team #
        ##################################################
            
        if nextServReqDockTeam == t:
            nextServReqDockTeam = t + dockTeamServiceRequestarrival(interArrivalTimeDock)
            queueServiceRequestDockTeam.append(t)
            dockers.append('SR_D')      # FIFO
            
            # Statistics #
            extReqDOListed.append([extReqDOID, t, 0, 0, 0])
            extReqDOID += 1    
    
        ##############################################
        # Next arrival event service request tugboat #
        ##############################################
        
        if nextServReqTug == t:
            nextServReqTug = t + tugboatServiceRequestarrival(interArrivalTime)
            queueServiceRequestTug.append(t)
            tugs.append('SR_T')         # FIFO
            
            # Statistics #
            extReqTUListed.append([extReqTuID, t, 0, 0, 0])
            extReqTuID += 1   
        
        #####################################
        # Event: Service request port basin #
        #####################################
            
        if len(queueServiceRequestPortBasin) > 0:                           # At least one request is in the 'Queue external basin request'
            if min(queueServiceRequestPortBasin) == t:                      # At least one request is supposed to leave the queue at the current time
                idx = queueServiceRequestPortBasin.index(min(queueServiceRequestPortBasin)) # Find index of request that is supposed to leave the queue
                if t >= min(nextPortBasinAvailable):                        # Check if port basin is still available
                    minIdx = portBasins.index('SR_PB')                      # These service requests have priority -> check at which place in the queue it was placed when no priority would have been used
                    portBasins.pop(minIdx)
                    assignPortBasin = nextPortBasinAvailable.index(min(nextPortBasinAvailable)) # Assign the earliest available port basin to external request
                    queueServiceRequestPortBasin.pop(idx)                   # Remove external request from the queue
                    timeServiceRequest = portBasinServiceRequest(portBasinMeanService, portBasinStdService) # Calculate service time
                    nextPortBasinAvailable[assignPortBasin] = t + timeServiceRequest            # Make port basin available at correct time
                    
                    # Statistics #
                    for z in range(len(extReqPBListed)):                    # Find ID of external request
                        if extReqPBListed[z][2] == 0:
                            ID = z
                            break
                    extReqPBListed[ID][2] = t                               # Start time
                    extReqPBListed[ID][3] = timeServiceRequest              # Service time
                    extReqPBListed[ID][4] = t + timeServiceRequest          # End time
    
                else:                                                       # Port basin is not available yet -> reschedule to moment where next port basin is supposed to be available
                    queueServiceRequestPortBasin.pop(idx)
                    queueServiceRequestPortBasin.append(min(nextPortBasinAvailable))

        ##################################
        # Event: Service request tugboat #
        ##################################
                            
        if len(queueServiceRequestTug) > 0:                                 # At least one request is in the 'Queue external tugboat request'
              if min(queueServiceRequestTug) == t:                          # At least one request is supposed to leave the queue at the current time
                  idx = queueServiceRequestTug.index(min(queueServiceRequestTug)) # Check index of service request that is supposed to leave the queue
                  
                  tugFine = False
                  if tugs[0] == 'SR_T':                                     # Check if the service request is the first one that is supposed to leave the queue -> FIFO policy
                      tugFine = True
                   
                  # Check if tugboat is available, else "reschedule".
                  if t >= min(nextTugboatArrival) and tugFine == True and tugsLiveCounter < nrTugboats: # Request can only be handled when a tugboat is available and FIFO is satisfied
                      tugsLiveCounter += 1                                  # Keep track of the number of tugboats that are busy -> needed to ensure that tugboat can be kept for same ship during multiple activities
    
                      assignTugboat = nextTugboatArrival.index(min(nextTugboatArrival)) # Assign tugboat to external request
                      queueServiceRequestTug.pop(0)
                      tugs.pop(0)
                      timeServiceRequest = tugboatServiceRequest(tugMeanService, tugStdService) # Calculate service time
                      nextTugboatArrival[assignTugboat] = t + timeServiceRequest # Calculate time at which tugboat is available again
                      tugBack.append(t + timeServiceRequest)                     # Same -> used to create event to update the number of available tugboats
                      
                      # Statistics #
                      for z in range(len(extReqTUListed)):              # Find ID of external request
                            if extReqTUListed[z][2] == 0:
                                ID = z 
                                break
                      extReqTUListed[ID][2] = t                         # Start time
                      extReqTUListed[ID][3] = timeServiceRequest        # Service time
                      extReqTUListed[ID][4] = t + timeServiceRequest    # End time
                  
                  else:                                                 # No tugboat available -> update to time where it is supposed to be available again
                      queueServiceRequestTug.pop(idx)
                      potenStartTime = -1
                      pot = 10 * T
                      if tugsLiveCounter == nrTugboats:                 # All tugboats are busy
                          if len(tugBack) > 0:                          # Check at which time first tugboat is back. List is empty when this is unknown, meaning that the ship is either entering the port or undocking. The time would be known if a tugboat is docking or leaving the port
                              potenStartTime = min(tugBack)
                          if len(queueInspection) > 0:                  # Jump to earliest event where inspection, unloading, or leaving takes place -> after that event a tugboat becomes available
                              pot = min(queueInspection)  
                          if len(queueUnloading) > 0:
                              if min(queueUnloading) < pot:
                                  pot = min(queueUnloading)
                          if len(queueLeaving) > 0:
                              if min(queueLeaving) < pot:
                                  pot = min(queueLeaving)
                          if potenStartTime == -1 and pot < 10 * T:
                              potenStartTime = pot     
                          elif potenStartTime == -1:                    # In case nothing can happen -> jump to next event in time
                              nextEventTemp = nextEvent.copy()
                              idxMin = nextEventTemp.index(min(nextEventTemp))
                              nextEventTemp.pop(idxMin)
                              potenStartTime = min(nextEventTemp)
                      else:                                             # At least one tugboat is available
                          if tugs[0] == 'A':                            # FIFO -> Arrival
                              potenStartTime = min(queueEntering)
                          elif tugs[0] == 'U':                          # FIFO -> Undocking
                              potenStartTime = min(queueUndocking)
                          else:
                              potenStartTime = min(nextTugboatArrival)  # FIFO -> external request -> set time to which next tugboat is back
                      queueServiceRequestTug.append(potenStartTime)

        ######################################
        # Event: Service request docker team #
        ######################################
            
        if len(queueServiceRequestDockTeam) > 0:                        # At least one request is in the 'Queue external dockers request'
            if min(queueServiceRequestDockTeam) == t:                   # At least one request is supposed to leave the queue at the current time
                idx = queueServiceRequestDockTeam.index(min(queueServiceRequestDockTeam)) # Check index of service request that is supposed to leave the queue
                
                doFine = False
                if dockers[0] == 'SR_D':                                # Check if the service request is the first one that is supposed to leave the queue -> FIFO policy
                    doFine = True
    
                if t >= min(nextDockerTeamAvailable) and doFine == True: # Request can only be handled when a docker team is available and FIFO is satisfied       

                    assignDockers = nextDockerTeamAvailable.index(min(nextDockerTeamAvailable))  # Assign docker team to external request
                    queueServiceRequestDockTeam.pop(idx)
                    timeServiceRequest = dockTeamServiceRequest(dockMeanService, dockStdService) # Calculate service time
                    nextDockerTeamAvailable[assignDockers] = t + timeServiceRequest              # Calculate time at which docker team is available again
                    
                    # Statistics #
                    dockers.pop(0)
                    for z in range(len(extReqDOListed)):                           # Find ID of external request
                        if extReqDOListed[z][2] == 0:
                            ID = z 
                            break
                    extReqDOListed[ID][2] = t                                      # Start time
                    extReqDOListed[ID][3] = timeServiceRequest                     # Service time
                    extReqDOListed[ID][4] = t + timeServiceRequest                 # End time 
                    
                else:
                    queueServiceRequestDockTeam.pop(idx)
                    if dockers[0] == 'L':                                          # FIFO -> Loading 
                        potenStartTime = min(queueLoading)
                    elif dockers[0] == 'U':                                        # FIFO -> Unloading 
                        potenStartTime = min(queueUnloading)
                    else:                                                          # FIFO -> external request -> set time to which next docker team is back
                        potenStartTime = min(nextDockerTeamAvailable)
                    queueServiceRequestDockTeam.append(potenStartTime)
 
        #####################
        # Event: Enter port #
        #####################   
 
        if len(queueEntering) > 0:                                                  # At least one ship is in the queue 'Wait for entering port'
            if min(queueEntering) == t:                                             # At least one ship is supposed to leave the queue at the current time
                idx = queueEntering.index(min(queueEntering))                       # Check index of ship that is supposed to leave the queue
                
                tugFine = False
                if tugs[0] == 'A':                                                  # Check if the ship is the first one that is supposed to leave the queue -> FIFO policy
                    tugFine = True
    
                if t >= min(nextTugboatArrival) and busyArrivals < len(nextTugboatArrival) - 1 and tugFine == True and tugsLiveCounter < nrTugboats: # Ship can only leave the queue when a tugboat is available, FIFO is satisfied, and when not all tugboats are busy with entering the port
                    tugsLiveCounter += 1                                            # Keep track of the number of tugboats that are busy -> needed to ensure that tugboat can be kept for same ship during multiple activities
                    busyArrivals += 1                                               # Used to avoid congestion in the system -> not all tugboats can be used to let ships enter the port, because then no ships can leave the port any more                      
                    tugs.pop(0)
                    assignTugboat = nextTugboatArrival.index(min(nextTugboatArrival)) # Assign tugboat to ship
                    queueEntering.pop(0) 

                    timeToEnterPort = enterLeavePort(lbEntLeave, ubEntLeave)        # Calculate service time 
                    nextTugboatArrival[assignTugboat] = t + timeToEnterPort         # Change time at which tugboat is supposed to be available again
                    
                    # Statistics and sequencing #
                    ID = shipEntering[0]
                    shipEntering.remove(ID)
                    shipsPropListed[ID][2] = t                    
                    shipsPropListed[ID][3] = timeToEnterPort

                    queueDocking.append(t + timeToEnterPort)                        # Set earliest time at which ship can leave the next queue
                    queueDockingTug.append(assignTugboat)                           # Keep track of the tugboat that is assigned to the ship -> also used for next activity
                    shipOTWDocking.append([ID, t + timeToEnterPort])
    
                else:                                                               # Reschedule
                    queueEntering.pop(idx)
                    if busyArrivals < len(nextTugboatArrival):                      # If tugboats are busy with entering port
                        potenStartTime = -1
                        pot = 10 * T
                        if tugsLiveCounter == nrTugboats:                           # If all tugboats are occupied
                            if len(tugBack) > 0:                                    # Jump to time where first tugboat is available again
                                potenStartTime = min(tugBack)     
                            if len(queueUndocking) > 0 and tugs[0] == 'U':          # Jump to undocking time if this is supposed to occur
                                if min(queueUndocking) < pot:
                                    pot = min(queueUndocking)
                            if len(queueDocking) > 0:
                                if min(queueDocking) < pot:
                                    pot = min(queueDocking)
                            if len(queueLeaving) > 0:
                                if min(queueLeaving) < pot:
                                    pot = min(queueLeaving)
                            if len(queueServiceRequestTug) > 0 and tugs[0] == 'SR_T':
                                if min(queueServiceRequestTug) < pot:
                                    pot = min(queueServiceRequestTug)
                            
                            if potenStartTime == -1 and pot < 10 * T:
                                potenStartTime = pot     
                            elif potenStartTime == -1:                                  # In case nothing can happen -> jump to next event in time
                                nextEventTemp = nextEvent.copy()
                                idxMin = nextEventTemp.index(min(nextEventTemp))
                                nextEventTemp.pop(idxMin)
                                potenStartTime = min(nextEventTemp)   
                                
                        else:                                                           # Entering port is allowed
                            if tugs[0] == 'SR_T':                                       # FIFO -> service request tugboat
                                potenStartTime = min(queueServiceRequestTug)
                            elif tugs[0] == 'U':                                        # FIFO -> Undocking tugboat
                                potenStartTime = min(queueUndocking)
                            elif berthsLiveCounter == nrBerths:                         # All berths are occupied
                                if 'U' in tugs:                                         # Let a ship first leave the port -> change FIFO order
                                    idx = tugs.index('U')
                                    tugs.pop(idx)
                                    tugs.insert(0, 'U')
                                    potenStartTime = min(queueUndocking)
                                else:                                                   # Jump to time where tugboat becomes available
                                    potenStartTime = max(min(nextBerthAvailable), min(nextPortBasinAvailable), min(queueDocking), min(nextTugboatArrival))
                            else:                                                       # Jump to time where tugboat becomes available
                                potenStartTime = max(min(nextBerthAvailable), min(nextPortBasinAvailable), min(queueDocking), min(nextTugboatArrival))
                    else:
                        if len(tugBack) > 0:
                            potenStartTime = min(tugBack)                               # Jump to time where first tugboat is available again
                        else:                                                       
                            potenStartTime = max(min(nextBerthAvailable), min(nextPortBasinAvailable), min(queueDocking), min(nextTugboatArrival)) # Jump to time where tugboat becomes available
                    queueEntering.append(potenStartTime)

        ###############
        # Event: Dock #
        ###############
            
        if len(queueDocking) > 0:                                                 # At least one ship is in the queue 'Wait for docking'
            if min(queueDocking) == t:                                            # At least one ship is supposed to leave the queue at the current time
                for i in shipOTWDocking:                                          # Keep track of ships that are arriving in the queue
                    if i[1] == t:
                        portBasins.append('D')                                    # FIFO -> docking operation  
                        shipDocking.append(i[0])
                        shipOTWDocking.remove(i)
                        
                        # Statistics #
                        shipsPropListed[i[0]][4] = t              
    
                idx = queueDocking.index(min(queueDocking))                       # Check index of ship that is supposed to leave the queue                  
                assignTugboat = queueDockingTug[idx]                              # Find tugboat that was also assigned to the ship when it entered the port
                
                waitPB = False
                pbFine = False
                
                for i in portBasins:                                              # Check whether there are no prioritized service requests for the port basin
                    if i[0] == 'SR_PB':
                        waitPB = True
                        break
                
                if waitPB == False:
                    if portBasins[0] == 'D':                                      # Check whether port basin is reservered for docking event
                        pbFine = True
    
                #Check if both port basin and berth is available, else "reschedule".
                if t >= min(nextPortBasinAvailable) and t >= min(nextBerthAvailable) and waitPB == False and pbFine == True and berthsLiveCounter < nrBerths: # Ship can only leave the queue when a berth is available, FIFO is satisfied, and there are no prioritized service requests for the port basin
                    berthsLiveCounter += 1                                        # Keep track of the number of berths that are busy -> needed to ensure that berth can be kept for same ship during multiple activities
                    dockTime = docking(dockingTime)
                    portBasins.pop(0)
                    busyArrivals -= 1                                             # Tugboat is not busy with 'Enter port' activity any more
                    nextTugboatArrival[assignTugboat] = t + dockTime              # Set time at which tugboat becomes available
                    tugBack.append(t + dockTime)                                  # Same -> create event to update the number of available tugboats
                    queueDocking.pop(idx)
                    queueDockingTug.pop(idx)
                    
                    assignPortBasin = nextPortBasinAvailable.index(min(nextPortBasinAvailable)) # Assign port basin to ship
                    nextPortBasinAvailable[assignPortBasin] = t + dockTime                      # Update time at which port basin is available again
                    assignBerth = nextBerthAvailable.index(min(nextBerthAvailable))             # Assign berth to ship
                    nextBerthAvailable[assignBerth] = t + dockTime                              # Update time at which berth is available again
    
                    # Statistics and sequencing #
                    ID = shipDocking[0]
                    shipDocking.remove(ID)  
                    shipsPropListed[ID][5] = t 
                    shipsPropListed[ID][6] = dockTime
                    
                    # Check if ship needs to be inspected

                    rndNumb = random.uniform(0, 1)
                    if rndNumb <= 0.25:
                        queueInspection.append(t + dockTime)
                        queueInspectionBerth.append(assignBerth)
                        shipOTWInspection.append([ID, t + dockTime])
    
                    else:
                        queueUnloading.append(t + dockTime)
                        queueUnloadingBerth.append(assignBerth)
                        shipOTWUnloading.append([ID, t + dockTime])
                   
                else:                                                                           # Reschedule
                    if portBasins[0] == 'D':                                                    # Port basin is scheduled for docking event
                        if berthsLiveCounter < nrBerths:                                        # Berth is available
                            potenStartTime = max(min(nextPortBasinAvailable), min(nextBerthAvailable)) # Set potential start time
                        else:                                                                   # Berth is not available
                            if len(queueUndocking) > 0:                                         # If ship can be undocked, undock this one
                                potenStartTime = max(min(queueUndocking), min(nextPortBasinAvailable))
                                if 'L' in portBasins:
                                    idxL = portBasins.index('L')
                                    portBasins[0] = 'L'
                                    portBasins[idxL] = 'D'
                            elif len(queueLoading) > 0:                                         # If no ship can be undocked but a ship can be unloaded, do this to make sure that a berth becomes available as soon as possible
                                potenStartTime = max(min(queueLoading), min(nextPortBasinAvailable))
                            elif len(queueUnloading) > 0:
                                potenStartTime = max(min(queueUnloading), min(nextPortBasinAvailable))
                            elif len(queueInspection) > 0:
                                potenStartTime = max(min(queueInspection), min(nextPortBasinAvailable))
                    elif portBasins[0] == 'L':                                                  # Port basin is scheduled for leaving the system -> FIFO policy
                        potenStartTime = min(queueUndocking)
                    else:                                                                       # Port basin is scheduled for external service request 
                        potenStartTime = min(queueServiceRequestPortBasin)
        
                    queueDocking.pop(idx)
                    queueDocking.append(potenStartTime)
                    nextTugboatArrival[assignTugboat] = potenStartTime                          # Change time to which tugboat becomes available
    
        ##################
        # Event: Inspect #
        ##################    
    
        if len(queueInspection) > 0:                                                            # At least one ship is in the queue 'Wait for inspection'
            if min(queueInspection) == t:                                                       # At least one ship is supposed to leave the queue at the current time
                for i in shipOTWInspection:                                                     # Keep track of ships that are arriving in the queue
                  if i[1] == t:
                      shipInspection.append(i[0])
                      shipOTWInspection.remove(i)
                      
                      # Statistics #
                      shipsPropListed[i[0]][7] = t

                idx = queueInspection.index(min(queueInspection))                               # Check index of ship that is supposed to leave the queue  
                assignBerth = queueInspectionBerth[idx]                                         # Make sure that berth remains assigned to ship
                
                # No check needed, as assumption is there is always people available for inspection
                inspectionTime = cargoInspection(meanInspection, stdInspection)                 # Calculate service time
                
                queueInspection.pop(idx)
                queueInspectionBerth.pop(idx)
                
                # Statistics  and sequencing #
                ID = shipInspection[0]
                shipInspection.remove(ID) 
                shipsPropListed[ID][8] = t     
                shipsPropListed[ID][9] = inspectionTime   
                
                shipOTWUnloading.append([ID, t + inspectionTime])
                nextBerthAvailable[assignBerth] = t + inspectionTime                            # Make sure that berth remains assigned to ship
                queueUnloading.append(t + inspectionTime)                                       # Enter ship in queue 'Wait for unloading'
                queueUnloadingBerth.append(assignBerth)

        #################
        # Event: Unload #
        #################
        
        if len(queueUnloading) > 0:                                                             # At least one ship is in the queue 'Wait for unloading'
            if min(queueUnloading) == t:                                                        # At least one ship is supposed to leave the queue at the current time
                for i in shipOTWUnloading:                                                      # Keep track of ships that are arriving in the queue
                   if i[1] == t:
                       dockers.append('U')                                                      # FIFO -> unloading operation
                       shipUnloading.append(i[0])
                       shipOTWUnloading.remove(i)
                       
                       # Statistics #
                       shipsPropListed[i[0]][10] = t                                         
    
                idx = queueUnloading.index(min(queueUnloading))                                 # Check index of ship that is supposed to leave the queue 
                assignBerth = queueUnloadingBerth[idx]                                          # Make sure that berth remains assigned to ship
                
                doFine = False
                if dockers[0] == 'U':                                                           # Check if the ship is the first one that is supposed to leave the queue -> FIFO policy
                    doFine = True
                    
                if t >= min(nextDockerTeamAvailable) and doFine == True:                        # Ship can only leave the queue when a docker team is available and FIFO is satisfied
                    unloadTime = unloading(lbUnloading, peakUnloading, ubUnloading)             # Calculate service time
                    dockers.pop(0)
                    queueUnloading.pop(idx)                                                     # Remove ship from queue
                    queueUnloadingBerth.pop(idx)
                    assignDockers = nextDockerTeamAvailable.index((min(nextDockerTeamAvailable))) # Assign docker team to ship
                    nextDockerTeamAvailable[assignDockers] = t + unloadTime                     # Update time at which docker team becomes available
                    nextBerthAvailable[assignBerth] = t + unloadTime                            # Update time at which berth becomes available

                    # Statistics and sequencing #
                    ID = shipUnloading[0]
                    shipUnloading.remove(ID) 
                    shipOTWLoading.append([ID, t + unloadTime])                
                    shipsPropListed[ID][11] = t 
                    shipsPropListed[ID][12] = unloadTime
                
                    queueLoading.append(t + unloadTime)                                         # Add ship to next queue
                    queueLoadingBerth.append(assignBerth)                                       # Make sure that berth remains assigned to the ship
                    
                else:                                                                           # Reschedule
                    potenStartTime = min(nextDockerTeamAvailable)
                    queueUnloading.pop(idx)
                    queueUnloading.append(potenStartTime)
                    nextBerthAvailable[assignBerth] = potenStartTime                            # Make sure that berth remains assigned to the ship
  
        ###############
        # Event: Load #
        ###############
                     
        if len(queueLoading) > 0:                                                               # At least one ship is in the queue 'Wait for loading'
            if min(queueLoading) == t:                                                          # At least one ship is supposed to leave the queue at the current time
                for i in shipOTWLoading:                                                        # Keep track of ships that are arriving in the queue
                   if i[1] == t:
                       dockers.append('L')                                                      # FIFO -> loading operation
                       shipLoading.append(i[0])
                       shipOTWLoading.remove(i)
                       
                       # Statistics #
                       shipsPropListed[i[0]][13] = t              
    
                idx = queueLoading.index(min(queueLoading))                                     # Check index of ship that is supposed to leave the queue
                assignBerth = queueLoadingBerth[idx]                                            # Make sure that berth remains assigned to ship
                
                doFine = False
                if dockers[0] == 'L':                                                           # Check if the ship is the first one that is supposed to leave the queue -> FIFO policy
                    doFine = True
                        
                if t >= min(nextDockerTeamAvailable) and doFine == True:
                    loadTime = loading(lbLoading, peakLoading, ubLoading)                       # Calculate service time
                    dockers.pop(0)
                    queueLoading.pop(idx)                                                       # Remove ship from queue
                    queueLoadingBerth.pop(idx)
                    nextBerthAvailable[assignBerth] = t + loadTime                              # Update time at which berth becomes available
                    assignDockers = nextDockerTeamAvailable.index(min(nextDockerTeamAvailable)) # Assign docker team to ship
                    nextDockerTeamAvailable[assignDockers] = t + loadTime                       # Update time at which docker team becomes available
                    
                    # Statistics and sequencing #
                    ID = shipLoading[0]
                    shipLoading.remove(ID)    
                    shipOTWUndocking.append([ID, t + loadTime])                
                    shipsPropListed[ID][14] = t   
                    shipsPropListed[ID][15] = loadTime   
    
                    queueUndocking.append(t + loadTime)                                         # Add ship to next queue
                    queueUndockingBerth.append(assignBerth)
    
                else:                                                                           # Reschedule
                    potenStartTime = min(nextDockerTeamAvailable)
                    queueLoading.pop(idx)
                    queueLoading.append(potenStartTime)
                    nextBerthAvailable[assignBerth] = potenStartTime                            # Make sure that berth remains assigned to ship

        #################
        # Event: Undock #
        #################
                     
        if len(queueUndocking) > 0:                                                             # At least one ship is in the queue 'Wait for undocking'
            if min(queueUndocking) == t:                                                        # At least one ship is supposed to leave the queue at the current time
                for i in shipOTWUndocking:                                                      # Keep track of ships that are arriving in the queue
                   if i[1] == t:
                       tugs.append('U')                                                         # FIFO -> undocking operation
                       portBasins.append('L')                                                   # FIFO -> leaving operation
                       shipUndocking.append(i[0])
                       shipOTWUndocking.remove(i)
                       
                       # Statistics #
                       shipsPropListed[i[0]][16] = t  
    
                idx = queueUndocking.index(min(queueUndocking))                                 # Check index of ship that is supposed to leave the queue
                assignBerth = queueUndockingBerth[idx]                                          # Make sure that berth remains assigned to ship
                
                tugFine = False                
                waitPB = False
                pbFine = False
                for i in portBasins:                                                            # Check if there is a prioritized external request for a port basin
                    if i[0] == 'SR_PB':
                        waitPB = True
                        break
                
                if waitPB == False:                                                             # Check if leaving operation for port basin and undocking operation for tugboat are the activities that need to happen first
                    if portBasins[0] == 'L':
                        pbFine = True
                    if tugs[0] == 'U':
                        tugFine = True
                
                if t >= min(nextPortBasinAvailable) and t >= min(nextTugboatArrival) and waitPB == False and pbFine == True and tugFine == True and tugsLiveCounter < nrTugboats: # Ship can only leave the queue when both a tugboat and port basin are available, FIFO is satisfied, and no prioritized external service requests for the port basin
                    tugsLiveCounter += 1                                                        # Keep track of the number of tugboats that are busy -> needed to ensure that tugboat can be kept for same ship during multiple activities
                    undockTime = undocking(undockingTime)                                       # Calculate service time
                    portBasins.pop(0)
                    tugs.pop(0)
                    queueUndocking.pop(idx)                                                     # Remove ship from queue
                    queueUndockingBerth.pop(idx)
                    
                    nextBerthAvailable[assignBerth] = t + undockTime                            # Update time at which berth becomes available
                    
                    assignPortBasin = nextPortBasinAvailable.index(min(nextPortBasinAvailable)) # Update time at which port basin becomes available
                    nextPortBasinAvailable[assignPortBasin] = t + undockTime
                    
                    assignTugboat =  nextTugboatArrival.index(min(nextTugboatArrival))          # Update time at which tugboat becomes available
                    nextTugboatArrival[assignTugboat] = t + undockTime                    
                    
                    # Statistics & sequencing #
                    ID = shipUndocking[0]
                    shipUndocking.remove(ID) 
    
                    shipOTWLeaving.append([ID, t + undockTime])  
                    shipsPropListed[ID][17] = t  
                    shipsPropListed[ID][18] = undockTime 

                    queueLeaving.append(t + undockTime)                                         # Add ship to next queue   
                    queueLeavingTug.append(assignTugboat)
                    
                else:                                                                           # Reschedule
                    if portBasins[0] == 'L':                                                    # Leaving operation is supposed to occur at port basin
                        potenStartTime = -1
                        pot = 10 * T
                        if tugsLiveCounter == nrTugboats:                                       # All tugboats are occupied
                            if len(tugBack) > 0:                                                # Jump to time where next tugboat becomes available
                                potenStartTime = min(tugBack)     
                            if len(queueInspection) > 0:                                        # Jump to time where first tugboat becomes available
                                if min(queueInspection) < pot:
                                    pot = min(queueInspection)
                            if len(queueUnloading) > 0:
                                if min(queueUnloading) < pot:
                                    pot = min(queueUnloading)                        
                            if len(queueLeaving) > 0:
                                if min(queueLeaving) < pot:
                                    pot = min(queueLeaving)
                            if len(queueServiceRequestTug) > 0:
                                if min(queueServiceRequestTug) < pot:
                                    pot = min(queueServiceRequestTug)                               
                            if potenStartTime == -1:
                                potenStartTime = pot                  
                        else:
                            if tugs[0] == 'SR_T':                                               # Next event is supposed to be a service request
                                potenStartTime = min(queueServiceRequestTug)
                            elif tugs[0] == 'A':                                                # Next event is supposed to be an arrival
                                if busyArrivals < len(nextTugboatArrival) -1:
                                    potenStartTime = min(queueEntering)
                                else:                                                           # Prioritize undocking event over arrival event since arrival may not take place (due to congestion)
                                    idxN = tugs.index('U')
                                    tugs.pop(idxN)
                                    tugs.insert(0, 'U')          
                                    potenStartTime = min(queueUndocking)
                            else:
                                potenStartTime = min(nextPortBasinAvailable)  
                    elif portBasins[0] == 'D':                                                  # Next event in port basin is supposed to be docking event
                        potenStartTime = min(queueDocking)
                    else:
                        potenStartTime = min(queueServiceRequestPortBasin)                      # Next event in port basin is supposed to be a service request -> priority
                    queueUndocking.pop(idx)                                                     # Remove ship from queue
                    queueUndocking.append(potenStartTime)                    
                    nextBerthAvailable[assignBerth] = potenStartTime                            # Update time at which berth becomes available
                    
                    if busyArrivals == nrTugboats - 1 and berthsLiveCounter == nrBerths:        # If both tugboats and berths are fully occupied -> prioritize undocking event to make a berth and tugboat available as soon as possible
                        idxT = tugs.index('U')
                        tugs.pop(idxT)
                        tugs.insert(0,'U')

        #####################
        # Event: Leave port #
        #####################
                    
        if len(queueLeaving) > 0:                                                               # At least one ship is in the queue 'Wait for leaving port'
            if min(queueLeaving) == t:                                                          # At least one ship is supposed to leave the queue at the current time
                for i in shipOTWLeaving:                                                        # Keep track of ships arriving in the queue
                   if i[1] == t:
                       shipLeaving.append(i[0])
                       shipOTWLeaving.remove(i)    
                       berthsLiveCounter -= 1                                                   # Make berth available again
                       
                       # Statistics #
                       shipsPropListed[i[0]][19] = t  
                       
                idx = queueLeaving.index(min(queueLeaving))                                     # Check index of ship that is supposed to leave the queue
                assignTugboat = queueLeavingTug[idx]                                            # Make sure that tugboat remains assigned to ship
                
                leavingPort = enterLeavePort(lbEntLeave, ubEntLeave)                            # Service time
                
                # Statistics & sequencing #
                ID = shipLeaving[0]
                shipLeaving.pop(idx)    
                shipEnd.append([ID, t + leavingPort]) 
                shipsPropListed[ID][20] = t                                                     # Start time
                shipsPropListed[ID][21] = leavingPort                                           # Service time
                shipsPropListed[ID][22] = t + leavingPort                                       # End time    
    
                queueLeaving.pop(idx)                                                           # Remove ship from queue
                queueLeavingTug.pop(idx)
                nextTugboatArrival[assignTugboat] = t + leavingPort                             # Update time at which tugboat becomes available  
                tugBack.append(t + leavingPort)                                                 # Same, create event
             
        if len(tugBack) > 0:                                                                    # At least one tugboat is busy
            if min(tugBack) == t:                                                               # At least one tugboat is arriving at this time
                idxDelete = tugBack.index(min(tugBack))
                tugBack.pop(idxDelete)
                tugsLiveCounter -= 1                                                            # Make tugboat available
        
        #############################################
        # Updating time t by identifying next event #
        #############################################
        
        nextEvent[0] = nextArrival                                                  
            
        if len(queueEntering) != 0:                                                             # If a queue is empty, set the time to sufficiently large such that it is not being selected as next event                                          
            nextEvent[1] = min(queueEntering)
        else:
            nextEvent[1] = 10 * T                                                    
         
        if len(queueDocking) != 0:
            nextEvent[2] = min(queueDocking)
        else:
            nextEvent[2] = 10 * T
            
        if len(queueUnloading) != 0:
            nextEvent[3] = min(queueUnloading)
        else:
            nextEvent[3] = 10 * T
    
        if len(queueInspection) != 0:
            nextEvent[4] = min(queueInspection)
        else:
            nextEvent[4] = 10 * T
            
        if len(queueLoading) != 0:
            nextEvent[5] = min(queueLoading)
        else:
            nextEvent[5] = 10 * T
        
        if len(queueUndocking) != 0:
            nextEvent[6] = min(queueUndocking)
        else:
            nextEvent[6] = 10 * T
            
        if len(queueLeaving) != 0:                                                
            nextEvent[7] = min(queueLeaving)
        else:
            nextEvent[7] = 10 * T                                 
        
        if len(queueServiceRequestPortBasin) != 0:
            nextEvent[8] = min(queueServiceRequestPortBasin)
        else:
            nextEvent[8] = 10 * T
    
        if len(queueServiceRequestDockTeam) != 0:
            nextEvent[9] = min(queueServiceRequestDockTeam)
        else:
            nextEvent[9] = 10 * T
    
        if len(queueServiceRequestTug) != 0:
            nextEvent[10] = min(queueServiceRequestTug)
        else:
            nextEvent[10] = 10 * T
            
        nextEvent[11] = nextPortBasinReq
    
        nextEvent[12] = nextServReqTug
    
        nextEvent[13] = nextServReqDockTeam
        
        if len(tugBack) != 0:
            nextEvent[14] = min(tugBack)
        else:
            nextEvent[14] = 10 * T
        
        t = min(nextEvent)                                                                  # Update time  
        
    ##################
    # Write to Excel #
    ##################
    
    columns = ['Ship ID', 'E: Queue entering port', 'L: Queue entering port', 'Time to enter port', 'E: Queue docking', 'L: Queue docking', 'Time to dock','E: Queue inspection', 'L: Queue inspection', 'Time to inspect','E: Queue unloading', 'L: Queue unloading', 'Time to unload', 'E: Queue loading', 'L: Queue loading', 'Time to load', 'E: Queue undocking', 'L: Queue undocking', 'Time to undock', 'E: Queue leaving', 'L: Queue leaving', 'Time to leave port', 'Left port']                                    
    df = pd.DataFrame(columns = columns)    
    
    for i in range(len(shipsPropListed)):
        df.loc[len(df)] = shipsPropListed[i]
    df = df.round(decimals = 2)    
    df.to_excel('outputSimulation.xlsx', index=False)    
            
    columns = ['Ext Req ID', 'Enter queue', 'Leave queue', 'Duration', 'Leave system']
    dfPB = pd.DataFrame(columns = columns)
    for i in range(len(extReqPBListed)):
        dfPB.loc[len(dfPB)] = extReqPBListed[i]
    dfPB = dfPB.round(decimals = 2)
    
    columns = ['Ext Req ID', 'Enter queue', 'Leave queue', 'Duration', 'Leave system']
    dfDO = pd.DataFrame(columns = columns)
    for i in range(len(extReqDOListed)):
        dfDO.loc[len(dfDO)] = extReqDOListed[i]
    dfDO = dfDO.round(decimals = 2)
    
    columns = ['Ext Req ID', 'Enter queue', 'Leave queue', 'Duration', 'Leave system']
    dfTU = pd.DataFrame(columns = columns)
    for i in range(len(extReqTUListed)):
        dfTU.loc[len(dfTU)] = extReqTUListed[i]
    dfTU = dfTU.round(decimals = 2)

    with pd.ExcelWriter('outputSimulation.xlsx') as writer:  
        df.to_excel(writer, sheet_name='Ships', index = False)    
        dfPB.to_excel(writer, sheet_name='Ext Req PB', index = False)
        dfDO.to_excel(writer, sheet_name='Ext Req DO', index = False)
        dfTU.to_excel(writer, sheet_name='Ext Req TU', index = False)

T = 3000                   # Total run time of simulation
N = 10               # Number of simulation runs

for i in range(N):
    print(i)
    runSim(T)
