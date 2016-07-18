/**
 * Created by juanjo on 04/046/16.
 * This file requires moment.js (http://momentjs.com/). Thanks to Iskren Ivov Chernev for his pretty work.
 * This file also make use of selectText function designed by Tom Oakley:
 * http://stackoverflow.com/questions/12243898/how-to-select-all-text-in-contenteditable-div
 * This file also make use of placeCaretAtEnd function designed by Tim Down:
 * http://stackoverflow.com/users/96100/tim-down
 */


var GAUSSPROJECT = {
    version: "1.0",
    need_to_be_updated: false  //if true: bars, links and columns have to be re-calculated (redrawn)
};

GAUSSPROJECT.glink_dependencies = {
    FS: 'Finish to Start',
    FF: 'Finish to Finish',
    SS: 'Start to Start',
    SF: 'Start to Finish'
};

GAUSSPROJECT.display_glinks = true;

GAUSSPROJECT.selected_gcolumn = null;
GAUSSPROJECT.insert_move_gcolumn_at = 'right'; //It can be 'right' (default) or 'left'

GAUSSPROJECT.initial_value = 0; //Used to detect changes
GAUSSPROJECT.final_value = 0;

GAUSSPROJECT.gcolumn_types = {
    estimate_time_days: 'Estimate time (d)',
    early_start_date: 'Early start (date)',
    early_start_datetime: 'Early start (datetime)',
    last_finish_date: 'Last Finish (date)',
    last_finish_datetime: 'Last Finish (datetime)',
    gtask_name: 'Task name',
    total_float: 'Total float',
    free_float: 'Free float',
    optimistic_time: 'Optimistic time (d)',
    likely_time: 'Likely time (d)',
    pessimistic_time: 'Pessimistic time (d)'
};

GAUSSPROJECT.parse_data = function (gprojects, gbaselines, gtasks, glinks, gcolumns) {
    GAUSSPROJECT.gprojects = gprojects;
    GAUSSPROJECT.gbaselines = gbaselines;
    GAUSSPROJECT.gtasks = gtasks;
    GAUSSPROJECT.gcolumns = gcolumns;
    GAUSSPROJECT.glinks = glinks;

    GAUSSPROJECT.parse_gprojects(GAUSSPROJECT.gprojects);
    GAUSSPROJECT.parse_gbaselines(GAUSSPROJECT.gbaselines);
    GAUSSPROJECT.parse_gtasks(GAUSSPROJECT.gtasks);
    GAUSSPROJECT.init_gantt();

};

GAUSSPROJECT.init_gantt = function () {
    GAUSSPROJECT.gproject = GAUSSPROJECT.gprojects[0];

    GAUSSPROJECT.gproject.active_gbaseline.init_left_pane();
    GAUSSPROJECT.gproject.active_gbaseline.init_right_pane();
    var gtasks = GAUSSPROJECT.gproject.active_gbaseline.gtasks;
    var gtasks_length = gtasks.length;
    for (var i = 0; i < gtasks_length; i++) {
        GAUSSPROJECT.draw_gtask(gtasks[i]);
    }
    GAUSSPROJECT.draw_glinks(GAUSSPROJECT.glinks);
};

GAUSSPROJECT.parse_gprojects = function (gprojects) {
    $.each(gprojects, function (index, gproject) {
        Object.defineProperties(gproject, {
            "config": {
                get: function () {
                    return {margin_task: 2, task_height: 22, line_width: 2, link_wrapper_width: 11};
                }, configurable: true
            },
            "gbaselines": {
                get: function () {
                    var gbaselines = [];
                    $.each(GAUSSPROJECT.gbaselines, function (index, gbaseline) {
                        if (gproject.pk == gbaseline.fields.gproject) {
                            gbaselines.push(gbaseline);
                        }
                    });
                    return gbaselines;
                }, configurable: true
            },
            "active_gbaseline": {
                get: function () {
                    var active_gbaseline = null;
                    $.each(GAUSSPROJECT.gbaselines, function (index, gbaseline) {
                        if (gbaseline.fields.active && gproject.pk == gbaseline.fields.gproject) {
                            active_gbaseline = gbaseline;
                        }
                    });
                    return active_gbaseline;
                }, configurable: true
            }
        });
    });
};

// Functions around the Gantt chart

GAUSSPROJECT.update_server_async = function (obj) {
    $.ajax({
        type: 'POST',
        url: "/gantt_ajax/",
        data: obj,
        dataType: 'json'
    });
};

