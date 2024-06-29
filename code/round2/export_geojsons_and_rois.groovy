// Usage:
// Open project in Qupath
// Automate > Show script editor
// Import this script in "Script Editor"
// Run the script by pressing: "Run..." -> "Run for Project"
//   After pressing, select all images and confirm using "ok" button
// Results are in `export/` subdirectory of QuPath project root
//   containing `ROIsTif/` and `geojsons/` directories with the results
// authors: Maximilian Otto, Kevin Zidane, Nicolai Wolfrom 

import qupath.lib.images.ImageData

def server = getCurrentServer()

def baseImageName = getProjectEntry().getImageName()

def exportPath = buildFilePath(PROJECT_BASE_DIR, 'export')

// export geojsons
def geojsonPath = buildFilePath(exportPath, 'geojsons')
mkdirs(geojsonPath)

def annotations = getAnnotationObjects()
exportObjectsToGeoJson(annotations,
                       buildFilePath(geojsonPath, baseImageName + ".geojson"),
                       "FEATURE_COLLECTION")

print 'Done! (' + baseImageName + ")"
