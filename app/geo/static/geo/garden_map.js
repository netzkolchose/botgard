function create_garden_map_interface() {
    const models = [];
    for (const model of ["territory", "department"]) {
        for (const elem of document.querySelectorAll("#current_"+model+" option")) {
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
    const garden_map = new GardenMapInterface(models);
    garden_map.on_selected = (values) => {
        //console.log("selected", values.model, values.pk, values);
        if (values.model === "department") {
            select_department(values.pk);
        } else if (values.model === "territory") {
            select_territory(values.pk, true);
        }
    }
    return garden_map;
}

function select_territory(pk, no_select_department) {
    //console.log("select_territory", pk, no_select_department);
    document.querySelector("#current_territory").value = pk;

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
    let ter_pk = null;
    for (const elem of document.querySelectorAll("#current_department option")) {
        if (elem.getAttribute("data-pk") == pk) {
            ter_pk = elem.getAttribute("data-territory-pk");
            break;
        }
    }
    document.querySelector("#current_department").value = pk;
    map_widget.garden_map.select("department", pk);

    if (ter_pk) {
        select_territory(ter_pk, true);
    }
}

function select_model_layer(model) {
    //console.log("select_model_layer", model);
    document.querySelector("#current_model").value = model;
    map_widget.garden_map.set_model_layer(model);
    const pk = document.querySelector("#current_" + model).value;
    // make sure, next drawing draws the right model
    map_widget.garden_map.select(model, pk);
}

function hook_ui_elements() {
    let first_ter_pk = null;
    for (const elem of document.querySelectorAll("#current_territory option")) {
        if (!first_ter_pk && elem.getAttribute("data-code") !== "-") {
            first_ter_pk = elem.value;
        }
    }
    document.querySelector("#current_territory").onchange = (event) => {
        select_territory(event.target.value);
    };
    if (first_ter_pk) {
        select_territory(first_ter_pk);
    }

    document.querySelector("#current_department").onchange = (event) => {
        select_model_layer("department");
        select_department(event.target.value);
    };

    document.querySelector("#current_model").onchange = (event) => {
        select_model_layer(event.target.value);
    };

    document.querySelector("#save-button").onclick = () => {
        map_widget.garden_map.get_data();
    };

    document.querySelector("#mode_select").onclick = () => {
        map_widget.disableDrawing();
    };

    document.querySelector("#mode_draw").onclick = () => {
        map_widget.enableDrawing();
    };
}

document.addEventListener("DOMContentLoaded", function() {

    hook_ui_elements();
    select_model_layer("department");
});