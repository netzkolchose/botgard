


$(function() {

    const
        $field_id = $("input#id_id_name"),
        $field_format = $("select#id_format");

    // make sure we are on the change-form page
    if (!$field_id.length)
        return;

    const format_to_content_type = {
        "svg": "application/svg",
        "csv": "text/csv",
    };

    let current_format = $field_format.val();
    $field_format.on("change", function() {
        current_format = $field_format.val();
    });

    const $editor = $(".field-svg_markup textarea");
    const editor = CodeMirror.fromTextArea(
        $editor[0],
        {
            lineNumbers: true
        }
    );
    // DEBUGGING
    //window.editor = editor;

    $("#import-button").on("click", function() {
        $("#import-file").click();
    });

    $("#import-file").on("change", function() {
        const files = $('#import-file')[0].files;
        if (files[0]) {

            // load file contents into editor
            const reader = new FileReader();
            reader.onload = function() {
                editor.getDoc().setValue(reader.result);
            };
            reader.readAsText(files[0]);

            // set default label identifier from filename
            if ($field_id && !$field_id.val()) {
                const fn = files[0].name;
                if (fn) {
                    $field_id.val(fn.split(".")[0]);
                }
            }
        }
    });

    /** Store the contents of the markup editor to a file */
    $("#export-button").on("click", function() {
        // from https://robkendal.co.uk/blog/2020-04-17-saving-text-to-client-side-file-using-vanilla-js

        const content = editor.getDoc().getValue();
        const content_type = format_to_content_type[current_format];
        const filename = $field_id.val()
            ? `${$field_id.val()}.${current_format}`
            : `export.${current_format}`;

        const a = document.createElement('a');
        const file = new Blob([content], {type: content_type});

        a.href = URL.createObjectURL(file);
        a.download = filename;
        a.click();

        URL.revokeObjectURL(a.href);
    });

    renderExample();
});



function renderExample() {
    const url = $('#svg-example').attr("data-url");
    if (!url)
        return;

    $.ajax({
        url: url,
    }).done(function(data) {
        $("#svg-example").html(data);
    });
}