GAUSSPROJECT.update_server = function (obj) {
    var idata = 'empty return';
    $.ajax({
        type: 'POST',
        url: "/gantt_ajax/",
        data: obj,
        dataType: 'json', //html
        async: false,
        success: function (result) {
            idata = result;
        }
    });
    return idata;
};
GAUSSPROJECT.rewrite_cells = function () {
    var start = new Date().getTime();
    var changed_gtasks =[];
    //var k=10;
    for (var k = 0; k < GAUSSPROJECT.gtasks.length; k++) {
        var gtask = GAUSSPROJECT.gtasks[k];
        var diff1 = String(gtask.estimate_time) != String(gtask.old_estimate_time);  //seconds
        var diff2 = String(gtask.early_start) != String(gtask.old_early_start); //milliseconds
        //var diff3 = String(gtask.last_finish) != String(gtask.old_last_finish); //milliseconds
        var diff3 = false;
        if (diff1 || diff2 || diff3) {
            console.log('Actividad: ', gtask.fields.name);
            console.log('estimate_time: ', String(gtask.estimate_time), String(gtask.old_estimate_time));
            console.log('early_start: ', String(gtask.early_start), String(gtask.old_early_start));
            //console.log('last_finish: ', String(gtask.last_finish), String(gtask.old_last_finish));
            changed_gtasks.push(gtask);
            gtask.old_estimate_time = gtask.estimate_time;
            gtask.old_early_start = gtask.early_start;
            gtask.old_last_finish = gtask.last_finish;
            for (var i = 0; i < GAUSSPROJECT.gcolumns.length; i++) {
                var col = GAUSSPROJECT.gcolumns[i];
                console.log(col.fields.content);
                var content = col.fields.content;
                $('#col' + col.pk + '_' + gtask.pk).html(html_column(content, gtask));
            }
        }
    }
    console.log('Cambiadas ', changed_gtasks.length, ' tareas');
    GAUSSPROJECT.redraw_gtasks();
    GAUSSPROJECT.redraw_glinks();
    var end = new Date().getTime();
    var time = end - start;
    console.log('Execution time: ' + time);
};
GAUSSPROJECT.update_cell = function (gtaskpk, gcolpk, value) {
    var $dom_gcol = $('#col' + gcolpk + '_' + gtaskpk);
    var gtask = queryget(GAUSSPROJECT.gtasks, gtaskpk);
    var gcol = queryget(GAUSSPROJECT.gcolumns, gcolpk);
    var content = gcol.fields.content;

    if (content == 'gtask_name') {
        if (gtask.fields.name != value) {
            GAUSSPROJECT.update_server({action: 'update_gtask_name', value: value, id: gtaskpk});
            gtask.fields.name = value;
        }
        return value;
    }
    else if (content == 'estimate_time_days') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        var mo = moment.duration(val, 'days');
        var diff = Math.abs(gtask.estimate_time.asSeconds() - mo.asSeconds()) > 100;
        if (diff) {
            gtask.fields.optimistic_time = mo;
            gtask.fields.likely_time = mo;
            gtask.fields.pessimistic_time = mo;
            GAUSSPROJECT.update_server_async({action: 'update_estimate_time_days', value: val, id: gtaskpk});
            GAUSSPROJECT.rewrite_cells();
        }
        return true;
    }
    else if (content == 'optimistic_time') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        var mo = moment.duration(val, 'days');
        gtask.fields.optimistic_time = mo;
        GAUSSPROJECT.update_server({action: 'update_optimistic_time', value: val, id: gtaskpk});
        for (var i = 0; i < GAUSSPROJECT.gcolumns.length; i++) {
            var col = GAUSSPROJECT.gcolumns[i];
            var col_content = col.fields.content;
            if (col_content == 'estimate_time_days') {
                $('#col' + col.pk + '_' + gtaskpk).html(roundToTwo(gtask.estimate_time.asDays()) + ' days');
            }
        }
        $dom_gcol.html(roundToTwo(gtask.fields.optimistic_time.asDays()) + ' days');
        GAUSSPROJECT.redraw_gtask(gtask);
        GAUSSPROJECT.redraw_glinks();
    }
    else if (content == 'likely_time') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        var mo = moment.duration(val, 'days');
        gtask.fields.likely_time = mo;
        GAUSSPROJECT.update_server({action: 'update_likely_time', value: val, id: gtaskpk});
        for (var i = 0; i < GAUSSPROJECT.gcolumns.length; i++) {
            var col = GAUSSPROJECT.gcolumns[i];
            var col_content = col.fields.content;
            if (col_content == 'estimate_time_days') {
                $('#col' + col.pk + '_' + gtaskpk).html(roundToTwo(gtask.estimate_time.asDays()) + ' days');
            }
        }
        $dom_gcol.html(roundToTwo(gtask.fields.likely_time.asDays()) + ' days');
        GAUSSPROJECT.redraw_gtask(gtask);
        GAUSSPROJECT.redraw_glinks();
    }
    else if (content == 'pessimistic_time') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        var mo = moment.duration(val, 'days');
        gtask.fields.pessimistic_time = mo;
        GAUSSPROJECT.update_server({action: 'update_pessimistic_time', value: val, id: gtaskpk});
        for (var i = 0; i < GAUSSPROJECT.gcolumns.length; i++) {
            var col = GAUSSPROJECT.gcolumns[i];
            var col_content = col.fields.content;
            if (col_content == 'estimate_time_days') {
                $('#col' + col.pk + '_' + gtaskpk).html(roundToTwo(gtask.estimate_time.asDays()) + ' days');
            }
        }
        $dom_gcol.html(roundToTwo(gtask.fields.pessimistic_time.asDays()) + ' days');
        GAUSSPROJECT.redraw_gtask(gtask);
        GAUSSPROJECT.redraw_glinks();
    }


    else if (content == 'priority') {
        return gtask.fields.priority;
    }
    else if (content == 'restriction') {
        return gtask.fields.restriction;
    }
    else if (content == 'restriction_date') {
        return gtask.fields.restriction_date;
    }
    else if (content == 'notes') {
        return gtask.fields.notes;
    }
    else if (content == 'gtask_parent') {
        return gtask.fields.gtask_parent;
    }
    else if (content == 'display_subtasks') {
        return gtask.fields.display_subtasks;
    }
    else if (content == 'datetimeafadfaf') {
        $div_col1.html(gtask[col.fields.content].format("DD/MM/YYYY, HH:mm"))
            .appendTo($div_row);
    } else if (content == 'dafafdadfate') {
        $div_col1.html(gtask[col.fields.content].format("DD/MM/YYYY"))
            .appendTo($div_row);
    } else if (content == 'asDaadfadfays') {
        $div_col1.html(gtask[col.fields.content].asDays())
            .appendTo($div_row);
    } else if (content == 'asDayadfas') {
        $div_col1.html(gtask[col.fields.content])
            .appendTo($div_row);
    }


    //if (gcol.fields.content == 'priority') {
    //    this.gtasks[pos].priority = new_data.priority;
    //}
    //if (gcol.fields.content == 'restriction') {
    //    this.gtasks[pos].restriction = new_data.restriction;
    //}
    //if (gcol.fields.content == 'restriction_date') {
    //    this.gtasks[pos].restriction_date = new_data.restriction_date;
    //}
    //if (gcol.fields.content == 'notes') {
    //    this.gtasks[pos].notes = new_data.notes;
    //}
    //if (gcol.fields.content == 'gtask_parent') {
    //    this.gtasks[pos].gtask_parent = new_data.gtask_parent;
    //}
    //if (gcol.fields.content == 'display_subtasks') {
    //    this.gtasks[pos].display_subtasks = new_data.display_subtasks;
    //}

};

