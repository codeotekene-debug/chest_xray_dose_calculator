document.addEventListener("DOMContentLoaded", function () {
    const authLinks = document.getElementById("auth-links");
    if (!authLinks) {
        return;
    }

    function renderAuthLinks(state) {
        if (state.logged_in) {
            authLinks.innerHTML = `
                <a class="button ghost" href="/logout" id="logout-link">Logout</a>
            `;
            const logoutLink = document.getElementById("logout-link");
            if (logoutLink) {
                logoutLink.addEventListener("click", function (event) {
                    event.preventDefault();
                    fetch("/logout", {
                        method: "POST",
                        headers: {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                    })
                        .then((response) => response.json())
                        .then((json) => {
                            renderAuthLinks(json);
                        })
                        .catch(() => {
                            authLinks.innerHTML = `
                                <a class="button ghost" href="/login">Login</a>
                                <a class="button" href="/register">Register</a>
                            `;
                        });
                });
            }
        } else {
            authLinks.innerHTML = `
                <a class="button ghost" href="/login">Login</a>
                <a class="button" href="/register">Register</a>
            `;
        }
    }

    fetch("/auth_status", {
        method: "GET",
        headers: {
            "Accept": "application/json",
        },
    })
        .then((response) => response.json())
        .then((json) => {
            renderAuthLinks(json);
        })
        .catch(() => {
            authLinks.innerHTML = `
                <a class="button ghost" href="/login">Login</a>
                <a class="button" href="/register">Register</a>
            `;
        });
});
