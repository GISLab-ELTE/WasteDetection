import "./style.css";
import "ol/ol.css";
import "ol-layerswitcher/dist/ol-layerswitcher.css";
import { Map, View } from "ol";
import TileLayer from "ol/layer/WebGLTile.js";
import GeoTIFF from "ol/source/GeoTIFF.js";
import OSM from "ol/source/OSM";
import LayerSwitcher from "ol-layerswitcher";
import LayerGroup from "ol/layer/Group";
import BingMaps from "ol/source/BingMaps";
import XYZ from "ol/source/XYZ";
import GeoJSON from "ol/format/GeoJSON";
import { Fill, Stroke, Style } from "ol/style";
import { Vector as VectorSource } from "ol/source";
import { Vector as VectorLayer } from "ol/layer";
import { defaults } from "ol/control/defaults";
import { ZoomSlider } from "ol/control";

// Constant values
const base_url = import.meta.env.VITE_DATA_URL;
const bingKey =
  "AgKv8E2vHuEwgddyzg_pRM6ycSRygeePXSFYTqc8jbikPT8ILyQxm1EF3YUmeRQ2";
const kiskore_bbox = [2283300, 6021945, 2284684, 6023968];
const kanyahaza_bbox = [2588995, 6087354, 2597328, 6091368];
const pusztazamor_bbox = [2090012, 6002140, 2095385, 6005579];
const raho_bbox = [2693024, 6114066, 2693905, 6114776];
const drina_bbox = [2145189, 5426572, 2147977, 5430040];

// Variables
var geojsonLayerGroup;
var aoisWithDates;
var satelliteImagesPaths;

// HTML elements
const selectedAOI = document.getElementById("type");
const selectedModel = document.getElementById("model");
const swipe = document.getElementById("swipe");

// Styles for GeoJSON polygons
const stylesClassified = {
  MultiPolygon: new Style({
    stroke: new Stroke({
      color: "rgb(255, 128, 0)",
      width: 3,
    }),
    fill: new Fill({
      color: "rgba(255, 128, 0, 0.5)",
    }),
  }),
};

const stylesHeatmapHigh = {
  MultiPolygon: new Style({
    stroke: new Stroke({
      color: "red",
      width: 3,
    }),
    fill: new Fill({
      color: "rgba(255, 0, 0, 0.5)",
    }),
  }),
};

const stylesHeatmapMedium = {
  MultiPolygon: new Style({
    stroke: new Stroke({
      color: "rgb(255, 255, 0)",
      width: 3,
    }),
    fill: new Fill({
      color: "rgba(255, 255, 0, 0.5)",
    }),
  }),
};

const stylesHeatmapLow = {
  MultiPolygon: new Style({
    stroke: new Stroke({
      color: "green",
      width: 3,
    }),
    fill: new Fill({
      color: "rgba(0, 255, 0, 0.5)",
    }),
  }),
};

const styleFunctionClassified = function (feature) {
  return stylesClassified[feature.getGeometry().getType()];
};

const styleFunctionHeatmapHigh = function (feature) {
  return stylesHeatmapHigh[feature.getGeometry().getType()];
};

const styleFunctionHeatmapMedium = function (feature) {
  return stylesHeatmapMedium[feature.getGeometry().getType()];
};

const styleFunctionHeatmapLow = function (feature) {
  return stylesHeatmapLow[feature.getGeometry().getType()];
};

// Sources and layers
const sourceClassified = new VectorSource({ format: new GeoJSON() });
const sourceHeatmapLow = new VectorSource({ format: new GeoJSON() });
const sourceHeatmapMedium = new VectorSource({ format: new GeoJSON() });
const sourceHeatmapHigh = new VectorSource({ format: new GeoJSON() });

const layerGeoTiff = new TileLayer({
  title: "Satellite image",
  visible: false,
});
const layerClassified = new VectorLayer({
  title: "Classified",
  style: styleFunctionClassified,
  visible: false,
});
const layerHeatmapLow = new VectorLayer({
  title: "Heatmap Low",
  style: styleFunctionHeatmapLow,
  visible: false,
});
const layerHeatmapMedium = new VectorLayer({
  title: "Heatmap Medium",
  style: styleFunctionHeatmapMedium,
  visible: false,
});
const layerHeatmapHigh = new VectorLayer({
  title: "Heatmap High",
  style: styleFunctionHeatmapHigh,
  visible: true,
});

// Dictionary of sources and layers
const sourcesAndLayers = {
  sources: [
    sourceClassified,
    sourceHeatmapHigh,
    sourceHeatmapLow,
    sourceHeatmapMedium,
  ],
  layers: [
    layerClassified,
    layerHeatmapHigh,
    layerHeatmapLow,
    layerHeatmapMedium,
  ],
};

// Map
const map = new Map({
  target: "map",
  layers: [
    new LayerGroup({
      title: "Base maps",
      layers: [
        new TileLayer({
          title: "None",
          type: "base",
          source: new XYZ({
            url: null,
          }),
        }),
        new TileLayer({
          title: "OpenStreetMap",
          type: "base",
          source: new OSM(),
        }),
        new TileLayer({
          title: "Bing Roads",
          type: "base",
          source: new BingMaps({
            key: bingKey,
            imagerySet: "Road",
          }),
        }),
        new TileLayer({
          title: "Bing Aerial",
          type: "base",
          source: new BingMaps({
            key: bingKey,
            imagerySet: "Aerial",
          }),
        }),
        new TileLayer({
          title: "Bing Hybrid",
          type: "base",
          source: new BingMaps({
            key: bingKey,
            imagerySet: "AerialWithLabels",
          }),
        }),
      ],
    }),
  ],
  view: new View({
    center: [0, 0],
    zoom: 2,
    maxZoom: 19,
  }),
  controls: defaults({ attribution: false }).extend([new ZoomSlider()]),
});

