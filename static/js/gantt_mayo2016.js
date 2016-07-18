/**
 * Created by juanjo on 17/04/16.
 * This file requires moment.js (http://momentjs.com/). Thanks to Iskren Ivov Chernev for his pretty work.
 * This file also make use of placeCaretAtEnd function designed by Tim Down:
 * http://stackoverflow.com/users/96100/tim-down
 */


//function init_left_pane(gbaseline) {
//    gbaseline.gcolumns.forEach(function (col, i) {
//        var $header = $("<div/>")
//            .attr("class", "gantt_list_column col" + col.pos)
//            .attr("data-col", col.pos)
//            .attr("data-content", col.content)
//            .attr("id", "col" + col.pos)
//            .css("width", col.width)
//            .html('<b>' + GAUSSPROJECT.gcolumn_types[col.content] + '</b>')
//            .appendTo($('#column_headers'));
//    });
//};
//
//function init_right_pane(gbaseline) {
//    var w = Math.max(800, gbaseline.duration('days') * gbaseline.scale + 100);
//    $("#right-header").css("width", w);
//
//    var d = gbaseline.start_date; //Date that will be increased
//    var e = gbaseline.end_date(); //Limit date for the while statement
//    var ds = 0; //The number of days in a month
//    var m_name = d.format('MMMM'); //Name of the month. Initially the month of start_date
//    while (d.isSameOrBefore(e)) {
//        d.add(1, 'd');
//        if (d.format('MMMM') != m_name) {
//            $("<div class='time_line'></div>").css("width", ds * gbaseline.scale).html(m_name + ' ' + d.format('YYYY')).appendTo($('#tl_months'));
//            ds = 0;
//            m_name = d.format('MMMM');
//        }
//        ds++;
//        $("<div class='time_line'></div>").css("width", gbaseline.scale).html(d.format('DD'))
//            .appendTo($('#tl_days'));
//    }
//    $("<div class='time_line'></div>").css("width", ds * gbaseline.scale).html(m_name + ' ' + d.format('YYYY')).appendTo($("#tl_months"));
//}


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

GAUSSPROJECT.gcolumn_types = {
    estimate_time_days: 'Estimate time (d)',
    early_start_date: 'Early start (date)',
    early_start_datetime: 'Early start (datetime)',
    last_finish_date: 'Last Finish (date)',
    last_finish_datetime: 'Last Finish (datetime)',
    gtask_name: 'Task name'
};

//GAUSSPROJECT.gprojects = [];

GAUSSPROJECT.gproject = function (obj) {
    this.model = obj.model || "gprojects.gproject";
    this.pk = obj.pk || "";
    this.name = obj.fields.name || "";
    this.notes = obj.fields.notes || "";
    this.gbaselines = [];
    this.active_gbaseline = function (gb) {
        for (i = 0; i < this.gbaselines.length; i++) {
            if (this.gbaselines[i].active) {
                var active = this.gbaselines[i]
            }
        }
        var gbaseline = gb || active;
        for (i = 0; i < this.gbaselines.length; i++) {
            if (this.gbaselines[i] == gbaseline) {
                this.gbaselines[i].active = true;
            } else {
                this.gbaselines[i].active = false;
            }
        }
        return gbaseline;
    };

    //GAUSSPROJECT.gprojects.push(this);
    return this;
};