//GAUSSPROJECT.update_gtask = function (new_data) {
//    if (new_data.content == 'gtask_name') {
//        var gtask = queryget(GAUSSPROJECT.gtasks, new_data.id);
//        gtask.fields.name = new_data.value;
//        GAUSSPROJECT.update_server({action: 'update_gtask_name', value: new_data.value, id: new_data.id});
//        return gtask;
//    }
//    if (new_data.content == 'estimate_time_days') {
//        var gtask = queryget(GAUSSPROJECT.gtasks, new_data.id);
//        var val = parseFloat(new_data.value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
//        var mo = moment.duration(val, 'days');
//        gtask.fields.optimistic_time = mo;
//        gtask.fields.likely_time = mo;
//        gtask.fields.pessimistic_time = mo;
//        GAUSSPROJECT.update_server({action: 'update_estimate_time_days', value: val, id: new_data.id});
//        return gtask;
//    }
//    if (new_data.content == 'optimistic_time') {
//        this.gtasks[pos].optimistic_time = new_data.optimistic_time;
//        this.update_screen_data(this.gtasks);
//    }
//    if (new_data.content == 'likely_time') {
//        this.gtasks[pos].likely_time = new_data.likely_time;
//        this.update_screen_data(this.gtasks);
//    }
//    if (new_data.content == 'pessimistic_time') {
//        this.gtasks[pos].pessimistic_time = new_data.pessimistic_time;
//        this.update_screen_data(this.gtasks);
//    }
//    if (new_data.content == 'priority') {
//        this.gtasks[pos].priority = new_data.priority;
//    }
//    if (new_data.content == 'restriction') {
//        this.gtasks[pos].restriction = new_data.restriction;
//    }
//    if (new_data.content == 'restriction_date') {
//        this.gtasks[pos].restriction_date = new_data.restriction_date;
//    }
//    if (new_data.content == 'notes') {
//        this.gtasks[pos].notes = new_data.notes;
//    }
//    if (new_data.content == 'gtask_parent') {
//        this.gtasks[pos].gtask_parent = new_data.gtask_parent;
//    }
//    if (new_data.content == 'display_subtasks') {
//        this.gtasks[pos].display_subtasks = new_data.display_subtasks;
//    }
//};

GAUSSPROJECT.add_task = function () {
    var gbaseline = GAUSSPROJECT.gproject.active_gbaseline.pk;
    var gtask = GAUSSPROJECT.update_server({action: 'add_task', id: gbaseline})[0];
    GAUSSPROJECT.gtasks.push(gtask);
    gtask = GAUSSPROJECT.gtasks[GAUSSPROJECT.gtasks.length - 1];
    GAUSSPROJECT.parse_gtasks([gtask]);
    GAUSSPROJECT.draw_gtask(gtask);
};

GAUSSPROJECT.remove_gtasks = function (list_gtask_pks) {
    $('.gantt_task_link').remove();
    for (var i = GAUSSPROJECT.glinks.length - 1; i > -1; i--) {
        var delete_glink = false;
        var glink = GAUSSPROJECT.glinks[i];
        for (var j = list_gtask_pks.length - 1; j > -1; j--) {
            if (glink.fields.successor == list_gtask_pks[j] || glink.fields.predecessor == list_gtask_pks[j]) {
                delete_glink = true;
            }
        }
        if (delete_glink) {
            var id = GAUSSPROJECT.glinks[i].pk;
            GAUSSPROJECT.glinks.splice(i, 1);
            GAUSSPROJECT.update_server({action: 'remove_glink', id: id});
        }
    }
    for (var i = GAUSSPROJECT.gtasks.length - 1; i > -1; i--) {
        var ss = GAUSSPROJECT.gtasks[i].successors;
        var gtask = GAUSSPROJECT.gtasks[i];
        for (var j = list_gtask_pks.length - 1; j > -1; j--) {
            if (gtask.pk == list_gtask_pks[j]) {

                $('#rowr' + gtask.fields.pos).remove();
                $('#rowl' + gtask.fields.pos).remove();
                var id = GAUSSPROJECT.gtasks[i].pk;

                GAUSSPROJECT.gtasks.splice(i, 1);
                GAUSSPROJECT.update_server({action: 'remove_gtask', id: id});
                for (var k = 0; k < ss.length; k++) {
                    GAUSSPROJECT.redraw_gtask(ss[k]);
                }
            }
        }
    }
    for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
        GAUSSPROJECT.redraw_gtask(GAUSSPROJECT.gtasks[i]);
    }
    GAUSSPROJECT.draw_glinks(GAUSSPROJECT.glinks);
};

GAUSSPROJECT.redraw_glinks = function () {
    $('.gantt_task_link').remove();
    GAUSSPROJECT.draw_glinks(GAUSSPROJECT.glinks);
};

GAUSSPROJECT.redraw_gtasks = function () {
    for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
        GAUSSPROJECT.redraw_gtask(GAUSSPROJECT.gtasks[i]);
    }
    GAUSSPROJECT.redraw_glinks();
};

GAUSSPROJECT.redraw_gtask = function (gtask) {
    // Redraw a gtask means redraw its successors as well:
    if (gtask.total_float == 0) {
        var class_type = 'gantt_gtask_bar_critical';
        $('#bar' + gtask.pk).removeClass('gantt_gtask_bar').addClass('gantt_gtask_bar_critical');
    } else {
        var class_type = 'gantt_gtask_bar';
        $('#bar' + gtask.pk).addClass('gantt_gtask_bar').removeClass('gantt_gtask_bar_critical');
    }
    var all_gtasks = gtask.all_successors;
    var all_gtasks_length = all_gtasks.length;
    for (var i = 0; i < all_gtasks_length; i++) {
        var actual_gtask = all_gtasks[i];
        var gll = parseInt(actual_gtask.left - 14);
        var glr = parseInt(actual_gtask.left + actual_gtask.width);
        $('#bar' + actual_gtask.pk)
            .css("margin-left", actual_gtask.left)
            .css("width", actual_gtask.width);
        $('#gll' + actual_gtask.pk).css("left", gll);
        $('#glr' + actual_gtask.pk).css("left", glr);
    }
};

