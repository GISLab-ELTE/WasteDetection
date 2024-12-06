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
import Draw from "ol/interaction/Draw.js";
import Overlay from "ol/Overlay.js";

// Constant values
const baseUrl = import.meta.env.VITE_DATA_URL;
const flaskUrl = import.meta.env.VITE_FLASK_URL;
const bingKey =
  "AgKv8E2vHuEwgddyzg_pRM6ycSRygeePXSFYTqc8jbikPT8ILyQxm1EF3YUmeRQ2";
const kiskoreBbox = [2283300, 6021945, 2284684, 6023968];
const kanyahazaBbox = [2588995, 6087354, 2597328, 6091368];
const pusztazamorBbox = [2090012, 6002140, 2095385, 6005579];
const rahoBbox = [2693024, 6114066, 2693905, 6114776];
const drinaBbox = [2145189, 5426572, 2147977, 5430040];
const drawType = "Polygon";

// Variables
var geojsonLayerGroup;
var aoisWithDates;
var satelliteImagesPaths;
var drawVisible = false;
var drawnFeatures = [];

// HTML elements
const selectedAOI = document.getElementById("location");
const selectedModel = document.getElementById("model");
const swipe = document.getElementById("swipe");
const annotationContainer = document.getElementById("annotation-popup");
const annotationCloser = document.getElementById("annotation-popup-closer");
const annotationSave = document.getElementById("annotation-save");
const annotationCancel = document.getElementById("annotation-cancel");

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
const sourceDraw = new VectorSource({ wrapX: false });

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
const layerDraw = new VectorLayer({
  source: sourceDraw,
  visible: false,
  zIndex: 100,
});

const draw = new Draw({
  source: sourceDraw,
  type: drawType,
  features: drawnFeatures,
});

const overlay = new Overlay({
  element: annotationContainer,
  autoPan: {
    animation: {
      duration: 250,
    },
  },
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
  overlays: [overlay],
  view: new View({
    center: [0, 0],
    zoom: 2,
    maxZoom: 19,
  }),
  controls: defaults({ attribution: false }).extend([new ZoomSlider()]),
});

var layerAnnotation = new LayerGroup({
  title: "Manual annotation",
  layers: [layerDraw],
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
    "<b>Date:</b> <br>" + dateArray.join("/");
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
    aoiBbox = kiskoreBbox;
  } else if (aoi == "Kanyahaza") {
    aoiBbox = kanyahazaBbox;
  } else if (aoi == "Pusztazamor") {
    aoiBbox = pusztazamorBbox;
  } else if (aoi == "Raho") {
    aoiBbox = rahoBbox;
  } else if (aoi == "Drina") {
    aoiBbox = drinaBbox;
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
  const res = await fetch(baseUrl + "satellite_images.json");
  satelliteImagesPaths = await res.json();

  for (var outKey of Object.keys(satelliteImagesPaths)) {
    for (var inKey of Object.keys(satelliteImagesPaths[outKey])) {
      satelliteImagesPaths[outKey][inKey]["src"] =
        baseUrl + satelliteImagesPaths[outKey][inKey]["src"];
    }
  }
};

const fetchGeojsonPaths = async function () {
  const res = await fetch(baseUrl + "geojson_files.json");
  aoisWithDates = await res.json();

  for (var modelId of Object.keys(aoisWithDates)) {
    const option = document.createElement("option");
    option.text = modelId;
    option.value = modelId;

    selectedModel.add(option);
    for (var outKey of Object.keys(aoisWithDates[modelId])) {
      for (var inKey of Object.keys(aoisWithDates[modelId][outKey])) {
        for (let i = 0; i < 4; i++) {
          aoisWithDates[modelId][outKey][inKey][i] =
            baseUrl + aoisWithDates[modelId][outKey][inKey][i];
        }
      }
    }
  }

  swipe.max =
    Object.keys(aoisWithDates[modelId][Object.keys(aoisWithDates[modelId])[0]])
      .length - 1;
};

const updateClassification = async function () {
  const aoi = selectedAOI.value;
  const model = selectedModel.value;
  const swipeValue = swipe.value;
  changeDate(Object.keys(aoisWithDates[model][aoi])[swipeValue]);
  setAOILayers(aoi);
  await displayExistingAnnotations();
};

const addDrawInteraction = function () {
  map.addInteraction(draw);
};
const removeDrawInteraction = function () {
  map.removeInteraction(draw);
};

const annotationContainerClose = function () {
  hideAnnotationPopup();
  removeLastDrawnFeature();
  return false;
};

const annotationContainerSave = async function () {
  hideAnnotationPopup();
  const lastDrawnFeature = sourceDraw.getFeatures().slice(-1)[0];
  const coordinates = lastDrawnFeature.getGeometry().getCoordinates();
  const annotationTypeValue = document.getElementById(
    "annotation-type-select",
  ).value;

  const satelliteImageId = await getSatelliteImageId(
    layerGeoTiff.getSource().key_,
  );
  const userId = await getUserId();
  const geom = createWKTPolygon(coordinates);
  const waste = Boolean(annotationTypeValue);

  postAnnotation(satelliteImageId, userId, geom, waste);

  return true;
};

const displayExistingAnnotations = async function () {
  var loginStatus = await checkLoginStatus();
  if (!loginStatus.logged_in) {
    return;
  }

  const satellite_image_id = await getSatelliteImageId(
    layerGeoTiff.getSource().key_,
  );

  try {
    const response = await fetch(
      flaskUrl + "get-annotations-for-current-user-and-current-satellite-image",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ satellite_image_id }),
        credentials: "include",
      },
    );
    if (response.ok) {
      const data = await response.json();
      sourceDraw
        .getFeatures()
        .forEach((feature) => sourceDraw.removeFeature(feature));
      data.forEach((feature) =>
        sourceDraw.addFeature(new GeoJSON().readFeatures(feature)[0]),
      );
    } else {
      console.error("Failed to fetch user ID:", response.statusText);
      return null;
    }
  } catch (error) {
    console.error("Error fetching user ID:", error);
    return null;
  }
};

