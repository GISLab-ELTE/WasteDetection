import './style.css';
import 'ol/ol.css';
import 'ol-layerswitcher/dist/ol-layerswitcher.css';
import {Map, View} from 'ol';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import LayerSwitcher from 'ol-layerswitcher';
import LayerGroup from "ol/layer/Group";
import BingMaps from 'ol/source/BingMaps';
import XYZ from 'ol/source/XYZ';
import GeoJSON from 'ol/format/GeoJSON';
import {Fill, Stroke, Style} from 'ol/style';
import {Vector as VectorSource} from 'ol/source';
import {Tile, Vector as VectorLayer} from 'ol/layer';
import {defaults} from 'ol/control/defaults';
import {ZoomSlider} from 'ol/control';
import { format } from 'ol/coordinate';

// Constant values
const base_url = import.meta.env.VITE_DATA_URL;
const bingKey = 'AgKv8E2vHuEwgddyzg_pRM6ycSRygeePXSFYTqc8jbikPT8ILyQxm1EF3YUmeRQ2';
const kiskore_bbox = [2283300, 6021945, 2284684, 6023968];
const kanyahaza_bbox = [2588995, 6087354, 2597328, 6091368];
const pusztazamor_bbox = [2090012, 6002140, 2095385, 6005579];
const raho_bbox = [2693024, 6114066, 2693905, 6114776];

// Variables
var geojsonLayerGroup;
var aoisWithDates;

// HTML elements
const selectedAOI = document.getElementById('type');
const swipe = document.getElementById('swipe');

// Styles for GeoJSON polygons
const stylesClassified = {
  'MultiPolygon': new Style({
    stroke: new Stroke({
      color: 'rgb(255, 128, 0)',
      width: 3,
    }),
    fill: new Fill({
      color: 'rgba(255, 128, 0, 0.5)',
    }),
  }),
};

const stylesHeatmapHigh = {
  'MultiPolygon': new Style({
    stroke: new Stroke({
      color: 'red',
      width: 3,
    }),
    fill: new Fill({
      color: 'rgba(255, 0, 0, 0.5)',
    }),
  }),
};

const stylesHeatmapMedium = {
  'MultiPolygon': new Style({
    stroke: new Stroke({
      color: 'rgb(255, 255, 0)',
      width: 3,
    }),
    fill: new Fill({
      color: 'rgba(255, 255, 0, 0.5)',
    }),
  }),
};

