document.addEventListener('DOMContentLoaded', function () {
    const $ = window.jQuery;

    $('.css-dropdown')
        .on('mouseenter touchend', function (e) {
            const $this = $(this);
            const ajaxPull = $this.data('ajax-url');
            if (ajaxPull) {
                $this.addClass('loading');
                $.get(ajaxPull).success(function() {
                   $('.css-dropdown-content', this).append(data);
                   $this.data('ajax-url', false);
                   $this.removeClass('loading');
                });
            }
            if (!$this.hasClass('open')) {
                $('.css-dropdown.open').removeClass('open');
                $this.addClass('open');
                if (e.originalEvent.target.nodeName != 'A') {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
            // position fixed dropdown list directly below the dropdown container
            var ofs = $this.offset();
            $('.css-dropdown-list', this).offset({left: ofs.left, top: ofs.top + 15.});
        })
        .on('mouseleave', function () {
            const $this = $(this);
            $this.removeClass('open');
        });

    // on body click
    $('body').on('touchend', function (e) {
        $('.css-dropdown.open').removeClass('open');
    });

}, false);