GAUSSPROJECT.gbaseline = function (obj, gproject) {
    this.config = {margin_task: 2, task_height: 22, line_width: 2, link_wrapper_width: 11};
    this.gproject = gproject;
    this.model = obj.model || "gprojects.gbaseline";
    this.pk = obj.pk || "";
    this.name = obj.fields.name || "";
    this.start_date = moment(obj.fields.start_date) || moment();
    this.scale = parseInt(obj.fields.scale) || 24;
    this.columns = parseInt(obj.fields.columns) || 3;
    this.active = obj.fields.active || false;
    this.show_glinks = true;
    this.gtasks = [];
    this.glinks = [];
    this.gcolumns = [];

    this.left_side = function () {
        return 12 - this.columns;
    };
    this.right_side = function () {
        return this.columns;
    };
    this.end_date = function () {
        var end_dates = [moment(this.start_date)];
        var gtasks = this.gtasks;
        for (var i = 0; i < gtasks.length; i++) {
            end_dates.push(gtasks[i].early_start().add(gtasks[i].estimate_time()));
        }
        return moment.max(end_dates);
    };
    this.duration = function (units) {
        //units is a string. It can be: 'days', 'weeks', 'years', 'seconds'
        var d = this.end_date().diff(this.start_date, units)
    };

    //this.remove_glinks = function (gtask) {
    //    var glinks = this.glinks;
    //    for (i = 0; i < this.glinks.length; i++) {
    //        if (this.glinks[i].predecessor.pk == gtask.pk || this.glinks[i].successor.pk == gtask.pk) {
    //            glinks = glinks.filter(function (el) {
    //                return el.pk !== this.glinks[i].pk
    //            }, this)
    //        }
    //    }
    //    this.glinks = glinks;
    //};

    this.update_server = function (obj) {
        $.post("/gantt_ajax/", obj, function (data) {
            return data;
        });
    };


    this.update_gtask = function (pos, new_data) {
        if (new_data.content = 'gtask_name') {
            this.gtasks[pos].name = new_data.name;
            this.update_server({action: 'update_name', pos: pos, value: new_data.name, id: new_data.id});
            return true;
        }
        if (new_data.content = 'estimate_time_days') {
            this.gtasks[pos].optimistic_time = new_data.estimate_time;
            this.gtasks[pos].likely_time = new_data.estimate_time;
            this.gtasks[pos].pessimistic_time = new_data.estimate_time;
            this.update_screen_data(this.gtasks);
        }
        if (new_data.content = 'optimistic_time') {
            this.gtasks[pos].optimistic_time = new_data.optimistic_time;
            this.update_screen_data(this.gtasks);
        }
        if (new_data.content = 'likely_time') {
            this.gtasks[pos].likely_time = new_data.likely_time;
            this.update_screen_data(this.gtasks);
        }
        if (new_data.content = 'pessimistic_time') {
            this.gtasks[pos].pessimistic_time = new_data.pessimistic_time;
            this.update_screen_data(this.gtasks);
        }
        if (new_data.content = 'priority') {
            this.gtasks[pos].priority = new_data.priority;
        }
        if (new_data.content = 'restriction') {
            this.gtasks[pos].restriction = new_data.restriction;
        }
        if (new_data.content = 'restriction_date') {
            this.gtasks[pos].restriction_date = new_data.restriction_date;
        }
        if (new_data.content = 'notes') {
            this.gtasks[pos].notes = new_data.notes;
        }
        if (new_data.content = 'gtask_parent') {
            this.gtasks[pos].gtask_parent = new_data.gtask_parent;
        }
        if (new_data.content = 'display_subtasks') {
            this.gtasks[pos].display_subtasks = new_data.display_subtasks;
        }
    };

    this.remove_gtasks = function (list_gtasks) {
        var new_glinks = [];
        var new_gtasks = [];
        //var affected_gtasks = [];
        //for (var i = 0;i < list_gtasks.length; i++){
        //    affected_gtasks = affected_gtasks.concat(list_gtasks[i].all_successors())
        //}
        var n = 0;
        for (var i = 0; i < this.glinks.length; i++) {
            var glink = this.glinks[i];
            var in_list = $.inArray(glink.successor.pk, list_gtasks) * $.inArray(glink.predecessor.pk, list_gtasks);
            if (in_list > 0) {
                new_glinks.push(glink);
                n = n + 1;
            }
        }
        var n = 0;
        for (var i = 0; i < this.gtasks.length; i++) {
            var gtask = this.gtasks[i];
            if ($.inArray(gtask.pk, list_gtasks) < 0) {
                gtask.pos = n;
                new_gtasks.push(gtask);
                $('#rowr' + gtask.pk).attr('data-pos', n);
                $('#rowl' + gtask.pk).attr('data-pos', n);
                n = n + 1;
            } else {
                $('#rowr' + gtask.pk).remove();
                $('#rowl' + gtask.pk).remove();
            }
        }
        this.gtasks = new_gtasks;
        this.glinks = new_glinks;
        this.update_screen_data(this.gtasks);
    };

    this.init_left_pane = function () {
        this.gcolumns.forEach(function (col, i) {
            var $header = $("<div/>")
                .attr("class", "gantt_list_column col" + col.pos)
                .attr("data-col", col.pos)
                .attr("data-content", col.content)
                .attr("id", "col" + col.pos)
                .css("width", col.width)
                .html('<b>' + GAUSSPROJECT.gcolumn_types[col.content] + '</b>')
                .appendTo($('#column_headers'));
        });
    };

    this.init_right_pane = function () {
        var w = Math.max(800, this.duration('days') * this.scale + 100);
        $("#right-header").css("width", w);

        var d = this.start_date; //Date that will be increased
        var e = this.end_date(); //Limit date for the while statement
        var ds = 0; //The number of days in a month
        var m_name = d.format('MMMM'); //Name of the month. Initially the month of start_date
        while (d.isSameOrBefore(e)) {
            d.add(1, 'd');
            if (d.format('MMMM') != m_name) {
                $("<div class='time_line'></div>")
                    .css("width", ds * this.scale).html(m_name + ' ' + d.format('YYYY')).appendTo($('#tl_months'));
                ds = 0;
                m_name = d.format('MMMM');
            }
            ds++;
            $("<div class='time_line'></div>")
                .css("width", this.scale)
                .html(d.format('DD'))
                .appendTo($('#tl_days'));
        }
        $("<div class='time_line'></div>")
            .css("width", ds * this.scale)
            .html(m_name + ' ' + d.format('YYYY'))
            .appendTo($("#tl_months"));
    };

    this.create_gtask = function (gtask) {
        // From this point, the list of left pane elements are defined
        var gll = parseInt(gtask.left() - 14);
        var glr = parseInt(gtask.left() + gtask.width());
        var $div_row = $("<div/>")
            .attr("class", 'row gtask_row row_info')
            .css("height", '28px')
            .css("margin-left", "0rem")
            .attr("data-id", gtask.pk)
            .attr("data-pos", gtask.pos)
            .attr("data-columns", 'undone')
            .attr("id", "rowl" + gtask.pk);
        var $div_check = $("<div/>")
            .attr("class", "gantt_list_column")
            .css("width", "20px")
            .css("resize", "none")
            .css("cursor", "pointer")
            .css("text-align", "center")
            //.css("background-color", "lightgray")
            //.html(gtask.pos)
            .appendTo($div_row);
        var $check = $("<input/>")
            .attr("type", "checkbox")
            //.attr("id", "check" + gtask.pos)
            .attr("name", "gtasks")
            .attr("value", gtask.pk)
            .attr("class", "check_gtask")
            //.attr("data-pos", gtask.pos)
            .appendTo($div_check);
        this.gcolumns.forEach(function (col, i) {
            var $div_col1 = $("<div/>")
                .attr("class", "gantt_list_column col" + col.pos)
                .attr("data-col", col.pos)
                //.attr("data-pos", gtask.pos)
                .attr("data-id", gtask.pk)
                .attr("data-content", col.content)
                .attr("id", col.content + gtask.pk)
                .attr("contenteditable", "true")
                .css("width", col.width)
                .html(gtask[col.content]())
                .appendTo($div_row);
        });
        $div_row.appendTo($('#task_list'));
        //if (gtask.pos == 0) {
        //    $div_row.appendTo($('#task_list'));
        //} else {
        //    var prev_pos = gtask.pos - 1;
        //    $div_row.insertAfter($('#rowl' + prev_pos));
        //}
        // Until here the list of elements needed to the left pane
        // From this point, the list of right pane elements are defined
        var $bar_side = $("<div/>")
            .attr("class", "gtask_row bar_side")
            .css("height", "28px")
            .attr("data-id", gtask.pk)
            .attr("data-pos", gtask.pos)
            .attr("data-columns", 'undone')
            .attr("id", "rowr" + gtask.pk);
        var $div_bar = $("<div/>")
            .attr("class", "gantt_gtask_bar")
            .attr("data-id", gtask.pk)
            .attr("id", "bar" + gtask.pk)
            .css("margin-left", gtask.left())
            .css("width", gtask.width())
            .css("height", "90%")
            .appendTo($bar_side);
        var div_progress = $("<div/>")
            .attr("class", "gantt_gtask_progress")
            .attr("id", "progress" + gtask.pk)
            .css("width", gtask.width_progress)
            .css("max-width", gtask.width())
            .appendTo($div_bar);
        var div_name = $("<div/>")
            .css("position", "absolute")
            .css("top", 0)
            .css("left", 0)
            .css("z-index", 300)
            .html(gtask.name)
            .appendTo($div_bar);
        var div_gll = $("<div/>")
            .attr("class", "gantt_link")
            .attr("id", "gll" + gtask.pk)
            .attr("data-id", gtask.pk)
            .css("left", gll)
            .appendTo($bar_side);
        var div_glr = $("<div/>")
            .attr("class", "gantt_link")
            .attr("id", "glr" + gtask.pk)
            .attr("data-id", gtask.pk)
            .css("left", glr)
            .appendTo($bar_side);
        $bar_side.appendTo($('#task_bars'));
        //if (gtask.pos == 0) {
        //    $bar_side.appendTo($('#task_bars'));
        //} else {
        //    var prev_pos = gtask.pos - 1;
        //    $bar_side.insertAfter($('#rowr' + prev_pos));
        //}
    };

    this.update_screen_data = function (gtasks) {
        $('.gantt_task_link').remove();
        var gcolumns = this.gcolumns;
        gtasks.forEach(function (gtask) {

            gcolumns.forEach(function (col, i) {
                var $col = $('#col' + col.pos + gtask.pk).html(gtask[col.content]());
            });

            var gll = parseInt(gtask.left() - 14);
            var glr = parseInt(gtask.left() + gtask.width());
            if ($('#bar' + gtask.pk).length > 0) {
                $('#bar' + gtask.pk)
                    .css("margin-left", gtask.left())
                    .css("width", gtask.width());
                $('#gll' + gtask.pk).css("left", gll);
                $('#glr' + gtask.pk).css("left", glr);
            }
        });
        if (this.show_glinks) {
            this.draw_glinks();
        }
    };

    this.draw_glinks = function () {
        var glinks = this.glinks;
        console.log(this.glinks.length);
        var margin_task = this.config.margin_task;
        var task_height = this.config.task_height;
        var line_width = this.config.line_width;
        var link_wrapper_width = this.config.link_wrapper_width;
        var rect0 = $('#task_bars')[0].getBoundingClientRect();
        glinks.forEach(function (l) {
            var predecessor = $('#bar' + l.predecessor.pk)[0];
            var successor = $('#bar' + l.successor.pk)[0];

            var rect1 = predecessor.getBoundingClientRect();
            var rect2 = successor.getBoundingClientRect();
            var p_ini = [parseInt(rect1.right) - parseInt(rect0.left), (parseInt(rect1.top) + parseInt(rect1.bottom) - parseInt(rect0.top) * 2) / 2];
            var p_fin = [parseInt(rect2.left) - parseInt(rect0.left), (parseInt(rect2.top) + parseInt(rect2.bottom) - parseInt(rect0.top) * 2) / 2];

            if (Math.abs(p_ini[0] - p_fin[0]) <= task_height) {
                var p1 = p_ini;
                var p2 = [p1[0] + task_height, p1[1]];
                var p3 = [p2[0], p1[1] + task_height / 2];
                var p4 = [p_fin[0] - task_height, p3[1]];
                var p5 = [p4[0], p_fin[1]];
                var p6 = p_fin;
                var points = [[p1, p2], [p2, p3], [p3, p4], [p4, p5], [p5, p6]];
            }
            else {
                var p1 = p_ini;
                var p2 = [p1[0] + task_height, p1[1]];
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

            if ($('#link' + l.pk).length > 0) {
                var $div_wrapper = $('#link' + l.pk).html('');
            } else {
                var $div_wrapper = $("<div/>")
                    .attr("class", "gantt_task_link")
                    .attr("id", "link" + l.pk)
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

    this.gproject.gbaselines.push(this);
    return this;
};


//GAUSSPROJECT.gproject.gbaseline.remove_gtask = function (gtask_pk, gtask_array, glink_array) {
//    //Removing gtasks from javascript objects and from DOM
//    for (var i = 0; i < gtask_array.length; i++) {
//        if (gtask_array[i].pk == gtask_pk) {
//            gtask_array.splice(i, 1);
//            $('#rowr' + gtask_pk).remove();
//            $('#rowl' + gtask_pk).remove();
//            break;
//        }
//    }
//};

GAUSSPROJECT.gtask = function (obj, gbaseline) {
    this.gbaseline = gbaseline;
    this.model = obj.model || "gprojects.gtask";
    this.pk = obj.pk || "";
    this.name = obj.fields.name || "Nueva tarea";
    this.pos = parseInt(obj.fields.pos) || 0;
    this.optimistic_time = moment.duration(obj.fields.optimistic_time) || moment.duration(1, "days");
    this.likely_time = moment.duration(obj.fields.likely_time) || moment.duration(1, "days");
    this.pessimistic_time = moment.duration(obj.fields.pessimistic_time) || moment.duration(1, "days");
    this.priority = parseInt(obj.fields.priority) || 500;
    this.restriction = obj.fields.restriction || "ASAP";
    this.restriction_date = moment(obj.fields.restriction_date) || null;
    this.progress = parseInt(obj.fields.progress) || 0;
    this.notes = obj.fields.notes || "";
    this.gtask_parent = queryget(this.gbaseline.gtasks, obj.fields.gtask_parent);
    this.display_subtasks = obj.fields.display_subtasks || true;

    this.has_subtasks = function () {
        var child = queryget(this.gbaseline.gtasks, this.pk, 'gtask_parent');
        return !!child;
    };
    this.predecessors = function () {
        var p = [];
        for (var i = 0; i < this.gbaseline.glinks.length; i++) {
            if (this.gbaseline.glinks[i].successor === this) {
                p.push(this.gbaseline.glinks[i].predecessor);
            }
        }
        return p;
    };
    this.successors = function () {
        var s = [];
        for (var i = 0; i < this.gbaseline.glinks.length; i++) {
            if (this.gbaseline.glinks[i].predecessor === this) {
                s.push(this.gbaseline.glinks[i].successor);
            }
        }
        return s;
    };
    this.all_successors = function () {
        var r = [];
        r.push(this);
        s = this.successors();
        for (var k = 0; k < s.length; k++) {
            r = r.concat(s[k].all_successors());
        }
        return r;
    };
    this.estimate_time = function () {
        var o = moment.duration(this.optimistic_time);
        var l = moment.duration(this.likely_time);
        var p = moment.duration(this.pessimistic_time);
        return moment.duration((o + 4 * l + p) / 6);
    };
    this.early_start = function () {
        var tearlys_array = [];
        var ps = this.predecessors();
        for (var k = 0; k < ps.length; k++) {
            tearlys_array.push(ps[k].early_start().add(ps[k].estimate_time()));
        }
        if (tearlys_array.length > 0) {
            return moment.max(tearlys_array);
        } else {
            return moment(this.gbaseline.start_date);
        }
    };
    this.last_finish = function () {
        var tlasts_array = [];
        var ss = this.successors();
        for (var k = 0; k < ss.length; k++) {
            tlasts_array.push(ss[k].last_finish().subtract(ss[k].estimate_time()));
        }
        if (tlasts_array.length > 0) {
            return moment.min(tlasts_array);
        } else {
            return moment(this.gbaseline.end_date());
        }
    };
    this.left = function () {
        var left_delta = this.early_start().diff(this.gbaseline.start_date);
        return parseInt(this.gbaseline.scale * left_delta / 3600 / 24000);
    };
    this.width = function () {
        return parseInt(this.gbaseline.scale * this.estimate_time().asMilliseconds() / 3600 / 24000);
    };
    // The following methods are defined only to show data strings in columns:
    this.estimate_time_days = function () {
        return this.estimate_time().asDays();
    };
    this.early_start_date = function () {
        return this.early_start().format("DD/MM/YYYY");
    };
    this.early_start_datetime = function () {
        return this.early_start().format("DD/MM/YYYY, HH:mm");
    };
    this.last_finish_date = function () {
        return this.last_finish().format("DD/MM/YYYY");
    };
    this.last_finish_datetime = function () {
        return this.last_finish().format("DD/MM/YYYY, HH:mm");
    };
    this.gtask_name = function () {
        return this.name;
    };


    this.gbaseline.gtasks.push(this);
    return this;
};

GAUSSPROJECT.glink = function (obj, gbaseline) {
    this.gbaseline = gbaseline;
    this.model = obj.model || "gprojects.gtask_link";
    this.pk = obj.pk || "";
    this.predecessor = queryget(this.gbaseline.gtasks, obj.fields.predecessor);
    this.successor = queryget(this.gbaseline.gtasks, obj.fields.successor);
    this.dependency = obj.fields.dependency || "FS";

    this.gbaseline.glinks.push(this);
    return this;
};

GAUSSPROJECT.gcolumn = function (obj, gbaseline) {
    this.gbaseline = gbaseline;
    this.model = obj.model || "gprojects.gcolumn";
    this.pk = obj.pk || "";
    this.pos = obj.fields.pos || 0;
    this.width = obj.fields.width || 100;
    this.content = obj.fields.content || 'estimate_time';
    //this.format = obj.fields.format || 'datetime';

    this.gbaseline.gcolumns.push(this);
    return this;
};


GAUSSPROJECT.parse = function (gproject, gbaselines, gtasks, glinks, gcolumns) {
    var gproject = new GAUSSPROJECT.gproject(gproject[0]);
    //for (var i = 0; i < gprojects.length; i++) {
    //    new GAUSSPROJECT.gproject(gprojects[i]);
    //}
    for (var i = 0; i < gbaselines.length; i++) {
        new GAUSSPROJECT.gbaseline(gbaselines[i], gproject);
    }
    var gbaseline = {pk: -1}; //An impossible value is given at the beginning
    for (var i = 0; i < gtasks.length; i++) {
        if (gtasks[i].fields.gbaseline != gbaseline.pk) {
            gbaseline = queryget(gproject.gbaselines, gtasks[i].fields.gbaseline)
        }
        new GAUSSPROJECT.gtask(gtasks[i], gbaseline);
    }
    for (var i = 0; i < glinks.length; i++) {
        if (glinks[i].fields.gbaseline != gbaseline.pk) {
            gbaseline = queryget(gproject.gbaselines, glinks[i].fields.gbaseline)
        }
        new GAUSSPROJECT.glink(glinks[i], gbaseline);
    }
    for (var i = 0; i < gcolumns.length; i++) {
        if (gcolumns[i].fields.gbaseline != gbaseline.pk) {
            gbaseline = queryget(gproject.gbaselines, gcolumns[i].fields.gbaseline)
        }
        new GAUSSPROJECT.gcolumn(gcolumns[i], gbaseline);
    }
    //gbaseline.init_right_pane();
    var w = Math.max(800, this.duration('days') * this.scale + 100);
        $("#right-header").css("width", w);

        var d = this.start_date; //Date that will be increased
        var e = this.end_date(); //Limit date for the while statement
        var ds = 0; //The number of days in a month
        var m_name = d.format('MMMM'); //Name of the month. Initially the month of start_date
        while (d.isSameOrBefore(e)) {
            d.add(1, 'd');
            if (d.format('MMMM') != m_name) {
                $("<div class='time_line'></div>")
                    .css("width", ds * this.scale).html(m_name + ' ' + d.format('YYYY')).appendTo($('#tl_months'));
                ds = 0;
                m_name = d.format('MMMM');
            }
            ds++;
            $("<div class='time_line'></div>")
                .css("width", this.scale)
                .html(d.format('DD'))
                .appendTo($('#tl_days'));
        }
        $("<div class='time_line'></div>")
            .css("width", ds * this.scale)
            .html(m_name + ' ' + d.format('YYYY'))
            .appendTo($("#tl_months"));
    gbaseline.init_left_pane();
    //init_right_pane(gbaseline);
    //init_left_pane(gbaseline);
    for (var i = 0; i < gbaseline.gtasks.length; i++) {
        gbaseline.create_gtask(gbaseline.gtasks[i]);
    }
    gbaseline.draw_glinks(gbaseline.glinks);
    return gproject;
};

GAUSSPROJECT.init_gantt = function (gbaseline) {
    gbaseline.init_left_pane();
    gbaseline.create_gtask(this);
};

//function delete_ducplicates(a) {
//    var uniqueNames = [];
//    $.each(a, function (i, el) {
//        if ($.inArray(el, uniqueNames) === -1) uniqueNames.push(el);
//    });
//}


function placeCaretAtEnd(el, atStart) {
    var atStart = atStart || false;
    el.focus();
    if (typeof window.getSelection != "undefined" && typeof document.createRange != "undefined") {
        var range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(atStart);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    } else if (typeof document.body.createTextRange != "undefined") {
        var textRange = document.body.createTextRange();
        textRange.moveToElementText(el);
        textRange.collapse(atStart);
        textRange.select();
    }
}

function remove_gtask(gtask_pk, gtask_array, glink_array) {
    //Removing gtasks from javascript objects and from DOM
    for (var i = 0; i < gtask_array.length; i++) {
        if (gtask_array[i].pk == gtask_pk) {
            gtask_array.splice(i, 1);
            $('#rowr' + gtask_pk).remove();
            $('#rowl' + gtask_pk).remove();
            break;
        }
    }
}

function removeByProp(array_objects, values, property) {
    property = property || 'pk';
    if (Object.prototype.toString.call(values) != '[object Array]') {
        values = [values];
    }
    var queryset = [];
    if (property == 'pk') {
        for (var i = 0; i < array_objects.length; i++) {
            if ($.inArray(array_objects[i].pk, values) > -1) {
                array_objects.splice(i, 1);
            }
        }
    } else {
        for (var i = 0; i < array_objects.length; i++) {
            if ($.inArray(array_objects[i]['fields'][property], values) > -1) {
                array_objects.splice(i, 1);
            }
        }
    }
    return array_objects
}


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

//function parseDuration(s){
//    // s is a string "4 11:34:25"  (4 days 11 hours 34 minutes 25 seconds)
//    var m = s.match(/\s*,?(\d+)\s*/g);
//    var seconds = parseInt(m[0])*24*3600 + parseInt(m[1])*3600 + parseInt(m[2])*60 + parseInt(m[3]);
//    var hours = seconds/3600;
//    var days = hours / 24;
//    return {seconds: seconds, hours: hours, days:days}
//}


function gproject(gtasks, glinks, gcolumns, gbaseline) {
    this.gtasks = gtasks;
    this.glinks = glinks;
    this.gcolumns = gcolumns;
    this.gbaseline = gbaseline;

    // Properties of the current gbaseline are defined:
    Object.defineProperties(gbaseline[0], {
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
                for (var i = 0; i < gtasks.length; i++) {
                    end_dates.push(gtasks[i].early_start.add(gtasks[i].estimate_time));
                }
                return moment.max(end_dates);
            }, configurable: true
        }
    });

    //All the gtasks are in the loop in order to: 1-define properties, 2-draw then in the page
    for (var n = 0; n < this.gtasks.length; n++) {
        // Properties of the current gtask are defined:
        Object.defineProperties(gtasks[n], {
            "has_subtasks": {
                get: function () {
                    var child = queryget(gtasks, this.pk, 'gtask_parent');
                    return !!child;
                }, configurable: true
            },
            "successors": {
                get: function () {
                    var s = [];
                    for (var i = 0; i < glinks.length; i++) {
                        if (glinks[i].fields.predecessor === this.pk) {
                            s.push(queryget(gtasks, glinks[i].fields.successor));
                        }
                    }
                    return s;
                }, configurable: true
            },
            "predecessors": {
                get: function () {
                    var s = [];
                    for (var i = 0; i < glinks.length; i++) {
                        if (glinks[i].fields.successor === this.pk) {
                            s.push(queryget(gtasks, glinks[i].fields.predecessor));
                        }
                    }
                    return s;
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
                    var o = moment.duration(this.fields.optimistic_time);
                    var l = moment.duration(this.fields.likely_time);
                    var p = moment.duration(this.fields.pessimistic_time);
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
                        return moment(gbaseline[0].fields.start_date);
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
                        return moment(gbaseline[0].end_date);
                    }
                }, configurable: true
            },
            "left": {
                get: function () {
                    var left_delta = this.early_start.diff(gbaseline[0].start_date);
                    return parseInt(gbaseline[0].fields.scale * left_delta / 3600 / 24000);
                }, configurable: true
            },
            "width": {
                get: function () {
                    return parseInt(gbaseline[0].fields.scale * this.estimate_time.asMilliseconds() / 3600 / 24000);
                }, configurable: true
            }
        });
        // At this point properties of the object are finished. It is started the drawing process. First the columns
        // are defined and then the bars are drawn

    }
}


//var p = new gproject(gts, glinks, gcolumns);


function gproject2(gtasks, glinks, columns) {
    this.gtasks = gtasks;
    this.glinks = glinks;
    this.columns = columns;
    for (var n = 0; n < this.gtasks.length; n++) {
        Object.defineProperties(gtasks[n], {
            "has_subtasks": {
                get: function () {
                    for (var i = 0; i < gtasks.length; i++) {
                        if (gtasks[i].fields.gtask_parent === this.pk) {
                            return true;
                        }
                    }
                    return false;
                }
            },
            "successors": {
                get: function () {
                    var s = [];
                    for (var i = 0; i < glinks.length; i++) {
                        if (glinks[i].fields.predecessor === this.pk) {
                            s.push(glinks[i].fields.successor);
                        }
                    }
                    return s;
                }
            },
            "predecessors": {
                get: function () {
                    var s = [];
                    for (var i = 0; i < glinks.length; i++) {
                        if (glinks[i].fields.successor === this.pk) {
                            s.push(glinks[i].fields.predecessor);
                        }
                    }
                    return s;
                }
            },
            //"c": {
            //    set: function (x) {
            //        this.a = x / 2;
            //    }
            //}
        });


        //this.gtasks[n].predecessors = function (gtask_id) {
        //    var p = [];
        //    for (var i = 0; i < this.glinks.length; i++) {
        //        if (this.glinks[i].fields.successor === gtask_id) {
        //            p.push(this.glinks[i].fields.predecessor);
        //        }
        //    }
        //    return p;
        //}
    }
}


function parse_gtasks(gtasks) {
    gtasks.forEach(function (gtask) {
        var gll = parseInt(gtask.left - 14);
        var glr = parseInt(gtask.left + gtask.width);
        if ($('#bar' + gtask.pk).length > 0) {
            $('#bar' + gtask.pk)
                .css("margin-left", gtask.left)
                .css("width", gtask.width);
            $('#gll' + gtask.pk).css("left", gll);
            $('#glr' + gtask.pk).css("left", glr);

        } else {
            // From this point, the list of left pane elements are defined
            var $div_row = $("<div/>")
                .attr("class", 'row gtask_row')
                .css("height", '28px')
                .css("margin-left", "0rem")
                .attr("data-id", gtask.pk)
                .attr("data-pos", gtask.fields.pos)
                .attr("data-columns", 'undone')
                .attr("id", "rowl" + gtask.pk)
                .appendTo($('#task_list'));
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
                //                            .css("vertical-align", "middle")
                .appendTo($div_check);
            var $div_col0 = $("<div/>")
                .attr("class", "col0 gantt_list_column")
                .attr("data-col", "0")
                .attr("data-pos", gtask.fields.pos)
                .attr("data-id", gtask.pk)
                .attr("data-content", 'name')
                .attr("id", "col0" + gtask.fields.pos)
                .attr("contenteditable", "true")
                .css("width", "150px")
                .html(gtask.fields.name)
                .appendTo($div_row);
            jsonGcolumns.forEach(function (col, i) {
                var $div_col1 = $("<div/>")
                    .attr("class", "gantt_list_column col" + col.fields.pos)
                    .attr("data-col", col.fields.pos)
                    .attr("data-pos", gtask.fields.pos)
                    .attr("data-id", gtask.pk)
                    .attr("data-content", col.fields.content)
                    .attr("id", "col" + col.fields.pos + gtask.fields.pos)
                    .attr("contenteditable", "true")
                    .css("width", "100px");
                if (col.fields.format == 'datetime') {
                    $div_col1.html(gtask[col.fields.content].format("DD/MM/YYYY, HH:mm"))
                        .appendTo($div_row);
                } else if (col.fields.format == 'date') {
                    $div_col1.html(gtask[col.fields.content].format("DD/MM/YYYY"))
                        .appendTo($div_row);
                } else if (col.fields.format == 'asDays') {
                    $div_col1.html(gtask[col.fields.content].asDays())
                        .appendTo($div_row);
                } else {
                    $div_col1.html(gtask[col.fields.content])
                        .appendTo($div_row);
                }
            });
            // Until here the list of elements needed to the left pane
            // From this point, the list of right pane elements are defined
            var $div2 = $("<div/>")
                .attr("class", "gtask_row")
                .css("height", "28px")
                .attr("data-id", gtask.pk)
                .attr("data-pos", gtask.fields.pos)
                .attr("data-columns", 'undone')
                .attr("id", "rowr" + gtask.pk)
                .appendTo($('#task_bars'));
            var $div_bar = $("<div/>")
                .attr("class", "gantt_gtask_bar")
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
        }
    });
}

function parse_glinks(glinks) {
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
            var p2 = [p1[0] + task_height, p1[1]];
            var p3 = [p2[0], p1[1] + task_height / 2];
            var p4 = [p_fin[0] - task_height, p3[1]];
            var p5 = [p4[0], p_fin[1]];
            var p6 = p_fin;
            var points = [[p1, p2], [p2, p3], [p3, p4], [p4, p5], [p5, p6]];
        }
        else {
            var p1 = p_ini;
            var p2 = [p1[0] + task_height, p1[1]];
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

        if ($('#link' + l.pk).length > 0) {
            var $div_wrapper = $('#link' + l.pk).html('');
        } else {
            var $div_wrapper = $("<div/>")
                .attr("class", "gantt_task_link")
                .attr("id", "link" + l.pk)
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
}
