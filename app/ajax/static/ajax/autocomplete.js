
/*
TODO: try to recreate the admin popup logic for foreign fields

// stuff below is copied from django.contrib.admin.static.js.admin.RelatedObjectLookup.js

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct
// element when the popup window is dismissed.
function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}

function showAdminPopup(triggeringLink, name_regexp, add_popup) {
    var name = triggeringLink.id.replace(name_regexp, '');
    name = id_to_windowname(name);
    var href = triggeringLink.href;
    if (add_popup) {
        if (href.indexOf('?') === -1) {
            href += '?_popup=1';
        } else {
            href += '&_popup=1';
        }
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function showRelatedObjectLookupPopup(triggeringLink) {
    return showAdminPopup(triggeringLink, /^lookup_/, true);
}
*/


$(function () {

    $('.autocomplete-modelfield').on("keyup", function(event) {
        var $elem = $(event.target);
        if (!$elem.val())
            $elem.attr("data-ac-state", "empty");
    });

    $('.autocomplete-modelfield').on("focusin", function(event) {
        var $elem = $(event.target);
        $elem.select();
    });

    $('.autocomplete-modelfield').autocomplete({
        delay: 200,
        minLength: 1,
        // fetch results and state
        source: function(request, response) {
            var $elem = $(this.element);
            var modelid = $elem.attr('data-ac-id');

            if (modelid) {
                $.getJSON(
                    $elem.attr('data-ac-json-url'),
                    { term: request.term, id: modelid },
                    function(data) {
                        updateAutocompleteWidgetState($elem, data);
                        if (data)
                            if (data.items)
                                response(data.items);
                    }
                );
            }
        },
        // update state on menu-close
        close: function(event, ui) {
            verifyAutocompleteField( $(event.target) );
        }
    });

    $('.autocomplete-verify').each(function() {
        verifyAutocompleteField($(this));
    });
});

function updateAutocompleteWidgetState($elem, data) {
    var state = "none";
    var fk = "";

    if (!$.isEmptyObject(data)) {
        state = data.state;
        if (data.fk)
            fk = data.fk;
    }

    $elem.attr('data-ac-state', state);

    // update change-link
    $elem.siblings(".autocomplete-related-widget-wrapper-link").each(function() {
        $link = $(this);
        if ($link.attr('data-ac-href')) {
            var href = "";
            if (fk)
                href = $link.attr('data-ac-href');
            if (href)
                href = href.replace("__fk__", fk);
            $link.attr("href", href);
        }
    });
}

function verifyAutocompleteField($elem) {
    var modelid = $elem.attr('data-ac-id');
    $.getJSON(
        $elem.attr('data-ac-json-url'),
        { term: $elem.val(), id: modelid },
        function(data) { updateAutocompleteWidgetState($elem, data); }
    );
}