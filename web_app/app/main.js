import './style.css';
import {Map, View} from 'ol';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import LayerSwitcher from 'ol-layerswitcher';
import LayerGroup from "ol/layer/group";
import BingMaps from 'ol/source/BingMaps';
import XYZ from 'ol/source/XYZ';
import GeoJSON from 'ol/format/GeoJSON';
import {Fill, Stroke, Style} from 'ol/style';
import {Vector as VectorSource} from 'ol/source';
import {Tile, Vector as VectorLayer} from 'ol/layer';
import {defaults} from 'ol/control/defaults';
import {OverviewMap, ZoomSlider} from 'ol/control';

// Constant values
const bingKey = 'AgKv8E2vHuEwgddyzg_pRM6ycSRygeePXSFYTqc8jbikPT8ILyQxm1EF3YUmeRQ2';
const kiskore_bbox = [2283300, 6021945, 2284684, 6023968];
const kanyahaza_bbox = [2588995, 6087354, 2597328, 6091368];
const pusztazamor_bbox = [2090012, 6002140, 2095385, 6005579];
const raho_bbox = [2693024, 6114066, 2693905, 6114776];

// Variables
var geojsonLayerGroup;

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

// Kiskore
const kiskoreSourceClassified = new VectorSource();
const kiskoreSourceHeatmapLow = new VectorSource();
const kiskoreSourceHeatmapMedium = new VectorSource();
const kiskoreSourceHeatmapHigh = new VectorSource();

const kiskoreLayerClassified = new VectorLayer({
  title: 'Classified',
  style: styleFunctionClassified,
});
const kiskoreLayerHeatmapLow = new VectorLayer({
  title: 'Heatmap Low',
  style: styleFunctionHeatmapLow,
});
const kiskoreLayerHeatmapMedium = new VectorLayer({
  title: 'Heatmap Medium',
  style: styleFunctionHeatmapMedium,
});
const kiskoreLayerHeatmapHigh = new VectorLayer({
  title: 'Heatmap High',
  style: styleFunctionHeatmapHigh,
});

// Kanyahaza
const kanyahazaSourceClassified = new VectorSource();
const kanyahazaSourceHeatmapLow = new VectorSource();
const kanyahazaSourceHeatmapMedium = new VectorSource();
const kanyahazaSourceHeatmapHigh = new VectorSource();

const kanyahazaLayerClassified = new VectorLayer({
  title: 'Classified',
  style: styleFunctionClassified,
});
const kanyahazaLayerHeatmapLow = new VectorLayer({
  title: 'Heatmap Low',
  style: styleFunctionHeatmapLow,
});
const kanyahazaLayerHeatmapMedium = new VectorLayer({
  title: 'Heatmap Medium',
  style: styleFunctionHeatmapMedium,
});
const kanyahazaLayerHeatmapHigh = new VectorLayer({
  title: 'Heatmap High',
  style: styleFunctionHeatmapHigh,
});

// Pusztazamor
const pusztazamorSourceClassified = new VectorSource();
const pusztazamorSourceHeatmapLow = new VectorSource();
const pusztazamorSourceHeatmapMedium = new VectorSource();
const pusztazamorSourceHeatmapHigh = new VectorSource();

const pusztazamorLayerClassified = new VectorLayer({
  title: 'Classified',
  style: styleFunctionClassified,
});
const pusztazamorLayerHeatmapLow = new VectorLayer({
  title: 'Heatmap Low',
  style: styleFunctionHeatmapLow,
});
const pusztazamorLayerHeatmapMedium = new VectorLayer({
  title: 'Heatmap Medium',
  style: styleFunctionHeatmapMedium,
});
const pusztazamorLayerHeatmapHigh = new VectorLayer({
  title: 'Heatmap High',
  style: styleFunctionHeatmapHigh,
});

// Raho
const rahoSourceClassified = new VectorSource();
const rahoSourceHeatmapLow = new VectorSource();
const rahoSourceHeatmapMedium = new VectorSource();
const rahoSourceHeatmapHigh = new VectorSource();

const rahoLayerClassified = new VectorLayer({
  title: 'Classified',
  style: styleFunctionClassified,
});
const rahoLayerHeatmapLow = new VectorLayer({
  title: 'Heatmap Low',
  style: styleFunctionHeatmapLow,
});
const rahoLayerHeatmapMedium = new VectorLayer({
  title: 'Heatmap Medium',
  style: styleFunctionHeatmapMedium,
});
const rahoLayerHeatmapHigh = new VectorLayer({
  title: 'Heatmap High',
  style: styleFunctionHeatmapHigh,
});

