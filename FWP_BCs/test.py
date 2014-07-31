import geopandas as gpd

MFnam = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/FWPvert.nam'
model_ws
gdf = gpd.GeoDataFrame.from_file(shape)
UTM83Z16_ft = {'proj':'utm', 'zone':16, 'datum':'NAD83', 'units':'us-ft', 'nodefs':True}
gdf_ft = gdf.to_crs(crs=UTM83Z16_ft)
shape_m = gdf_ft.to_file('D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_pumping_wells_test.shp')