const stylesHeatmapLow = {
  'MultiPolygon': new Style({
    stroke: new Stroke({
      color: 'green',
      width: 3,
    }),
    fill: new Fill({
      color: 'rgba(0, 255, 0, 0.5)',
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

// VectorSources and VectorLayers
const sourceClassified = new VectorSource({format: new GeoJSON()});
const sourceHeatmapLow = new VectorSource({format: new GeoJSON()});
const sourceHeatmapMedium = new VectorSource({format: new GeoJSON()});
const sourceHeatmapHigh = new VectorSource({format: new GeoJSON()});

const layerClassified = new VectorLayer({
  title: 'Classified',
  style: styleFunctionClassified,
});
const layerHeatmapLow = new VectorLayer({
  title: 'Heatmap Low',
  style: styleFunctionHeatmapLow,
});
const layerHeatmapMedium = new VectorLayer({
  title: 'Heatmap Medium',
  style: styleFunctionHeatmapMedium,
});
const layerHeatmapHigh = new VectorLayer({
  title: 'Heatmap High',
  style: styleFunctionHeatmapHigh,
});

// Dictionary of sources and layers
const sourcesAndLayers = {
  'sources': [
    sourceClassified,
    sourceHeatmapHigh,
    sourceHeatmapLow,
    sourceHeatmapMedium,
  ],
  'layers': [
    layerClassified,
    layerHeatmapHigh,
    layerHeatmapLow,
    layerHeatmapMedium,
  ],
};

// Map
const map = new Map({
  target: 'map',
  layers: [
    new LayerGroup({
      title: 'Base maps',
      layers: [
        new TileLayer({
          title: 'None',
          type: 'base',
          source: new XYZ({
            url: null,
          }),
        }),
        new TileLayer({
          title: 'OpenStreetMap',
          type: 'base',
          source: new OSM(),
        }),
        new TileLayer({
          title: 'Bing Roads',
          type: 'base',
          source: new BingMaps({
            key: bingKey,
            imagerySet: 'Road',
          }),
        }),
        new TileLayer({
          title: 'Bing Aerial',
          type: 'base',
          source: new BingMaps({
            key: bingKey,
            imagerySet: 'Aerial',
          }),
        }),
        new TileLayer({
          title: 'Bing Hybrid',
          type: 'base',
          source: new BingMaps({
            key: bingKey,
            imagerySet: 'AerialWithLabels',
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
  controls: defaults({ attribution: false }).extend([
    new ZoomSlider()
  ])
});

// Layer Switcher
var layerSwitcher = new LayerSwitcher({
  tipLabel: 'Layer control',
  groupSelectStyle: 'children',
  reverse: false,
});
map.addControl(layerSwitcher);

// Functions
// TODO: is this needed?
const removeLayersFromMap = function() {
  for (const source of sourcesAndLayers['sources']) {
    source.clear();
  };

  map.removeLayer(geojsonLayerGroup);
};

const changeDate = function(newDate) {
  var dateArray = newDate.split('-');
  dateArray.reverse();
  document.getElementById('date').innerHTML = '<b>Date:</b> ' + dateArray.join('/');
}

const setAOILayers = function() {
  const aoi = selectedAOI.value;
  const swipeValue = swipe.value;
  const date = Object.keys(aoisWithDates[aoi])[swipeValue];
  const layers = [];

  removeLayersFromMap();

  for (let i = 0; i < 4; i++) {
    sourcesAndLayers['sources'][i].setUrl(aoisWithDates[aoi][date][i]);
    sourcesAndLayers['sources'][i].refresh();
    sourcesAndLayers['layers'][i].setSource(sourcesAndLayers['sources'][i]);
    layers[i] = sourcesAndLayers['layers'][i];
  };

  geojsonLayerGroup = new LayerGroup({
    title: 'Data layers',
    layers: layers,
  });

  map.addLayer(geojsonLayerGroup);
};

const changeAOI = function () {
  let aoiBbox = null;
  const aoi = selectedAOI.value;
  const swipeValue = swipe.value;

  changeDate(Object.keys(aoisWithDates[aoi])[swipeValue]);
  setAOILayers();

  if (aoi == 'Kiskore') {
    aoiBbox = kiskore_bbox;
  } else if (aoi == 'Kanyahaza') {
    aoiBbox = kanyahaza_bbox;
  } else if (aoi == 'Pusztazamor') {
    aoiBbox = pusztazamor_bbox;
  } else if (aoi == 'Raho') {
    aoiBbox = raho_bbox;
  } else {
    aoiBbox = null;
  }
  if (aoiBbox !== null) {
    map.getView().fit(aoiBbox, map.getSize());
  }
};

const resizeMap = function () {
  var userInputsHeight = document.getElementById('user-inputs').offsetHeight;
  var remainingHeight = window.innerHeight - userInputsHeight - 10
  document.getElementById('map').style.height = remainingHeight.toString() + "px";
  map.updateSize();
};

const fetchGeojsonPaths = async function () {
  const res = await fetch(base_url + 'geojson_files.json');
  aoisWithDates = await res.json();

  for (var out_key of Object.keys(aoisWithDates)) {
    for (var in_key of Object.keys(aoisWithDates[out_key])) {
      for (let i = 0; i < 4; i++) {
        aoisWithDates[out_key][in_key][i] = base_url + aoisWithDates[out_key][in_key][i];
      };
    };
  };
};

// Events
selectedAOI.onchange = changeAOI;

swipe.addEventListener('input', function () {
  const aoi = selectedAOI.value;
  const swipeValue = swipe.value;
  changeDate(Object.keys(aoisWithDates[aoi])[swipeValue]);
  setAOILayers(aoi);
});

window.onresize = function()
{
  setTimeout( resizeMap, 200);
}

await fetchGeojsonPaths();
resizeMap();
changeAOI();
