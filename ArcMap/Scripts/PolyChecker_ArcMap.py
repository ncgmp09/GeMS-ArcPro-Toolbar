import arcpy, os, shutil, sys

# Path to store geoprocessing files
user_profile_path = os.environ['USERPROFILE']
gdb = r"{}/AppData/Local/Temp/PolyChecker/PolyCheck.gdb".format(user_profile_path)

# GDB already exists, delete it
# Create GDB
if not arcpy.Exists(gdb):
    if not arcpy.Exists(os.path.dirname(gdb)):
        os.makedirs(os.path.dirname(gdb))
    arcpy.CreateFileGDB_management(os.path.dirname(gdb), os.path.basename(gdb))

arcpy.AddMessage(str(arcpy.Exists(gdb)) + ' ' + os.path.dirname(gdb))
arcpy.env.workspace = gdb
arcpy.env.overwriteOutput = True


##


# Script arguments
MapUnitPolys = arcpy.GetParameterAsText(0)
if MapUnitPolys == '#' or not MapUnitPolys:
    MapUnitPolys = "MapUnitPolys"  # provide a default value if unspecified

MapUnitPolys_CopyFeatures = arcpy.GetParameterAsText(1)

# Set Geoprocessing environments
MapUnitPolys = MapUnitPolys

# Validate that all Polygons have a map unit

invalid_polygon_found = False

with arcpy.da.SearchCursor(MapUnitPolys, ['SHAPE@', 'MapUnit', 'OBJECTID']) as cursor:
    for row in cursor:
        # Does this Polygon have a map unit
        if row[1] == "" or row[1] == "<Null>" or row[1] is None or row[1] is 0:
            invalid_polygon_found = True
            arcpy.AddMessage('Polygon OBJECT ID:{} is missing map unit... exiting.'.format(row[2]))


# Invalid polygons were found, terminate
if (invalid_polygon_found):
    arcpy.AddMessage("Check results and fill in the missing map unit")
    sys.exit(1)

Polygon_Neighbors = "{}/polytest".format(gdb)

PolygonNeighbor_TableSelect = "{}/PolygonNeighbor_TableSelect".format(gdb)

inFeatures_lyr = "Polygon_Neighbors_tv".format(gdb)

dropFields = ["MapUnitPolys_IdentityConfidence", "PolygonNeighbor_TableSelect_NODE_COUNT", "MapUnitPolys_Label", "MapUnitPolys_Notes", "MapUnitPolys_Symbol", "PolygonNeighbor_TableSelect_OBJECTID"]

# Process: Polygon Neighbors
arcpy.PolygonNeighbors_analysis(MapUnitPolys, Polygon_Neighbors, "OBJECTID;MapUnit", "NO_AREA_OVERLAP", "BOTH_SIDES",
                                "", "METERS", "SQUARE_METERS")


Polygon_Neighbors_tv = arcpy.MakeTableView_management(Polygon_Neighbors, "Polygon_Neighbors_tv")[0]
# Process: Select Layer By Attribute
arcpy.SelectLayerByAttribute_management(Polygon_Neighbors_tv, "NEW_SELECTION", "src_MapUnit = nbr_MapUnit")

# Process: Table Select
arcpy.TableSelect_analysis(Polygon_Neighbors, PolygonNeighbor_TableSelect, "src_MapUnit = nbr_MapUnit")

arcpy.GetCount_management(PolygonNeighbor_TableSelect)

arcpy.AddMessage(arcpy.GetMessages())

#  No Polygons were found, Terminate

if int(arcpy.GetCount_management(PolygonNeighbor_TableSelect)[0]) > 0:
    arcpy.MakeFeatureLayer_management(MapUnitPolys, inFeatures_lyr)
else:
    arcpy.AddMessage("done! No polygons need to be checked")
    sys.exit(1)

# Process: Add Join
arcpy.AddJoin_management(inFeatures_lyr, "OBJECTID", PolygonNeighbor_TableSelect, "src_OBJECTID", "KEEP_COMMON")

# Process: Copy Features
arcpy.CopyFeatures_management(inFeatures_lyr, MapUnitPolys_CopyFeatures, "", "0", "0", "0")

#  Delete Fields in output

arcpy.DeleteField_management(MapUnitPolys_CopyFeatures, dropFields)


arcpy.AddMessage(MapUnitPolys_CopyFeatures)

# Process: Remove Join
arcpy.RemoveJoin_management(inFeatures_lyr, "")

# Execute Delete
arcpy.Delete_management(PolygonNeighbor_TableSelect)
arcpy.Delete_management(Polygon_Neighbors)

arcpy.AddMessage('All done! Check Polygons')

