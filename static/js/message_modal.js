(function () {
  const modalEl = document.getElementById("messageModal");
  if (!modalEl) {
    console.error("messageModal not found. Did you include components/message_modal.html?");
    return;
  }

  const bsModal = new bootstrap.Modal(modalEl);

  const alertEl = document.getElementById("messageModalAlert");
  const projectIdEl = document.getElementById("mmProjectId");
  const customerIdEl = document.getElementById("mmCustomerId");
  const translatorIdEl = document.getElementById("mmTranslatorId");

  const recipientTypeEl = document.getElementById("mmRecipientType");
  const subjectEl = document.getElementById("mmSubject");
  const bodyEl = document.getElementById("mmBody");
  const sendBtn = document.getElementById("mmSendBtn");

  function showAlert(type, text) {
    alertEl.className = `alert alert-${type}`;
    alertEl.textContent = text;
    alertEl.classList.remove("d-none");
  }

  function clearAlert() {
    alertEl.classList.add("d-none");
    alertEl.textContent = "";
  }

  function resolveRecipientUserId() {
    const recipientType = recipientTypeEl.value;
    if (recipientType === "CUSTOMER") return customerIdEl.value;
    if (recipientType === "TRANSLATOR") return translatorIdEl.value;
    return "";
  }

  async function sendEmail() {
    clearAlert();

    const projectId = projectIdEl.value;
    const recipientType = recipientTypeEl.value;
    const recipientUserId = resolveRecipientUserId();
    const subject = (subjectEl.value || "").trim();
    const body = (bodyEl.value || "").trim();

    if (!projectId) return showAlert("danger", "Missing project id.");
    if (!recipientUserId) return showAlert("danger", `Missing ${recipientType.toLowerCase()} id.`);
    if (!subject) return showAlert("warning", "Subject cannot be empty.");
    if (!body) return showAlert("warning", "Message cannot be empty.");

    sendBtn.disabled = true;

    try {
      const res = await fetch("/api/email/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          recipient_type: recipientType,
          recipient_user_id: recipientUserId,
          subject: subject,
          body: body
        })
      });

      const isJson = (res.headers.get("content-type") || "").includes("application/json");
      const data = isJson ? await res.json() : null;

      if (!res.ok) {
        const msg = (data && (data.message || data.error)) || `Failed (${res.status})`;
        showAlert("danger", msg);
        return;
      }

      showAlert("success", "Email sent.");
      bodyEl.value = "";

      setTimeout(() => bsModal.hide(), 600);
    } catch (e) {
      showAlert("danger", `Network error: ${e}`);
    } finally {
      sendBtn.disabled = false;
    }
  }

  sendBtn.addEventListener("click", sendEmail);

  window.openMessageModal = function (projectId, customerId, translatorId) {
    clearAlert();

    projectIdEl.value = projectId || "";
    customerIdEl.value = customerId || "";
    translatorIdEl.value = translatorId || "";

    recipientTypeEl.value = "CUSTOMER";
    subjectEl.value = "Regarding your feedback";
    bodyEl.value = "";

    bsModal.show();
  };
})();
