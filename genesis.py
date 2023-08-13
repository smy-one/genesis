#@title Genesis SMY retreat prana group assignment system
# https://siddhamaha.link/genesis-notebook
#
# Dedicated to the loving expansion of our profound Siddha Maha Yoga sangha throughout
# the world by the grace of our wonderful Guruji, Swami Nardanand Paramahans

# Purpose: to assign new sadhaks (seekers) to prana groups according to the following criteria:
# Every two months Siddha Maha Yoga holds an online retreat whereby ~100 new sadhaks are initiated into the system.
# Part of the experience is to share daily with a small "prana group" consisting of two prana partners and around 6 new sadhaks
# We have a set of criteria to guide the prana group assignment process:
#  - Even new sadhak gender balance
#  - Even new sadhak age distribution
#  - Prana group time matches ideally each new sadhak's first choice, failing tha their second choice time slot
#  - New sadhaks are not in the same group as anyone they know, here defined as their referrer or a spouse
#
# Todo: Notion integration - https://github.com/ramnes/notion-sdk-py
# Todo: More accurate gender and age distribution ideals
#
# NB Unexpected EOF error may be the result of the sheet not being filled properly!
# Todo: rethink the "acceptances" tag - doesn't seem to be used anymore - leads to empty bin problems


!pip install --upgrade gspread

import numpy as np
import copy
import pickle
import pprint
import random
from google.colab import auth
import gspread
from oauth2client.client import GoogleCredentials
from datetime import datetime
import cProfile, pstats, io
from pstats import SortKey
from enum import Enum

