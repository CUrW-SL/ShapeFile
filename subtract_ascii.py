import getopt
import sys
import numpy as np
import linecache

try:
    FIRST_ASCII_FILE_PATH = 'input/case1.asc'
    SECOND_ASCII_FILE_PATH = 'input/case2.asc'
    RESULT_ASCII_FILE_PATH = 'input/result.asc'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:s:",
                                   ["first=", "second="])
    except getopt.GetoptError as er:
        print('GetoptError : ', er)
        print('opts : ', opts)
        print('args : ', args)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-f", "--first"):
            FIRST_ASCII_FILE_PATH = float(arg)
        elif opt in ("-s", "--second"):
            SECOND_ASCII_FILE_PATH = float(arg)
    print('{FIRST_ASCII_FILE_PATH, SECOND_ASCII_FILE_PATH}: ', {FIRST_ASCII_FILE_PATH, SECOND_ASCII_FILE_PATH})
    ascii_grid1 = np.loadtxt(FIRST_ASCII_FILE_PATH, skiprows=6)
    ascii_grid2 = np.loadtxt(SECOND_ASCII_FILE_PATH, skiprows=6)
    ascii1_line1 = linecache.getline(FIRST_ASCII_FILE_PATH, 1)
    ascii1_line2 = linecache.getline(FIRST_ASCII_FILE_PATH, 2)
    ascii1_line3 = linecache.getline(FIRST_ASCII_FILE_PATH, 3)
    ascii1_line4 = linecache.getline(FIRST_ASCII_FILE_PATH, 4)
    ascii1_line5 = linecache.getline(FIRST_ASCII_FILE_PATH, 5)
    ascii1_line6 = linecache.getline(FIRST_ASCII_FILE_PATH, 6)
    ascii_grid1[ascii_grid1 == -9999] = 0.00
    ascii_grid2[ascii_grid2 == -9999] = 0.00
    result_grid = ascii_grid1 - ascii_grid2
    result_grid = np.subtract(ascii_grid1, ascii_grid2)
    result_grid[result_grid == 0.00] = -9999
    print(result_grid)
    header = ascii1_line1 + ascii1_line2 + ascii1_line3 + ascii1_line4 + ascii1_line5 + ascii1_line6.strip()
    print(header)
    np.savetxt(RESULT_ASCII_FILE_PATH, result_grid, header=header, fmt="%1.2f", comments='')
except Exception as e:
    print("Subtracting ascii file exception|e : ", e)
