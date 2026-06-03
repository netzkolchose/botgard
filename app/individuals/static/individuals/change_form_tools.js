
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
});

