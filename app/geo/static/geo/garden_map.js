function create_garden_map_interface(interactive=true, form_element_name=null) {
    //console.log("create_garden_map_interface", form_element_name);
    const models = [];
    for (const model of ["territory", "department"]) {
        let selector = "#current_"+model+" option"
        if (form_element_name) {
            selector = `#id_${form_element_name}_div_map ${selector}`;
        }
        for (const elem of document.querySelectorAll(selector)) {
            const pk = elem.getAttribute("data-pk");
            const code = elem.getAttribute("data-code");
            const name = elem.getAttribute("data-name");
            const polygon = elem.getAttribute("data-polygon");

            let features = null;
            if (polygon && polygon !== "None") {
                features = wkt_to_features(polygon);
                features.forEach(feature => {
                    feature.set("model", model);
                    feature.set("pk", pk);
                    feature.set("code", code);
                    feature.set("name", name);
                });
            }
            models.push({model, pk, code, name, features});
        }
    }
    const garden_map = new GardenMapInterface(models, interactive);
    garden_map.on_selected = (values) => {
        // console.log("selected", values.model, values.pk, values);
        if (values.model === "department") {
            select_department(values.pk);
        } else if (values.model === "territory") {
            select_territory(values.pk, true);
        }
        const elem = document.querySelector("#delete-polygon-button");
        if (elem) {
            elem.removeAttribute("disabled");
        }
    }
    garden_map.on_unselected = () => {
        const elem = document.querySelector("#delete-polygon-button");
        if (elem) {
            elem.setAttribute("disabled", "");
        }
    };

    if (form_element_name) {
        if (form_element_name.startsWith("outplanting") && form_element_name.indexOf("__prefix__") < 0) {
            const elem_name = form_element_name.slice(0, form_element_name.length-9);
            const elem = document.querySelector(`#id_${elem_name}-department`);
            if (elem) {
                const widget_name = `geodjango_${form_element_name.replaceAll("-", "_")}`;
                elem.onchange = (event) => {
                    console.log("CHANGE", elem_name, widget_name, event.target.value);
                    try {
                        eval(widget_name).garden_map.zoom_to_model("department", event.target.value);
                    } catch (e) {console.log("ERROR", e)}
                };
            }
        }
    }

    return garden_map;
}

function select_territory(pk, no_select_department) {
    //console.log("select_territory", pk, no_select_department);
    const elem = document.querySelector("#current_territory");
    if (!elem) return;

    elem.value = pk;

    let first_dep_pk = null;
    for (const elem of document.querySelectorAll("#current_department option")) {
        if (pk == elem.getAttribute("data-territory-pk")) {
            elem.removeAttribute("hidden");
            if (!first_dep_pk) {
                first_dep_pk = elem.value;
            }
        }
        else {
            elem.setAttribute("hidden", "hidden");
        }
    }
    if (!no_select_department && first_dep_pk) {
        select_department(first_dep_pk);
    }
}

function select_department(pk) {
    //console.log("select_department", pk);

    const elem = document.querySelector("#current_department");
    if (!elem) return;
    try {
        map_widget
    } catch (e) {
        return;
    }

    let ter_pk = null;
    for (const elem of document.querySelectorAll("#current_department option")) {
        if (elem.getAttribute("data-pk") == pk) {
            ter_pk = elem.getAttribute("data-territory-pk");
            break;
        }
    }
    elem.value = pk;
    map_widget.garden_map.select("department", pk);

    if (ter_pk) {
        select_territory(ter_pk, true);
    }
}

function select_model_layer(model) {
    //console.log("select_model_layer", model);
    let elem = document.querySelector("#current_model");
    if (!elem) return;

    elem.value = model;
    map_widget.garden_map.set_model_layer(model);
    const pk = document.querySelector("#current_" + model).value;
    // make sure, next drawing draws the right model
    map_widget.garden_map.select(model, pk);

    elem = document.querySelector("#delete-polygon-button");
    if (elem) {
        elem.innerText = elem.getAttribute(`data-${model}`);
    }
}

function save_map() {
    const error_elem = document.querySelector(".errornote");
    const info_elem = document.querySelector(".info-message");

    const feature_list = map_widget.garden_map.get_data();
    fetch(
        document.querySelector("#map").getAttribute("data-save-url"),
        {
            method: "post",
            body: JSON.stringify({features: feature_list}),
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                error_elem.innerText = data.error;
                error_elem.classList.remove("hidden");
            }
            if (data.message) {
                info_elem.innerText = data.message + " " + new Date().toTimeString();
                info_elem.classList.remove("hidden");
            }
        })
        .catch(error => {
            error_elem.innerText = error.toString();
            error_elem.classList.remove("hidden");
        });

    error_elem.classList.add("hidden");
    info_elem.classList.add("hidden");
}

function hook_ui_elements() {
    let first_ter_pk = null;
    for (const elem of document.querySelectorAll("#current_territory option")) {
        if (!first_ter_pk && elem.getAttribute("data-code") !== "-") {
            first_ter_pk = elem.value;
        }
    }

    let elem = document.querySelector("#current_territory");
    if (elem) {
        elem.onchange = (event) => {
            select_territory(event.target.value);
        };
        if (first_ter_pk) {
            select_territory(first_ter_pk);
        }
    }

    elem = document.querySelector("#current_department");
    if (elem) {
        elem.onchange = (event) => {
            select_model_layer("department");
            select_department(event.target.value);
        };
    }

    elem = document.querySelector("#current_model");
    if (elem) {
        elem.onchange = (event) => {
            select_model_layer(event.target.value);
        };
    }

    elem = document.querySelector("#save-button");
    if (elem) {
        elem.onclick = () => {
            save_map();
        };
    }

    elem = document.querySelector("#mode_select");
    if (elem) {
        elem.onclick = () => {
            map_widget.setMode("select");
        };
    }

    elem = document.querySelector("#mode_modify");
    if (elem) {
        elem.onclick = () => {
            map_widget.setMode("modify");
        };
    }

    elem = document.querySelector("#mode_draw");
    if (elem) {
        elem.onclick = () => {
            map_widget.setMode("draw");
        };
    }

    elem = document.querySelector("#delete-polygon-button");
    if (elem) {
        elem.onclick = () => {
            if (map_widget.garden_map.current_model && map_widget.garden_map.current_model_pk) {
                map_widget.garden_map.delete_model(
                    map_widget.garden_map.current_model,
                    map_widget.garden_map.current_model_pk,
                );
            }
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {

    hook_ui_elements();
    select_model_layer("department");
});