# *** This needs to be manually set:
newPgs = {
    "PG01" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG02" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG03" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG04" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG05" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG06" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG07" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG08" : {"pp1" : "", "pp2" : "", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG09" : {"pp1" : "", "pp2" : "", "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG10" : {"pp1" : "", "pp2" : "", "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG11" : {"pp1" : "", "pp2" : "", "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG12" : {"pp1" : "", "pp2" : "", "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG13" : {"pp1" : "", "pp2" : "", "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG14" : {"pp1" : "", "pp2" : "", "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    "PG15" : {"pp1" : "", "pp2" : "", "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    "PG16" : {"pp1" : "", "pp2" : "", "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    "PG17" : {"pp1" : "", "pp2" : "", "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    }

returningPgs = {
    "APG01" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG02" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG03" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG04" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG05" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG06" : {"time" : "3pm", "sadhaks" : {}, "advanced" : "yes"},
    "APG07" : {"time" : "3pm", "sadhaks" : {}, "advanced" : "yes"},
    "APG08" : {"time" : "8:30pm", "sadhaks" : {}, "advanced" : "yes"},
}

Operation = Enum('Operation', ['SWAP', 'MOVE_SADHAK1', 'MOVE_SADHAK2'])

# Constants
NEW_SADHAKS = True # <--- Very important, if False, assign returning sadhaks
GOOGLE_SHEET = 'https://docs.google.com/spreadsheets/d/1t52lVnikS8fica4mGiuvX_zkPeALT6mCyipKRzH2b9o'

# The following need to be updated every retreat:
RETREAT = SADHAK_SHEET = "R19"
SADHAK_SHEET += " new" if NEW_SADHAKS else " APG"
NUM_NEW_SADHAKS = 95
NUM_RETURNING_SADHAKS = 62
PG_COL = "AR"
TIME_COL = "AS"
NAME_COL = "B"
SADHAK_DETAILS_COL = "AW"
GROUP_SIZE = 6
IDEAL_MH_PG_SIZE = 14 / 7 # TODO: calculate this

NUM_SADHAKS = NUM_NEW_SADHAKS if NEW_SADHAKS else NUM_RETURNING_SADHAKS
pgs = newPgs if NEW_SADHAKS else returningPgs


# Genetic algorithm hyperparameters
POPSIZE = 100
MUTATIONS_PER_GENERATION = 50000
FAST_MUTATIONS_PER_GENERATION = 3000

use_profiler = True

# Google sheets setup
#from google.colab import auth
#auth.authenticate_user()
#import gspread
#from oauth2client.client import GoogleCredentials
#gc = gspread.authorize(GoogleCredentials.get_application_default())

from google.colab import auth
auth.authenticate_user()
import gspread
from google.auth import default
creds, _ = default()
gc = gspread.authorize(creds)

# Reads the sadhak names and a precomposed python hashmap of relevant sadhak attributes from the Google sheet
def getSadhaksFromGoogleSheet():
  worksheet = gc.open_by_url(GOOGLE_SHEET).worksheet(SADHAK_SHEET)

  sadhaks = {}
  nameRange = NAME_COL + "2:" + NAME_COL + str(NUM_SADHAKS + 1)
  valueRange = SADHAK_DETAILS_COL + "2:" + SADHAK_DETAILS_COL + str(NUM_SADHAKS + 1)
  sadhakNames = worksheet.range(nameRange)
  sadhakValues = worksheet.range(valueRange)

  while sadhakNames or sadhakValues:
    sadhakCell = sadhakNames.pop()
    sadhakName = sadhakCell.value
    sadhakRow = sadhakCell.row
    sadhakValue = sadhakValues.pop().value
    print(sadhakName, ": ", sadhakValue)
    sadhaks[sadhakName] = eval(sadhakValue)
    # Row is needed for when we add the prana group assignments at the end - see setPGsInGoogleSheet()
    sadhaks[sadhakName]["row"] = sadhakRow

  return sadhaks

# Writes each sadhak's prana group assignment back to the Google sheet
# TODO: set the pg's directly in Notion: https://pythonrepo.com/repo/minwook-shin-notion-database
def setPGsInGoogleSheet(pgs):
  worksheet = gc.open_by_url(GOOGLE_SHEET).worksheet(SADHAK_SHEET)
  pgList = [""] * NUM_SADHAKS
  timeList = [""] * NUM_SADHAKS
  for pg in pgs:
    for sadhak in pgs[pg]["sadhaks"]:
      # Set the next sadhak pg in the list to be moved into the sheet
#      print(pgs[pg]["sadhaks"][sadhak], pgs[pg]["sadhaks"][sadhak]["row"]-2)
#      print(pgs[pg]["sadhaks"][sadhak]["row"]-2, ": ", pgs[pg]["time"][sadhak]["row"]-2)
      pgList[pgs[pg]["sadhaks"][sadhak]["row"]-2] = [pg]
      timeList[pgs[pg]["sadhaks"][sadhak]["row"]-2] = [pgs[pg]["time"]]
  print(pgList)
  worksheet.update(PG_COL + "2:" + PG_COL + str(NUM_SADHAKS + 1), pgList)
  worksheet.update(TIME_COL + "2:" + TIME_COL + str(NUM_SADHAKS + 1), timeList)

# printPGs(pgs) -- Prints all the sadhak names for each prana group in pgs
# Not really used anymore
def printPGs(pgs):
  for pg in pgs:
    print(pg, ": ", end='')
    for sadhak in pgs[pg]["sadhaks"]:
      print(sadhak, end=', ')
  print()

# scorePG(pg) -- score the prana group pg
def scorePG(pg):
  mhCount = 0
  ppCount = 0
  appCount = 0
  ageCounts = {"17 - 34 yrs old" : 0, "35 - 55 yrs old" : 0, "Over 56 yrs old" : 0}
  genderCounts = {"Female" : 0, "Male" : 0}
  score = {"time" : 0, "knows" : 0, "gender" : 0, "age" : 0, "mh" : 0, "mh_group_size" : 0, "pp" : 0, "group_size" : 0, "total" : 0}
  sadhaks = pg["sadhaks"]
  knows = {}
  for sadhak in sadhaks:
    if NEW_SADHAKS and sadhaks[sadhak]["age"] != "":
      ageCounts[sadhaks[sadhak]["age"]] += 1

    if sadhaks[sadhak]["gender"] in ["Female", "Male"]:
      genderCounts[sadhaks[sadhak]["gender"]] += 1

    if sadhaks[sadhak]["time1"] != pg["time"]:
      if sadhaks[sadhak]["time2"] != "":
        # mild penalty for not assigning first choice time slot
        score["time"] += 10
        if sadhaks[sadhak]["time2"] != pg["time"]:
          # heavy penalty for not assigning either time slot
          score["time"] += 50
      else:
        # heavy penalty for not getting their one slot
        score["time"] += 50

    if NEW_SADHAKS and sadhaks[sadhak]["mh"] == "yes":
      if pg["advanced"] != "yes":
        # super heavy penalty for sadhak with mh issues not assigned to an advanced group
        score["mh"] += 50
      else:
        mhCount += 1

    for s in sadhaks[sadhak]["knows"]:
      if NEW_SADHAKS:
        if pg["pp1"] == s or pg["pp2"] == s:
          #print("Sadhak ", sadhak, " knows ", s)
          # heavy penalty for knowing someone in the group
          score["knows"] += 20
      for other_sadhak in sadhaks:
        if other_sadhak == s:
#          print (sadhak + " knows " + other_sadhak)
          score["knows"] += 20

    if not NEW_SADHAKS:
      if sadhaks[sadhak]["app"] == "yes":
        appCount += 1
      elif sadhaks[sadhak]["pp"] == "yes":
        ppCount += 1

  # Score age variance
  if NEW_SADHAKS:
    ideal = len(sadhaks) / 3 # age categories
    for age in ageCounts:
      score["age"] += (abs(ageCounts[age] - ideal)) ** 2

  # Score gender variance
  ideal = len(sadhaks) / 2
  genderScore = 0
  for gender in genderCounts:
    # We heavily penalize very lopsided groups by squaring the delta from ideal
    score["gender"] += (genderCounts[gender] - ideal) ** 2

  # Score mh variance from ideal
  if NEW_SADHAKS and pg["advanced"] == "yes":
    score["mh_group_size"] += (mhCount - IDEAL_MH_PG_SIZE) ** 4

  # Score leadership
  if not NEW_SADHAKS:
    ppScore = 50
    if appCount > 0:
      ppScore = 0
    elif ppCount > 0:
      ppScore = 10
    score["pp"] = ppScore
  else:
    score["pp"] = 0

  # Score group size if it's the endgame
  if len(sadhaks) < GROUP_SIZE - 1: # and len(pgsPop) < POPSIZE
    score["group_size"] += 10

#  if random.randint(1,1000) == 1:
#    print("Scoring pg: ", pg)
#    print("ageCounts: ", ageCounts)
#    print("genderCounts: ", genderCounts)
#    print("score = ", score)

  # Don't round yet, do this when summing pg scores
  score["total"] = score["age"] + score["gender"] + score["time"] + score["knows"] + score["mh"] + score["mh_group_size"] + score["pp"] + score["group_size"]
  return score

def cloneList(list):
  list_copy = list[:]
  return list_copy

# mutatePGs(pgs) -- perform one "mutation" - a set of swaps of sadhaks between different pg's in pgs
def mutatePGs(pgs, score = 10000):
  # mutant = copy.deepcopy(pgs) # TODO: deepcopy is slow! Only deepcopy pg's you need to, unless score ends up being lower
  mutant = pickle.loads(pickle.dumps(pgs, -1))
  # Randomize the # swaps in the mutation for fun
  for x in range (1, random.randint(1,20)):
    # Pick two random sadhaks in different pgs
    pg1key = list(mutant)[random.randint(0, len(mutant)-2)] # exclude "bin"
    pg2key = pg1key
    pg2keyNoBin = pg1key
    while pg1key == pg2key:
      # make sure it's a different pg
      pg2key = list(mutant)[random.randint(0, len(mutant)-1)]
    while pg2keyNoBin == pg1key:
      pg2keyNoBin = list(mutant)[random.randint(0, len(mutant)-2)]

    # Swap the sadhaks. Very tedious verbose code :-(
    sadhakList1 = mutant[pg1key]["sadhaks"]
    sadhak1key = list(sadhakList1)[random.randint(0, len(sadhakList1)-1)]
    sadhak1val = sadhakList1[sadhak1key]
    if pg2key == "bin": # and sadhak1val["acceptances"] != "": # priority sadhaks have no chance of being sent to the bin
      pg2key = pg2keyNoBin
    sadhakList2 = mutant[pg2key]["sadhaks"]
    sadhak2key = list(sadhakList2)[random.randint(0, len(sadhakList2)-1)]
    sadhak2val = sadhakList2[sadhak2key]

    # Choose which operation to perform
    operation = Operation.SWAP;
    if len(sadhakList1) < GROUP_SIZE and len(sadhakList2) == GROUP_SIZE:
      if random.randint(1,2) == 1 or len(sadhakList1) < GROUP_SIZE - 1:
        operation = Operation.MOVE_SADHAK2
        # print("Moving sadhak %s from %s (%d) to %s (%d) => " % (sadhak2key, pg2key, len(sadhakList2), pg1key, len(sadhakList1)), end = "")
    elif len(sadhakList1) == GROUP_SIZE and len(sadhakList2) < GROUP_SIZE:
      if random.randint(1,2) == 1 or len(sadhakList2) < GROUP_SIZE - 1:
        operation = Operation.MOVE_SADHAK1
        # print("Moving sadhak %s from %s (%d) to %s (%d) => " % (sadhak1key, pg1key, len(sadhakList1), pg2key, len(sadhakList2)), end = "")
    elif len(sadhakList1) == GROUP_SIZE-1 and len(sadhakList2) == GROUP_SIZE-1:
      sel = random.randint(1,3)
      if sel == 1:
        operation = Operation.MOVE_SADHAK1
      elif sel == 2:
        operation = Operation.MOVE_SADHAK2
      else:
        operation = Operation.SWAP

    # Perform the operation
    if operation == Operation.SWAP or operation == Operation.MOVE_SADHAK1:
      sadhakList1.pop(sadhak1key)
    if operation == Operation.SWAP or operation == Operation.MOVE_SADHAK2:
      sadhakList1[sadhak2key] = sadhak2val
      sadhakList2.pop(sadhak2key)
    if operation == Operation.SWAP or operation == Operation.MOVE_SADHAK1:
      sadhakList2[sadhak1key] = sadhak1val
    #if operation == Operation.MOVE_SADHAK1 or operation == Operation.MOVE_SADHAK2:
      # print("%s, %s: %s, %s: %s" % (operation, pg1key, list(sadhakList1.keys()), pg2key, list(sadhakList2.keys())))

  return mutant;

# scorePGs(pgs) -- add up all the scores of each pg in pgs
def scorePGs(pgs):
  totalScore = {"time" : 0, "knows" : 0, "gender" : 0, "age" : 0, "mh" : 0, "mh_group_size" : 0, "pp" : 0, "group_size" : 0, "total" : 0}
  for pg in pgs:
    if pg != "bin":
      score = scorePG(pgs[pg])
      totalScore["total"] += score["total"]
      totalScore["age"] += score["age"]
      totalScore["gender"] += score["gender"]
      totalScore["time"] += score["time"]
      totalScore["knows"] += score["knows"]
      totalScore["mh"] += score["mh"]
      totalScore["mh_group_size"] += score["mh_group_size"]
      totalScore["pp"] += score["pp"]
      totalScore["group_size"] += score["group_size"]

  # Now we round; tedious code
  totalScore["total"] = int(totalScore["total"])
  totalScore["age"] = int(totalScore["age"])
  totalScore["gender"] = int(totalScore["gender"])
  totalScore["time"] = int(totalScore["time"])
  totalScore["knows"] = int(totalScore["knows"])
  totalScore["mh"] = int(totalScore["mh"])
  totalScore["mh_group_size"] = int(totalScore["mh_group_size"])
  totalScore["pp"] = int(totalScore["pp"])
  return totalScore

def initialPGs(pgs):
  initialPgs = copy.deepcopy(pgs)
  sortedSadhaks = []
  optionals = []
  shuffledSortedSadhaks = []
  for sadhak in sadhaks:
#    if sadhaks[sadhak]["acceptances"] != "": # priority
    sortedSadhaks.append(sadhak)
#    else:
#      optionals.append(sadhak)
  # shake it up
  perm = np.random.permutation(len(sortedSadhaks))
  for x in range(0, len(sortedSadhaks)):
    shuffledSortedSadhaks.append(sortedSadhaks[perm[x]])
  shuffledSortedSadhaks.extend(optionals)
  #print("shuffledSortedSadhaks:", shuffledSortedSadhaks)

  sadhak_iter = iter(shuffledSortedSadhaks)
  try:
    index = 0
    for x in range(1, GROUP_SIZE + 1):
#      print("x = ", x, ":")
      for pg in pgs:
        if pg != "bin": # Don't fill the excess sadhak bin until the end
          if index < len(shuffledSortedSadhaks): # Handle sadhak shortages
            sadhak_name = shuffledSortedSadhaks[index]
            sadhak_value = sadhaks[sadhak_name]
            index += 1
            initialPgs[pg]["sadhaks"][sadhak_name] = sadhak_value
#          else:
#            print("skipped member # ", x, " for ", pg)
    while index < len(shuffledSortedSadhaks):
      # Fill the bin with excess sadhaks
      sadhak_name = shuffledSortedSadhaks[index]
      index += 1
      sadhak_value = sadhaks[sadhak_name]
      initialPgs["bin"]["sadhaks"][sadhak_name] = sadhak_value
  except StopIteration:
    # do nothing
    x = 10
  return initialPgs

# randomPGAssignment(pgs) --
def randomPGAssignment(pgs):
  randomPgs = copy.deepcopy(pgs)

  perm = np.random.permutation(len(sadhaks))
  randSadhaks = {}
  #print("# sadhaks: ", GROUP_SIZE * (len(pgs) - 1))
  for x in range(0, GROUP_SIZE * (len(pgs) - 1)):
    key = list(sadhaks)[perm[x]]
    value = list(sadhaks.values())[perm[x]]
    randSadhaks[key] = value
  sadhak_iter = iter(randSadhaks)
  try:
    for pg in pgs:
      if pg != "bin":
        for x in range(1, GROUP_SIZE + 1):
          sadhak_name = next(sadhak_iter)
          sadhak_value = randSadhaks[sadhak_name]
          randomPgs[pg]["sadhaks"][sadhak_name] = sadhak_value
  #  printPGs(randomPgs)

  except StopIteration:
    # do nothing
    print("StopIteration: ", StopIteration)

  return randomPgs

# dropSadhak(sadhakName): drop sadhakName from their pg then return possible rebalancings
# - Remove sadhak from their group
# - Score the sadhak's group
# - Try moving every single other sadhak into the group, see if the score improves
# - Suggest a bunch of possible moves that improve things
def dropSadhak(sadhakName):
  return

# moveSadhak(sadhakName, pgName): move sadhakName to pgName
def moveSadhak(sadhakName, pgName):
  return

# swapSadhak(sadhakName): swap sadhakName with any other sadhak yielding the best score
# swapSadhak(sadhakName, sadhakName2): swap sadhakName with sadhakName2
# swapSadhak(sadhakName, pgName): swap sadhakName with someone in pgName yielding the best score
def swapSadhak(sadhakName, sadhakName2, pgName):
  return

bestPGs = {}
bestScore = {"time" : 0, "knows" : 0, "gender" : 0, "age" : 0, "mh" : 0, "mh_group_size" : 0, "pp" : 0, "total" : 10000}
random.seed(datetime.now())
sadhaks = getSadhaksFromGoogleSheet()

# initialPGAssignment(pgs) -- assign sadhaks to pgs
# Not really used anymore
def initialPGAssignment(pgs):
  sadhak_iter = iter(sadhaks)
  for pg in pgs:
    for x in range(1, GROUP_SIZE + 1):
      sadhak_name = next(sadhak_iter)
      sadhak_value = sadhaks[sadhak_name]
      pgs[pg]["sadhaks"][sadhak_name] = sadhak_value
  return 1

# getKey(item) -- used to sort arrays of [score, pgs]
def getKey(item):
  return item[0]

# Business time!
# So the way this works is:
# 1) Generate N random pg assignments sets (pgs's)
# 2) Mutate them all randomly MUTATIONS_PER_GENERATION times
# 3) Collect best N pgs's - each one must be better than its parent!
# 4) Keep track of the global best pgs
# 5) Repeat with this set. Over time, like Earth the population will start to dwindle as it becomes
#     harder to mutate better pgs's. This continues until there are is only one pgs left
# Simple right?

print("Assigning ", "new" if NEW_SADHAKS else "returning", " sadhaks to prana groups")
gen = 0
pgsPop = []
sortedSadhaks = []
#pgs, sortedSadhaks = initialPGs(pgs)

startTime = datetime.now()
print("Start time: ", startTime)

pr = cProfile.Profile()
if use_profiler:
  pr.enable()

for x in range(0, POPSIZE):
  pgsPop.append(initialPGs(pgs))

while len(pgsPop) > 1:
  gen += 1
  print("Generation", gen, ": population", len(pgsPop))
  print()
  bestMutants = []
  batch = []

  for pgs in pgsPop:
    nextPgs = pgsPop.pop(0)
    score = scorePGs(nextPgs)["total"]
    batch.append([score, nextPgs])

  # Experiment!
  if len(pgsPop) < POPSIZE:
    mutationCount = MUTATIONS_PER_GENERATION
  else:
    mutationCount = FAST_MUTATIONS_PER_GENERATION # initial speedy period

  for x in range(0, mutationCount):
    # find best mutants out of <many> tries
    batchIndex = random.randint(0, len(batch)-1)
    score = batch[batchIndex][0]
    pg = batch[batchIndex][1]
    mutant = mutatePGs(pg)
    #if mutant:
    mutantScore = scorePGs(mutant)
    if mutantScore["total"] < score: # score comparison
      if len(bestMutants) < POPSIZE:
        bestMutants.append([mutantScore["total"], mutant])
        bestMutants = sorted(bestMutants, key=getKey, reverse = False) # score comparison
      else:
        worstBestMutantScore = bestMutants[-1][0]
        if mutantScore["total"] < worstBestMutantScore: # score comparison
          out = bestMutants.pop()
          bestMutants.append([mutantScore["total"], mutant])
          bestMutants = sorted(bestMutants, key=getKey, reverse = False) # score comparison
      if mutantScore["total"] < bestScore["total"]: # score comparison
        bestScore = mutantScore
        bestPGs = mutant
        print("New low score!", bestScore["total"], bestScore)
        print(mutant)
        print()

  # Next generation population is the best scored POPSIZE pgs's from the combined starting population + best mutants found
  pool = batch + bestMutants
  pool = sorted(pool, key=getKey, reverse = False) # score comparison
  print("Next gen scores: ", end='')
  pgsPop = []
  size = min(POPSIZE, len(pool))
  for x in range(0, size):
    pgsPop.append(pool[x][1])
    print(pool[x][0], end=', ')
  print()

# Print the best score
print("Best score: ", bestScore)
print(bestPGs)
print("Pretty print this at: https://www.cleancss.com/python-beautify")

# Time check: count up the # sadhaks who didn't get either of their preferred time slots
missedTimes = 0
secondTimes = 0
missedSadhaks = []
apgCounts = {}
for pg in bestPGs:
  if pg != "bin":
    sadhaks = bestPGs[pg]["sadhaks"]
    for sadhak in sadhaks:
      if sadhaks[sadhak]["time1"] != bestPGs[pg]["time"]:
        if sadhaks[sadhak]["time2"] != bestPGs[pg]["time"]:
          missedTimes += 1
          missedSadhaks.append(sadhak)
        else:
          secondTimes += 1
      if bestPGs[pg]["advanced"] == "yes" and sadhaks[sadhak]["mh"] == "yes":
        if pg in apgCounts:
          apgCounts[pg] += 1
        else:
          apgCounts[pg] = 1
print("# sadhaks who got their second choice time: ", secondTimes)
print("# sadhaks who couldn't be assigned a time that works: ", missedTimes)
if missedTimes > 0:
  print("Sadhaks who couldn't be assigned a time: ", missedSadhaks)
print("apg sizes: ", apgCounts)

endTime = datetime.now()
print("End time: ", endTime)
td = endTime - startTime
print("Duration:", ':'.join(str(td).split(':')[:2]))

if use_profiler:
  pr.disable()
  s = io.StringIO()
  sortby = SortKey.CUMULATIVE
  ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
  ps.print_stats()
  print(s.getvalue())

# Write back to Google sheet, one day Notion
setPGsInGoogleSheet(bestPGs)
print("Sheet is updated: https://earthshot.link/genesis-sheet")
