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

import numpy as np
import copy
import pickle
import pprint
import random
#from google.colab import auth
import gspread
#from oauth2client.client import GoogleCredentials
from datetime import datetime
import cProfile, pstats, io
from pstats import SortKey
from enum import Enum
import matplotlib.pyplot as plt
import numpy as np

# *** This needs to be manually set:
newPgs = {
    # 6am
    "PG01" : {"pp1" : "Siphiwe Tapisi", "pp1_email": "stapisi@proton.me", "pp2" : "Monnet Zubieta", "pp2_email": "dmonnet@me.com", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG02" : {"pp1" : "Julie Liu", "pp1_email": "liujjr@gmail.com", "pp2" : "Nafiseh Gholami", "pp2_email": "nafiseh.gholami@outlook.com", "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG03" : {"pp1" : "Kelly Lawler", "pp1_email": "kellylaw555@gmail.com",  "pp2" : "Shannon Sims", "pp2_email": "shannon@foodartlove.com",  "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG04" : {"pp1" : "Kristen Grove", "pp1_email": "kristen@heavencollective.com",  "pp2" : "Mia Gentile", "pp2_email": "miagentile589@gmail.com",  "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG05" : {"pp1" : "Jae Ariadne", "pp1_email": "jaeariadne@pm.me",  "pp2" : "Paula Baker-Laporte", "pp2_email": "paula@econest.com",  "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    "PG06" : {"pp1" : "Savita Maa", "pp1_email": "sunoresenceoflove@gmail.com",  "pp2" : "", "pp2_email": "",  "time" : "6am", "sadhaks" : {}, "advanced" : "no"},
    # 3pm
    "PG07" : {"pp1" : "Marc Weinstein", "pp1_email": "weinstein.marc1@gmail.com",  "pp2" : "Kristina Maz", "pp2_email": "kristinamaz@gmail.com",  "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG08" : {"pp1" : "Alex Volkov", "pp1_email": "altryne@gmail.com",  "pp2" : "Manesha Lakhiani", "pp2_email": "manesha123@gmail.com",  "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG09" : {"pp1" : "Padma", "pp1_email": "tabathaa@hotmail.com",  "pp2" : "Apollo Luce", "pp2_email": "pecraddock3@gmail.com",  "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG10" : {"pp1" : "Luke Lida", "pp1_email": "lukeniida@gmail.com",  "pp2" : "Maria Aguirre", "pp2_email": "emariaaguirre@gmail.com",  "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    "PG11" : {"pp1" : "Jill Fox", "pp1_email": "Jill@jillfoxhealing.com",  "pp2" : "Leah Conway", "pp2_email": "leah@leahjoy.com",  "time" : "3pm", "sadhaks" : {}, "advanced" : "no"},
    # 8:30pm
    "PG12" : {"pp1" : "Sole Weiler", "pp1_email": "info@soleweller.com",  "pp2" : "Joshua Getz", "pp2_email": "jgetz85@gmail.com",  "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    "PG13" : {"pp1" : "Marialidia 'Molly' Marcotulli", "pp1_email": "marialidiamarcotulli@gmail.com",  "pp2" : "Jolene Lin", "pp2_email": "jolenelin.work@gmail.com",  "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    "PG14" : {"pp1" : "Dulini", "pp1_email": "dulinil@hotmail.com",  "pp2" : "Markus Rauhecker", "pp2_email": "mrauhecker@gmail.com",  "time" : "8:30pm", "sadhaks" : {}, "advanced" : "no"},
    }

returningPgs = {
    "APG01" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG02" : {"time" : "6am", "sadhaks" : {}, "advanced" : "yes"},
    "APG03" : {"time" : "3pm", "sadhaks" : {}, "advanced" : "yes"},
    "APG04" : {"time" : "3pm", "sadhaks" : {}, "advanced" : "yes"},
    "APG05" : {"time" : "8:30pm", "sadhaks" : {}, "advanced" : "yes"},
#    "bin" : {"time" : "8:30pm", "sadhaks" : {}, "advanced": "yes"},
}

Operation = Enum('Operation', ['SWAP', 'MOVE_SADHAK1', 'MOVE_SADHAK2'])

# Constants
NEW_SADHAKS = True # <--- Very important, if False, assign returning sadhaks
#GOOGLE_SHEET = 'https://docs.google.com/spreadsheets/d/1t52lVnikS8fica4mGiuvX_zkPeALT6mCyipKRzH2b9o'
SHEET_ID = '1i2eV1zxZ_Y_Kw1tU8ciYI3qsmkZo1fyS68vcjQz49js'
GOOGLE_SHEET = 'https://docs.google.com/spreadsheets/d/' + SHEET_ID

# The following need to be updated every retreat:
RETREAT = SADHAK_SHEET = "R21"
NEW_SADHAK_SHEET = RETREAT + " new"
APG_SADHAK_SHEET = RETREAT + " APG"
SADHAK_SHEET = NEW_SADHAK_SHEET if NEW_SADHAKS else APG_SADHAK_SHEET
PG_SHEET = RETREAT + " pgs"
NUM_NEW_SADHAKS = 82
NUM_RETURNING_SADHAKS = NUM_APG_SADHAKS = 40
if NEW_SADHAKS:
  PG_COL = "AC"
  TIME_COL = "AD"
  NAME_COL = "AE"
  SADHAK_DETAILS_COL = "AI"
  GROUP_SIZE = 6
  IDEAL_MH_PG_SIZE = 14 / 7 # TODO: calculate this
else:
  PG_COL = "L"
  TIME_COL = "M"
  NAME_COL = "N"
  SADHAK_DETAILS_COL = "R"
  GROUP_SIZE = 9 # 6

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

#from google.colab import auth
#auth.authenticate_user()
#import gspread
#from google.auth import default
#creds, _ = default()
#gc = gspread.authorize(creds)
