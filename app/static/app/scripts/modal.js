var processes = [];
var versions = {};
var software_index = 0;
var version_index = 0;
var versions_changed = false;

function form_control () {
    current_date = new Date();
    current_date_info = [
        current_date.getFullYear(),
        to_double_digits(current_date.getMonth() + 1),
        to_double_digits(current_date.getDate())
    ];
    current_date_str = current_date_info.join('-');

    if (versions_changed) {
        $('#id_software').children('option').remove();
        $('#id_version').children('option').remove();
        versions_changed = false;
    }

    if ($('#id_software').children('option').length == 0) {
        for (var software in versions) {
            $('#id_software').append('<option value="' + software + '">' + software + '</option>');
        }
        $('#id_software').prop('selectedIndex', software_index);
    }

    if (($('#id_version').prop("tagName") == 'SELECT') && ($('#id_version').children('option').length == 0)) {
        for (var i in versions[$('#id_software').val()]) {
            version = versions[$('#id_software').val()][i];
            $('#id_version').append('<option value="' + version + '">' + version + '</option>');
        }
        $('#id_version').prop('selectedIndex', version_index);
    }

    $('#id_software').change(function () {
        software_index = $('#id_software').prop('selectedIndex');
        if ($('#id_version').prop("tagName") == 'SELECT') {
            $('#id_version > option').remove();
            for (var i in versions[$('#id_software').val()]) {
                version = versions[$('#id_software').val()][i];
                $('#id_version').append('<option value="' + version + '">' + version + '</option>');
            }
            version_index = $('#id_version').prop('selectedIndex');
        }
    });

    $('#id_version').change(function () {
        if ($('#id_version').prop("tagName") == 'SELECT') {
            version_index = $('#id_version').prop('selectedIndex');
        }
    });

    [...Array(processes.length)].map((_, i) => {
        var todo_id = '#id_todo_' + String(i + 1);
        var due_date_id = '#id_due_date_' + String(i + 1);

        $(due_date_id).prop('disabled', !processes[i].has_due_date || $(todo_id).val() == 'False');

        $(todo_id).change(function () {
            if (processes[i].has_due_date) {
                $(due_date_id).prop('disabled', $(todo_id).val() == 'False');
                $(due_date_id).val($(todo_id).val() == 'False' ? '' : current_date_str)
            }
        });
    })

    $('form').submit(function () {
        $('.loading').removeClass('hide');
    })
}

$('#modal').on('shown.bs.modal', function (e) {
    software_index = 0;
    version_index = 0;
    if (document.querySelector('#processes')) {
        processes = JSON.parse(document.getElementById('processes').textContent);
    }
    if (document.querySelector('#versions')) {
        versions = JSON.parse(document.getElementById('versions').textContent);
        versions_changed = true;
    }
    form_control();
    $('.loading').addClass('hide');
});

const handle_mutation = (mutations, observer) => {
    mutations.forEach(mutation => {
        form_control();
        $('.loading').addClass('hide');
    });
};
observer = new MutationObserver(handle_mutation);
observer.observe(document.getElementById('modal'), {
    childList: true,
    subtree: true
});
