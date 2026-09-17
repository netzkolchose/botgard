
$(function() {

    /** Display an info if the accession number and the ipen accession number are different */
    function hook_accession_number_check() {

        const input_accession_number = document.querySelector("#id_accession_number");
        const input_ipen_accession_number = document.querySelector("#id_ipen_accession_number");

        document.querySelectorAll(".submit-row").forEach(function (elem) {
            const infobox = document.createElement("div");
            infobox.setAttribute("hidden", "hidden");
            infobox.classList.add("submit-row-info-box");
            elem.appendChild(infobox);
        });

        function check_accession_number() {
            const acc_1 = input_accession_number.value;
            const acc_2 = input_ipen_accession_number.value;
            //console.log("X", acc_1, acc_2);

            const info_boxes = document.querySelectorAll(".submit-row-info-box");
            if (acc_1 !== acc_2) {
                info_boxes.forEach(function (elem) {
                    elem.innerText = `Info: Die Akzessionsnummer (${acc_1}) und die IPEN-Akzessionsnummer (${acc_2}) sind unterschiedlich!`;
                    elem.removeAttribute("hidden");
                });
            } else {
                info_boxes.forEach(function (elem) {
                    elem.setAttribute("hidden", "hidden");
                });
            }
        }

        if (input_accession_number && input_ipen_accession_number) {
            input_accession_number.addEventListener("change", check_accession_number);
            input_ipen_accession_number.addEventListener("change", check_accession_number);
            check_accession_number();
        }
    }

    hook_accession_number_check();

    function hook_add_button() {
        // intercept the outplanting inline add-button
        // the copied proxy template has some js source code
        // where "__prefix__" must be replaced with inline-index-number
        const elem = document.querySelector("#outplanting_set-group a.addlink");
        if (elem) {
            // hide the old button and add a new one
            const new_elem = $(elem).clone().get()[0];
            elem.parentElement.appendChild(new_elem);
            elem.setAttribute("hidden", "hidden");
            new_elem.onclick = function(event) {
                event.stopPropagation();
                event.preventDefault();
                elem.click();
                hook_add_button();

                const maps = document.querySelectorAll("#outplanting_set-group .dj_map");
                if (maps.length > 1) {
                    // -1 is proxy, -2 is the new inline form
                    const elem = maps[maps.length - 2];
                    const match = elem.getAttribute("id").match(/id_outplanting_set-(\d+)/);
                    if (match) {
                        const inline_index = match[1];
                        const source_elem = elem.parentElement.querySelector(".script-content");
                        const patched_code = source_elem.innerText.replaceAll(
                            "__prefix__",
                            inline_index,
                        );
                        eval(patched_code);
                    }
                }
            };
        }
    }

    setTimeout(hook_add_button, 300);

    // display the current IPEN nicely readable in the IPEN section
    function show_full_ipen() {
        const url_elem = document.querySelector('[data-individual-ipen-url]');
        if (!url_elem) return;
        const url = url_elem.getAttribute("data-individual-ipen-url");

        const params = {
            ipen_country: $("#id_ipen_country").val(),
            ipen_transfer_restricted: $("#id_ipen_transfer_restricted").val(),
            ipen_garden_code: $("#id_ipen_garden_code").val(),
            ipen_accession_number: $("#id_ipen_accession_number").val(),
        };
        if (params.ipen_country) {
            params.ipen_country = params.ipen_country.split(" ")[0];
        }
        if (params.ipen_garden_code) {
            const match = /\(([A-Za-z]+)\//g.exec(params.ipen_garden_code);
            if (match) {
                params.ipen_garden_code = match[1];
            } else {
                params.ipen_garden_code = "";
            }
        }
        fetch(url + "?" + new URLSearchParams(params))
            .then(response => {
                if (response.status !== 200) { throw "Error"; }
                return response.text();
            })
            .then(text => {
                const elem = document.querySelector('div.form-row.field-ipen_country').parentElement.querySelector("h2");
                if (!elem.querySelector("#full-ipen-text")) {
                    const space_elem = document.createElement("span");
                    space_elem.innerHTML = "&nbsp;"
                    elem.appendChild(space_elem);
                    const new_elem = document.createElement("span");
                    new_elem.setAttribute("id", "full-ipen-text")
                    elem.appendChild(new_elem);
                }
                elem.querySelector("#full-ipen-text").innerText = text;
            })
            .catch(error => {});
    }

    let _ipen_change_timeout = null;
    function ipen_has_changed_debounced() {
        if (_ipen_change_timeout) {
            clearTimeout(_ipen_change_timeout);
        }
        _ipen_change_timeout = setTimeout(show_full_ipen, 400);
    }

    function hook_ipen_change() {
        for (const query of ["#id_ipen_country", "#id_ipen_transfer_restricted", "#id_ipen_garden_code", "#id_ipen_accession_number"]) {
            const elem = document.querySelector(query);
            if (elem) {
                elem.addEventListener("change", ipen_has_changed_debounced);
                elem.addEventListener("keyup", ipen_has_changed_debounced);
            }
        }
    }

    show_full_ipen();
    hook_ipen_change();
});

