/* global ol */
'use strict';
document.addEventListener("DOMContentLoaded", function() {

    const map_layers = [
        new ol.layer.Tile({source: new ol.source.OSM()})
    ];

    window.geodjango_map = new ol.Map({
        target: "map",
        layers: map_layers,
        view: new ol.View({
            zoom: 17
        })
    });
});