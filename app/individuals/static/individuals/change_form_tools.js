
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
});

