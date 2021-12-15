$(function() {

    const $container = $(".seed-catalog-container");
    const add_seed_url = $container.attr("data-add-url");
    const remove_seed_url = $container.attr("data-remove-url");

    function hook_add_remove_click() {
        $('a[data-catalog]').on("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            const
                catalog_id = e.target.getAttribute("data-catalog"),
                seed_id = e.target.getAttribute("data-seed"),
                action = e.target.getAttribute("data-action");

            exec_seed_action(action, catalog_id, seed_id);
        });
    }

    function exec_seed_action(action, catalog_id, seed_id) {
        let url;
        switch (action) {
            case "add": url = add_seed_url; break;
            case "remove": url = remove_seed_url; break;
            default: alert("Something went wrong"); return;
        }

        /* replace '0' with seed_id and '1' with catalog_id.
            Must be careful because we replace numbers with other numbers!
         */
        url = url.replace("0", "X").replace("1", catalog_id).replace("X", seed_id);

        window
            .fetch(
                new Request(url),
                {
                    "method": "GET",  // TODO: really should be PATCH or POST!
                }
            )
            .then(function(response) {
                if (response.status !== 200)
                    throw "Sorry, the catalog could not be edited";
                return response.text();
            })
            .then(function(text) {
                $container.html(text);
                hook_add_remove_click();
            })
            .catch(function(error) {
                alert(`${error}`);
            })
        ;
    }

    hook_add_remove_click();
});