GAUSSPROJECT.draw_gtask = function (gtask) {
    var pos_before = gtask.fields.pos - 1;
    var div_findit = false;
    do {
        if (pos_before < 0) {
            var $div_columns_before = $('#task_list-1');
            var $div_bars_before = $('#task_bars-1');
            div_findit = true;
        } else {
            if ($('#rowl' + pos_before).length > 0) {
                var $div_columns_before = $('#rowl' + pos_before);
                var $div_bars_before = $('#rowr' + pos_before);
                div_findit = true;
            }
            else {
                pos_before--;
            }
        }
    } while (div_findit == false);

    var $div_row = $("<div/>")
        .attr("class", 'row gtask_row col_side')
        .css("height", '28px')
        .css("margin-left", "0rem")
        .attr("data-id", gtask.pk)
        .attr("data-pos", gtask.fields.pos)
        .attr("data-columns", 'undone')
        .attr("id", "rowl" + gtask.fields.pos)
        .insertAfter($div_columns_before);
    var $div_check = $("<div/>")
        .attr("class", "gantt_list_column")
        .css("width", "20px")
        .css("resize", "none")
        .css("border", "none")
        .appendTo($div_row);
    var $check = $("<input/>")
        .attr("type", "checkbox")
        .attr("name", "gtasks")
        .attr("value", gtask.pk)
        .attr("class", "check_gtask")
        .attr("data-id", gtask.pk)
        .appendTo($div_check);
    GAUSSPROJECT.gcolumns.forEach(function (col, i) {
        var $div_col1 = $("<div/>")
            .attr("class", "gantt_list_column col" + col.pk)
            .attr("data-colpk", col.pk)
            .attr("data-id", gtask.pk)
            .attr("id", "col" + col.pk + '_' + gtask.pk)
            .attr("contenteditable", "true")
            .css("width", col.fields.width + "px")
            .css("text-align", col.fields.align)
            .html(html_column(col.fields.content, gtask))
            .appendTo($div_row);
        if (col.fields.content == 'gtask_name') {
            $div_col1.focus();
        }
    });

    var gll = parseInt(gtask.left - 14);
    var glr = parseInt(gtask.left + gtask.width);
    if (gtask.total_float == 0) {
        var class_type = 'gantt_gtask_bar_critical';
    } else {
        var class_type = 'gantt_gtask_bar';
    }
    var $div2 = $("<div/>")
        .attr("class", "gtask_row bar_side")
        .css("height", "28px")
        .attr("data-id", gtask.pk)
        .attr("data-pos", gtask.fields.pos)
        .attr("data-columns", 'undone')
        .attr("id", "rowr" + gtask.fields.pos)
        .insertAfter($($div_bars_before));
    var $div_bar = $("<div/>")
        .attr("class", class_type)
        .attr("data-id", gtask.pk)
        .attr("id", "bar" + gtask.pk)
        .css("margin-left", gtask.left)
        .css("width", gtask.width)
        .css("height", "90%")
        .appendTo($div2);
    var div_progress = $("<div/>")
        .attr("class", "gantt_gtask_progress")
        .attr("id", "bar" + gtask.pk)
        .css("width", gtask.width_progress)
        .css("max-width", gtask.width)
        .appendTo($div_bar);
    var div_name = $("<div/>")
        .css("position", "absolute")
        .css("top", 0)
        .css("left", 0)
        .css("z-index", 300)
        .html(gtask.fields.name)
        .appendTo($div_bar);
    var div_gll = $("<div/>")
        .attr("class", "gantt_link")
        .attr("id", "gll" + gtask.pk)
        .attr("data-id", gtask.pk)
        .css("left", gll)
        .appendTo($div2);
    var div_glr = $("<div/>")
        .attr("class", "gantt_link")
        .attr("id", "glr" + gtask.pk)
        .attr("data-id", gtask.pk)
        .css("left", glr)
        .appendTo($div2);
};

GAUSSPROJECT.parse_gbaselines = function (gbaselines) {
    $.each(gbaselines, function () {
        Object.defineProperties(this, {
            "config": {
                get: function () {
                    return {margin_task: 2, task_height: 22, line_width: 2, link_wrapper_width: 11};
                }, configurable: true
            },
            "gtasks": {
                get: function () {
                    var gb = this;
                    var found_gtasks = $.grep(GAUSSPROJECT.gtasks, function (gt) {
                        return gt.fields.gbaseline == gb.pk;
                    });
                    return found_gtasks;
                }, configurable: true
            },
            "left_side": {
                get: function () {
                    return 12 - parseInt(this.fields.columns);
                }, configurable: true
            },
            "right_side": {
                get: function () {
                    return parseInt(this.fields.columns);
                }, configurable: true
            },
            "start_date": {
                get: function () {
                    return moment(this.fields.start_date);
                }, configurable: true
            },
            "end_date": {
                get: function () {
                    var end_dates = [moment(this.fields.start_date)];
                    $.each(GAUSSPROJECT.gtasks, function () {
                        end_dates.push(this.early_start.add(this.estimate_time));
                    });
                    return moment.max(end_dates);
                }, configurable: true
            },
            "gproject": {
                get: function () {
                    for (var i = 0; i < GAUSSPROJECT.gprojects.length; i++) {
                        if (GAUSSPROJECT.gprojects[i].pk == this.fields.gproject) {
                            return GAUSSPROJECT.gprojects[i];
                        }
                    }
                }, configurable: true
            }
        });
        this.duration = function (units) {
            //units is a string. It can be: 'days', 'weeks', 'years', 'seconds'
            return this.end_date.diff(this.start_date, units)
        };
        this.init_left_pane = function () {
            //var left = 20;
            $('<div class="gantt_list_column" style="width: 20px;border: none;text-align: center;"><i class="fa fa-check-square-o"></i></div>')
                .appendTo($('#column_headers'));
            $.each(GAUSSPROJECT.gcolumns, function (index, col) {
                var $header = $("<div/>")
                    .attr("class", "gantt_list_column gantt_header_column col" + col.pk)
                    //.attr("data-col", col.fields.pos)
                    .attr("data-colpk", col.pk)
                    //.attr("data-content", col.fields.content)
                    .attr("id", "col" + col.pk)
                    .css("width", col.fields.width)
                    .css("text-align", col.fields.align)
                    .css("position", "relative")
                    .html('<b>' + GAUSSPROJECT.gcolumn_types[col.fields.content] + '</b>')
                    .appendTo($('#column_headers'));
            });
        };


        this.init_right_pane = function () {
            // The right panel has two parts: timeline and bars (tasks representation)

            // These lines are dedicated to draw the timeline
            var w = Math.max(800, this.duration('days') * this.scale + 100);
            $("#right-header").css("width", w);

            var d = this.start_date; //Date that will be increased
            var e = moment.max(this.end_date, this.start_date.add(30, 'd')); //Limit date for the while statement
            var ds = 0; //The number of days in a month
            var m_name = d.format('MMMM'); //Name of the month. Initially the month of start_date
            while (d.isSameOrBefore(e)) {
                d.add(1, 'd');
                if (d.format('MMMM') != m_name) {
                    $("<div class='time_line'></div>")
                        .css("width", ds * this.fields.scale).html(m_name + ' ' + d.format('YYYY')).appendTo($('#tl_months'));
                    ds = 0;
                    m_name = d.format('MMMM');
                }
                ds++;
                $("<div class='time_line'></div>")
                    .css("width", this.fields.scale)
                    .html(d.format('DD'))
                    .appendTo($('#tl_days'));
            }
            $("<div class='time_line'></div>")
                .css("width", ds * this.fields.scale)
                .html(m_name + ' ' + d.format('YYYY'))
                .appendTo($("#tl_months"));
        };
    });
};


function queryget(array_objects, value, property) {
    property = property || 'pk';
    if (property == 'pk') {
        for (var i = 0; i < array_objects.length; i++) {
            if (array_objects[i].pk === value) {
                return array_objects[i];
            }
        }
    } else {
        for (var i = 0; i < array_objects.length; i++) {
            if (array_objects[i]['fields'][property] === value) {
                return array_objects[i];
            }
        }
    }
    return null;
}

