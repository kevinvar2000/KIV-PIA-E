function showAlert(type, text) {
    const container = document.getElementById("alert-container-js");
    const template = document.getElementById("alert-template");

    // Clone the template
    const alertEl = template.content.firstElementChild.cloneNode(true);

    // if error in type, change to danger for bootstrap
    if (type === "error") type = "danger";

    // Set alert type (bootstrap class)
    alertEl.classList.add(`alert-${type}`);

    // Set text
    alertEl.querySelector(".alert-text").textContent = text;

    // Append to container
    container.appendChild(alertEl);
}