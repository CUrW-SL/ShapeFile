#!/usr/bin/python3

import datetime
import getopt
import json
import os
import sys
import traceback
import pandas as pd
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
    for line in lines[0:]:
        if line == '\n':
            break
        v = line.split(',')
        # Get flood level (Elevation)
        # waterLevels.append('%s %s' % (v[0], v[1]))
        # Get flood depth (Depth)
        index = int(v[0])+1
        waterLevels.append('%s %s' % (str(index), v[3]))
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

    #For Niluka
    # ncols:492
    #nrows:533
    #xllcorner:396935.00000
    #yllcorner:482565.00000

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    # cols = 492
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1
    # rows = 533
    print('>>>>>  cols: %d, rows: %d' % (cols, rows))

    Grid = [[missingVal for x in range(cols)] for y in range(rows)]

    print(Grid)

    for level in waterLevels :
        v = level.split()
        i, j = CellMap[int(v[0])]
        water_level = round(decimal.Decimal(v[1]), 2)
        if (i >= cols or j >= rows) :
            print('i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
        if water_level >= WATER_LEVEL_DEPTH_MIN:
            #Grid[j][i] = float(v[1])
            Grid[j][i] = water_level

    print('ncols:', cols)
    print('nrows:', rows)
    print('xllcorner:',boudary['long_min'] - gap/2)
    print('yllcorner:',boudary['lat_min'] - gap/2)

    EsriGrid.append('%s\t%s\n' % ('ncols', cols))
    EsriGrid.append('%s\t%s\n' % ('nrows', rows))
    EsriGrid.append('%s\t%s\n' % ('xllcorner', boudary['long_min'] - gap/2))
    EsriGrid.append('%s\t%s\n' % ('yllcorner', boudary['lat_min'] - gap/2))
    EsriGrid.append('%s\t%s\n' % ('cellsize', gap))
    EsriGrid.append('%s\t%s\n' % ('NODATA_value', missingVal))

    for j in range(0, rows) :
        arr = []
        for i in range(0, cols) :
            arr.append(Grid[j][i])

        EsriGrid.append('%s\n' % (' '.join(str(x) for x in arr)))
    return EsriGrid


def get_grid_boudary(gap=30.0):
    "longitude  -> x : larger value"
    "latitude   -> y : smaller value"

    long_min = 1000000000.0
    lat_min = 1000000000.0
    long_max = 0.0
    lat_max = 0.0

    with open(CADPTS_DAT_FILE) as f:
        lines = f.readlines()
        for line in lines :
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


def get_cell_grid(boudary, gap=30.0):
    CellMap = {}

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1

    with open(CADPTS_DAT_FILE) as f:
        lines = f.readlines()
        for line in lines :
            v = line.split()
            i = int((float(v[1]) - boudary['long_min']) / gap)
            j = int((float(v[2]) - boudary['lat_min']) / gap)
            if not isinstance(i, numbers.Integral) or not isinstance(j, numbers.Integral) :
                print('### WARNING i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            if (i >= cols or j >= rows) :
                print('### WARNING i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            if i >= 0 or j >= 0 :
                CellMap[int(v[0])] = (i, rows - j -1)

    print(CellMap)
    return CellMap


def read_input(input_path):
    print('read_input|input_path:', input_path)
    try:
        topo_df = pd.read_csv(input_path+'TOPO.DAT', sep="\s+", names=['x', 'y', 'ground_elv'])

        maxwselev_df = pd.read_csv(input_path+'MAXWSELEV.OUT', sep="\s+", names=['cell_id', 'x', 'y', 'surface_elv']).drop(
            'cell_id', 1)

        maxwselev_df["elevation"] = maxwselev_df["surface_elv"] - topo_df["ground_elv"]
        # maxwselev_df.loc[maxwselev_df.elevation < 0, 'elevation'] = 0

        # new_maxwselev_df = maxwselev_df[maxwselev_df.elevation >= 0.3]

        maxwselev_df.to_csv('output/'+INPUT_MODE+'_shape_data.csv', encoding='utf-8', columns=['x', 'y', 'elevation'], header=False)
    except Exception as e:
        print("Exception|e : ", e)


try:
    # INPUT_MODE = '25yr_4PUMPS_0.3m_ini_wl'
    # INPUT_MODE = '25yr_4PUMPS_0.4m_ini_wl'
    # INPUT_MODE = '25yr_4PUMPS_0.5m_ini_wl'
    #
    # INPUT_MODE = '25yr_5PUMPS_0.3m_ini_wl'
    # INPUT_MODE = '25yr_5PUMPS_0.4m_ini_wl'
    # INPUT_MODE = '25yr_5PUMPS_0.5m_ini_wl'
    #
    # INPUT_MODE = '50yr_4PUMPS_0.3m_ini_wl'
    # INPUT_MODE = '50yr_4PUMPS_0.4m_ini_wl'
    # INPUT_MODE = '50yr_4PUMPS_0.5m_ini_wl'
    #
    # INPUT_MODE = '50yr_5PUMPS_0.3m_ini_wl'
    # INPUT_MODE = '50yr_5PUMPS_0.4m_ini_wl'
    # INPUT_MODE = '50yr_5PUMPS_0.5m_ini_wl'

    # INPUT_MODE = '4PUMPS'
    # INPUT_MODE = 'ALL_5PUMPS'
    INPUT_MODE = 'WITHOUT_ANY_PUMPS'

    # FLO2D_MODEL = 'FLO2D_30'
    # FLO2D_MODEL = 'FLO2D_150'
    FLO2D_MODEL = 'FLO2D_250'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm:i:", [
            "help", "model=", "input="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-m", "--model"):
            FLO2D_MODEL = arg
        elif opt in ("-i", "--input"):
            INPUT_MODE = arg
    INPUT_PATH = 'input/' + INPUT_MODE + '/'
    WATER_LEVEL_DEPTH_MIN = 0.3
    SHAPE_DATA_FILE = 'output/'+INPUT_MODE+'_shape_data.csv'
    OUTPUT_DIR = 'output'
    CADPTS_DAT_FILE = INPUT_PATH+'CADPTS.DAT'
    SHAPE_ASC_FILE = 'output/'+INPUT_MODE+'_shape_data.asc'

    date = ''
    time = ''
    path = ''
    output_suffix = ''
    start_date = ''
    start_time = ''
    forceInsert = False


    if FLO2D_MODEL == 'FLO2D_250':
        print("FLO2D_MODEL : ",FLO2D_MODEL)
        GRID_SIZE = 250.0
        appDir = OUTPUT_DIR
    elif FLO2D_MODEL == 'FLO2D_150':
        print("FLO2D_MODEL : ",FLO2D_MODEL)
        GRID_SIZE = 150.0
        appDir = OUTPUT_DIR
    elif FLO2D_MODEL == 'FLO2D_30':
        print("FLO2D_MODEL : ",FLO2D_MODEL)
        GRID_SIZE = 30.0
        appDir = OUTPUT_DIR

    print('Processing FLO2D model on', appDir)

    read_input(INPUT_PATH)

    # Check SHAPE_DATA_FILE file exists
    if not os.path.exists(SHAPE_DATA_FILE):
        print('Unable to find file : ', SHAPE_DATA_FILE)
        sys.exit()

    # Create OUTPUT Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    buffer_size = 65536

    with open(SHAPE_DATA_FILE) as infile:
        waterLevelLines = []
        boundary = get_grid_boudary(gap=GRID_SIZE)
        CellGrid = get_cell_grid(boundary, gap=GRID_SIZE)
        file = open(SHAPE_ASC_FILE, 'w')
        while True:
            lines = infile.readlines(buffer_size)
            if not lines:
                break
            for line in lines:
                waterLevelLines.append(line)
        waterLevels = get_water_level_grid(waterLevelLines)
        EsriGrid = get_esri_grid(waterLevels, boundary, CellGrid, gap=GRID_SIZE)
        file.writelines(EsriGrid)
        file.close()
except Exception as e:
    print(e)
    traceback.print_exc()
finally:
    print('Completed processing Extracting Water Level Grid.')
