
function toggle_selection(event) {
    var el = event.target;
    if ($('#selected li[value='+el.id+']').length) {
        $('#selected li[value='+el.id+']').remove();
    } else {
        $('<li>').attr({value: el.id}).text(el.value).appendTo($('#selected'));
        $("#selected").sortable('refresh');

    }
}

function update_settings() {
    var res = [];
    var elems = $('#selected li');
    for (var i=0; i<elems.length; i++) {
        res.push([$(elems[i]).attr('value'), $(elems[i]).text()]);

    }
    $('#'+tablesettings.settings_id).val(JSON.stringify(res));

}

$(document).ready(function() {
    $.get(tablesettings.tree_url, function (response) {
        $('#tree').html(response);
        $('#tree input').change(toggle_selection);
    });
    $('#' + tablesettings.model.split('.')[1] + '_configure_form').submit(update_settings);

    $('#selected').sortable();
});