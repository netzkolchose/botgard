document.addEventListener('DOMContentLoaded', function () {
        const $ = window.jQuery;


        const Notes = function(elem) {
            this.elem = $(elem);
            this.list = $('.element-list', this.elem);
            this._csrf_token = $('[name="csrfmiddlewaretoken"]', this.elem).val();
            this._new_note_url = $('[data-new-item-url]', this.elem).data('new-item-url');
            this._current_page_url = this.elem.data('current-page-url');
            this.init_note = function(note) {
                const note_text = $('.text[contenteditable="True"]', note);
                const note_edit_url = $('.text[data-change-url]', note).data('change-url');

                const save = $.debounce(250, function(text, node, original_event){
                    $.ajax({
                        type: 'POST',
                        url: note_edit_url,
                        data: {
                            'csrfmiddlewaretoken': this._csrf_token,
                            'text': text
                        }
                    }).done(function(data){
                        // in case of a blur write back the server response as it contains
                        // the cleaned markup
                        if (original_event.type == "blur") {
                            note_text.html(data);
                        }
                    })
                }.bind(this));

                note_text.on('blur keyup paste input', function(e) {
                    var new_text = note_text.html();
                    save(new_text, note_text, e);
                }.bind(this));

                const delete_button = $('.tool-button.delete', note);
                const delete_confirm_message = delete_button.data('confirm-message');
                delete_button.on('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    const url = delete_button.attr('href');
                    if (confirm(delete_confirm_message)) {
                        $.ajax({
                            type: 'POST',
                            url: url,
                            data: {
                                'csrfmiddlewaretoken': this._csrf_token
                            }
                        }).done(function(data){
                            $(note).remove();
                        });
                    } else {
                    }
                }.bind(this));

                const publish_button = $('.tool-button.public-on', note);
                const publish_confirm_message = publish_button.data('confirm-message');
                publish_button.on('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    const url = publish_button.attr('href');
                    if (confirm(publish_confirm_message)) {
                        $.ajax({
                            type: 'POST',
                            url: url,
                            data: {
                                'csrfmiddlewaretoken': this._csrf_token
                            }
                        }).done(function(data){
                            $(note).attr('data-is-public', 'True');
                        });
                    } else {
                    }
                }.bind(this));


                const unpublish_button = $('.tool-button.public-off', note);
                const unpublish_confirm_message = unpublish_button.data('confirm-message');
                unpublish_button.on('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    const url = unpublish_button.attr('href');
                    if (confirm(unpublish_confirm_message)) {
                        $.ajax({
                            type: 'POST',
                            url: url,
                            data: {
                                'csrfmiddlewaretoken': this._csrf_token
                            }
                        }).done(function(data){
                            $(note).attr('data-is-public', 'False');
                        });
                    } else {
                    }
                }.bind(this))


            };

            this.new_note = function() {
                $.ajax({
                    type: 'POST',
                    url: this._new_note_url,
                    data: {
                        'url': this._current_page_url,
                        'csrfmiddlewaretoken': this._csrf_token
                    }
                    }).done(function(data){
                        this.list.prepend($(data));
                        const new_note = this.list.find('li')[0];
                        $('[contenteditable]', new_note).focus();
                        this.init_note(new_note);
                }.bind(this));
            };

            this._attachEvents = function() {
                $('.add-element', this.elem).on('click', this.new_note.bind(this));
                $('.list-element.note', this.elem).each(function(i, e){
                    this.init_note(e)
                }.bind(this));
            };

            this._attachEvents();

            return this
        };

        const Bookmarks = function (elem) {
            this.elem = $(elem);
            this.triggersAdd = $('button.add-element', this.elem);
            this.templateAddEdit = $('template.add-edit-form', this.elem)[0];
            this.list = $('.element-list', this.elem);

            this._is_adding = false;

            this._makeSortable = function(elem) {
                if (elem) {} else elem = this.list;
                $(elem).sortable('destroy');
                $(elem).sortable({
                    items: ':not(.empty-list)',
                    forcePlaceholderSize: true
                }).bind('sortupdate', function(e, ui) {
                    var update_data = [];
                    $('li:not(.empty-list)', this.list).each(function(i,e) {
                        update_data.push({
                            'elem': $(e).data('element-key'),
                            'order': i + 1
                        })
                    });
                    $.ajax({
                        type: 'POST',
                        url: this.list.data('order-update-url'),
                        data: {
                                'elements': JSON.stringify(update_data),
                                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]', this.elem).val()
                            }
                    })
                }.bind(this))
            };


            this.saveElement = function (form) {
                this._is_adding = false;

                return $.ajax({
                    type: form.attr('method'),
                    url: form.attr('action'),
                    data: form.serialize() // serializes the form's elements.
                });
            };

            this.deleteBookmark = function (e) {
                e.preventDefault();
                const delete_item = $(e.currentTarget).closest('li');
                const delete_url = $(e.currentTarget).attr('href');
                const delete_bookmark_message = $(e.currentTarget).data('confirm-message');
                if (confirm(delete_bookmark_message)) {
                    $.ajax(delete_url, {}).done(function (data) {
                        delete_item.remove();
                    })
                } else {}
            };

            this._validateForm = function (form) {
                const titlefield = $('input[name="title"]');
                const title = titlefield.val();

                if (titlefield && title.length > 0) return true;

                return false
            };

            this._addElement = function () {
                if (!this._is_adding) {
                    this._is_adding = true;

                    // render the template
                    const new_bookmark_form = this.templateAddEdit.content.querySelector('li');
                    const title_input = new_bookmark_form.querySelector('[name="title"]');
                    title_input.value = document.title.split('|')[0].trim();

                    this.list.prepend(document.importNode(new_bookmark_form, true));


                    // prepare for user-edit
                    const current_title_input = $('input[name="title"]', this.list);
                    const current_submit_button = $('button[type="submit"]', this.list);
                    const current_cancel_button = $('button[type="reset"]', this.list);
                    const current_new_element_form = $('form', this.list);

                    current_title_input.focus();

                    // attach events to buttons
                    current_new_element_form.on('reset', function (e) {
                        current_new_element_form.closest('li').remove();
                        this._is_adding = false;
                    }.bind(this));

                    current_new_element_form.on('submit', function (e) {
                        e.preventDefault();
                        e.stopPropagation();

                        // validate inputs
                        if (this._validateForm(current_new_element_form)) {
                            this.saveElement(current_new_element_form).then(
                                function(data) {
                                    current_new_element_form.closest('li').remove();
                                    const new_item = $(data);
                                    this.list.prepend(new_item);
                                    $('.tool-button.delete',new_item).on('click', this.deleteBookmark.bind(this));
                                    this._makeSortable()
                                }.bind(this))

                        } else {
                            current_title_input.focus();
                            current_title_input.addClass('error');
                            window.setTimeout(function(){
                                current_title_input.removeClass('error');
                            }, 500)
                        }
                    }.bind(this));
                }
            };

            this._attachEvents = function () {
                this.triggersAdd.on('click', this._addElement.bind(this));
                $('.tool-button.delete', this.elem).on('click', this.deleteBookmark.bind(this));
                this._makeSortable();
            };

            this._attachEvents();
        };


        const SideBar = function (elem, trigger) {

            this.elem = $(elem);
            this.triggers = $(trigger);
            this._is_visible = false;


            this.show = function () {
                this.elem.addClass('open');
                $('body').addClass('side_bar_open');
                Cookies.set('botgardjs-sidebar-visible', 'true');
                this._is_visible = true;
            };

            this.hide = function () {
                this.elem.removeClass('open');
                $('body').removeClass('side_bar_open');
                this._is_visible = false;
                Cookies.set('botgardjs-sidebar-visible', 'false');
            };

            this.toggle = function (e) {
                if (this._is_visible) this.hide();
                else this.show();
            };


            this._conditional_hide = function(){
                if ($(window).width() < 1280) {
                    this.hide();
                }
            };

            this._bind_events = function () {
                this.triggers.on('click', this.toggle.bind(this));
                $(window).on('resize', this._conditional_hide.bind(this));
                $('body').on('click', this._conditional_hide.bind(this));
                this.elem.on('click', function(e){
                    e.stopPropagation();
                });
            };


            this._bind_events();

            this.bookmarks = new Bookmarks($('.bookmarks', this.elem));
            this.notes = new Notes($('.notes', this.elem));

            if (Cookies.get('botgardjs-sidebar-visible') == 'true') {
                this.show();
            };

            return this;
        };

        const _sidebar = new SideBar('#sidebar', '#sidebar .trigger');

    }
);