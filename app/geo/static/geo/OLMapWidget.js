/* global ol */
'use strict';

/**
 * This file is copied from django 5.2 contrib/gis/
 * and adjusted to BotGard's needs
 */

const MAP_SRID = 'EPSG:3857';

/** Take a feature WKT string and convert to array of ol.Feature
    and ake care of transformation
 */
function wkt_to_features(wkt_string) {
    const wkt_reader = new ol.format.WKT();
    const [srid_str, feature_str] = wkt_string.split(";");
    const srid = `EPSG:${srid_str.split("=")[1]}`;
    const features = wkt_reader.readFeatures(feature_str);
    if (srid !== MAP_SRID) {
        features.forEach(feature => {
            feature.getGeometry().transform(srid, MAP_SRID);
        });
    }
    return features;
}

class BotGardGeometryTypeControl extends ol.control.Control {
    // Map control to switch type when geometry type is unknown
    constructor(opt_options) {
        const options = opt_options || {};

        const element = document.createElement('div');
        element.className = 'switch-type type-' + options.type + ' ol-control ol-unselectable';
        if (options.active) {
            element.classList.add("type-active");
        }

        super({
            element: element,
            target: options.target
        });
        const self = this;
        const switchType = function(e) {
            e.preventDefault();
            if (options.widget.currentGeometryType !== self) {
                options.widget.map.removeInteraction(options.widget.interactions.draw);
                options.widget.interactions.draw = new ol.interaction.Draw({
                    features: options.widget.featureCollection,
                    type: options.type
                });
                options.widget.map.addInteraction(options.widget.interactions.draw);
                options.widget.currentGeometryType.element.classList.remove('type-active');
                options.widget.currentGeometryType = self;
                element.classList.add("type-active");
            }
        };

        element.addEventListener('click', switchType, false);
        element.addEventListener('touchstart', switchType, false);
    }
}

/** Interface between BotGardMapWidget and garden-map.js */
class GardenMapInterface {
    constructor(territories, departments) {
        this.territories = territories;
        this.departments = departments;
        this.on_selected = (values) => null;
        this.widget = null;
    }

    select(model_name, pk) {
        let selected = false;
        for (const feature of this.widget.garden_map_feature_collection.getArray()) {
            if (feature.values_.model === model_name && feature.values_.pk == pk) {
                this.widget.interactions.select.selectFeature(feature);
                selected = true;
                break;
            }
        }
        if (!selected) {
            this.widget.interactions.select.clearSelection();
        }
    }
}


function create_garden_map_polygon_style(is_selected) {
    return new ol.style.Style({
        renderer(coordinates, state) {
            const ctx = state.context;
            const code = state.feature.getId();

            ctx.fillStyle = is_selected ? "rgba(150, 150, 250, .5)" : "rgba(100, 100, 200, .5)";
            ctx.strokeStyle = is_selected ? "rgba(100, 100, 255, .7)" : "rgba(50, 50, 255, .7)";
            ctx.lineWidth = is_selected ? 4 : 2;
            for (const polygon of coordinates) {
                if (typeof polygon !== "object")
                    return;
                for (const coords of polygon) {
                    ctx.beginPath();
                    for (const coord of coords) {
                        ctx.lineTo(coord[0], coord[1]);
                    }
                    ctx.fill();
                    ctx.stroke();
                }
            }
        }
    });
}


class BotGardMapWidget {
    constructor(options) {
        this.map = null;
        this.interactions = {draw: null, modify: null, select: null};
        this.typeChoices = false;
        this.ready = false;

        // Default options
        this.options = {
            // default to full germany
            default_lat: 51.4,
            default_lon: 10.8,
            default_zoom: 5.4,
            is_collection: options.geom_name.includes('Multi') || options.geom_name.includes('Collection')
        };

        // Altering using user-provided options
        for (const property in options) {
            if (Object.hasOwn(options, property)) {
                this.options[property] = options[property];
            }
        }
        if (!options.base_layer) {
            this.options.base_layer = new ol.layer.Tile({source: new ol.source.OSM()});
        }

        this.map = this.createMap();
        //console.log("X", this.map.getView().getProjection());
        this.featureCollection = new ol.Collection();
        this.featureOverlay = new ol.layer.Vector({
            map: this.map,
            source: new ol.source.Vector({
                features: this.featureCollection,
                useSpatialIndex: false // improve performance
            }),
            updateWhileAnimating: true, // optional, for instant visual feedback
            updateWhileInteracting: true // optional, for instant visual feedback
        });

        // Populate and set handlers for the feature container
        const self = this;
        this.featureCollection.on('add', function(event) {
            const feature = event.element;
            feature.on('change', function() {
                self.serializeFeatures();
            });
            if (self.ready) {
                self.serializeFeatures();
                if (!self.options.is_collection) {
                    self.disableDrawing(); // Only allow one feature at a time
                }
            }
        });

        const initial_value = document.getElementById(this.options.id).value;
        if (initial_value) {
            const jsonFormat = new ol.format.GeoJSON();
            const features = jsonFormat.readFeatures('{"type": "Feature", "geometry": ' + initial_value + '}');
            const extent = ol.extent.createEmpty();
            features.forEach(function(feature) {
                this.featureOverlay.getSource().addFeature(feature);
                ol.extent.extend(extent, feature.getGeometry().getExtent());
            }, this);
            // Center/zoom the map
            this.map.getView().fit(extent, {minResolution: 1});
        } else {
            this.map.getView().setCenter(this.defaultCenter());
        }

        /* ---- setup GardenMap interaction ---- */

        this.garden_map = this.options.garden_map;

        if (!this.garden_map) {
            this.garden_map_feature_overlay = null;
            this.garden_map_feature_collection = null;
        } else {
            this.garden_map.widget = this;
            this.garden_map_feature_collection = new ol.Collection();
            this.garden_map_feature_overlay = new ol.layer.Vector({
                map: this.map,
                style: create_garden_map_polygon_style(false),
                source: new ol.source.Vector({
                    features: this.garden_map_feature_collection,
                    useSpatialIndex: false // improve performance,
                }),
                updateWhileAnimating: true, // optional, for instant visual feedback
                updateWhileInteracting: true // optional, for instant visual feedback
            });

            for (const item of this.garden_map.departments) {
                if (item.features) {
                    this.garden_map_feature_overlay.getSource().addFeatures(item.features);
                }
            }
        }

        this.createInteractions();
        if (initial_value && !this.options.is_collection) {
            this.disableDrawing();
        }
        const clearNode = document.getElementById(this.map.getTarget()).nextElementSibling;
        if (clearNode.classList.contains('clear_features')) {
            clearNode.querySelector('a').addEventListener('click', (ev) => {
                ev.preventDefault();
                self.clearFeatures();
            });
        }
        this.ready = true;
    }

