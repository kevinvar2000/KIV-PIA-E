function toggleLanguages() {
    var role = document.getElementById('id_role').value;
    var langDiv = document.getElementById('languages-container');
    langDiv.style.display = (role === 'translator') ? 'block' : 'none';
}

document.addEventListener("DOMContentLoaded", function() {
    $('#id_languages').selectpicker();

    $('#id_languages').on('changed.bs.select', function () {
    let selected = $(this).find("option:selected").map(function(){ return $(this).text(); }).get();
    document.getElementById("selected-languages-text").textContent = 
        selected.length ? "Selected: " + selected.join(", ") : "";
    });
});