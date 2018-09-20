

try:
    buf_size = 65536
    input_file_path = 'input/TIMDEP.OUT'
    output_file_path = 'output/result.csv'
    output_file = open(output_file_path, 'w')
    with open(input_file_path) as infile:
        #Lines = []
        while True:
            lines = infile.readlines(buf_size)
            if not lines:
                break
            for line in lines:
                match = line.split('       ')[0]
                #print(match)
                if match == '    41974' or match == 41974:
                    print(line)
                    #Lines.append(line)
                    output_file.writelines(line)
    output_file.close()
except Exception as e:
    print("Exception|e : ", e)