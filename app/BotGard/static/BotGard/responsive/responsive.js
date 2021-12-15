

document.addEventListener('DOMContentLoaded', function() {
    const $ = window.jQuery;


    // filter-toggle:
    const changelist_filters_select = "#changelist-filter";
    $(changelist_filters_select + ' h2').on('click', function(e){
        const $this = $(this);
        $(changelist_filters_select).toggleClass('open');
    });


}, false);