function queryfilter(array_objects, values, property, return_pks) {
    property = property || 'pk';
    return_pks = return_pks || false;
    if (Object.prototype.toString.call(values) != '[object Array]') {
        values = [values];
    }
    var queryset = [];
    if (property == 'pk') {
        for (var i = 0; i < array_objects.length; i++) {
            if ($.inArray(array_objects[i].pk, values) > -1) {
                if (return_pks) {
                    queryset.push(array_objects[i].pk);
                } else {
                    queryset.push(array_objects[i]);
                }
            }
        }
    } else {
        for (var i = 0; i < array_objects.length; i++) {
            if ($.inArray(array_objects[i]['fields'][property], values) > -1) {
                if (return_pks) {
                    queryset.push(array_objects[i].pk);
                } else {
                    queryset.push(array_objects[i]);
                }
            }
        }
    }
    return queryset
}


GAUSSPROJECT.parse_gtasks = function (gtasks) {
    $.each(gtasks, function () {
        //for (var h=0;h<gtasks.length;h++){
        //    var this = gtasks[h];
        this.fields.pessimistic_time = moment.duration(this.fields.pessimistic_time);
        this.fields.optimistic_time = moment.duration(this.fields.optimistic_time);
        this.fields.likely_time = moment.duration(this.fields.likely_time);
        Object.defineProperties(this, {
            "gbaseline": {
                get: function () {
                    for (var i = 0; i < GAUSSPROJECT.gbaselines.length; i++) {
                        if (GAUSSPROJECT.gbaselines[i].pk == this.fields.gbaseline) {
                            return GAUSSPROJECT.gbaselines[i];
                        }
                    }
                }, configurable: true
            },
            "has_subtasks": {
                get: function () {
                    var child = queryget(GAUSSPROJECT.gtasks, this.pk, 'gtask_parent');
                    return !!child;
                }, configurable: true
            },
            "successors": {
                get: function () {
                    var s = [];
                    for (var i = 0; i < GAUSSPROJECT.glinks.length; i++) {
                        if (GAUSSPROJECT.glinks[i].fields.predecessor === this.pk) {
                            s.push(queryget(GAUSSPROJECT.gtasks, GAUSSPROJECT.glinks[i].fields.successor));
                        }
                    }
                    return s;
                }, configurable: true
            },
            "predecessors": {
                get: function () {
                    var p = [];
                    for (var i = 0; i < GAUSSPROJECT.glinks.length; i++) {
                        if (GAUSSPROJECT.glinks[i].fields.successor === this.pk) {
                            p.push(queryget(GAUSSPROJECT.gtasks, GAUSSPROJECT.glinks[i].fields.predecessor));
                        }
                    }
                    return p;
                }, configurable: true
            },
            "all_successors": {
                get: function () {
                    var r = [];
                    r.push(this);
                    s = this.successors;
                    for (var k = 0; k < s.length; k++) {
                        r = r.concat(s[k].all_successors);
                    }
                    return r;
                }, configurable: true
            },
            "estimate_time": {
                get: function () {
                    var o = this.fields.optimistic_time;
                    var l = this.fields.likely_time;
                    var p = this.fields.pessimistic_time;
                    return moment.duration((o + 4 * l + p) / 6);
                }, configurable: true
            },
            "early_start": {
                get: function () {
                    var tearlys_array = [];
                    var ps = this.predecessors;
                    for (var k = 0; k < ps.length; k++) {
                        tearlys_array.push(ps[k].early_start.add(ps[k].estimate_time));
                    }
                    if (tearlys_array.length > 0) {
                        return moment.max(tearlys_array);
                    } else {
                        return moment(this.gbaseline.fields.start_date);
                    }
                }, configurable: true
            },
            "last_finish": {
                get: function () {
                    var tlasts_array = [];
                    var ss = this.successors;
                    for (var k = 0; k < ss.length; k++) {
                        tlasts_array.push(ss[k].last_finish.subtract(ss[k].estimate_time));
                    }
                    if (tlasts_array.length > 0) {
                        return moment.min(tlasts_array);
                    } else {
                        return moment(this.gbaseline.end_date);
                    }
                }, configurable: true
            },
            "free_float": {
                get: function () {
                    var t_earlys_successors = [this.last_finish];
                    var ss = this.successors;
                    for (var k = 0; k < ss.length; k++) {
                        t_earlys_successors.push(ss[k].early_start);
                    }
                    var t_last_predecessors = [this.early_start];
                    var ps = this.predecessors;
                    for (var k = 0; k < ps.length; k++) {
                        t_last_predecessors.push(ps[k].last_finish);
                    }
                    var min_t_early = moment.min(t_earlys_successors);
                    var max_t_last = moment.max(t_last_predecessors);
                    var difference = moment.duration(min_t_early.diff(max_t_last));
                    var subtract = difference.subtract(this.estimate_time);
                    if ((subtract < moment.duration(1000)) && (subtract > moment.duration(-1000))) {
                        subtract = moment.duration(0)
                    }
                    return subtract;
                }, configurable: true
            },
            "total_float": {
                get: function () {
                    var early_last = moment.duration(this.last_finish.diff(this.early_start));
                    var subtract = early_last.subtract(this.estimate_time);
                    if ((subtract < moment.duration(1000)) && (subtract > moment.duration(-1000))) {
                        subtract = moment.duration(0)
                    }
                    return subtract;
                }, configurable: true
            },
            "left": {
                get: function () {
                    var left_delta = this.early_start.diff(this.gbaseline.start_date);
                    return parseInt(this.gbaseline.fields.scale * left_delta / 3600 / 24000);
                }, configurable: true
            },
            "width": {
                get: function () {
                    return parseInt(this.gbaseline.fields.scale * this.estimate_time.asMilliseconds() / 3600 / 24000);
                }, configurable: true
            }
        });
    });
    for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
        var gtask = GAUSSPROJECT.gtasks[i];
        gtask.old_estimate_time = gtask.estimate_time;
        gtask.old_early_start = gtask.early_start;
        gtask.old_last_finish = gtask.last_finish;
    }
};

GAUSSPROJECT.toggle_glinks = function () {
    if (GAUSSPROJECT.display_glinks) {
        $('.gantt_task_link').remove();
        GAUSSPROJECT.display_glinks = false;
    } else {
        GAUSSPROJECT.draw_glinks(GAUSSPROJECT.glinks);
        GAUSSPROJECT.display_glinks = true;
    }
};

