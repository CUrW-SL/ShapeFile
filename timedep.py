import getopt
import sys

try:
    buf_size = 65536
    TIMEDEP_FILE_PATH = 'TIMDEP.OUT'
    TIMEDEP_S_FILE_PATH = 'TIMDEP_S.OUT'
    START_HOUR = 12.00
    END_HOUR = 24.00
    output_file = open(TIMEDEP_S_FILE_PATH, 'w')

    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:e:",
                                   ["start=", "end="])
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
    print('{START_HOUR, END_HOUR}: ', {START_HOUR, END_HOUR})
    with open(TIMEDEP_FILE_PATH) as infile:
        while True:
            lines = infile.readlines(buf_size)
            if not lines:
                break
            for line in lines:
                numbers = line.split('       ')
                # print(numbers)
                if (len(numbers) == 1):
                    hour = float(line.strip())
                    if (hour >= START_HOUR and hour <= END_HOUR):
                        write = True
                    else:
                        write = False
                if write:
                    if (len(numbers) == 1):
                        print(line)
                    output_file.writelines(line)

    output_file.close()
except Exception as e:
    print("Exception|e : ", e)
