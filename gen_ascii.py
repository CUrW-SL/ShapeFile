import datetime
import getopt
import json
import os
import sys
import traceback
from os.path import join as pjoin
import math, numbers
import decimal


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
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1
    # rows = 533
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

    # print('ncols:', cols)
    # print('nrows:', rows)
    # print('xllcorner:',boudary['long_min'] - gap/2)
    # print('yllcorner:',boudary['lat_min'] - gap/2)

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
    buf_size = 65536
    # MODEL_FOLDER = 'input/25yr_4PUMPS_0.3m_ini_wl/'
    # MODEL_FOLDER = 'input/25yr_4PUMPS_0.4m_ini_wl/'
    # MODEL_FOLDER = 'input/25yr_4PUMPS_0.5m_ini_wl/'
    #
    # MODEL_FOLDER = 'input/25yr_5PUMPS_0.3m_ini_wl/'
    # MODEL_FOLDER = 'input/25yr_5PUMPS_0.4m_ini_wl/'
    # MODEL_FOLDER = 'input/25yr_5PUMPS_0.5m_ini_wl/'
    #
    # MODEL_FOLDER = 'input/50yr_4PUMPS_0.3m_ini_wl/'
    # MODEL_FOLDER = 'input/50yr_4PUMPS_0.4m_ini_wl/'
    # MODEL_FOLDER = 'input/50yr_4PUMPS_0.5m_ini_wl/'
    #
    # MODEL_FOLDER = 'input/50yr_5PUMPS_0.3m_ini_wl/'
    # MODEL_FOLDER = 'input/50yr_5PUMPS_0.4m_ini_wl/'
    # MODEL_FOLDER = 'input/50yr_5PUMPS_0.5m_ini_wl/'

    # MODEL_FOLDER = 'input/4PUMPS/'
    # MODEL_FOLDER = 'input/ALL_5PUMPS/'

    # output_file = open(TIMEDEP_S_FILE_PATH, 'w')
    GRID_SIZE = 5
    # INPUT = 'Saunders-Existing'
    INPUT = 'Saunders-Storage'
    # INPUT = 'Torrington-Excisting'
    # INPUT = 'Torrington-tertiary-drain'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:e:i:g:",
                                   ["start=", "end=", "input=", "grid="])
    except getopt.GetoptError as er:
        print('GetoptError : ', er)
        print('opts : ', opts)
        print('args : ', args)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-s", "--start"):
            START_HOUR = float(arg)
        elif opt in ("-e", "--end"):
            END_HOUR = float(arg)
        elif opt in ("-i", "--input"):
            INPUT = arg
        elif opt in ("-g", "--grid"):
            GRID_SIZE = int(arg)
    RUN_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
    RUN_DATE = datetime.datetime.strptime(RUN_DATE, '%Y-%m-%d')
    MODEL_FOLDER = 'input/{}/'.format(INPUT)

    TIMEDEP_FILE_PATH = MODEL_FOLDER + 'TIMDEP.OUT'
    # TIMEDEP_S_FILE_PATH = 'TIMDEP_S.OUT'
    CADPTS_DAT_FILE_PATH = MODEL_FOLDER + 'CADPTS.DAT'
    WATER_LEVEL_FILE = 'water_level.asc'
    ASCII_DIR = MODEL_FOLDER + 'ASCII'
    START_HOUR = 0.00
    END_HOUR = 96.00
    WATER_LEVEL_DEPTH_MIN = 0.15
    if not os.path.exists(ASCII_DIR):
        os.makedirs(ASCII_DIR)

    with open(TIMEDEP_FILE_PATH) as infile:
        waterLevelLines = []
        boundary = get_grid_boudary(gap=GRID_SIZE)
        CellGrid = get_cell_grid(boundary, gap=GRID_SIZE)
        while True:
            lines = infile.readlines(buf_size)
            if not lines:
                break
            for line in lines:
                numbers = line.split('       ')
                if len(numbers) == 1:
                    hour = float(line.strip())
                    # if(hour>=START_HOUR and hour<=END_HOUR):
                    if hour >= START_HOUR:
                        write = True
                    else:
                        write = False
                if write:
                    if len(numbers) == 1:
                        print(line)
                        if len(waterLevelLines) > 0:
                            waterLevels = get_water_level_grid(waterLevelLines)
                            EsriGrid = get_esri_grid(waterLevels, boundary, CellGrid, gap=GRID_SIZE)
                            fileModelTime = RUN_DATE + datetime.timedelta(hours=float(line.strip()))
                            fileModelTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                            fileName = WATER_LEVEL_FILE.rsplit('.', 1)
                            fileName = "%s-%s.%s" % (fileName[0], fileModelTime, fileName[1])
                            WATER_LEVEL_FILE_PATH = pjoin(ASCII_DIR, fileName)
                            file = open(WATER_LEVEL_FILE_PATH, 'w')
                            file.writelines(EsriGrid)
                            file.close()
                            print('Write to :', fileName)
                            waterLevelLines = []
                    else:
                        waterLevelLines.append(line)
except Exception as e:
    print("Exception|e : ", e)
