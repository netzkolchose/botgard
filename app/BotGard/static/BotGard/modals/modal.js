document.addEventListener('DOMContentLoaded', function() {
    const $ = window.jQuery;

    $('a[data-modal], button[data-modal]').on('click', function(e) {
        e.preventDefault();
        const target = $(this).data('modal');
        $('div[data-modal="'+target+'"]').toggleClass('open');
    });

    $('[data-modal] a.close').on('click', function(e) {
        e.preventDefault();
        $(this).closest('[data-modal]').removeClass('open');
    });
});
