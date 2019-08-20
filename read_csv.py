

try:
    buf_size = 65536
    input_file_path = 'input/TIMDEP.OUT'
    # output_file_path = 'output/result.csv'
    # output_file = open(output_file_path, 'w')
    count = 0
    count1 = 0
    count2 = 0
    with open(input_file_path) as infile:
        #Lines = []
        while True:
            lines = infile.readlines(buf_size)
            if not lines:
                break
            for line in lines:
                match = line.split('       ')[0]
                #print(match)
                if match == '      618' or match == 618:
                    count = count + 1
                    #Lines.append(line)
                    # output_file.writelines(line)
                if match == '     2669' or match == 2669:
                    count1 = count1 + 1
                if match == '     2686' or match == 2686:
                    count2 = count2 + 1
    # output_file.close()
    print('618 - ', count)
    print('2669 - ', count1)
    print('2686 - ', count2)
except Exception as e:
    print("Exception|e : ", e)