// Dictionary of sources and layers
const sourcesAndLayers = {
  'kiskore': {
    'sources': [
      kiskoreSourceClassified,
      kiskoreSourceHeatmapHigh,
      kiskoreSourceHeatmapMedium,
      kiskoreSourceHeatmapLow,
    ],
    'layers': [
      kiskoreLayerClassified,
      kiskoreLayerHeatmapHigh,
      kiskoreLayerHeatmapMedium,
      kiskoreLayerHeatmapLow,
    ],
  },
  'kanyahaza': {
    'sources': [
      kanyahazaSourceClassified,
      kanyahazaSourceHeatmapHigh,
      kanyahazaSourceHeatmapMedium,
      kanyahazaSourceHeatmapLow,
    ],
    'layers': [
      kanyahazaLayerClassified,
      kanyahazaLayerHeatmapHigh,
      kanyahazaLayerHeatmapMedium,
      kanyahazaLayerHeatmapLow,
    ],
  },
  'pusztazamor': {
    'sources': [
      pusztazamorSourceClassified,
      pusztazamorSourceHeatmapHigh,
      pusztazamorSourceHeatmapMedium,
      pusztazamorSourceHeatmapLow,
    ],
    'layers': [
      pusztazamorLayerClassified,
      pusztazamorLayerHeatmapHigh,
      pusztazamorLayerHeatmapMedium,
      pusztazamorLayerHeatmapLow,
    ],
  },
  'raho': {
    'sources': [
      rahoSourceClassified,
      rahoSourceHeatmapHigh,
      rahoSourceHeatmapMedium,
      rahoSourceHeatmapLow,
    ],
    'layers': [
      rahoLayerClassified,
      rahoLayerHeatmapHigh,
      rahoLayerHeatmapMedium,
      rahoLayerHeatmapLow,
    ],
  },
};

