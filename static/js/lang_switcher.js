function loadLanguage(lang) {
    fetch(`/static/json/${lang}.json`)
        .then(res => res.json())
        .then(trans => {
            document.querySelectorAll("[data-i18n]").forEach(el => {
                const key = el.getAttribute("data-i18n");
                el.textContent = trans[key] || key;
            });
            localStorage.setItem("lang", lang);
        });
}

document.addEventListener("DOMContentLoaded", () => {
    const saved = localStorage.getItem("lang") || "en";

    const select = document.getElementById("lang-select");
    if (select) select.value = saved;

    loadLanguage(saved);
});
