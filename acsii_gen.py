#!/usr/bin/python3

import datetime
import getopt
import json
import os
import sys
import traceback
from os.path import join as pjoin
import math, numbers
import decimal


def usage():
    usage_text = """
Usage: ./FLO2DTOLEVELGRID_GEN.py [-d YYYY-MM-DD] [-t HH:MM:SS] [-p -o -h] [-S YYYY-MM-DD] [-T HH:MM:SS]

-h  --help          Show usage
-f #TODO
-F  --flo2d_config  Configuration for FLO2D model run
-d  --date          Date in YYYY-MM-DD. Default is current date.
-t  --time          Time in HH:MM:SS. If -d passed, then default is 00:00:00. Otherwise Default is current time.
-p  --path          FLO2D model path which include HYCHAN.OUT
-o  --out           Suffix for 'water_level-<SUFFIX>' and 'water_level_grid-<SUFFIX>' output directories.
                    Default is 'water_level-<YYYY-MM-DD>' and 'water_level_grid-<YYYY-MM-DD>' same as -d option value.
-S  --start_date    Base Date of FLO2D model output in YYYY-MM-DD format. Default is same as -d option value.
-T  --start_time    Base Time of FLO2D model output in HH:MM:SS format. Default is set to 00:00:00
"""
    print(usage_text)


def get_water_level_grid(lines):
    waterLevels = []
    for line in lines[1:]:
        if line == '\n':
            break
        v = line.split()
        waterLevels.append('%s %s' % (v[0], v[1]))
    return waterLevels


