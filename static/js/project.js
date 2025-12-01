async function downloadOriginal(projectId) {
    ajaxDownloadFile(`/api/project/${projectId}/download/original`);
}


async function downloadTranslation(projectId) {
    ajaxDownloadFile(`/api/project/${projectId}/download/translation`);
}


async function ajaxDownloadFile(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json().catch(() => null);
            showAlert("error", error?.error || "Download failed.");
            return;
        }

        const blob = await response.blob();

        let filename = "file";
        const disp = response.headers.get("Content-Disposition");
        if (disp && disp.includes("filename=")) {
            filename = disp.split("filename=")[1].replace(/"/g, "");
        }

        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();

        setTimeout(() => URL.revokeObjectURL(a.href), 200);
    } catch (e) {
        showAlert("error", "Network error during download.");
    }
}


async function uploadTranslatedFile(projectId) {
    const input = document.getElementById(`upload-input-${projectId}`);
    const file = input.files[0];

    if (!file) {
        showAlert("warning", "Please select a file.");
        return;
    }

    // check max file size (10 MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
        showAlert("error", "File exceeds the maximum size of 10 MB.");
        return;
    }

    const formData = new FormData();
    formData.append("translated_file", file);

    const response = await fetch(`/api/project/${projectId}/upload`, {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        showAlert("error", data.error || "Upload failed");
        return;
    }

    showAlert("success", "Translated file uploaded!");

    setTimeout(() => location.reload(), 1200);
}


async function acceptProject(projectId) {
    try {
        const response = await fetch(`/api/project/${projectId}/accept`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"  // optional, backend may ignore
            }
        });

        const data = await response.json();

        if (!response.ok) {
            showAlert("error", data.error || "Failed to accept project.");
            return;
        }

        showAlert("success", data.message || "Project accepted!");

        // Optional: refresh after delay
        setTimeout(() => location.reload(), 1200);

    } catch (err) {
        console.error("Accept error:", err);
        showAlert("error", "Network error.");
    }
}


async function rejectProject(projectId) {
    const feedbackEl = document.getElementById(`feedback-${projectId}`);
    const feedback = feedbackEl.value.trim();

    if (!feedback) {
        showAlert("warning", "Feedback is required.");
        return;
    }

    console.log("Rejecting project with feedback:", feedback);

    const payload = { feedback: feedback };

    try {
        const response = await fetch(`/api/project/${projectId}/reject`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            showAlert("error", data.error || "Failed to reject project.");
            return;
        }

        showAlert("success", data.message || "Project rejected.");

        // Optional reload
        setTimeout(() => location.reload(), 1200);

    } catch (err) {
        console.error("Reject error:", err);
        showAlert("error", "Network error during rejection.");
    }
}


async function closeProject(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}/close`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"  // optional, backend may ignore
            }
        });
        const data = await response.json();
        if (!response.ok) {
            showAlert("error", data.error || "Failed to close project.");
            return;
        }
        showAlert("success", data.message || "Project closed successfully!");

        // Optional: refresh after delay
        setTimeout(() => location.reload(), 1200);
    } catch (err) {
        console.error("Close project error:", err);
        showAlert("error", "Network error while closing project.");
    }
}


async function createProject(event) {
    event.preventDefault(); // stop full reload

    const name = document.getElementById("project_name").value.trim();
    const description = document.getElementById("description").value.trim();
    const language = document.getElementById("id_target_language").value;
    const sourceFile = document.getElementById("source_file").files[0];

    if (!name || !description || !language || !sourceFile) {
        showAlert("warning", "All fields are required.");
        return;
    }

    // check max file size (10 MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    if (sourceFile.size > MAX_FILE_SIZE) {
        showAlert("error", "Source file exceeds the maximum size of 10 MB.");
        return;
    }

    const formData = new FormData();
    formData.append("project_name", name);
    formData.append("description", description);
    formData.append("language", language);
    formData.append("source_file", sourceFile);

    try {
        const response = await fetch("/api/projects", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            showAlert("error", data.error || "Failed to create project.");
            return;
        }

        showAlert("success", data.message || "Project created successfully!");

        // Optional reload after creation
        setTimeout(() => window.location.reload(), 1200);

    } catch (err) {
        console.error("Create project error:", err);
        showAlert("error", "Network error while creating project.");
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("createProjectForm");
    if (form) {
        form.addEventListener("submit", createProject);
    }
});
