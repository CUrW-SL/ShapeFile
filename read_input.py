

try:
    topo_df = pd.read_csv('input/TOPO.DAT', sep="\s+", names=['x', 'y', 'ground_elv'])

    maxwselev_df = pd.read_csv('input/MAXWSELEV.OUT', sep="\s+", names=['cell_id','x', 'y', 'surface_elv']).drop('cell_id', 1)

    maxwselev_df["elevation"] = maxwselev_df["surface_elv"] - topo_df["ground_elv"]
    #maxwselev_df.loc[maxwselev_df.elevation < 0, 'elevation'] = 0

    #new_maxwselev_df = maxwselev_df[maxwselev_df.elevation >= 0.3]

    maxwselev_df.to_csv('output/shape_data.csv', encoding='utf-8', columns=['x','y','elevation'], header=False)
except Exception as e:
    print("Exception|e : ", e)