def get_esri_grid(waterLevels, boudary, CellMap, gap=30.0, missingVal=-9999):
    "Esri GRID format : https://en.wikipedia.org/wiki/Esri_grid"
    "ncols         4"
    "nrows         6"
    "xllcorner     0.0"
    "yllcorner     0.0"
    "cellsize      50.0"
    "NODATA_value  -9999"
    "-9999 -9999 5 2"
    "-9999 20 100 36"
    "3 8 35 10"
    "32 42 50 6"
    "88 75 27 9"
    "13 5 1 -9999"

    EsriGrid = []

    # For Niluka
    # ncols:492
    # nrows:533
    # xllcorner:396935.00000
    # yllcorner:482565.00000

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    # rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1
    rows = 533
    # print('>>>>>  cols: %d, rows: %d' % (cols, rows))

    Grid = [[missingVal for x in range(cols)] for y in range(rows)]

    # print(Grid)

    for level in waterLevels:
        v = level.split()
        i, j = CellMap[int(v[0])]
        water_level = round(decimal.Decimal(v[1]), 2)
        if (i >= cols or j >= rows):
            print('i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
        if water_level >= WATER_LEVEL_DEPTH_MIN:
            # Grid[j][i] = float(v[1])
            Grid[j][i] = water_level

    print('ncols:', cols)
    print('nrows:', rows)
    print('xllcorner:', boudary['long_min'] - gap / 2)
    print('yllcorner:', boudary['lat_min'] - gap / 2)

    EsriGrid.append('%s\t%s\n' % ('ncols', cols))
    EsriGrid.append('%s\t%s\n' % ('nrows', rows))
    EsriGrid.append('%s\t%s\n' % ('xllcorner', boudary['long_min'] - gap / 2))
    EsriGrid.append('%s\t%s\n' % ('yllcorner', boudary['lat_min'] - gap / 2))
    EsriGrid.append('%s\t%s\n' % ('cellsize', gap))
    EsriGrid.append('%s\t%s\n' % ('NODATA_value', missingVal))

    for j in range(0, rows):
        arr = []
        for i in range(0, cols):
            arr.append(Grid[j][i])

        EsriGrid.append('%s\n' % (' '.join(str(x) for x in arr)))
    return EsriGrid


def get_grid_boudary(gap=250.0):
    "longitude  -> x : larger value"
    "latitude   -> y : smaller value"

    long_min = 1000000000.0
    lat_min = 1000000000.0
    long_max = 0.0
    lat_max = 0.0

    with open(CADPTS_DAT_FILE_PATH) as f:
        lines = f.readlines()
        for line in lines:
            values = line.split()
            long_min = min(long_min, float(values[1]))
            lat_min = min(lat_min, float(values[2]))

            long_max = max(long_max, float(values[1]))
            lat_max = max(lat_max, float(values[2]))

    return {
        'long_min': long_min,
        'lat_min': lat_min,
        'long_max': long_max,
        'lat_max': lat_max
    }


def get_cell_grid(boudary, gap=250.0):
    CellMap = {}

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1

    with open(CADPTS_DAT_FILE_PATH) as f:
        lines = f.readlines()
        for line in lines:
            v = line.split()
            i = int((float(v[1]) - boudary['long_min']) / gap)
            j = int((float(v[2]) - boudary['lat_min']) / gap)
            if not isinstance(i, numbers.Integral) or not isinstance(j, numbers.Integral):
                print('### WARNING i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            if (i >= cols or j >= rows):
                print('### WARNING i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            if i >= 0 or j >= 0:
                CellMap[int(v[0])] = (i, rows - j - 1)

    return CellMap


try:
    CONFIG = json.loads(open('CONFIG.dist.json').read())

    CWD = os.getcwd()
    TIMDEP_FILE = 'TIMDEP.OUT'
    WATER_LEVEL_FILE = 'water_level_grid.asc'
    WATER_LEVEL_DIR = 'water_level_grid'
    OUTPUT_DIR = 'OUTPUT'
    RUN_FLO2D_FILE = 'RUN_FLO2D.json'
    FLO2D_MODEL = 'FLO2D_30'
    GRID_SIZE = 150
    WATER_LEVEL_DEPTH_MIN = 0.3

    CADPTS_DAT_FILE = 'CADPTS.DAT'

    if 'TIMDEP_FILE' in CONFIG:
        TIMDEP_FILE = CONFIG['TIMDEP_FILE']
    if 'WATER_LEVEL_FILE' in CONFIG:
        WATER_LEVEL_FILE = CONFIG['WATER_LEVEL_FILE']
    if 'OUTPUT_DIR' in CONFIG:
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']
    if 'FLO2D_MODEL' in CONFIG:
        FLO2D_MODEL = CONFIG['FLO2D_MODEL']
    if 'CADPTS_DAT_FILE' in CONFIG:
        CADPTS_DAT_FILE = CONFIG['CADPTS_DAT_FILE']
    if 'WATER_LEVEL_DEPTH_MIN' in CONFIG:
        WATER_LEVEL_DEPTH_MIN = CONFIG['WATER_LEVEL_DEPTH_MIN']

    date = ''
    time = ''
    path = ''
    output_suffix = ''
    start_date = ''
    start_time = ''
    flo2d_config = ''
    forceInsert = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hF:d:t:p:o:S:T:fn:",
                                   ["help", "flo2d_config=", "date=", "time=", "path=", "out=", "start_date=",
                                    "start_time=", "name=", "forceInsert"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-F", "--flo2d_config"):
            flo2d_config = arg
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-t", "--time"):
            time = arg
        elif opt in ("-p", "--path"):
            path = arg.strip()
        elif opt in ("-o", "--out"):
            output_suffix = arg.strip()
        elif opt in ("-S", "--start_date"):
            start_date = arg.strip()
        elif opt in ("-T", "--start_time"):
            start_time = arg.strip()
        elif opt in ("-n", "--name"):
            run_name = arg.strip()
        elif opt in ("-f", "--forceInsert"):
            forceInsert = True

    print("Current working directory : ", CWD)

    if FLO2D_MODEL == 'FLO2D_250':
        print("FLO2D_MODEL : ", FLO2D_MODEL)
        GRID_SIZE = 250.0
        appDir = pjoin(CWD, date + '_Kelani')
    elif FLO2D_MODEL == 'FLO2D_150':
        print("FLO2D_MODEL : ", FLO2D_MODEL)
        GRID_SIZE = 150.0
        appDir = pjoin(CWD, date + '_Kelani')
    elif FLO2D_MODEL == 'FLO2D_30':
        print("FLO2D_MODEL : ", FLO2D_MODEL)
        GRID_SIZE = 30.0
        appDir = pjoin(CWD, date + '_Kelani')
    else:
        GRID_SIZE = 250.0
        appDir = pjoin(CWD, date + '_Kelani')

    if GRID_SIZE == 'GRID_SIZE':
        print("FLO2D_MODEL GRID_SIZE: ", GRID_SIZE)
        GRID_SIZE = GRID_SIZE

    if path:
        appDir = pjoin(CWD, path)

    print("CADPTS_DAT_FILE : ", CADPTS_DAT_FILE)
    CADPTS_DAT_FILE_PATH = pjoin(appDir, CADPTS_DAT_FILE)
    print("CADPTS_DAT_FILE_PATH : ", CADPTS_DAT_FILE_PATH)
    # Load FLO2D Configuration file for the Model run if available
    FLO2D_CONFIG_FILE = pjoin(appDir, RUN_FLO2D_FILE)
    if flo2d_config:
        FLO2D_CONFIG_FILE = pjoin(CWD, flo2d_config)
    FLO2D_CONFIG = json.loads('{}')
    # Check FLO2D Config file exists
    if os.path.exists(FLO2D_CONFIG_FILE):
        FLO2D_CONFIG = json.loads(open(FLO2D_CONFIG_FILE).read())

    # Default run for current day
    now = datetime.datetime.now()
    # Use FLO2D Config file data, if available
    if 'MODEL_STATE_DATE' in FLO2D_CONFIG and len(FLO2D_CONFIG['MODEL_STATE_DATE']):
        now = datetime.datetime.strptime(FLO2D_CONFIG['MODEL_STATE_DATE'], '%Y-%m-%d')
    if date:
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    # Use FLO2D Config file data, if available
    if 'MODEL_STATE_TIME' in FLO2D_CONFIG and len(FLO2D_CONFIG['MODEL_STATE_TIME']):
        now = datetime.datetime.strptime('%s %s' % (date, FLO2D_CONFIG['MODEL_STATE_TIME']), '%Y-%m-%d %H:%M:%S')
    if time:
        now = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    time = now.strftime("%H:%M:%S")

    if start_date:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date.strftime("%Y-%m-%d")
    # Use FLO2D Config file data, if available
    elif 'TIMESERIES_START_DATE' in FLO2D_CONFIG and len(FLO2D_CONFIG['TIMESERIES_START_DATE']):
        start_date = datetime.datetime.strptime(FLO2D_CONFIG['TIMESERIES_START_DATE'], '%Y-%m-%d')
        start_date = start_date.strftime("%Y-%m-%d")
    else:
        start_date = date

    if start_time:
        start_time = datetime.datetime.strptime('%s %s' % (start_date, start_time), '%Y-%m-%d %H:%M:%S')
        start_time = start_time.strftime("%H:%M:%S")
    # Use FLO2D Config file data, if available
    elif 'TIMESERIES_START_TIME' in FLO2D_CONFIG and len(FLO2D_CONFIG['TIMESERIES_START_TIME']):
        start_time = datetime.datetime.strptime('%s %s' % (start_date, FLO2D_CONFIG['TIMESERIES_START_TIME']),
                                                '%Y-%m-%d %H:%M:%S')
        start_time = start_time.strftime("%H:%M:%S")
    else:
        start_time = datetime.datetime.strptime(start_date, '%Y-%m-%d')  # Time is set to 00:00:00
        start_time = start_time.strftime("%H:%M:%S")

    print('Extract Water Level Grid Result of FLO2D on', date, '@', time,
          'with Bast time of', start_date, '@', start_time)

    OUTPUT_DIR_PATH = pjoin(CWD, OUTPUT_DIR)
    TIMEDEP_FILE_PATH = pjoin(appDir, TIMDEP_FILE)

    WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, date))
    # Use FLO2D Config file data, if available
    if 'FLO2D_OUTPUT_SUFFIX' in FLO2D_CONFIG and len(FLO2D_CONFIG['FLO2D_OUTPUT_SUFFIX']):
        WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, FLO2D_CONFIG['FLO2D_OUTPUT_SUFFIX']))
    if output_suffix:
        WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, output_suffix))

    print('Processing FLO2D model on', appDir)

    # Check BASE.OUT file exists
    if not os.path.exists(TIMEDEP_FILE_PATH):
        print('Unable to find file : ', TIMEDEP_FILE_PATH)
        sys.exit()

    # Create OUTPUT Directory
    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)

    buffer_size = 65536
    with open(TIMEDEP_FILE_PATH) as infile:
        waterLevelLines = []
        boundary = get_grid_boudary(gap=GRID_SIZE)
        CellGrid = get_cell_grid(boundary, gap=GRID_SIZE)
        while True:
            lines = infile.readlines(buffer_size)
            if not lines:
                break
            for line in lines:
                if len(line.split()) == 1:
                    if len(waterLevelLines) > 0:
                        waterLevels = get_water_level_grid(waterLevelLines)
                        EsriGrid = get_esri_grid(waterLevels, boundary, CellGrid, gap=GRID_SIZE)

                        # Create Directory
                        if not os.path.exists(WATER_LEVEL_DIR_PATH):
                            os.makedirs(WATER_LEVEL_DIR_PATH)
                        # Get Time stamp Ref:http://stackoverflow.com/a/13685221/1461060
                        ModelTime = float(waterLevelLines[0].split()[0])
                        fileModelTime = datetime.datetime.strptime('%s %s' % (start_date, start_time),
                                                                   '%Y-%m-%d %H:%M:%S')
                        fileModelTime = fileModelTime + datetime.timedelta(hours=ModelTime)
                        dateAndTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                        if fileModelTime >= now:
                            # Create files
                            fileName = WATER_LEVEL_FILE.rsplit('.', 1)
                            fileName = "%s-%s.%s" % (fileName[0], dateAndTime, fileName[1])
                            WATER_LEVEL_FILE_PATH = pjoin(WATER_LEVEL_DIR_PATH, fileName)
                            file = open(WATER_LEVEL_FILE_PATH, 'w')
                            file.writelines(EsriGrid)
                            file.close()
                            print('Write to :', fileName)
                        else:
                            print('Skip. Current model time:' + dateAndTime +
                                  ' is not greater than ' + now.strftime("%Y-%m-%d_%H-%M-%S"))
                        waterLevelLines = []
                waterLevelLines.append(line)

except Exception as e:
    print(e)
    traceback.print_exc()
finally:
    print('Completed processing Extracting Water Level Grid.')
