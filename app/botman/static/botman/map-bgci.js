window.addEventListener("DOMContentLoaded", () => {

    const main_elem = document.querySelector(".garden-mapping");
    const post_url = main_elem.getAttribute("data-url");
    const error_text = main_elem.getAttribute("data-error-text");

    for (const elem of document.querySelectorAll(".bgci-garden")) {
        elem.onclick = () => {
            const garden_pk = elem.getAttribute("data-garden-pk");
            const bgci_id = elem.getAttribute("data-bgci-id");
            const csrf_token = document.querySelector(
                '.garden-mapping input[name="csrfmiddlewaretoken"]'
            ).value;
            fetch(`${post_url}?pk=${garden_pk}&id=${bgci_id}`, {
                "method": "POST",
                "headers": {
                    "X-CSRFToken": csrf_token,
                }
            })
                .then(response => {
                    if (response.status >= 400) {
                        window.alert(error_text);
                    } else {
                        const garden_elem = document.querySelector(`.garden-row[data-garden-pk="${garden_pk}"]`);
                        garden_elem.style.display = "none";
                    }
                })
                .catch(() => {
                    window.alert(error_text);
                });
        }
    }
});