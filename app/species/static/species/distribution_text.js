var CHAR_SIZE_MAP = {
    w: 1./18,
    m: 1./20,
    o: 1./22,
    e: 1./32,
    n: 1./31,
    i: 1./60,
    j: 1./60,
    l: 1./60,
    t: 1./60,
    f: 1./60,
    ' ': 1./60,
};

function getTextSize(text) {
    if (!text)
        return 0;

    var len = 0;
    var ltext = text.toLowerCase();
    for (var i in ltext) {
        var c = ltext[i];
        if (c in CHAR_SIZE_MAP)
            len += CHAR_SIZE_MAP[c];
        else
            len += 1./40;
        //console.log(text[i], len);
    }
    return len;
}



function onDistributionTextChange() {
    let
        $input = $("#id_area_of_distribution_etikettxt"),
        text = $input.val(),
        text_length = Math.round(getTextSize(text) * 100.);
    $input.siblings(".help").text(`${text_length}%`);
}


$(function(){
    $("#id_area_of_distribution_etikettxt").on("keyup", function(event) {
        onDistributionTextChange();
    });
    onDistributionTextChange();
});

