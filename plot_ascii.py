import datetime
import os
from os.path import join as pjoin
import math, numbers
import decimal
import pandas as pd
import numpy as np
import linecache
import matplotlib.pyplot as plt


def get_water_level_grid(lines):
    waterLevels = []
    for line in lines[0:]:
        if line == '\n':
            break
        v = line.split(',')
        # Get flood level (Elevation)
        # waterLevels.append('%s %s' % (v[0], v[1]))
        # Get flood depth (Depth)
        index = int(v[0]) + 1
        waterLevels.append('%s %s' % (str(index), v[3]))
    return waterLevels


def get_esri_grid(water_level_min, waterLevels, boudary, CellMap, gap=30.0, missingVal=-9999):
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

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1
    print('>>>>>  cols: %d, rows: %d' % (cols, rows))

    Grid = [[missingVal for x in range(cols)] for y in range(rows)]

    print(Grid)

    for level in waterLevels:
        v = level.split()
        i, j = CellMap[int(v[0])]
        water_level = round(decimal.Decimal(v[1]), 2)
        if (i >= cols or j >= rows):
            print('i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
        if water_level >= water_level_min:
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


def get_grid_boudary(cadpts_file, gap=250.0):
    "longitude  -> x : larger value"
    "latitude   -> y : smaller value"

    long_min = 1000000000.0
    lat_min = 1000000000.0
    long_max = 0.0
    lat_max = 0.0

    with open(cadpts_file) as f:
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


def get_cell_grid(cadpts_file, boudary, gap=250.0):
    CellMap = {}

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1

    with open(cadpts_file) as f:
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


def create_multi_ascii(timedep_file, cadpts_file, grid_size, start_date, start_time, water_level_file,
                       water_level_dir_path,
                 water_level_min):
    buffer_size = 65536

    now = datetime.datetime.now()
    with open(timedep_file) as infile:
        waterLevelLines = []
        boundary = get_grid_boudary(cadpts_file, gap=grid_size)
        CellGrid = get_cell_grid(cadpts_file, boundary, gap=grid_size)
        while True:
            lines = infile.readlines(buffer_size)
            if not lines:
                break
            for line in lines:
                if len(line.split()) == 1:
                    if len(waterLevelLines) > 0:
                        waterLevels = get_water_level_grid(waterLevelLines)
                        EsriGrid = get_esri_grid(water_level_min, waterLevels, boundary, CellGrid, gap=grid_size)

                        # Create Directory
                        if not os.path.exists(water_level_dir_path):
                            os.makedirs(water_level_dir_path)
                        # Get Time stamp Ref:http://stackoverflow.com/a/13685221/1461060
                        ModelTime = float(waterLevelLines[0].split()[0])
                        fileModelTime = datetime.datetime.strptime('%s %s' % (start_date, start_time),
                                                                   '%Y-%m-%d %H:%M:%S')
                        fileModelTime = fileModelTime + datetime.timedelta(hours=ModelTime)
                        dateAndTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                        if fileModelTime >= now:
                            # Create files
                            fileName = water_level_file.rsplit('.', 1)
                            fileName = "%s-%s.%s" % (fileName[0], dateAndTime, fileName[1])
                            water_level_file_path = pjoin(water_level_dir_path, fileName)
                            file = open(water_level_file_path, 'w')
                            file.writelines(EsriGrid)
                            file.close()
                            print('Write to :', fileName)
                        else:
                            print('Skip. Current model time:' + dateAndTime +
                                  ' is not greater than ' + now.strftime("%Y-%m-%d_%H-%M-%S"))
                        waterLevelLines = []
                waterLevelLines.append(line)


def create_single_ascii(cadpts_file, grid_size, shape_data_file, water_level_dir_path, water_level_min):
    buffer_size = 65536
    with open(shape_data_file) as infile:
        waterLevelLines = []
        boundary = get_grid_boudary(cadpts_file, gap=grid_size)
        print('create_single_ascii|boundary : ', boundary)
        CellGrid = get_cell_grid(cadpts_file, boundary, gap=grid_size)
        print('create_single_ascii|CellGrid : ', CellGrid)
        shape_ascii_file = os.path.join(water_level_dir_path, 'max_wl_ascii.asc')
        file = open(shape_ascii_file, 'w')
        while True:
            lines = infile.readlines(buffer_size)
            if not lines:
                break
            for line in lines:
                waterLevelLines.append(line)
        print('create_single_ascii|len(waterLevelLines) : ', len(waterLevelLines))
        waterLevels = get_water_level_grid(waterLevelLines)
        print('create_single_ascii|len(waterLevels) : ', len(waterLevels))
        EsriGrid = get_esri_grid(water_level_min, waterLevels, boundary, CellGrid, gap=grid_size)
        print('create_single_ascii|EsriGrid : ', EsriGrid)
        file.writelines(EsriGrid)
        file.close()
        return shape_ascii_file


def create_esri_grid_plot(ascii_file, plot_image_file):
    ascii_data = np.loadtxt(ascii_file, skiprows=6)

    ncols = int(linecache.getline(ascii_file, 1).split('	')[1])
    nrows = int(linecache.getline(ascii_file, 2).split('	')[1])
    xllcorner = float(linecache.getline(ascii_file, 3).split('	')[1])
    yllcorner = float(linecache.getline(ascii_file, 4).split('	')[1])
    cellsize = float(linecache.getline(ascii_file, 5).split('	')[1])
    NODATA_value = float(linecache.getline(ascii_file, 6).split('	')[1])

    ascii_data[ascii_data == NODATA_value] = np.nan

    print('create_esri_grid_plot|ascii_data : ', ascii_data)
    print('create_esri_grid_plot|ncols : ', ncols)
    print('create_esri_grid_plot|nrows : ', nrows)
    print('create_esri_grid_plot|xllcorner : ', xllcorner)
    print('create_esri_grid_plot|yllcorner : ', yllcorner)
    print('create_esri_grid_plot|cellsize : ', cellsize)
    print('create_esri_grid_plot|NODATA_value : ', NODATA_value)

    cellsize = 0.25
    fig, ax = plt.subplots()
    ax.set_title('Inundation Map')
    # img_plot = ax.imshow(ascii_data, cmap='jet')
    map_extent = [
        0, 0 + ncols * cellsize,
        0, 0 + nrows * cellsize]

    img_plot = ax.imshow(ascii_data, extent=map_extent, cmap='jet')
    cbar = fig.colorbar(img_plot)
    # cbar = plt.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14)
    cbar.set_label('Water Level (m)')
    ax.grid(True)
    # plt.show()
    plt.savefig(plot_image_file, bbox_inches='tight')


if __name__ == '__main__':
    output_dir = '/home/hasitha/PycharmProjects/ShapeFile/output'
    water_level_file = 'water_level_grid.asc'
    maxwl_file = '/home/hasitha/PycharmProjects/ShapeFile/input/plot_in/MAXWSELEV.OUT'
    cadpts_file = '/home/hasitha/PycharmProjects/ShapeFile/input/plot_in/CADPTS.DAT'
    topo_file = '/home/hasitha/PycharmProjects/ShapeFile/input/plot_in/TOPO.DAT'
    water_level_min = 0.3
    start_date = '2020-07-09'
    start_time = '08:00:00'
    water_level_dir_path = pjoin(output_dir, start_date)
    try:
        topo_df = pd.read_csv(topo_file, sep="\s+", names=['x', 'y', 'ground_elv'])
        maxwselev_df = pd.read_csv(maxwl_file, sep="\s+",
                                   names=['cell_id', 'x', 'y', 'surface_elv']).drop('cell_id', 1)
        maxwselev_df["elevation"] = maxwselev_df["surface_elv"] - topo_df["ground_elv"]
        shape_data_file = os.path.join(water_level_dir_path, 'shape_data.csv')
        maxwselev_df.to_csv(shape_data_file, encoding='utf-8',
                            columns=['x', 'y', 'elevation'], header=False)
        try:
            create_single_ascii(cadpts_file, 250, shape_data_file, water_level_dir_path, water_level_min)
        except Exception as ex:
            print("create_single_ascii|Exception : ", str(ex))
    except Exception as e:
        print("Exception|e : ", str(e))

if __name__ == '__main__':
    output_dir = '/home/hasitha/PycharmProjects/ShapeFile/output'
    ascii_file = '/home/hasitha/PycharmProjects/ShapeFile/output/2020-07-09/max_wl_ascii.asc'
    plot_image_file = os.path.join(output_dir, 'ascii_plot.png')
    create_esri_grid_plot(ascii_file, plot_image_file)