GAUSSPROJECT.remove_glink = function (glink_id) {
    for (var i = GAUSSPROJECT.glinks.length - 1; i > -1; i--) {
        if (GAUSSPROJECT.glinks[i].pk == glink_id) {
            GAUSSPROJECT.glinks.splice(i, 1);
            GAUSSPROJECT.update_server({action: 'remove_glink', id: glink_id});
        }
    }
    GAUSSPROJECT.redraw_gtasks();
};

GAUSSPROJECT.draw_glinks = function (glinks) {
    var margin_task = 2;
    var task_height = margin_task * 11;
    var line_width = 2;
    var link_wrapper_width = task_height / 2;
    var rect0 = $('#task_bars')[0].getBoundingClientRect();
    glinks.forEach(function (l) {
        var predecessor = $('#bar' + l.fields.predecessor)[0];
        var successor = $('#bar' + l.fields.successor)[0];
        var rect1 = predecessor.getBoundingClientRect();
        var rect2 = successor.getBoundingClientRect();
        var p_ini = [parseInt(rect1.right) - parseInt(rect0.left), (parseInt(rect1.top) + parseInt(rect1.bottom) - parseInt(rect0.top) * 2) / 2];
        var p_fin = [parseInt(rect2.left) - parseInt(rect0.left), (parseInt(rect2.top) + parseInt(rect2.bottom) - parseInt(rect0.top) * 2) / 2];

        if (Math.abs(p_ini[0] - p_fin[0]) <= task_height) {
            var p1 = p_ini;
            var p2 = [p1[0] + task_height / 2, p1[1]];
            var p3 = [p2[0], p1[1] + task_height / 2];
            var p4 = [p_fin[0] - task_height / 2, p3[1]];
            var p5 = [p4[0], p_fin[1]];
            var p6 = p_fin;
            var points = [[p1, p2], [p2, p3], [p3, p4], [p4, p5], [p5, p6]];
        }
        else {
            var p1 = p_ini;
            var p2 = [p1[0] + task_height / 2, p1[1]];
            var p3 = [p2[0], p_fin[1]];
            var p4 = p_fin;
            var points = [[p1, p2], [p2, p3], [p3, p4]];
        }

        function shift(p0, p1) {
            var left = -1 * link_wrapper_width / 2;
            var top = -1 * link_wrapper_width / 2;
            if ((p0[0] - p1[0]) > 0) {
                left = -link_wrapper_width / 2 - (p0[0] - p1[0]);
            }
            if ((p0[1] - p1[1]) > 0) {
                top = -link_wrapper_width / 2 - (p0[1] - p1[1]);
            }
            return [left, top]
        }

        if ($('#glink' + l.pk).length > 0) {
            var $div_wrapper = $('#glink' + l.pk).html('');
        } else {
            var $div_wrapper = $("<div/>")
                .attr("class", "gantt_task_link")
                .attr("id", "glink" + l.pk)
                .attr("data-id", l.pk);
        }

        points.forEach(function (p, i) {
            var top_wrapper = p[0][1] + shift(p[0], p[1])[1] + line_width;
            var left_wrapper = p[0][0] + shift(p[0], p[1])[0];
            var width_wrapper = link_wrapper_width + Math.abs(p[0][0] - p[1][0]);
            var height_wrapper = link_wrapper_width + Math.abs(p[0][1] - p[1][1]);

            var width_line = line_width + Math.abs(p[0][0] - p[1][0]);
            var height_line = line_width + Math.abs(p[0][1] - p[1][1]);

            var margin = link_wrapper_width / 2;

            var $div_wrapper_child = $("<div/>")
                .attr("class", "gantt_line_wrapper")
                .css("top", top_wrapper)
                .css("left", left_wrapper)
                .css("height", height_wrapper)
                .css("width", width_wrapper)
                .css("top", top_wrapper);
            var $div_line = $("<div/>")
                .css("top", top_wrapper)
                .css("height", height_line)
                .css("width", width_line)
                .css("margin-top", margin)
                .css("margin-left", margin)
                .appendTo($div_wrapper_child);
            $div_wrapper.append($div_wrapper_child);
            if (i === points.length - 1) {
                var $arrow = $("<div/>")
                    .css("top", top_wrapper + margin - line_width)
                    .css("left", left_wrapper + width_wrapper - link_wrapper_width)
                    .attr("class", "gantt_link_arrow gantt_link_arrow_right")
                    .appendTo($div_wrapper);
            }
        });
        $div_wrapper.appendTo($('#task_bars'));
    });
};


/*
 * DOM activity related to glinks
 */
// If mouse is over a row where bars are drawn, then ball-links (divs with gantt_link class) are shown.
$('body').on('mouseover', '.bar_side', function (e) {
    var id = $(this).data('id');
    var pos = $(this).data('pos');
    $('.gantt_link').hide();
    $('#gll' + id).show();
    $('#glr' + id).show();
});
// When mouse leaves the .bar_side the ball-links (divs with gantt_link class) are hidden.
$('body').on('mouseover', '#left-header, #right-header, .row_info, .col_side', function (e) {
    $('.gantt_link').hide();
});

var down = false;
var pointx, pointy;
$('body').on('mousedown', '.gantt_link', function (event) {
    event = event || window.event; // IE-ism

    // If pageX/Y aren't available and clientX/Y are,
    // calculate pageX/Y - logic taken from jQuery.
    // (This is to support old IE)
    if (event.pageX == null && event.clientX != null) {
        eventDoc = (event.target && event.target.ownerDocument) || document;
        doc = eventDoc.documentElement;
        body = eventDoc.body;

        event.pageX = event.clientX +
            (doc && doc.scrollLeft || body && body.scrollLeft || 0) -
            (doc && doc.clientLeft || body && body.clientLeft || 0);
        event.pageY = event.clientY +
            (doc && doc.scrollTop || body && body.scrollTop || 0) -
            (doc && doc.clientTop || body && body.clientTop || 0 );
    }

    $('#task_origin').val($(this).data('id'));
    if ($(this).hasClass('left_link')) {
        $('#task_origin_type').val('S');
    } else {
        $('#task_origin_type').val('F');
    }

    down = true;
    pointx = event.pageX;
    pointy = event.pageY;
    var $div = $("<div/>")
        .attr("id", "dinamic_link")
        .css("position", "absolute")
        .css("left", event.pageX)
        .css("top", event.pageY)
        .css("width", "0px")
        .css("height", "2px")
        .css("border-top", "2px dashed red");

    $div.appendTo($('#gantt_schedule'));

});