// Layer Switcher
var layerSwitcher = new LayerSwitcher({
  tipLabel: "Layer control",
  groupSelectStyle: "children",
  reverse: false,
});
map.addControl(layerSwitcher);

// Functions
const removeLayersFromMap = function () {
  for (const source of sourcesAndLayers["sources"]) {
    source.clear();
  }

  map.removeLayer(geojsonLayerGroup);
};

const changeDate = function (newDate) {
  var dateArray = newDate.split("-");
  dateArray.reverse();
  document.getElementById("date").innerHTML =
    "<b>Date:</b> " + dateArray.join("/");
};

const setAOILayers = function () {
  const aoi = selectedAOI.value;
  const model = selectedModel.value;
  const swipeValue = swipe.value;
  const date = Object.keys(aoisWithDates[model][aoi])[swipeValue];
  const layers = [];

  removeLayersFromMap();

  layerGeoTiff.setSource(
    new GeoTIFF({
      sources: [
        {
          url: satelliteImagesPaths[aoi][date]["src"],
          bands: [3, 2, 1],
          nodata: 0,
          min: satelliteImagesPaths[aoi][date]["min"],
          max: satelliteImagesPaths[aoi][date]["max"],
        },
      ],
      transition: 0,
    }),
  );
  layers[0] = layerGeoTiff;

  for (let i = 0; i < 4; i++) {
    sourcesAndLayers["sources"][i].setUrl(aoisWithDates[model][aoi][date][i]);
    sourcesAndLayers["sources"][i].refresh();
    sourcesAndLayers["layers"][i].setSource(sourcesAndLayers["sources"][i]);
    layers[i + 1] = sourcesAndLayers["layers"][i];
  }

  geojsonLayerGroup = new LayerGroup({
    title: "Data layers",
    layers: layers,
  });

  map.addLayer(geojsonLayerGroup);
};

const changeAOI = function () {
  let aoiBbox = null;
  const aoi = selectedAOI.value;
  const model = selectedModel.value;

  swipe.value = 0;
  swipe.max = Object.keys(aoisWithDates[model][aoi]).length - 1;

  const swipeValue = swipe.value;

  changeDate(Object.keys(aoisWithDates[model][aoi])[swipeValue]);
  setAOILayers();

  if (aoi == "Kiskore") {
    aoiBbox = kiskore_bbox;
  } else if (aoi == "Kanyahaza") {
    aoiBbox = kanyahaza_bbox;
  } else if (aoi == "Pusztazamor") {
    aoiBbox = pusztazamor_bbox;
  } else if (aoi == "Raho") {
    aoiBbox = raho_bbox;
  } else if (aoi == "Drina") {
    aoiBbox = drina_bbox;
  } else {
    aoiBbox = null;
  }
  if (aoiBbox !== null) {
    map.getView().fit(aoiBbox, map.getSize());
  }
};

const resizeMap = function () {
  var userInputsHeight = document.getElementById("user-inputs").offsetHeight;
  var remainingHeight = window.innerHeight - userInputsHeight - 10;
  document.getElementById("map").style.height =
    remainingHeight.toString() + "px";
  map.updateSize();
};

const fetchSatelliteImagePaths = async function () {
  const res = await fetch(base_url + "satellite_images.json");
  satelliteImagesPaths = await res.json();

  for (var out_key of Object.keys(satelliteImagesPaths)) {
    for (var in_key of Object.keys(satelliteImagesPaths[out_key])) {
      satelliteImagesPaths[out_key][in_key]["src"] =
        base_url + satelliteImagesPaths[out_key][in_key]["src"];
    }
  }
};

const fetchGeojsonPaths = async function () {
  const res = await fetch(base_url + "geojson_files.json");
  aoisWithDates = await res.json();

  for (var model_id of Object.keys(aoisWithDates)) {
    const option = document.createElement("option");
    option.text = model_id;
    option.value = model_id;

    selectedModel.add(option);
    for (var out_key of Object.keys(aoisWithDates[model_id])) {
      for (var in_key of Object.keys(aoisWithDates[model_id][out_key])) {
        for (let i = 0; i < 4; i++) {
          aoisWithDates[model_id][out_key][in_key][i] =
            base_url + aoisWithDates[model_id][out_key][in_key][i];
        }
      }
    }
  }

  swipe.max =
    Object.keys(
      aoisWithDates[model_id][Object.keys(aoisWithDates[model_id])[0]],
    ).length - 1;
};

const updateClassification = function () {
  const aoi = selectedAOI.value;
  const model = selectedModel.value;
  const swipeValue = swipe.value;
  changeDate(Object.keys(aoisWithDates[model][aoi])[swipeValue]);
  setAOILayers(aoi);
};

// Events
selectedAOI.onchange = changeAOI;
selectedModel.onchange = updateClassification;

swipe.addEventListener("input", updateClassification);

window.onresize = function () {
  setTimeout(resizeMap, 200);
};

await fetchSatelliteImagePaths();
await fetchGeojsonPaths();
resizeMap();
changeAOI();
