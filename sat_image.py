import ast
import datetime as dt
import logging
import os
import zipfile
import matplotlib
import numpy as np
from curw.rainfall.wrf.extraction import utils as ext_utils
from mpl_toolkits.basemap import cm
from curw.rainfall.wrf import utils

try:
    lat_min = max(-4.0, -3.06107)
    lon_min = max(60.0, 71.2166)
    lat_max = min(40.0, 18.1895)
    lon_max = min(93.0, 90.3315)
    output_prefix = 'jaxa_sat'
    out_file_path = '/home/hasitha/PycharmProjects/ShapeFile/output'
    zip_file_path = '/home/hasitha/PycharmProjects/ShapeFile/input/gsmap_now.20190123.0530_0629.05_AsiaSS.csv.zip'
    sat_zip = zipfile.ZipFile(zip_file_path)
    sat = np.genfromtxt(sat_zip.open(os.path.basename(zip_file_path).replace('.zip', '')), delimiter=',', names=True)
    print(':', [])
    sat_filt = np.sort(
        sat[(sat['Lat'] <= lat_max) & (sat['Lat'] >= lat_min) & (sat['Lon'] <= lon_max) & (sat['Lon'] >= lon_min)],
        order=['Lat', 'Lon'])
    lats = np.sort(np.unique(sat_filt['Lat']))
    lons = np.sort(np.unique(sat_filt['Lon']))

    data = sat_filt['RainRate'].reshape(len(lats), len(lons))

    ext_utils.create_asc_file(np.flip(data, 0), lats, lons, out_file_path)

    # clevs = np.concatenate(([-1, 0], np.array([pow(2, i) for i in range(0, 9)])))
    # clevs = 10 * np.array([0.1, 0.5, 1, 2, 3, 5, 10, 15, 20, 25, 30])
    # norm = colors.BoundaryNorm(boundaries=clevs, ncolors=256)
    # cmap = plt.get_cmap('jet')
    clevs = [0, 1, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300]
    # clevs = [0.1, 0.5, 1, 2, 3, 5, 10, 15, 20, 25, 30, 50, 75, 100]
    norm = None
    cmap = cm.s3pcpn

    ts = dt.datetime.strptime(os.path.basename(out_file_path).replace(output_prefix + '_', '').replace('.asc', ''),
                              '%Y-%m-%d_%H:%M')
    lk_ts = utils.datetime_utc_to_lk(ts)
    title_opts = {
        'label': output_prefix + ' ' + lk_ts.strftime('%Y-%m-%d %H:%M') + ' LK\n' + ts.strftime(
            '%Y-%m-%d %H:%M') + ' UTC',
        'fontsize': 30
    }
    ext_utils.create_contour_plot(data, out_file_path + '.png', np.min(lats), np.min(lons), np.max(lats), np.max(lons),
                                  title_opts, clevs=clevs, cmap=cmap, norm=norm)
except Exception as e:
    print('Exception|e:', e)
