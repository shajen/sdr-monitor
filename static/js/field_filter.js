$(document).ready(updateFieldsFilter);

function updateField(field) {
    var count = 0;
    $("input[id^=input_][id*='" + field + "']").each(function () {
        if ($(this).is(':checked')) {
            count += 1;
        }
    });
    $("#" + field + "_list_select_count").text(count);
}

function onChange(id) {
    updateField($("#" + id).attr('field-id'));
}

function updateFieldsFilter() {
    $.datetimepicker.setLocale('pl');
    params = new URLSearchParams(window.location.search);
    for (p of params) {
        field = $("#input_" + p[0]);
        field.val(p[1]);
        field.prop("checked", true);
    }
    $("input[id^=input_]").each(function () {
        updateField($(this).attr('field-id'));
        const inputType = $(this).attr('input-type');
        if (inputType == "datetime") {
            $(this).datetimepicker({ format: 'Y-m-d H:i', dayOfWeekStart: 1 });
        }
        else if (inputType == "date") {
            $(this).datetimepicker({ format: 'Y-m-d', dayOfWeekStart: 1, timepicker: false });
        }
        else if (inputType == "duration") {
            $(this).timepicker({
                showSeconds: true,
                showMeridian: false,
                secondStep: 1,
                minuteStep: 1,
                defaultTime: false,
                icons: { up: 'bi bi-chevron-compact-up', down: 'bi bi-chevron-compact-down' }
            });
        }
    });
    $("input[id^=input_][id*='_select_']").change(function () {
        onChange(this.id);
    });
    $("input[id^=input_][id*='_range_']").change(function () {
        onChange(this.id);
    });
}
