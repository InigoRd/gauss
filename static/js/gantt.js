/**
 * Created by juanjo on 04/046/16.
 * This file requires moment.js (http://momentjs.com/). Thanks to Iskren Ivov Chernev for his pretty work.
 * This file also make use of selectText function designed by Tom Oakley:
 * http://stackoverflow.com/questions/12243898/how-to-select-all-text-in-contenteditable-div
 * This file also make use of placeCaretAtEnd function designed by Tim Down:
 * http://stackoverflow.com/users/96100/tim-down
 * This file requires setOps.js (https://gist.github.com/jabney/d9d5c13ad7f871ddf03f). Thanks to James Abney
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

GAUSSPROJECT.gtasks_to_be_updated = []; //List of gtasks that must be updated in an asynchronous way.
GAUSSPROJECT.gtasks_to_be_updated_next_element = 0;

GAUSSPROJECT.gtask_edited = null; //The gtask that is being edited in the gantt diagram

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
GAUSSPROJECT.gcolumn_editable = {
    estimate_time_days: true,
    early_start_date: false,
    early_start_datetime: false,
    last_finish_date: false,
    last_finish_datetime: false,
    gtask_name: true,
    total_float: false,
    free_float: false,
    optimistic_time: true,
    likely_time: true,
    pessimistic_time: true
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


GAUSSPROJECT.rewrite_next_gtask_columns = function (next_gtask) {
    var start = new Date().getTime();
    // Obtain the gtask which columns need to be updated. It can be an argument or obtained if argument doesn't exist
    if (typeof next_gtask === 'undefined') {
        next_gtask = GAUSSPROJECT.gtasks_to_be_updated.splice(0, 1)[0]; //Take gtask removing it from array
    } else {
        $('#optimistic_time').val(html_column('optimistic_time', next_gtask));
        $('#likely_time').val(html_column('likely_time', next_gtask));
        $('#pessimistic_time').val(html_column('pessimistic_time', next_gtask));
        $('#estimate_time_days').val(html_column('estimate_time_days', next_gtask));
        if (next_gtask.total_float == 0) {
            GAUSSPROJECT.gtasks_to_be_updated = GAUSSPROJECT.gtasks.slice(); //In order to not delete gtasks
        } else {
            GAUSSPROJECT.gtasks_to_be_updated = next_gtask.all_successors.concat(next_gtask.parallels);
        }
        for (var i = 0; i < GAUSSPROJECT.gtasks_to_be_updated.length; i++) {
            GAUSSPROJECT.redraw_gtask(GAUSSPROJECT.gtasks_to_be_updated[i]);
        }
        GAUSSPROJECT.redraw_glinks();
    }
    for (var i = 0; i < GAUSSPROJECT.gcolumns.length; i++) {
        var col = GAUSSPROJECT.gcolumns[i];
        var content = col.fields.content;
        $('#col' + col.pk + '_' + next_gtask.pk).html(html_column(content, next_gtask));
    }
    //GAUSSPROJECT.gtasks_to_be_updated.splice(0, 1); // Remove the gtask which columns have been updated
    if (GAUSSPROJECT.gtasks_to_be_updated.length > 0) { // If more gtasks need to be updated, the function is called again after 100 milliseconds
        setTimeout(GAUSSPROJECT.rewrite_next_gtask_columns, 100);
    }
    var end = new Date().getTime();
    var time = end - start;
    //console.log('The needed time to update columns of gtask: ' + time);
};


GAUSSPROJECT.update_cell = function (gtaskpk, gcolpk, value) { //gcolpk puede ser el pk de la columna o el content de la misma
    if (gtaskpk != 0) {
        var $dom_gcol = $('#col' + gcolpk + '_' + gtaskpk);
        var gtask = queryget(GAUSSPROJECT.gtasks, gtaskpk);
        var gcol = queryget(GAUSSPROJECT.gcolumns, gcolpk);
        var content = gcol.fields.content;
    } else {
        var gtask = GAUSSPROJECT.gtask_edited;
        var content = gcolpk;
    }

    if (content == 'gtask_name') {
        if (gtask.fields.name != value) {
            GAUSSPROJECT.update_server({action: 'update_gtask_name', value: value, id: gtask.pk});
            gtask.fields.name = value;
        }
        return value;
    }
    else if (content == 'estimate_time_days') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        console.log('estimate_time_days', val);
        var mo = moment.duration(val, 'days');
        var diff = Math.abs(gtask.estimate_time.asSeconds() - mo.asSeconds()) > 100;
        if (diff) {
            gtask.fields.optimistic_time = mo;
            gtask.fields.likely_time = mo;
            gtask.fields.pessimistic_time = mo;
            GAUSSPROJECT.update_server_async({action: 'update_estimate_time_days', value: val, id: gtask.pk});
            GAUSSPROJECT.rewrite_next_gtask_columns(gtask);
        }
        return true;
    }
    else if (content == 'optimistic_time') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        console.log('optimistic_time', val);
        var mo = moment.duration(val, 'days');
        gtask.fields.optimistic_time = mo;
        GAUSSPROJECT.update_server({action: 'update_optimistic_time', value: val, id: gtask.pk});
        GAUSSPROJECT.rewrite_next_gtask_columns(gtask);
    }
    else if (content == 'likely_time') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        console.log('likely_time', val);
        var mo = moment.duration(val, 'days');
        gtask.fields.likely_time = mo;
        GAUSSPROJECT.update_server({action: 'update_likely_time', value: val, id: gtask.pk});
        GAUSSPROJECT.rewrite_next_gtask_columns(gtask);
    }
    else if (content == 'pessimistic_time') {
        var val = parseFloat(value.replace(/[^0-9.,]/g, '').replace(/[,]/g, '.'));
        console.log('pessimistic_time', val);
        var mo = moment.duration(val, 'days');
        gtask.fields.pessimistic_time = mo;
        GAUSSPROJECT.update_server({action: 'update_pessimistic_time', value: val, id: gtask.pk});
        GAUSSPROJECT.rewrite_next_gtask_columns(gtask);
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


GAUSSPROJECT.add_task = function () {
    var gbaseline = GAUSSPROJECT.gproject.active_gbaseline.pk;
    var gtask = GAUSSPROJECT.update_server({action: 'add_task', id: gbaseline})[0];
    GAUSSPROJECT.gtasks.push(gtask);
    gtask = GAUSSPROJECT.gtasks[GAUSSPROJECT.gtasks.length - 1];
    GAUSSPROJECT.parse_gtasks([gtask]);
    GAUSSPROJECT.draw_gtask(gtask);
};

GAUSSPROJECT.insert_task = function (id) {
    var gtasks_length = GAUSSPROJECT.gtasks.length;
    // First we find the gtask where new gtask will be inserted:
    for (var i = 0; i < gtasks_length; i++) {
        if (GAUSSPROJECT.gtasks[i].pk == id) {
            var checked_gtask = GAUSSPROJECT.gtasks[i];
        }
    }
    // Second, all gtasks with bigger positions are modified to their new positions:
    var new_gtask_pos = checked_gtask.fields.pos;
    for (var k = 0; k < gtasks_length; k++) {
        if (GAUSSPROJECT.gtasks[k].fields.pos >= new_gtask_pos) {
            GAUSSPROJECT.gtasks[k].fields.pos = GAUSSPROJECT.gtasks[k].fields.pos + 1;
        }
    }
    // Third, new gtask is created and screen is updated
    var gtask = GAUSSPROJECT.update_server({action: 'insert_task', id: id})[0];
    GAUSSPROJECT.gtasks.push(gtask);
    GAUSSPROJECT.parse_gtasks([gtask]);
    GAUSSPROJECT.draw_gtask(gtask);
    GAUSSPROJECT.redraw_glinks();
};

GAUSSPROJECT.moveup_gtask = function (prev, curr) {
    var gtasks_length = GAUSSPROJECT.gtasks.length;
    for (var i = 0; i < gtasks_length; i++) {
        if (GAUSSPROJECT.gtasks[i].pk == prev) {
            var previous = GAUSSPROJECT.gtasks[i];
        } else if (GAUSSPROJECT.gtasks[i].pk == curr) {
            var current = GAUSSPROJECT.gtasks[i];
        }
    }
    var previous_pos = previous.fields.pos;
    previous.fields.pos = current.fields.pos;
    current.fields.pos = previous_pos;

    GAUSSPROJECT.update_server_async({action: 'moveup_gtask', prev: prev, curr: curr});
    $('#rowl' + curr).insertBefore($('#rowl' + prev));
    $('#rowr' + curr).insertBefore($('#rowr' + prev));
    GAUSSPROJECT.redraw_glinks();
};

GAUSSPROJECT.movedown_gtask = function (next, curr) {
    var gtasks_length = GAUSSPROJECT.gtasks.length;
    for (var i = 0; i < gtasks_length; i++) {
        if (GAUSSPROJECT.gtasks[i].pk == next) {
            var gnext = GAUSSPROJECT.gtasks[i];
        } else if (GAUSSPROJECT.gtasks[i].pk == curr) {
            var current = GAUSSPROJECT.gtasks[i];
        }
    }
    var gnext_pos = gnext.fields.pos;
    gnext.fields.pos = current.fields.pos;
    current.fields.pos = gnext_pos;

    GAUSSPROJECT.update_server_async({action: 'movedown_gtask', next: next, curr: curr});
    $('#rowl' + curr).insertAfter($('#rowl' + next));
    $('#rowr' + curr).insertAfter($('#rowr' + next));
    GAUSSPROJECT.redraw_glinks();
};

GAUSSPROJECT.edit_gtask = function (id) {
    var gtasks_length = GAUSSPROJECT.gtasks.length;
    for (var i = 0; i < gtasks_length; i++) {
        if (GAUSSPROJECT.gtasks[i].pk == id) {
            GAUSSPROJECT.gtask_edited = GAUSSPROJECT.gtasks[i];
        }
    }
    // General tab
    $('#gtask_name').val(GAUSSPROJECT.gtask_edited.fields.name).data('id', GAUSSPROJECT.gtask_edited.pk);
    $('#estimate_time_days').val(html_column('estimate_time_days', GAUSSPROJECT.gtask_edited));
    $('#optimistic_time').val(html_column('optimistic_time', GAUSSPROJECT.gtask_edited));
    $('#likely_time').val(html_column('likely_time', GAUSSPROJECT.gtask_edited));
    $('#pessimistic_time').val(html_column('pessimistic_time', GAUSSPROJECT.gtask_edited));
    $('#gtask_id').val(GAUSSPROJECT.gtask_edited.pk);
    $('.option_predecessors').remove();
    var possible_predecessors = GAUSSPROJECT.gtask_edited.possible_predecessors;
    var p_p_length = possible_predecessors.length;
    for (var i = 0; i < p_p_length; i++) {
        var $option = $("<option/>")
            .attr("class", "option_predecessors")
            .attr('value', possible_predecessors[i].pk)
            .html(possible_predecessors[i].fields.name)
            .appendTo($('#id_predecessors'));
    }
    var predecessors = GAUSSPROJECT.gtask_edited.predecessors;
    var p_length = predecessors.length;
    for (var i = 0; i < p_length; i++) {
        var $option = $("<option/>")
            .attr("class", "option_predecessors")
            .attr('value', predecessors[i].pk)
            .attr('selected', 'selected')
            .html(predecessors[i].fields.name)
            .appendTo($('#id_predecessors'));
    }
};

GAUSSPROJECT.change_predecessors = function (ps) {
    var id = GAUSSPROJECT.gtask_edited.pk;
    if (ps) { //If ps is null means that there was only one predecessor and it has been removed
        var gtask_pk = setOps.difference(ps, GAUSSPROJECT.get_pks(GAUSSPROJECT.gtask_edited.predecessors))[0];
        var current_ps = ps.length;
        var old_ps = GAUSSPROJECT.gtask_edited.predecessors.length;
    } else {
        var gtask_pk = GAUSSPROJECT.gtask_edited.predecessors[0].pk;
        var current_ps = 0;
        var old_ps = 1;
    }
    if (current_ps > old_ps) { // That means a predecessor has been added
        GAUSSPROJECT.create_glink(gtask_pk, id);
    } else { //Just in the case a predecessor has been removed
        console.log('edited ', id, 'removed predecessor with id ', gtask_pk);
        for (var i = 0; i < GAUSSPROJECT.glinks.length; i++) {
            if (GAUSSPROJECT.glinks[i].fields.successor == id && GAUSSPROJECT.glinks[i].fields.predecessor == gtask_pk) {
                GAUSSPROJECT.remove_glink(GAUSSPROJECT.glinks[i].pk);
            }
        }
    }
};

GAUSSPROJECT.get_pks = function (objs) {
    objs_length = objs.length;
    var pks = [];
    for (var i = 0; i < objs_length; i++) {
        pks.push(objs[i].pk);
    }
    return pks;
};
GAUSSPROJECT.get_attrs = function (objs, attr) {
    objs_length = objs.length;
    var attrs = [];
    for (var i = 0; i < objs_length; i++) {
        attrs.push(objs[i].fields[attr]);
    }
    return attrs;
};
//GAUSSPROJECT.update_predecessors = function (list_pks){ //list_pks: list of predecessors pk
//
//    var gtask = GAUSSPROJECT.gtask_edited;
//
//    var old_predecessors = [];
//    for (var i= 0; i< gtask.predecessors.length; i++){
//        old_predecessors.push(gtask.predecessors[i].pk);
//    }
//    //http://www.2ality.com/2015/01/es6-set-operations.html
//    var sop = new Set(old_predecessors);
//    var snp = new Set(list_pks);
//    var deleted = new Set([...sop].filter(x => !snp.has(x)));
//    var added = new Set([...snp].filter(x => !sop.has(x)));
//    // https://gist.github.com/jabney/d9d5c13ad7f871ddf03f
//
//    gtask = Gtask.objects.get(id=request.POST['gtask_id'])
//            gproject = gtask.gbaseline.gproject
//            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
//                old_predecessors = Gtask_link.objects.filter(successor=gtask).values_list('predecessor__id', flat=True)
//                new_predecessors = request.POST.getlist('predecessors')
//                sop = set(old_predecessors)
//                snp = set(new_predecessors)
//                deleted = Gtask.objects.filter(id__in=list(sop - snp))
//                for predecessor in deleted:
//                    Gtask_link.objects.get(predecessor=predecessor, successor=gtask, gbaseline=gtask.gbaseline).delete()
//                added = Gtask.objects.filter(id__in=list(snp - sop))
//                for predecessor in added:
//                    Gtask_link.objects.create(predecessor=predecessor, successor=gtask, gbaseline=gtask.gbaseline)
//};


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
                $('#rowr' + gtask.pk).remove();
                $('#rowl' + gtask.pk).remove();
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
    var gtask_pos = gtask.fields.pos;
    var before_pk = 0; // As pk can never be 0, there is not conflict in initial div
    var before_pos = -1;
    var gtask_list_length = GAUSSPROJECT.gtasks.length;
    for (var i = 0; i < gtask_list_length; i++) {
        var pos = GAUSSPROJECT.gtasks[i].fields.pos;
        if (pos < gtask_pos && pos > before_pos) {
            before_pos = pos;
            before_pk = GAUSSPROJECT.gtasks[i].pk;
        }
    }
    var $div_columns_before = $('#rowl' + before_pk);
    var $div_bars_before = $('#rowr' + before_pk);

    var $div_row = $("<div/>")
        .attr("class", 'row gtask_row col_side')
        .css("height", '28px')
        .css("margin-left", "0rem")
        .attr("data-id", gtask.pk)
        .attr("data-columns", 'undone')
        .attr("id", "rowl" + gtask.pk)
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
            .attr("contenteditable", GAUSSPROJECT.gcolumn_editable[col.fields.content])
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
        .attr("data-columns", 'undone')
        .attr("id", "rowr" + gtask.pk)
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


GAUSSPROJECT.create_gbaseline = function () {
    var current_gbaseline = GAUSSPROJECT.gproject.active_gbaseline;
    $.post("/gantt_ajax/", {action: 'create_gbaseline', id: current_gbaseline.pk},
        function (resp) {
            current_gbaseline.fields.active = false;
            $('.fa-check-circle-o').addClass('fa-circle-o').removeClass('fa-check-circle-o');
            var new_gbaseline = JSON.parse(resp['gbaseline']);
            var new_gtasks = JSON.parse(resp['gtasks']);
            var new_glinks = JSON.parse(resp['glinks']);
            var new_gcolumns = JSON.parse(resp['gcols']);
            GAUSSPROJECT.parse_gbaselines(new_gbaseline);
            GAUSSPROJECT.gbaselines.push(new_gbaseline[0]);
            GAUSSPROJECT.parse_gtasks(new_gtasks);
            GAUSSPROJECT.gtasks = new_gtasks;
            GAUSSPROJECT.gcolumns = new_gcolumns;
            GAUSSPROJECT.glinks = new_glinks;
            $('.gantt_task_link').remove();
            $('.gtask_row').remove();
            var gtasks_length = new_gtasks.length;
            for (var i = 0; i < gtasks_length; i++) {
                GAUSSPROJECT.draw_gtask(new_gtasks[i]);
            }
            GAUSSPROJECT.draw_glinks(GAUSSPROJECT.glinks);
            $('#reveal_creating_baseline').foundation('close');
        }, 'json');
};

GAUSSPROJECT.edit_gbaseline = function (id) {
    var gbaseline = queryget(GAUSSPROJECT.gbaselines, parseInt(id));
    $('#gbaseline_name').val(gbaseline.fields.name);
    $('#gbaseline_start_date').val(gbaseline.fields.start_date);
    $('#gbaseline_scale').val(gbaseline.fields.scale);
    if (gbaseline.fields.active == true){
        $('#switch_active_gbaseline').attr('checked', true);
    }
    $('#reveal_edit_baseline').foundation('open');
    $('.active_switch').foundation(); //in order to get the switch on if checked is true
};

GAUSSPROJECT.save_gbaseline_changes = function (id){
    var gbaseline = queryget(GAUSSPROJECT.gbaselines, parseInt(id));
};

GAUSSPROJECT.parse_gbaselines = function (gbaselines) {
    $.each(gbaselines, function () {
        var fa = this.fields.active ? "fa fa-check-circle-o" : "fa fa-circle-o";
        var $li = $("<li/>")
            .css('padding-right', '10px')
            .css('z-index', 1000)
            .attr('title', 'Baseline created on ' + this.fields.created)
            .appendTo($('#menu_code-fork'));
        var $a = $("<a/>")
            .attr('data-id', this.pk)
            .attr('class', 'select_gbaseline')
            .html("<i class='" + fa + "'></i> " + this.fields.name)
            .appendTo($li);
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
                    .attr("data-colpk", col.pk)
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
            "parallels": { //Activities that are made in parallel with this.
                get: function () {
                    var p = [];
                    var length = GAUSSPROJECT.gtasks.length;
                    for (var i = 0; i < length; i++) {
                        var cond1 = GAUSSPROJECT.gtasks[i].early_start.isBefore(this.early_finish);
                        var cond2 = GAUSSPROJECT.gtasks[i].early_finish.isAfter(this.early_start);
                        if (cond1 && cond2 && GAUSSPROJECT.gtasks[i].pk != this.pk) {
                            p.push(GAUSSPROJECT.gtasks[i]);
                        }
                    }
                    return p;
                }, configurable: true
            },
            "successors": {
                get: function () {
                    var s = [];
                    for (var i = 0; i < GAUSSPROJECT.glinks.length; i++) {
                        if (GAUSSPROJECT.glinks[i].fields.predecessor === this.pk) {
                            var g = queryget(GAUSSPROJECT.gtasks, GAUSSPROJECT.glinks[i].fields.successor);
                            s.push(g);
                        }
                    }
                    return s;
                }, configurable: true
            },
            "all_successors": {
                get: function () {
                    //http://stackoverflow.com/questions/18004547/javascript-recursive-function-to-iterate-through-elements
                    var r = [];

                    function walkSuccessors(gtask) {
                        r.push(gtask);
                        for (var i = 0; i < gtask.successors.length; i++) {
                            walkSuccessors(gtask.successors[i]);
                        }
                    }

                    walkSuccessors(this);
                    return r;
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
            "all_predecessors": {
                get: function () {
                    //http://stackoverflow.com/questions/18004547/javascript-recursive-function-to-iterate-through-elements
                    var r = [];

                    function walkPredecessors(gtask) {
                        r.push(gtask);
                        for (var i = 0; i < gtask.predecessors.length; i++) {
                            walkPredecessors(gtask.predecessors[i]);
                        }
                    }

                    walkPredecessors(this);
                    return r;
                }, configurable: true
            },
            "impossible_predecessors": {
                get: function () {
                    return this.all_predecessors.concat(this.all_successors);
                }, configurable: true
            },
            "possible_predecessors": {
                get: function () {
                    var impossible_predecessors = this.all_predecessors.concat(this.all_successors);
                    var possible_predecessors = [];
                    for (var i = 0; i < GAUSSPROJECT.gtasks.length; i++) {
                        var is_possible = true;
                        for (var k = 0; k < impossible_predecessors.length; k++) {
                            if (GAUSSPROJECT.gtasks[i].pk == impossible_predecessors[k].pk) {
                                is_possible = false;
                            }
                        }
                        if (is_possible) {
                            possible_predecessors.push(GAUSSPROJECT.gtasks[i]);
                        }
                    }
                    return possible_predecessors;
                }, configurable: true
            },
            //"all_successors_b": {
            //    get: function () {
            //        var r = [];
            //
            //        function walkSuccessors(gtask, func) {
            //            func(gtask);
            //            for (var i = 0; i < gtask.successors.length; i++) {
            //                walkSuccessors(gtask.successors[i], func);
            //            }
            //        }
            //
            //        function pushGtask(currentGtask) {
            //            r.push(currentGtask);
            //        }
            //
            //        walkSuccessors(this, pushGtask);
            //        return r;
            //    }, configurable: true
            //},
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
            "early_finish": {
                get: function () {
                    return this.early_start.add(this.estimate_time);
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
            "last_start": {
                get: function () {
                    return this.last_finish.subtract(this.estimate_time);
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
    console.log('remove glink ', glink_id);
    for (var i = GAUSSPROJECT.glinks.length - 1; i > -1; i--) {
        if (GAUSSPROJECT.glinks[i].pk == glink_id) {
            GAUSSPROJECT.glinks.splice(i, 1);
            GAUSSPROJECT.update_server({action: 'remove_glink', id: glink_id});
        }
    }
    GAUSSPROJECT.redraw_gtasks();
};

GAUSSPROJECT.create_glink = function (orig, dest, dependency) {
    //orig and dest are the pk's of origin and destination gtasks
    //dependency is the type of dependency; by default is FS
    dependency = dependency || 'FS';
    var gtask_dest = queryget(GAUSSPROJECT.gtasks, parseInt(dest));
    var impossible_predecessors = GAUSSPROJECT.get_pks(gtask_dest.impossible_predecessors);
    var impossible_predecessors_length = impossible_predecessors.length;
    var possible = true;
    for (var i = 0; i < impossible_predecessors_length; i++) {
        if (impossible_predecessors[i] == orig) {
            possible = false;
        }
    }
    if (possible) {
        var resp = GAUSSPROJECT.update_server({
            action: 'create_link', dependency: dependency,
            b_id: GAUSSPROJECT.gproject.active_gbaseline.pk, gtask_d: dest, gtask_o: orig
        });
        GAUSSPROJECT.glinks.push(resp[0]);
        GAUSSPROJECT.redraw_gtasks();
    }
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
            var p3 = [p2[0], p1[1] + Math.sign(p_fin[1] - p_ini[1]) * task_height / 2];
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
        GAUSSPROJECT.create_glink(orig, dest, dependency);
        //var no_exists = true;
        //var glinks_length = GAUSSPROJECT.glinks.length;
        //for (var i = 0; i < glinks_length; i++) {
        //    if (GAUSSPROJECT.glinks[i].predecessor === orig && GAUSSPROJECT.glinks[i].successor === dest) {
        //        no_exists = false;
        //    }
        //}
        //var resp = GAUSSPROJECT.update_server({
        //    action: 'create_link', dependency: dependency,
        //    b_id: GAUSSPROJECT.gproject.active_gbaseline.pk, gtask_d: dest, gtask_o: orig
        //});
        //if (no_exists) {
        //    GAUSSPROJECT.glinks.push(resp[0]);
        //    GAUSSPROJECT.redraw_gtasks();
        //}
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
            if (GAUSSPROJECT.gcolumns[i].fields.pos >= new_column_pos) {
                GAUSSPROJECT.gcolumns[i].fields.pos = GAUSSPROJECT.gcolumns[i].fields.pos + 1;
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
                .attr("contenteditable", GAUSSPROJECT.gcolumn_editable[new_column.fields.content])
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
    else if (content == 'early_start_date') {
        return gtask.early_start.format('DD/MM/YYYY');
    }
    else if (content == 'early_start_datetime') {
        return gtask.early_start.format('DD/MM/YYYY HH:mm');
    }
    else if (content == 'last_finish_date') {
        return gtask.last_finish.format('DD/MM/YYYY');
    }
    else if (content == 'last_finish_datetime') {
        return gtask.last_finish.format('DD/MM/YYYY HH:mm');
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

// http://stackoverflow.com/questions/9229645/remove-duplicates-from-javascript-array
function remove_duplicates(a) {
    var seen = {};
    var out = [];
    var len = a.length;
    var j = 0;
    for (var i = 0; i < len; i++) {
        var item = a[i];
        if (seen[item] !== 1) {
            seen[item] = 1;
            out[j++] = item;
        }
    }
    return out;
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