// If mouseup not in a gantt_link_control, nothing must be done except remove the glink
$('body').mouseup(function (e) {
    down = false;
    $('#dinamic_link').remove();
    // if the target of the click is a div container with class "gantt_link":
    // if ($('.gantt_link').is(e.target))
    if ($('.gantt_link').is(e.target)) {
        var toy = $('#task_origin_type').val();
        if ($(e.target).hasClass('left_link')) {
            var dependency = toy + 'S';
        } else {
            var dependency = toy + 'F';
        }
        var orig = $('#task_origin').val();
        var dest = $(e.target).data('id');
        var no_exists = true;
        var glinks_length = GAUSSPROJECT.glinks.length;
        for (var i = 0; i < glinks_length; i++) {
            if (GAUSSPROJECT.glinks[i].predecessor === orig && GAUSSPROJECT.glinks[i].successor === dest) {
                no_exists = false;
            }
        }
        var resp = GAUSSPROJECT.update_server({
            action: 'create_link', dependency: dependency,
            b_id: GAUSSPROJECT.gproject.active_gbaseline.pk, gtask_d: dest, gtask_o: orig
        });
        if (no_exists) {
            GAUSSPROJECT.glinks.push(resp[0]);
            //var gtask_origin = queryget(GAUSSPROJECT.gtasks, resp[0].fields.predecessor);
            GAUSSPROJECT.redraw_gtasks();
            //GAUSSPROJECT.redraw_glinks();
        }
        //$.post("/gantt_ajax/", {
        //        action: 'create_link', dependency: dependency,
        //        b_id: GAUSSPROJECT.gproject.active_gbaseline.pk, gtask_d: dest, gtask_o: orig
        //    },
        //    function (resp) {
        //        if (no_exists) {
        //            GAUSSPROJECT.glinks.push(resp[0]);
        //            var gtask_origin = queryget(GAUSSPROJECT.gtasks, resp[0].fields.predecessor);
        //            //$('.gantt_task_link').remove();
        //            GAUSSPROJECT.redraw_gtask(gtask_origin);
        //            //GAUSSPROJECT.draw_glinks(GAUSSPROJECT.glinks);
        //            GAUSSPROJECT.redraw_glinks();
        //        }
        //    }, 'json');
    }
});


$('#gantt_schedule').mousemove(function (event) {
    // If the button of the mouse is pressed:
    if (down) {
        var eventDoc, doc, body, pageX, pageY;

        event = event || window.event; // IE-ism

        // If pageX/Y aren't available and clientX/Y are,
        // calculate pageX/Y - logic taken from jQuery.
        // (This is to support old IE)
        if (event.pageX == null && event.clientX != null) {
            eventDoc = (event.target && event.target.ownerDocument) || document;
            doc = eventDoc.documentElement;
            body = eventDoc.body;

            event.pageX = event.clientX +
                (doc && doc.scrollLeft || body && body.scrollLeft || 0) -
                (doc && doc.clientLeft || body && body.clientLeft || 0);
            event.pageY = event.clientY +
                (doc && doc.scrollTop || body && body.scrollTop || 0) -
                (doc && doc.clientTop || body && body.clientTop || 0 );
        }

        // Using event.pageX / event.pageY here:
        var w = Math.sqrt(Math.pow((parseInt(event.pageX) - parseInt(pointx)), 2) + Math.pow((parseInt(event.pageY) - parseInt(pointy)), 2));
        var d = Math.atan2(parseInt(event.pageX) - parseInt(pointx), parseInt(pointy) - parseInt(event.pageY)) * 360 / 2 / Math.PI - 90;

        $('#dinamic_link').css('width', w)
            .css('transform-origin', 'left top')
            .css('transform', 'rotate(' + d + 'deg)');
    }
});


//Other DOM activities:

$('body').on('click', '.item_menu_header', function (e) {
    e.preventDefault();
    var action = $(this).data('action');
    var current_column = queryget(GAUSSPROJECT.gcolumns, GAUSSPROJECT.selected_gcolumn.data('colpk'));
    $('.menu_header').hide();
    // ******************************************************************
    if (action == 'gcolumn-align-center') {
        $('.col' + current_column.pk).css('text-align', 'center');
        GAUSSPROJECT.update_server_async({action: action, id: current_column.pk});
        // ******************************************************************
    } else if (action == 'gcolumn-align-right') {
        $('.col' + current_column.pk).css('text-align', 'right');
        GAUSSPROJECT.update_server_async({action: action, id: current_column.pk});
        // ******************************************************************
    } else if (action == 'gcolumn-align-left') {
        $('.col' + current_column.pk).css('text-align', 'left');
        GAUSSPROJECT.update_server_async({action: action, id: current_column.pk});
        // ******************************************************************
    } else if (action == 'gcolumn-move-right') {
        GAUSSPROJECT.update_server_async({action: action, id: current_column.pk});
        var right_column = queryget(GAUSSPROJECT.gcolumns, current_column.fields.pos + 1, 'pos');
        if (right_column) {
            var current_column_pos = current_column.fields.pos;
            current_column.fields.pos = right_column.fields.pos;
            right_column.fields.pos = current_column_pos;
            $('#col' + current_column.pk).insertAfter($('#col' + right_column.pk));
            for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
                var $col_orig = $('#col' + current_column.pk + '_' + GAUSSPROJECT.gtasks[i].pk);
                var $col_dest = $('#col' + right_column.pk + '_' + GAUSSPROJECT.gtasks[i].pk);
                $col_orig.insertAfter($col_dest);
            }
        }
        // ******************************************************************
    } else if (action == 'gcolumn-move-left') {
        GAUSSPROJECT.update_server_async({action: action, id: current_column.pk});
        var left_column = queryget(GAUSSPROJECT.gcolumns, current_column.fields.pos - 1, 'pos');
        if (left_column) {
            var current_column_pos = current_column.fields.pos;
            current_column.fields.pos = left_column.fields.pos;
            left_column.fields.pos = current_column_pos;
            $('#col' + current_column.pk).insertBefore($('#col' + left_column.pk));
            for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
                var $col_orig = $('#col' + current_column.pk + '_' + GAUSSPROJECT.gtasks[i].pk);
                var $col_dest = $('#col' + left_column.pk + '_' + GAUSSPROJECT.gtasks[i].pk);
                $col_orig.insertBefore($col_dest);
            }
        }
        // ******************************************************************
    } else if (action == 'gcolumn-remove') {
        var current_column_pos = current_column.fields.pos;
        for (var i = GAUSSPROJECT.gcolumns.length - 1; i > -1; i--) {
            if (GAUSSPROJECT.gcolumns[i].fields.pos > current_column_pos) {
                GAUSSPROJECT.gcolumns[i].fields.pos = GAUSSPROJECT.gcolumns[i].fields.pos - 1;
            } else if (GAUSSPROJECT.gcolumns[i].fields.pos == current_column_pos) {
                GAUSSPROJECT.gcolumns.splice(i, 1);
            }
        }
        GAUSSPROJECT.update_server_async({action: action, id: current_column.pk});
        $('.col' + current_column.pk).remove();
        // ******************************************************************
    } else if (action == 'gcolumn-insert') {
        var current_column_pos = current_column.fields.pos;
        var new_column = GAUSSPROJECT.update_server({
            direction: GAUSSPROJECT.insert_move_gcolumn_at,
            action: action,
            id: current_column.pk,
            content: $(this).data('content')
        });
        new_column = new_column[0];
        GAUSSPROJECT.gcolumns.push(new_column);
        if (GAUSSPROJECT.insert_move_gcolumn_at == 'left') {
            var new_column_pos = current_column_pos;
        } else {
            var new_column_pos = current_column_pos + 1;
        }
        for (var i = 0; i < GAUSSPROJECT.gcolumns.length; i++) {
            if (GAUSSPROJECT.gcolumns[i].pos >= new_column_pos) {
                GAUSSPROJECT.gcolumns[i].pos = GAUSSPROJECT.gcolumns[i].pos + 1;
            }
        }
        var $new_header = $("<div/>")
            .attr("class", "gantt_list_column gantt_header_column col" + new_column.pk)
            .attr("data-colpk", new_column.pk)
            .attr("id", "col" + new_column.pk)
            .css("width", new_column.fields.width)
            .css("text-align", new_column.fields.align)
            .css("position", "relative")
            .html('<b>' + GAUSSPROJECT.gcolumn_types[new_column.fields.content] + '</b>');
        if (GAUSSPROJECT.insert_move_gcolumn_at == 'left') {
            $new_header.insertBefore($('#col' + current_column.pk));
        } else {
            $new_header.insertAfter($('#col' + current_column.pk));
        }
        for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
            var gtask = GAUSSPROJECT.gtasks[i];
            var $col_orig = $('#col' + current_column.pk + '_' + gtask.pk);
            var $col_dest = $("<div/>")
                .attr("class", "gantt_list_column col" + new_column.pk)
                .attr("data-colpk", new_column.pk)
                .attr("data-id", gtask.pk)
                .attr("id", "col" + new_column.pk + '_' + gtask.pk)
                .attr("contenteditable", "true")
                .css("width", new_column.fields.width + "px")
                .css("text-align", new_column.fields.align)
                .html(html_column(new_column.fields.content, gtask));
            if (GAUSSPROJECT.insert_move_gcolumn_at == 'left') {
                $col_dest.insertBefore($col_orig);
            } else {
                $col_dest.insertAfter($col_orig);
            }
        }
    }
});