// Dictionary of AOIs with dates
const aoisWithDates = {
  'kiskore': {
    '2019-05-02': [
      Kiskore_20190502_classified,
      Kiskore_20190502_heatmap_high,
      Kiskore_20190502_heatmap_medium,
      Kiskore_20190502_heatmap_low,
    ],
    '2019-07-02': [
      Kiskore_20190702_classified,
      Kiskore_20190702_heatmap_high,
      Kiskore_20190702_heatmap_medium,
      Kiskore_20190702_heatmap_low,
    ],
    '2019-09-02': [
      Kiskore_20190902_classified,
      Kiskore_20190902_heatmap_high,
      Kiskore_20190902_heatmap_medium,
      Kiskore_20190902_heatmap_low,
    ],
    '2020-07-05': [
      Kiskore_20200705_classified,
      Kiskore_20200705_heatmap_high,
      Kiskore_20200705_heatmap_medium,
      Kiskore_20200705_heatmap_low,
    ],
    '2020-08-01': [
      Kiskore_20200801_classified,
      Kiskore_20200801_heatmap_high,
      Kiskore_20200801_heatmap_medium,
      Kiskore_20200801_heatmap_low,
    ],
  },
  'kanyahaza': {
    '2020-09-16': [
      Kanyahaza_20200916_classified,
      Kanyahaza_20200916_heatmap_high,
      Kanyahaza_20200916_heatmap_medium,
      Kanyahaza_20200916_heatmap_low,
    ],
    '2021-04-10': [
      Kanyahaza_20210410_classified,
      Kanyahaza_20210410_heatmap_high,
      Kanyahaza_20210410_heatmap_medium,
      Kanyahaza_20210410_heatmap_low,
    ],
    '2021-07-09': [
      Kanyahaza_20210709_classified,
      Kanyahaza_20210709_heatmap_high,
      Kanyahaza_20210709_heatmap_medium,
      Kanyahaza_20210709_heatmap_low,
    ],
    '2021-07-25': [
      Kanyahaza_20210725_classified,
      Kanyahaza_20210725_heatmap_high,
      Kanyahaza_20210725_heatmap_medium,
      Kanyahaza_20210725_heatmap_low,
    ],
    '2021-09-08': [
      Kanyahaza_20210908_classified,
      Kanyahaza_20210908_heatmap_high,
      Kanyahaza_20210908_heatmap_medium,
      Kanyahaza_20210908_heatmap_low,
    ],
  },
  'pusztazamor': {
    '2017-08-01': [
      Pusztazamor_20170801_classified,
      Pusztazamor_20170801_heatmap_high,
      Pusztazamor_20170801_heatmap_medium,
      Pusztazamor_20170801_heatmap_low,
    ],
    '2018-08-01': [
      Pusztazamor_20180801_classified,
      Pusztazamor_20180801_heatmap_high,
      Pusztazamor_20180801_heatmap_medium,
      Pusztazamor_20180801_heatmap_low,
    ],
    '2019-06-01': [
      Pusztazamor_20190601_classified,
      Pusztazamor_20190601_heatmap_high,
      Pusztazamor_20190601_heatmap_medium,
      Pusztazamor_20190601_heatmap_low,
    ],
    '2020-07-01': [
      Pusztazamor_20200701_classified,
      Pusztazamor_20200701_heatmap_high,
      Pusztazamor_20200701_heatmap_medium,
      Pusztazamor_20200701_heatmap_low,
    ],
    '2021-07-01': [
      Pusztazamor_20210701_classified,
      Pusztazamor_20210701_heatmap_high,
      Pusztazamor_20210701_heatmap_medium,
      Pusztazamor_20210701_heatmap_low,
    ],
  },
  'raho': {
    '2020-09-10': [
      Raho_20200910_classified,
      Raho_20200910_heatmap_high,
      Raho_20200910_heatmap_medium,
      Raho_20200910_heatmap_low,
    ],
    '2020-09-23': [
      Raho_20200923_classified,
      Raho_20200923_heatmap_high,
      Raho_20200923_heatmap_medium,
      Raho_20200923_heatmap_low,
    ],
    '2021-06-21': [
      Raho_20210621_classified,
      Raho_20210621_heatmap_high,
      Raho_20210621_heatmap_medium,
      Raho_20210621_heatmap_low,
    ],
    '2021-08-01': [
      Raho_20210801_classified,
      Raho_20210801_heatmap_high,
      Raho_20210801_heatmap_medium,
      Raho_20210801_heatmap_low,
    ],
    '2021-09-09': [
      Raho_20210909_classified,
      Raho_20210909_heatmap_high,
      Raho_20210909_heatmap_medium,
      Raho_20210909_heatmap_low,
    ],
  }
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
    new OverviewMap({
      layers: [
        new Tile({
          source: new OSM()
        })
      ]
    }),
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
const removeLayersFromMap = function() {
  for (const nameOfAOI of Object.keys(sourcesAndLayers)) {
    for (const source of sourcesAndLayers[nameOfAOI]['sources']) {
      source.clear();
    };
  };

  map.removeLayer(geojsonLayerGroup);
};

const changeDate = function(newDate) {
  document.getElementById('date').innerHTML = newDate;
}

const setAOILayers = function() {
  const aoi = selectedAOI.value;
  const swipeValue = swipe.value;
  const date = Object.keys(aoisWithDates[aoi])[swipeValue];
  const layers = [];

  removeLayersFromMap();

  for (let i = 0; i < 4; i++) {
    sourcesAndLayers[aoi]['sources'][i].addFeatures(new GeoJSON().readFeatures(aoisWithDates[aoi][date][i]));
    sourcesAndLayers[aoi]['layers'][i].setSource(sourcesAndLayers[aoi]['sources'][i]);
    layers[i] = sourcesAndLayers[aoi]['layers'][i];
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
  
  changeDate('Dátum: ' + Object.keys(aoisWithDates[aoi])[swipeValue]);
  setAOILayers();

  if (aoi == 'kiskore') {
    aoiBbox = kiskore_bbox;
  } else if (aoi == 'kanyahaza') {
    aoiBbox = kanyahaza_bbox;
  } else if (aoi == 'pusztazamor') {
    aoiBbox = pusztazamor_bbox;
  } else if (aoi == 'raho') {
    aoiBbox = raho_bbox;
  } else {
    aoiBbox = null;
  }
  if (aoiBbox !== null) {
    map.getView().fit(aoiBbox, map.getSize());
  }
};

// Events
selectedAOI.onchange = changeAOI;

swipe.addEventListener('input', function () {
  const aoi = selectedAOI.value;
  const swipeValue = swipe.value;
  changeDate('Dátum: ' + Object.keys(aoisWithDates[aoi])[swipeValue]);
  setAOILayers(aoi);
});

changeAOI();
