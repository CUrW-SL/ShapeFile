import getopt
import sys
from datetime import datetime, timedelta

WIN_OUTPUT_DIR_PATH = r"D:\flo2d_output"

try:
    buf_size = 65536
    GRID_SIZE = 250
    INPUT = '2016May'
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
    CADPTS_DAT_FILE_PATH = MODEL_FOLDER + 'CADPTS.DAT'
    WATER_LEVEL_FILE = 'water_level.asc'
    ASCII_DIR = MODEL_FOLDER + 'ASCII'
    START_HOUR = 0.00
    END_HOUR = 96.00
    WATER_LEVEL_DEPTH_MIN = 0.15
except Exception as e:
    print("Exception|e : ", e)

