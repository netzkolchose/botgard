/**
 * Created by stephan on 26/11/2016.
 */

// return-key on filter-input
$(function () {

    // build the pseudo-form and submit
    function build_submit_form ($form) {
        var $fields = $form.find('.filter-form-element');
        var $newForm = django.jQuery('<form>', {
            'action': ''
        });
        $fields.each(function () {
            if (!($(this).val() === "")) {
                $newForm.append($("<input>").val($(this).val()).attr('name', $(this).attr('name')));
            }
        });
        $newForm.css('display', 'none').appendTo('body');
        $newForm.submit();
    }

    // handler for all iterable fields
    $('.filter-form-wrapper').each(function () {
        var $this = $(this);

        // attach handler to all enter-presses on fields
        $this.find('.filter-form-element').on('keypress', function (e) {
            if (e.keyCode === 13) {
                e.preventDefault();
                build_submit_form($(this).closest('form'));
            }
        });

        // for selects also register a handler for change
        $this.find('select.filter-form-element').on('change', function (e) {
            build_submit_form($(this).closest('form'));
        });

        // reset button handler
        $this.find('button.filter-form-reset').on('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            $this.find('.filter-form-element').val('');
            build_submit_form($(this).closest('form'))
        });

        // ajax auto-complete
        /*$this.find('input.filter-form-element').autocomplete({
            delay: 200,
			minLength: 2,
            source: function(request, response) {
                modelid = $(this.element).attr('id')
                //console.log($(this.element), "|", request);
                if (modelid) {
                    $.getJSON(
                        "/ajax/model/fieldvalues.json",
                        { term: request.term, id: modelid },
                        function(data) { if (data) response(data.items); }
                    );
                }
            }
        });*/
    });

    function install_csv_export_warning() {
        $(".csv-export-button").on("click", function(event) {
            var $elem = $(event.target);
            var num_items = parseInt($elem.data("num-items"));
            var num_items_per_sec = parseInt($elem.data("num-items-per-sec"));
            var time_it_takes = Math.round(num_items / Math.max(1, num_items_per_sec));
            if (time_it_takes > 5) {
                var text = $elem.data("confirmation-text");
                text = text.replace("<sec>", time_it_takes);
                if (!confirm(text)) {
                    event.preventDefault();
                }
            }
        });

    }

    /** hook to input focus events and save name of focused input as hidden form field */
    function hook_search_focus_recall() {
        $("#changelist-form input").on("focus", function(e) {
            const input_name = e.target.name;
            if (input_name) {
                const $form = $("#changelist-form");
                if (!$form.find('input[name="_focus_input"]').length)
                    $form.append($(
                        `<input class="filter-form-element" name="_focus_input" type="hidden" value="${input_name}">`
                    ));
                else
                    $form.find('input[name="_focus_input"]').val(input_name);
            }
        });
    }

    /** set previous input focus if known */
    function recall_search_focus() {
        const $elem = $('#changelist-form input[name="_focus_input"]');
        if ($elem && $elem.length) {
            const input_name = $elem.val();
            const $input = $(`#changelist-form input[name="${input_name}"]`);
            $input.focus();
        }
    }

    // exclude our custom filter-fields from django's change-form submit handler, if form is submitted
    $('#changelist-form').on('submit', function (e) {
        const
            form  = e.originalEvent.target,
            form_data = new FormData(form),
            action = form_data.get("action"),
            is_save_event = e.originalEvent?.submitter?.getAttribute("name") === "_save";

        if (is_save_event || !action?.length || !action.startsWith("label_")) {
            $(this).find('.filter-form-element').attr('disabled', 'disabled');
        }
    });

    // add confirmations for labels with unchecked nomenclatures
    $('.label-link.nomenclature-unchecked').on("click", function(event) {
        if (!confirm(event.target.getAttribute("data-confirm-text"))) {
            event.preventDefault();
        }
    });

    install_csv_export_warning();
    recall_search_focus();
    hook_search_focus_recall();
});

$(document).ready(function() {
    /* put the custom properties of all type inlines into one flex-box */
    function sort_custom_properties() {
        const fieldset = document.querySelector("fieldset.custom-properties-fieldset");
        if (!fieldset) {
            return;
        }

        const prop_divs = [];
        const error_lis = [];
        fieldset.querySelectorAll("div.form-row").forEach(function(formrow) {
            let found_some = false;
            formrow.querySelectorAll("div.custom-property").forEach(function(propdiv) {
                prop_divs.push(propdiv);
                found_some = true;
            })
            /* Note: if we don't find them, we are probably in a read-only view,
                which is messed up anyway (right now), so keep it as it is
             */
            if (found_some) {
                const errorlist = formrow.querySelector("ul.errorlist");
                if (errorlist) {
                    errorlist.querySelectorAll("li").forEach(function (li) {
                        error_lis.push(li);
                    });
                }
                formrow.parentElement.removeChild(formrow);
            }
        });

        prop_divs.sort(function(a, b) {
            const o1 = parseInt(a.getAttribute("data-property-order"));
            const o2 = parseInt(b.getAttribute("data-property-order"));
            return o1 - o2;
        });

        const formrow = document.createElement("div");
        formrow.classList.add("form-row");
        if (error_lis.length) {
            const errorlist = document.createElement("ul");
            formrow.appendChild(errorlist);
            errorlist.classList.add("errorlist");
            for (const li of error_lis) {
                errorlist.appendChild(li);
            }
        }
        const flex = document.createElement("div");
        formrow.appendChild(flex);
        flex.classList.add("custom-properties");
        for (const propdiv of prop_divs) {
            flex.appendChild(propdiv);
        }
        fieldset.appendChild(formrow);
    }

    sort_custom_properties();
});

