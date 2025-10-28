$(document).ready(function() {

    // ✅ 1. Helper to parse selected languages (from visible text or select input)
    const parseLanguages = () => {

        // get selected options if using <select multiple>
        const select = $("#languages");
        if (select.length) {
            return select.val() || []; // returns an array of selected values
        }

        // fallback: parse from text container
        const raw = ($("#selected-languages-text").text() || "").trim();
        if (!raw) return [];
        return raw
            .split(/[,\n;]+/)
            .map(s => s.trim())
            .filter(Boolean);
    };

    // ✅ 2. Show/hide languages section when role changes
    const $languagesContainer = $("#languages-container"); // corrected element reference
    const toggleLanguages = () => {
    
        const role = ($("#id_role").val() || "CUSTOMER").toUpperCase();
        // Show the entire container, not just text
        if ($languagesContainer.length) $languagesContainer.toggle(role === "TRANSLATOR");
    };
    toggleLanguages();
    $("#id_role").on("change", toggleLanguages);

    // ✅ 3. Register form submit
    $("#registerForm").on("submit", function(e) {

        e.preventDefault();

        const role = ($("#id_role").val() || "CUSTOMER").toUpperCase();
        const languages = parseLanguages();

        const userData = {
            name: $("#id_name").val(),
            email: $("#id_email").val(),
            password: $("#id_password").val(),
            role: role
        };

        if (role === "TRANSLATOR") {
            if (!languages.length) {
                alert("Please select at least one language you translate.");
                return;
            }
            userData.languages = languages;
        }

        $.ajax({
            url: "/api/users",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(userData),
            success: function(response) {
                alert("Registration successful!");
                window.location.href = "/auth/login";
            },
            error: function(xhr) {
                // safer error handling
                let msg = "Registration failed";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    msg = xhr.responseJSON.error;
                }
                alert(msg);
            }
        });
    });

    // ✅ 4. Login form submit
    $("#loginForm").on("submit", function(e) {
        e.preventDefault();

        const loginData = {
            // email: $("#email").val(),
            name: $("#id_name").val(),
            password: $("#id_password").val()
        };

        console.log("Login data:", loginData);

        $.ajax({
            url: "/auth/api/login",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(loginData),
            success: function(response) {
                alert("Welcome back!");
                const role = response.role || "CUSTOMER";
                if (role === "TRANSLATOR") {
                    window.location.href = "/api/translator";
                    return;
                } else if (role === "ADMINISTRATOR") {
                    window.location.href = "/api/administrator";
                    return;
                } else {
                    window.location.href = "/api/customer";
                    return;
                }
            },
            error: function(xhr) {
                let msg = "Login failed";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    msg = xhr.responseJSON.error;
                }
                alert(msg);
            }
        });
    });

});
