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
    constructor(models) {
        this.models = models;
        this.widget = null; // filled by BotGardMapWidget
        this.current_model_layer = "territory";
        this.current_model = null;
        this.current_model_pk = null;
        this.on_selected = (values) => null;
    }

    select(model_name, pk) {
        this.current_model = model_name;
        this.current_model_pk = pk;
        this.widget.interactions.select.clearSelection();
        let selected = false;
        for (const feature of this.widget.garden_map_feature_collection.getArray()) {
            if (feature.values_.model === model_name && feature.values_.pk == pk) {
                this.widget.interactions.select.selectFeature(feature);
                selected = true;
                break;
            }
        }
    }

    set_model_layer(model_name) {
        this.current_model_layer = model_name;
        this.widget.map.render();
    }

    get_data() {
        console.log("FEATURES:")
        for (const feature of this.widget.garden_map_feature_collection.getArray()) {
            console.log(feature.values_);
        }
    }

    get_current_values() {
        for (const m of this.models) {
            if (m.pk === this.current_model_pk && m.model === this.current_model) {
                return m;
            }
        }
        //console.log("NOT FOUND", this.current_model, this.current_model_pk);
    }
}

const MAP_COLORS = {
    "territory": "rgba(100, 200, 100, .5)",
    "territory_selected": "rgba(150, 250, 150, .5)",
    "territory_stroke": "rgba(50, 200, 70, .7)",
    "territory_stroke_selected": "rgba(100, 255, 100, .7)",
    "department": "rgba(100, 100, 200, .5)",
    "department_selected": "rgba(150, 150, 250, .5)",
    "department_stroke": "rgba(50, 50, 255, .7)",
    "department_stroke_selected": "rgba(100, 100, 255, .7)",
    "text": "rgba(255, 255, 255, .8)",
    "text_selected": "rgba(255, 255, 255, 1)",
    "text_stroke": "rgba(0, 0, 0, .6)",
    "text_stroke_selected": "rgba(0, 0, 0, 1)",
};

function create_garden_map_polygon_style(style_type) {
    return new ol.style.Style({
        renderer(coordinates, state) {
            const ctx = state.context;
            const feature = state.feature;
            const widget = feature.get("widget");
            const model = feature.get("model");
            const code = feature.get("code");
            const is_selected = style_type === "selected";

            if (!widget)
                return;

            if (widget.garden_map.current_model_layer === "territory") {
                if (model === "department")
                    return;
            }

            ctx.lineWidth = is_selected ? 4 : 2;
            ctx.font = "bold 16px sans";
            for (const polygon of coordinates) {
                if (!(typeof polygon === "object" && typeof polygon[0] === "object")) {
                    return;
                }
                let min_x = null, min_y = null;
                let center_x = 0, center_y = 0;
                for (const coords of polygon) {
                    ctx.beginPath();
                    for (const coord of coords) {
                        ctx.lineTo(coord[0], coord[1]);
                        if (min_x === null || coord[0] < min_x) min_x = coord[0];
                        if (min_y === null || coord[1] < min_y) min_y = coord[1];
                        center_x += coord[0];
                        center_y += coord[1];
                    }
                    center_x /= coords.length;
                    center_y /= coords.length;
                    ctx.fillStyle = MAP_COLORS[model + (is_selected ? "_selected" : "")];
                    ctx.strokeStyle = MAP_COLORS[model + "_stroke" + (is_selected ? "_selected" : "")];
                    ctx.fill();
                    ctx.stroke();
                    if (code !== null) {
                        const rect = ctx.measureText(code);
                        const x = center_x - rect.width / 2;
                        const y = center_y + (rect.actualBoundingBoxAscent + rect.actualBoundingBoxDescent) / 2;
                        ctx.fillStyle = MAP_COLORS["text" + (is_selected ? "_selected" : "")];
                        ctx.strokeStyle = MAP_COLORS["text_stroke" + (is_selected ? "_selected" : "")];
                        ctx.strokeText(code, x, y);
                        ctx.fillText(code, x, y);
                    }
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

        this.map_interactions = undefined;
        if (options.garden_map) {
            this.map_interactions = ol.interaction.defaults.defaults({
                shiftDragZoom: false,
                pinchZoom: false,
            });
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

        /* ---- setup GardenMap data ---- */

        this.garden_map = this.options.garden_map;

        if (!this.garden_map) {
            this.garden_map_feature_overlay = null;
            this.garden_map_feature_collection = null;
        } else {
            this.garden_map.widget = this;
            this.garden_map_feature_collection = new ol.Collection();
            this.garden_map_feature_overlay = new ol.layer.Vector({
                map: this.map,
                style: create_garden_map_polygon_style(),
                source: new ol.source.Vector({
                    features: this.garden_map_feature_collection,
                    useSpatialIndex: false // improve performance,
                }),
                updateWhileAnimating: true, // optional, for instant visual feedback
                updateWhileInteracting: true // optional, for instant visual feedback
            });

            for (const item of this.garden_map.models) {
                if (item.features) {
                    item.features.forEach(feature => feature.set("widget", this));
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
            interactions: this.map_interactions,
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
                condition: ol.events.condition.singleClick,
                style: create_garden_map_polygon_style("selected"),
                multi: true,
            });
            this.interactions.select.on("select", (e)=> {
                if (e.mapBrowserEvent && e.selected && e.selected.length) {
                    for (let i = e.selected.length - 1; i >= 0; --i) {
                        if (e.selected[i].values_.model === widget.garden_map.current_model_layer) {
                            widget.garden_map.on_selected(e.selected[i].values_);
                            break;
                        }
                    }
                }
            });
            this.interactions.modify = new ol.interaction.Modify({
                features: this.garden_map_feature_collection,
                deleteCondition: function (event) {
                    return ol.events.condition.shiftKeyOnly(event) &&
                        ol.events.condition.singleClick(event);
                }
            });
            this.interactions.draw = new ol.interaction.Draw({
                type: "MultiPolygon",
                features: this.garden_map_feature_collection,
                //condition: ol.events.condition.shiftKey,
                //condition: event => ol.events.condition.singleClick(event) && ol.events.condition.shiftKey(event),
                freehandCondition: event => false,
                //style: create_garden_map_polygon_style("draw"),
            });
            this.interactions.draw.on("drawstart", (e) => {
                // copy current selected object values on draw-start
                const cur_values = widget.garden_map.get_current_values();
                e.feature.set("widget", widget);
                if (cur_values) {
                    // setting ID somehow breaks the drawning interaction
                    //e.feature.setId(cur_values.pk);
                    for (const key of Object.keys(cur_values)) {
                        if (key !== "features") {
                            //console.log({key, value: cur_values[key]});
                            e.feature.set(key, cur_values[key]);
                        }
                    }
                }
            });
            this.map.addInteraction(this.interactions.modify);
            this.map.addInteraction(this.interactions.select);
            this.map.addInteraction(this.interactions.draw);
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
