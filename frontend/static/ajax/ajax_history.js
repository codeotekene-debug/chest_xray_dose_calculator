const historyBody = document.querySelector("[data-history-body]");
const historyError = document.querySelector("[data-history-error]");

if (historyBody) {
    async function loadHistory() {
        if (historyError) {
            historyError.textContent = "";
        }
        historyBody.innerHTML = "<tr><td colspan=\"7\">Loading history...</td></tr>";

        try {
            const response = await fetch("/history_data");
            if (!response.ok) {
                throw new Error("Could not load history.");
            }
            const records = await response.json();
            if (!Array.isArray(records) || records.length === 0) {
                historyBody.innerHTML = "<tr><td colspan=\"7\">No history records found.</td></tr>";
                return;
            }

            historyBody.innerHTML = records
                .map((row) => {
                    const escapedName = String(row.patient_name).replace(/</g, "&lt;").replace(/>/g, "&gt;");
                    const escapedId = String(row.patient_id).replace(/</g, "&lt;").replace(/>/g, "&gt;");
                    return `
                        <tr>
                            <td>${row.created_at}</td>
                            <td>${escapedName}</td>
                            <td>${escapedId}</td>
                            <td>${row.xray_type}</td>
                            <td>${row.esd_mgy}</td>
                            <td>${row.status}</td>
                            <td><a href="/results?id=${row.id}">View</a></td>
                        </tr>
                    `;
                })
                .join("");
        } catch (error) {
            historyBody.innerHTML = "<tr><td colspan=\"7\">Unable to load history.</td></tr>";
            if (historyError) {
                historyError.textContent = error.message;
            }
        }
    }

    loadHistory();
}
