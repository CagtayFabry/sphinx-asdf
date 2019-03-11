function onClick(link) {
    current = $('.tab-pane.fade.in.active')[0];

    if ($(link).hasClass('anyof-previous')) {
        prev = $(current).prev();
        if ($(prev).hasClass('tab-pane')) {
            $(current).removeClass('in active');
            $(prev).addClass('in active');
        }
    }
    else if ($(link).hasClass('anyof-next')) {
        next = $(current).next();
        if ($(next).hasClass('tab-pane')) {
            $(current).removeClass('in active');
            $(next).addClass('in active');
        }
    }
    else {
        $(current).removeClass('in active');
        id = link.href.split('#')[1];
        active = document.getElementById(id);
        $(active).addClass('in active');
    }
}