    createMap() {
        return new ol.Map({
            target: this.options.map_id,
            layers: [this.options.base_layer],
            view: new ol.View({
                zoom: this.options.default_zoom
            })
        });
    }

    createInteractions() {
        if (!this.garden_map) {
            // Initialize the modify interaction
            this.interactions.modify = new ol.interaction.Modify({
                features: this.featureCollection,
                deleteCondition: function (event) {
                    return ol.events.condition.shiftKeyOnly(event) &&
                        ol.events.condition.singleClick(event);
                }
            });

            // Initialize the draw interaction
            let geomType = this.options.geom_name;
            if (geomType === "Geometry" || geomType === "GeometryCollection") {
                // Default to Point, but create icons to switch type
                geomType = "Point";
                this.currentGeometryType = new BotGardGeometryTypeControl({widget: this, type: "Point", active: true});
                this.map.addControl(this.currentGeometryType);
                this.map.addControl(new BotGardGeometryTypeControl({widget: this, type: "LineString", active: false}));
                this.map.addControl(new BotGardGeometryTypeControl({widget: this, type: "Polygon", active: false}));
                this.typeChoices = true;
            }
            this.interactions.draw = new ol.interaction.Draw({
                features: this.featureCollection,
                type: geomType
            });

            this.map.addInteraction(this.interactions.draw);
            this.map.addInteraction(this.interactions.modify);
        }
        else // if this.garden_map
        {
            const widget = this;
            this.interactions.select = new ol.interaction.Select({
                condition: ol.interaction.singleClick,
                style: create_garden_map_polygon_style(true),
            });
            this.interactions.select.on("select", (e)=> {
                if (e.mapBrowserEvent && e.selected && e.selected.length) {
                    widget.garden_map.on_selected(e.selected[0].values_);
                }
            });
            this.interactions.modify = new ol.interaction.Modify({
                features: this.garden_map_feature_collection,
                deleteCondition: function (event) {
                    return ol.events.condition.shiftKeyOnly(event) &&
                        ol.events.condition.singleClick(event);
                }
            });
            this.map.addInteraction(this.interactions.modify);
            this.map.addInteraction(this.interactions.select);
        }
    }

    defaultCenter() {
        const center = [this.options.default_lon, this.options.default_lat];
        if (this.options.map_srid) {
            return ol.proj.transform(center, 'EPSG:4326', this.map.getView().getProjection());
        }
        return center;
    }

    enableDrawing() {
        this.interactions.draw.setActive(true);
        if (this.typeChoices) {
            // Show geometry type icons
            const divs = document.getElementsByClassName("switch-type");
            for (let i = 0; i !== divs.length; i++) {
                divs[i].style.visibility = "visible";
            }
        }
    }

    disableDrawing() {
        if (this.interactions.draw) {
            this.interactions.draw.setActive(false);
            if (this.typeChoices) {
                // Hide geometry type icons
                const divs = document.getElementsByClassName("switch-type");
                for (let i = 0; i !== divs.length; i++) {
                    divs[i].style.visibility = "hidden";
                }
            }
        }
    }

    clearFeatures() {
        this.featureCollection.clear();
        // Empty textarea widget
        document.getElementById(this.options.id).value = '';
        this.enableDrawing();
    }

    serializeFeatures() {
        // Three use cases: GeometryCollection, multigeometries, and single geometry
        let geometry = null;
        const features = this.featureOverlay.getSource().getFeatures();
        if (this.options.is_collection) {
            if (this.options.geom_name === "GeometryCollection") {
                const geometries = [];
                for (let i = 0; i < features.length; i++) {
                    geometries.push(features[i].getGeometry());
                }
                geometry = new ol.geom.GeometryCollection(geometries);
            } else {
                geometry = features[0].getGeometry().clone();
                for (let j = 1; j < features.length; j++) {
                    switch (geometry.getType()) {
                    case "MultiPoint":
                        geometry.appendPoint(features[j].getGeometry().getPoint(0));
                        break;
                    case "MultiLineString":
                        geometry.appendLineString(features[j].getGeometry().getLineString(0));
                        break;
                    case "MultiPolygon":
                        geometry.appendPolygon(features[j].getGeometry().getPolygon(0));
                    }
                }
            }
        } else {
            if (features[0]) {
                geometry = features[0].getGeometry();
            }
        }
        const jsonFormat = new ol.format.GeoJSON();
        document.getElementById(this.options.id).value = jsonFormat.writeGeometry(geometry);
    }
}
