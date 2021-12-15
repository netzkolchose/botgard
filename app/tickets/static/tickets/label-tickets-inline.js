/**
 * Mass actions for LaserGravurTicket attached individuals
 */
$(function() {

    let tr;
    try {
        tr = JSON.parse($(".bg-translations").attr("data-tr"));
    }
    catch (e) {
        // If we don't find bg-translations, we're probably one the wrong page
        return;
    }

    function add_mass_actions() {
        const $container = $("#etikett_individual_set-group");
        if (!$container.length) {
            console.log("ERROR: Did not find container for attached individuals");
            return;
        }

        const $header = $container.find("fieldset th.column-etikett_type");
        const $newheader = $("<div>");
        $newheader.append($("<span>").text($header.text()));
        $newheader.append($("<button>")
            .text(tr["change_many"])
            .attr("id", "label-type-mass-action-button")
            .on("click", show_mass_actions)
        );
        $newheader.append($("<div>").attr("id", "label-type-mass-action-container"));
        $header.html($newheader);
    }

    function hide_mass_actions() {
        $("#label-type-mass-action-button").show();
        const $container = $("#label-type-mass-action-container");
        $container.empty();
        enable_save_buttons(true);
    }

    function enable_save_buttons(enable) {
        $('.submit-row input[name="_save"]').prop( "disabled", !!!enable);
        $('.submit-row input[name="_continue"]').prop( "disabled", !!!enable);
        $('.submit-row input[name="_addanother"]').prop( "disabled", !!!enable);
    }

    function show_mass_actions(e) {
        e.preventDefault();
        e.stopPropagation();

        enable_save_buttons(false);

        $("#label-type-mass-action-button").hide();
        const $container = $("#label-type-mass-action-container");

        const $select = $("#id_etikett_individual_set-0-etikett_type")
            .clone()
            .attr("id", "mass-action-label-type")
        ;
        const $actions = $("<div>");

        $actions
            .append($("<div>").append($select))
            .append($("<button>").text(tr["change_all"]).on("click", function (e) { handle_action_button(e, "all"); }))
            .append($("<button>").text(tr["change_unattributes"]).on("click", function (e) { handle_action_button(e, "empty"); }))
            .append($("<button>").text(tr["cancel"]).on("click", function (e) { handle_action_button(e, "cancel"); }));
        $container.append($actions);
        //hide_mass_actions();
    }

    function handle_action_button(e, action) {
        e.preventDefault();
        e.stopPropagation();

        if (action === "all" || action === "empty") {
            const new_select_value = $("#mass-action-label-type").val();
            $("tr.dynamic-etikett_individual_set").each(function(i, row) {
                const
                    $row = $(row),
                    individual = $row.find("td.field-individual").find("input").val(),
                    $select = $row.find("td.field-etikett_type").find("select"),
                    select_value = $select.val();

                if (!individual || !individual.length)
                    return;

                if (action === "empty" && (select_value && select_value.length))
                    return;

                $select.val(new_select_value);
            });
            //$selects.val(value);
        }
        hide_mass_actions();
    }

    add_mass_actions();
});