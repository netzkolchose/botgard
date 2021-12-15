
function updateSubtribusFields() {
    var name = $("#id_family").val();
    //console.log(name);
    var enable = name == "Asteraceae";
    $("#id_subfamily").attr("disabled", !enable);
    $("#id_tribus").attr("disabled", !enable);
    $("#id_subtribus").attr("disabled", !enable);
}


$(function(){
    $("#id_family").on("change", function(event) {
        updateSubtribusFields();
    });
    updateSubtribusFields();
});