const removeLastDrawnFeature = function () {
  sourceDraw.removeFeature(sourceDraw.getFeatures().slice(-1)[0]);
};

const hideAnnotationPopup = function () {
  overlay.setPosition(undefined);
  annotationCloser.blur();
};

const addAnnotation = function () {
  map.addLayer(layerAnnotation);
};

const removeAnnotation = function () {
  map.removeLayer(layerAnnotation);
};

const checkLoginStatus = async function () {
  try {
    const response = await fetch(flaskUrl + "check-login", {
      method: "GET",
      credentials: "include",
    });
    if (response.ok) {
      const data = await response.json();
      return data;
    } else {
      console.error("Failed to fetch login status:", response.statusText);
      return null;
    }
  } catch (error) {
    console.error("Error fetching login status:", error);
    return null;
  }
};

const changeElemsBasedOnLoginStatus = async function () {
  var loginStatus = await checkLoginStatus();
  const loginLogoutButton = document.getElementById("login-button");

  if (loginStatus.logged_in) {
    loginLogoutButton.innerHTML = "Logout";
    loginLogoutButton.onclick = logout;
    addAnnotation();
  } else {
    loginLogoutButton.innerHTML = "Login";
    loginLogoutButton.onclick = () => (window.location.href = "login.html");
    removeAnnotation();
  }
};

const getUserId = async function () {
  try {
    const response = await fetch(flaskUrl + "check-login", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });
    if (response.ok) {
      const data = await response.json();
      return data.user_id;
    } else {
      console.error("Failed to fetch user ID:", response.statusText);
      return null;
    }
  } catch (error) {
    console.error("Error fetching user ID:", error);
    return null;
  }
};

const getFilenameFromSrc = function (src) {
  const parts = src.split("/");
  const lastElement = parts[parts.length - 1];
  return lastElement;
};

const getSatelliteImageId = async function (src) {
  const filename = getFilenameFromSrc(src);

  try {
    const response = await fetch(flaskUrl + "get-satellite-image-id", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename }),
      credentials: "include",
    });
    if (response.ok) {
      const data = await response.json();
      return data.satellite_image_id;
    } else {
      console.error("Failed to fetch satellite image ID:", response.statusText);
      return null;
    }
  } catch (error) {
    console.error("Error fetching satellite image ID:", error);
    return null;
  }
};

const logout = function () {
  fetch(flaskUrl + "logout", {
    method: "POST",
    credentials: "include",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message === "Logged out successfully") {
        window.location.reload();
      }
    })
    .catch((error) => console.error("Error:", error));
};

const createWKTPolygon = function (coordinates) {
  const coordinatesString = coordinates.map((coordPair) =>
    coordPair.map((coord) => coord.join(" ")).join(", "),
  );
  const wktPolygon = `POLYGON((${coordinatesString}))`;
  return wktPolygon;
};

const postAnnotation = function (satellite_image_id, user_id, geom, waste) {
  fetch(flaskUrl + "annotations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ satellite_image_id, user_id, geom, waste }),
    credentials: "include",
  })
    .then((response) => response.json())
    .catch((error) => console.error("Error:", error));
};

// Events
selectedAOI.onchange = changeAOI;
selectedModel.onchange = updateClassification;

swipe.addEventListener("input", updateClassification);

window.onresize = function () {
  setTimeout(resizeMap, 200);
};

layerDraw.on("change:visible", function () {
  if (!drawVisible) {
    addDrawInteraction();
    drawVisible = true;
  } else {
    removeDrawInteraction();
    drawVisible = false;
  }
});

draw.on("drawend", function (evt) {
  const polygon = evt.feature;
  const coordinate = polygon.getGeometry().getInteriorPoint().getCoordinates();
  overlay.setPosition(coordinate);
});

annotationCloser.onclick = annotationContainerClose;
annotationCancel.onclick = annotationContainerClose;
annotationSave.onclick = annotationContainerSave;

document.addEventListener("DOMContentLoaded", async function () {
  await changeElemsBasedOnLoginStatus();
});

await fetchSatelliteImagePaths();
await fetchGeojsonPaths();
resizeMap();
changeAOI();
await displayExistingAnnotations();
