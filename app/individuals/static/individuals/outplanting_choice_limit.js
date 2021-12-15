
/* Limit choices in department field to selected territory */
function limitOutplantingChoices(idx) {
    var terr_id   = "#id_outplanting_set-" + idx + "-territory";
    var depart_id = "#id_outplanting_set-" + idx + "-department";
    var code = $(terr_id + " option:selected").text().split(" ")[0];
    $options = $(depart_id + " option");
    for (var i=0; i<$options.length; ++i) {
        var opt = $options[i];
        var depcode = opt.text.split("-")[0];
        opt.hidden = !(code === depcode);
    }
}

function hookToOutplantingFormsetRow(idx) {
    var terr_id   = "#id_outplanting_set-" + idx + "-territory";
    var $terr = $(terr_id);

    $terr.off("change");
    $terr.on("change", function() { limitOutplantingChoices(idx); });
    limitOutplantingChoices(idx);
}

function hookToOutplantingFormset() {
    for (var idx=0; idx<30; ++idx) {
        hookToOutplantingFormsetRow(idx);
    }
}

$(function() {
    // hook to existing rows
    hookToOutplantingFormset();
    // re-hook on "add row" link
    $("#outplanting_set-group tr.add-row a").on("click", hookToOutplantingFormset);
});

