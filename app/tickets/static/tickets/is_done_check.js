

function hookToLabelLinks() {

    var $links = $("a.print-label-link");

    $links.on("click", function(event) {
        event.preventDefault();
        var $elem = $(event.target);
        var url = $elem.attr("data-label-url");
        if (url)
            $.ajax(url).done(function(){
                $("span.label-done-indicator[data-label-url=\"" + url + "\"]").html("✓");
            });
        window.open($elem.attr("href"));
    });

}



$(function() {
    hookToLabelLinks();
});