//Functions to get certain behaviours without flood the code

function html_column(content, gtask) {
    if (content == 'gtask_name') {
        return gtask.fields.name;
    }
    else if (content == 'estimate_time_days') {
        return roundToTwo(gtask.estimate_time.asDays()) + ' days';
    }
    else if (content == 'optimistic_time') {
        return roundToTwo(gtask.fields.optimistic_time.asDays()) + ' days';
    }
    else if (content == 'likely_time') {
        return roundToTwo(gtask.fields.likely_time.asDays()) + ' days';
    }
    else if (content == 'pessimistic_time') {
        return roundToTwo(gtask.fields.pessimistic_time.asDays()) + ' days';
    }
    else if (content == 'total_float') {
        return roundToTwo(gtask.total_float.asDays()) + ' days';
    }
    else if (content == 'free_float') {
        return roundToTwo(gtask.free_float.asDays()) + ' days';
    }
    else if (content == 'priority') {
        return gtask.fields.priority;
    }
    else if (content == 'restriction') {
        return gtask.fields.restriction;
    }
    else if (content == 'restriction_date') {
        return gtask.fields.restriction_date;
    }
    else if (content == 'notes') {
        return gtask.fields.notes;
    }
    else if (content == 'gtask_parent') {
        return gtask.fields.gtask_parent;
    }
    else if (content == 'display_subtasks') {
        return gtask.fields.display_subtasks;
    }
    else if (content == 'datetimeafadfaf') {
        $div_col1.html(gtask[col.fields.content].format("DD/MM/YYYY, HH:mm"))
            .appendTo($div_row);
    } else if (content == 'dafafdadfate') {
        $div_col1.html(gtask[col.fields.content].format("DD/MM/YYYY"))
            .appendTo($div_row);
    } else if (content == 'asDaadfadfays') {
        $div_col1.html(gtask[col.fields.content].asDays())
            .appendTo($div_row);
    } else if (content == 'asDayadfas') {
        $div_col1.html(gtask[col.fields.content])
            .appendTo($div_row);
    }
}


function roundToTwo(num) {
    return +(Math.round(num + "e+2") + "e-2");
}

/**
 * jQuery selectText plugin
 *
 * Select a div content editable when is focused
 *
 * * This file also make use of selectText function designed by Tom Oakley:
 * http://stackoverflow.com/questions/12243898/how-to-select-all-text-in-contenteditable-div
 *
 */

jQuery.fn.selectText = function () {
    var doc = document;
    var element = this[0];
    if (doc.body.createTextRange) {
        var range = document.body.createTextRange();
        range.moveToElementText(element);
        range.select();
    } else if (window.getSelection) {
        var selection = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(element);
        selection.removeAllRanges();
        selection.addRange(range);
    }
};

/**
 * jQuery alterClass plugin
 *
 * Remove element classes with wildcard matching. Optionally add classes:
 *   $( '#foo' ).alterClass( 'foo-* bar-*', 'foobar' )
 *
 * Copyright (c) 2011 Pete Boere (the-echoplex.net)
 * Free under terms of the MIT license: http://www.opensource.org/licenses/mit-license.php
 *
 */
(function ($) {

    $.fn.alterClass = function (removals, additions) {
        var self = this;
        if (removals.indexOf('*') === -1) {
            // Use native jQuery methods if there is no wildcard matching
            self.removeClass(removals);
            return !additions ? self : self.addClass(additions);
        }
        var patt = new RegExp('\\s' +
            removals.replace(/\*/g, '[A-Za-z0-9-_]+').split(' ').join('\\s|\\s') +
            '\\s', 'g');
        self.each(function (i, it) {
            var cn = ' ' + it.className + ' ';
            while (patt.test(cn)) {
                cn = cn.replace(patt, ' ');
            }
            it.className = $.trim(cn);
        });
        return !additions ? self : self.addClass(additions);
    };
})(jQuery);




