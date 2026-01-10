// --- Global ---
let currentOperatorId = null;
let currentOperatorName = null;

document.addEventListener('DOMContentLoaded', () => {
    // Session Restore
    if (sessionStorage.getItem('canteen_role')) {
        currentOperatorId = sessionStorage.getItem('canteen_op_id');
        currentOperatorName = sessionStorage.getItem('canteen_op_user');
    }

    // --- Helpers ---
    window.formatDate = function (isoStr) {
        if (!isoStr) return '-';
        // Handle "YYYY-MM-DD HH:mm:ss" or "YYYY-MM-DD"
        try {
            const datePart = isoStr.split(' ')[0];
            const [y, m, d] = datePart.split('-');
            if (!y || !m || !d) return isoStr;
            return `${d}-${m}-${y}`;
        } catch (e) { return isoStr; }
    }

    // --- Page Specific Init ---
    const path = window.location.pathname;
    if (path === '/admin') {
        initAdmin();
    } else if (path === '/operator') {
        initOperator();
    } else if (path === '/' || path.endsWith('login.html')) {
        initLogin();
    }
});

function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}

// --- Login Logic ---
function initLogin() {
    if (!document.getElementById('login-username')) return;

    let loginRole = 'operator';
    window.setLoginRole = function (role) {
        loginRole = role;
        document.getElementById('btn-role-operator').classList.toggle('active', role === 'operator');
        document.getElementById('btn-role-admin').classList.toggle('active', role === 'admin');
    }

    window.handleLogin = async function () {
        const user = document.getElementById('login-username').value;
        const pass = document.getElementById('login-password').value;

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: loginRole, username: user, password: pass })
            });

            if (!res.ok) {
                const text = await res.text();
                alert(`Server Error (${res.status}): ${text.substring(0, 200)}`);
                return;
            }

            const data = await res.json();

            if (data.status === 'success') {
                sessionStorage.setItem('canteen_role', data.role);
                if (data.role === 'operator') {
                    sessionStorage.setItem('canteen_op_id', data.id);
                    sessionStorage.setItem('canteen_op_user', data.username);
                    window.location.href = '/operator';
                } else {
                    window.location.href = '/admin';
                }
            } else {
                alert(data.message);
            }
        } catch (e) {
            console.error(e);
            alert("Client/Network Error: " + e.message);
        }
    }
}

// --- Admin Logic (Global) ---

window.showTab = function (tabId) {
    // Toggle Sections
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active-section'));
    const activeEl = document.getElementById(tabId);
    if (activeEl) activeEl.classList.add('active-section');

    // Toggle Tabs
    document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));
    // Try to find the button that called this
    const btn = document.querySelector(`button[onclick="showTab('${tabId}')"]`);
    if (btn) btn.classList.add('active');

    // Load Data
    if (tabId === 'admin-students') loadStudents();
    if (tabId === 'admin-operators') loadOperators();
    if (tabId === 'admin-staff') loadStaff();
    if (tabId === 'admin-reports') loadReports();
}

window.addStudent = async function () {
    const id = document.getElementById('edit-std-id').value;
    const name = document.getElementById('new-std-name').value;
    const regd_no = document.getElementById('new-std-regd').value;
    const phone = document.getElementById('new-std-phone').value;
    // const status = document.getElementById('new-std-status').value; // Deprecated
    const remaining = document.getElementById('new-std-remaining').value || 0;
    const mode = document.getElementById('new-std-mode').value;
    const branch = document.getElementById('new-std-branch').value || 'General';
    const amount = document.getElementById('new-std-amount').value || 0;

    if (!name) return alert("Enter Student Name");

    try {
        const method = id ? 'PUT' : 'POST';
        const body = {
            name: name,
            regd_no: regd_no,
            phone: phone,

            // payment_status: status,
            remaining_amount: remaining,
            payment_mode: mode,
            dept: branch,
            amount_paid: amount
        };
        if (id) body.id = id;

        const res = await fetch('/api/students', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!res.ok) {
            const errData = await res.json();
            alert("Error: " + (errData.error || errData.message || "Unknown error"));
            return;
        }

        // Reset form
        document.getElementById('edit-std-id').value = '';
        document.getElementById('new-std-name').value = '';
        document.getElementById('new-std-regd').value = '';
        document.getElementById('new-std-phone').value = '';
        document.getElementById('new-std-branch').value = '';
        document.getElementById('new-std-amount').value = '';
        document.getElementById('btn-add-student').textContent = 'Add Student';
        document.getElementById('btn-add-student').classList.remove('warning-btn'); // if we use different color for update

        loadStudents();
    } catch (e) { alert("Error saving student: " + e); }
}

window.editStudent = function (student) {
    // Populate Modal
    document.getElementById('edit-modal-id').value = student.id;
    document.getElementById('edit-modal-name').value = student.name;
    document.getElementById('edit-modal-regd').value = student.regd_no || '';
    document.getElementById('edit-modal-dept').value = student.dept || '';
    document.getElementById('edit-modal-phone').value = student.phone || '';
    document.getElementById('edit-modal-remaining').value = student.remaining_amount || 0;

    // Show Modal
    document.getElementById('edit-modal').classList.remove('hidden');
}

window.submitEditStudent = async function () {
    const id = document.getElementById('edit-modal-id').value;
    const name = document.getElementById('edit-modal-name').value;
    const regd_no = document.getElementById('edit-modal-regd').value;
    const dept = document.getElementById('edit-modal-dept').value;
    const phone = document.getElementById('edit-modal-phone').value;
    const remaining = document.getElementById('edit-modal-remaining').value;

    if (!name) return alert("Name is required");

    try {
        const res = await fetch('/api/students', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: id,
                name: name,
                regd_no: regd_no,
                dept: dept,
                phone: phone,
                remaining_amount: remaining
                // We preserve other fields implicitly in backend or they are not editable here
            })
        });

        if (res.ok) {
            alert("Student Updated Successfully");
            document.getElementById('edit-modal').classList.add('hidden');
            loadStudents();
        } else {
            const err = await res.json();
            alert("Update Failed: " + (err.error || "Unknown Error"));
        }
    } catch (e) {
        alert("Network Error: " + e);
    }
}

window.deleteStudent = async function (id) {
    console.log("Delete Requested for ID:", id);
    if (confirm("Confirm: Delete student ID " + id + "?")) {
        try {
            const res = await fetch(`/api/students?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                // Check if we were editing this one
                if (document.getElementById('edit-std-id').value == id) {
                    // Reset form
                    document.getElementById('edit-std-id').value = '';
                    document.getElementById('btn-add-student').textContent = 'Add Student';
                }
                alert("Success: Student deleted.");
                loadStudents();
            } else {
                const err = await res.text();
                alert("Failed: Server returned " + res.status + "\n" + err);
            }
        } catch (e) {
            console.error(e);
            alert("Network Error during delete: " + e);
        }
    }
}

window.addOperator = async function () {
    const user = document.getElementById('new-op-user').value;
    const pass = document.getElementById('new-op-pass').value;
    if (!user || !pass) return alert("Fill details");

    try {
        await fetch('/api/operators', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        document.getElementById('new-op-user').value = '';
        document.getElementById('new-op-pass').value = '';
        loadOperators();
    } catch (e) { alert("Error adding operator: " + e); }
}

window.deleteOperator = async function (id) {
    if (confirm("Delete Operator ID " + id + "?")) {
        try {
            const res = await fetch(`/api/operators?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                alert("Operator Deleted");
                loadOperators();
            } else {
                alert("Delete Failed");
            }
        } catch (e) { alert("Error deleting operator: " + e); }
    }
}

window.exportCSV = function (type) {
    let url = '/api/export';
    if (type) {
        url += '?type=' + type;
    }
    window.location.href = url;
}

window.updateExcel = async function () {
    try {
        const btn = document.querySelector('button[onclick="updateExcel()"]');
        const originalText = btn.textContent;
        btn.textContent = "Updating...";
        btn.disabled = true;

        const res = await fetch('/api/backup/excel', { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            alert("Success: " + data.message);
        } else {
            alert("Error: " + data.message);
        }
        btn.textContent = originalText;
        btn.disabled = false;
    } catch (e) {
        alert("Network Error: " + e);
    }
}

async function loadStudents() {
    try {
        const res = await fetch('/api/students', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-students-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach((s, index) => {
                // Serialize object for edit function
                const sData = JSON.stringify(s).replace(/"/g, "&quot;");
                tbody.innerHTML += `
                    <tr>
                        <td>${index + 1} (ID: ${s.id})</td>
                        <td>${s.name}</td>
                        <td>${s.regd_no || '-'}</td>
                        <td>${s.phone || '-'}</td>
                        <td>${s.dept || '-'}</td>
                        <td>B:${s.breakfast_count} / L:${s.lunch_count} / D:${s.dinner_count}</td>
                        <td style="color: ${s.remaining_amount > 0 ? 'red' : 'green'}; font-weight: bold;">₹${s.remaining_amount || 0}</td>
                        <td>₹${s.amount_paid || 0}</td>
                        <td>
                            <button onclick="window.editStudent(${sData})" class="primary-btn" style="padding: 5px 10px; font-size: 0.8em;">Edit</button>
                            <button onclick="window.openPayModal(${s.id}, '${s.name}')" class="primary-btn" style="padding: 5px 10px; font-size: 0.8em; background-color: #27ae60; margin-left: 5px;">Pay</button>
                            <button onclick="window.viewStudentReport(${s.id})" class="secondary-btn" style="padding: 5px 10px; font-size: 0.8em; margin-left: 5px;">Report</button>
                            <button onclick="window.deleteStudent(${s.id})" class="danger-btn" style="padding: 5px 10px; font-size: 0.8em; margin-left: 5px;">Delete</button>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Students Fault", e); }
}

async function loadOperators() {
    try {
        const res = await fetch('/api/operators', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-operators-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach(op => {
                tbody.innerHTML += `
                    <tr>
                        <td>${op.id}</td>
                        <td>${op.username}</td>
                        <td><button onclick="window.deleteOperator(${op.id})" class="danger-btn">Delete</button></td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Operators Fault", e); }
}

async function loadReports() {
    try {
        const res = await fetch('/api/reports/meals');
        const stats = await res.json();
        const div = document.getElementById('admin-meal-stats');
        if (div) {
            let html = '<ul>';
            for (const [meal, count] of Object.entries(stats)) {
                if (meal === 'revenue') continue;
                html += `<li><strong>${meal}:</strong> ${count}</li>`;
            }
            html += '</ul>';
            if (stats.revenue !== undefined) {
                html += `<div style="margin-top: 10px; border-top: 1px solid #ddd; padding-top: 5px;">
                            <strong>Total Collection:</strong> <span style="color: green; font-weight: bold; font-size: 1.1em;">₹${stats.revenue}</span>
                         </div>`;
            }
            div.innerHTML = html;
        }
    } catch (e) { console.error("Load Reports Fault", e); }
}

// --- Student Report Logic ---

window.viewStudentReport = async function (id, month = '', year = '', startDate = '', endDate = '') {
    // Store ID for filtering
    if (id) document.getElementById('report-student-id').value = id;
    else id = document.getElementById('report-student-id').value;

    if (!id) return;

    try {
        let url = `/api/reports/student/${id}`;
        // Support both methods or prioritize date range
        let params = [];
        if (startDate || endDate) {
            if (startDate) params.push(`start_date=${startDate}`);
            if (endDate) params.push(`end_date=${endDate}`);
        } else if (month && year) {
            params.push(`month=${month}`);
            params.push(`year=${year}`);
        }

        if (params.length > 0) url += '?' + params.join('&');

        const res = await fetch(url);
        const text = await res.text();

        let data;
        try {
            data = JSON.parse(text);
        } catch (jsonErr) {
            console.error("Server returned non-JSON:", text);
            throw new Error("Server returned invalid data");
        }

        if (!res.ok) {
            alert("Error: " + (data.error || "Failed to load report"));
            return;
        }
        const std = data.student;

        // Populate Meta
        document.getElementById('report-meta').innerHTML = `
            <p><strong>Name:</strong> ${std.name} (${std.regd_no || 'N/A'})</p>
            <p><strong>Remaining (Debt):</strong> <span style="color:red">₹${std.remaining_amount || 0}</span></p>
            <p><strong>Total Paid:</strong> ₹${std.amount_paid || 0}</p>
        `;

        // Populate Summary
        if (data.summary) {
            document.getElementById('report-summary').innerHTML = `
                <div style="flex: 1; text-align: center;"><strong>Breakfast</strong><br>${data.summary.breakfast}</div>
                <div style="flex: 1; text-align: center;"><strong>Lunch</strong><br>${data.summary.lunch}</div>
                <div style="flex: 1; text-align: center;"><strong>Dinner</strong><br>${data.summary.dinner}</div>
                <div style="flex: 1; text-align: center; border-left: 1px solid #ddd;"><strong>Est. Cost</strong><br>₹${data.summary.total_cost}</div>
            `;
        }

        // Populate Meals
        const mealTbody = document.getElementById('report-meals-list');
        mealTbody.innerHTML = '';
        if (data.meals.length === 0) {
            mealTbody.innerHTML = '<tr><td colspan="4">No meals recorded.</td></tr>';
        } else {
            data.meals.forEach(m => {
                const bBtn = m.breakfast ? `Yes <button onclick="window.deleteMeal(${std.id}, '${m.date}', 'breakfast')" class="danger-btn" style="padding: 0 4px; font-size: 0.7em;">&times;</button>` : '-';
                const lBtn = m.lunch ? `Yes <button onclick="window.deleteMeal(${std.id}, '${m.date}', 'lunch')" class="danger-btn" style="padding: 0 4px; font-size: 0.7em;">&times;</button>` : '-';
                const dBtn = m.dinner ? `Yes <button onclick="window.deleteMeal(${std.id}, '${m.date}', 'dinner')" class="danger-btn" style="padding: 0 4px; font-size: 0.7em;">&times;</button>` : '-';

                mealTbody.innerHTML += `
                    <tr>
                        <td>${formatDate(m.date)}</td>
                        <td>${bBtn}</td>
                        <td>${lBtn}</td>
                        <td>${dBtn}</td>
                    </tr>
                `;
            });
        }

        // Populate Money
        const moneyTbody = document.getElementById('report-money-list');
        moneyTbody.innerHTML = '';
        if (data.transactions.length === 0) {
            moneyTbody.innerHTML = '<tr><td colspan="6">No transactions found.</td></tr>';
        } else {
            // Header needs update to support mixed types? 
            // Current header: Date | Bill No | Item | Amount | Mode
            // For Payment: Date | - | Fee Payment | Amount | Mode
            data.transactions.forEach(t => {
                const isPay = t.type === 'Payment';
                const canDelete = t.id !== undefined;

                moneyTbody.innerHTML += `
                    <tr style="background-color: ${isPay ? '#e8f8f5' : 'inherit'}">
                        <td>${formatDate(t.date)}</td>
                        <td>${t.type === 'Food' ? '#' : ''}</td>
                        <td>${t.item}</td>
                        <td style="color: ${t.color}; font-weight: bold;">₹${t.amount}</td>
                        <td>${t.mode}</td>
                        <td>
                            ${canDelete ? `<button onclick="window.deleteTransaction(${t.id}, ${id})" class="danger-btn" style="padding: 2px 8px; font-size: 0.8em;">&times;</button>` : ''}
                        </td>
                    </tr>
                `;
            });
        }

        // Show Modal
        document.getElementById('report-modal').classList.remove('hidden');

    } catch (e) {
        console.error(e);
        // Try to show more details if it's not just a generic fetch error
        alert("Report Error: " + e.message + "\nCheck console for details.");
    }
}

// Open Filter Modal
window.openFilterModal = function () {
    document.getElementById('filter-modal').classList.remove('hidden');
}

// Apply Filter from Modal
window.applyFilter = function () {
    const start = document.getElementById('filter-start-date').value;
    const end = document.getElementById('filter-end-date').value;

    if (start && end && start > end) {
        return alert("Start Date must be before End Date");
    }

    document.getElementById('filter-modal').classList.add('hidden');
    viewStudentReport(null, '', '', start, end);
}

// Clear Filter
window.clearFilter = function () {
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    document.getElementById('filter-modal').classList.add('hidden');
    viewStudentReport(null);
}

window.openPayModal = function (id, name) {
    document.getElementById('pay-student-id').value = id;
    document.getElementById('pay-student-name').textContent = "Paying for: " + name;
    document.getElementById('pay-amount').value = '';
    document.getElementById('pay-modal').classList.remove('hidden');
    document.getElementById('pay-amount').focus();
}

window.deleteTransaction = async function (txId, studentId) {
    if (confirm("Are you sure you want to delete/undo this transaction?")) {
        try {
            const res = await fetch(`/api/transactions?id=${txId}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status === 'success') {
                alert("Transaction Reversed.");
                viewStudentReport(studentId); // Reload report
                loadStudents(); // Reload background list
            } else {
                alert("Error: " + data.error);
            }
        } catch (e) {
            alert("Network Error: " + e);
        }
    }
}

window.deleteMeal = async function (sId, date, type) {
    if (confirm(`Remove ${type} for ${date}?\nThis will remove the transaction if found, or just clear the record.`)) {
        try {
            const res = await fetch(`/api/meals?student_id=${sId}&date=${date}&type=${type}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status === 'success') {
                // Refresh
                viewStudentReport(sId);
                loadStudents();
            } else {
                alert("Error: " + data.error);
            }
        } catch (e) { alert("Network Error: " + e); }
    }
}

window.resetStudentHistory = async function () {
    const sId = document.getElementById('report-student-id').value;
    if (!sId) return;

    if (confirm("DANGER: This will delete ALL meals and transactions for this student and reset their balance to 0.\n\nAre you sure exactly?")) {
        if (confirm("Double Check: This cannot be undone.")) {
            try {
                const res = await fetch('/api/students/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_id: sId })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    alert("History Cleared.");
                    viewStudentReport(sId);
                    loadStudents();
                } else {
                    alert("Error: " + data.error);
                }
            } catch (e) { alert("Network Error: " + e); }
        }
    }
}

window.submitPayment = async function () {
    const id = document.getElementById('pay-student-id').value;
    const amount = document.getElementById('pay-amount').value;
    const mode = document.getElementById('pay-mode').value;

    if (!amount || amount <= 0) return alert("Enter valid amount");

    try {
        const res = await fetch('/api/students/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: id, amount: amount, mode: mode })
        });

        const data = await res.json();
        if (data.status === 'success') {
            alert("Payment Successful!");
            document.getElementById('pay-modal').classList.add('hidden');
            loadStudents(); // Refresh table
        } else {
            alert("Error: " + data.error);
        }
    } catch (e) {
        alert("Network Error: " + e);
    }
}

function initAdmin() {
    // Guard
    if (sessionStorage.getItem('canteen_role') !== 'admin') {
        window.location.href = '/';
        return;
    }
    // Load initial
    showTab('admin-students');

    // Search Listener
    const searchInput = document.getElementById('admin-student-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#admin-students-list tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }

    // Enter Key Listener for Add Student
    const inputs = document.querySelectorAll('#new-std-name, #new-std-regd, #new-std-branch, #new-std-amount, #new-std-remaining, #new-std-mode');
    console.log("Attached Enter Listener to " + inputs.length + " inputs");

    inputs.forEach(input => {
        input.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                console.log("Enter pressed in " + input.id);
                addStudent();
            }
        });
    });
}


// --- Operator Logic ---
function initOperator() {
    if (sessionStorage.getItem('canteen_role') !== 'operator') {
        window.location.href = '/';
        return;
    }

    const opName = sessionStorage.getItem('canteen_op_user');
    if (opName && document.getElementById('op-username-display')) {
        document.getElementById('op-username-display').textContent = opName;
    }

    loadOperatorData();

    // Event Listeners for search
    const searchInput = document.getElementById('bill-student-search');
    if (searchInput) {
        searchInput.addEventListener('change', handleStudentSearch);
        searchInput.addEventListener('input', handleStudentSearch);
    }

    // Initialize UI State (ensure correct visibility for default selection)
    toggleUserType();
}
// (Functions for operator like generateBill kept global or attached to window if needed, or defined here)
// Currently initOperator logic was defining them on window. Let's make them global to be safe.

window.toggleUserType = function () {
    const type = document.querySelector('input[name="userType"]:checked').value;

    // Toggle Inputs
    const h = document.getElementById('input-hostel'); if (h) h.classList.toggle('hidden', type !== 'hostel');
    const s = document.getElementById('input-staff'); if (s) s.classList.toggle('hidden', type !== 'staff');
    const n = document.getElementById('input-normal'); if (n) n.classList.toggle('hidden', type !== 'normal');

    // Toggle Amount Section visibility
    const amtGrp = document.getElementById('grp-amount');
    if (amtGrp) amtGrp.classList.toggle('hidden', type === 'hostel' || type === 'staff');

    // Reset Meals to single default (Breakfast) to avoid confusion when switching
    // active classes
    document.querySelectorAll('#opt-meal-type .option-btn').forEach(b => b.classList.remove('active'));
    const defBtn = document.querySelector('#opt-meal-type button[data-value="Breakfast"]');
    if (defBtn) defBtn.classList.add('active');
    document.getElementById('bill-meal-type').value = 'Breakfast';

    // Toggle Payment Options & Amount Readonly
    const accBtn = document.querySelector('button[data-value="Account"]');
    const cashBtn = document.querySelector('button[data-value="Cash"]');
    const upiBtn = document.querySelector('button[data-value="UPI"]');
    const amtInput = document.getElementById('bill-amount');

    if (type === 'hostel') {
        // Hostel: Account Only, Auto Price
        if (accBtn) { accBtn.parentElement.style.display = ''; accBtn.style.display = 'inline-block'; accBtn.click(); }
        if (cashBtn) cashBtn.style.display = 'none';
        if (upiBtn) upiBtn.style.display = 'none';

        // Lock Amount
        if (amtInput) amtInput.readOnly = true;
        recalculateHostelTotal();

    } else if (type === 'staff') {
        // Staff: Account Only (Modified Request)
        if (accBtn) { accBtn.parentElement.style.display = ''; accBtn.style.display = 'inline-block'; accBtn.click(); }
        if (cashBtn) cashBtn.style.display = 'none';
        if (upiBtn) upiBtn.style.display = 'none';

        // Lock Amount and Calc
        if (amtInput) amtInput.readOnly = true;
        recalculateHostelTotal();

    } else {
        // Others: Cash/UPI Only, Manual Price
        if (accBtn) accBtn.style.display = 'none';
        if (cashBtn) { cashBtn.style.display = 'inline-block'; cashBtn.click(); }
        if (upiBtn) upiBtn.style.display = 'inline-block';

        // Unlock Amount
        if (amtInput) amtInput.readOnly = false;
        selectAmount(50, document.querySelector('#opt-amount button[onclick*="50"]')); // Default 50
    }
}

window.selectMeal = function (meal, btn) {
    const userType = document.querySelector('input[name="userType"]:checked').value;
    const isHostel = userType === 'hostel';

    if (isHostel) {
        // Multi-Select Logic
        btn.classList.toggle('active');

        // Update hidden input (comma joined)
        const activeBtns = document.querySelectorAll('#opt-meal-type .option-btn.active');
        const selected = Array.from(activeBtns).map(b => b.getAttribute('data-value'));

        // If nothing selected, force select the clicked one back (at least one needed)
        if (selected.length === 0) {
            btn.classList.add('active');
            selected.push(meal);
        }

        document.getElementById('bill-meal-type').value = selected.join(',');
        recalculateHostelTotal();

    } else {
        // Single Select Logic
        document.querySelectorAll('#opt-meal-type .option-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('bill-meal-type').value = meal;
        // If Staff, update price
        if (userType === 'staff') recalculateHostelTotal();
    }
}

function recalculateHostelTotal() {
    // Pricing: Breakfast=20, Lunch=40, Dinner=40
    const activeBtns = document.querySelectorAll('#opt-meal-type .option-btn.active');
    let total = 0;
    activeBtns.forEach(btn => {
        const m = btn.getAttribute('data-value');
        if (m === 'Breakfast') total += 20;
        else if (m === 'Lunch') total += 40;
        else if (m === 'Dinner') total += 40;
    });
    document.getElementById('bill-amount').value = total;
}

window.generateBill = async function () {
    const userType = document.querySelector('input[name="userType"]:checked').value;
    // For manual types, amount is total; for hostel, amount is calculated per meal.
    // However, the backend expects a single amount per bill.
    // So for Hostel Multi-Meal, we must generate MULTIPLE bills.

    const mealRaw = document.getElementById('bill-meal-type').value; // "Breakfast,Lunch"
    const meals = mealRaw.split(',');

    // Validate inputs
    let studentId = null;
    let guestName = null;
    let mode = document.getElementById('bill-payment-mode').value;

    if (userType === 'hostel') {
        studentId = document.getElementById('bill-student-id').value;
        const val = document.getElementById('bill-student-search').value;
        if (!studentId && val) {
            const match = val.match(/\[ID: (\d+)\]/);
            if (match) studentId = match[1];
        }
        // Extract Name for Receipt
        if (val) {
            const nameMatch = val.match(/^(.*?) \(/);
            if (nameMatch) guestName = nameMatch[1];
        }
        if (!studentId) return alert("Select a valid student.");

    } else if (userType === 'staff') {
        const val = document.getElementById('bill-staff-search').value;
        if (!val) return alert("Select a Staff member.");

        const match = val.match(/\[ID: (\d+)\]/);
        if (match) {
            studentId = match[1];
            const nameMatch = val.match(/^(.*?) \(/);
            if (nameMatch) guestName = nameMatch[1];
        } else {
            return alert("Select valid Staff from list");
        }
    } else {
        guestName = document.getElementById('bill-guest-name').value || "Guest";
    }

    // Processing Loop
    // For non-hostel, it's just one meal (length 1). Amount is manual.
    // For hostel, it can be multiple. Amount matches meal type.

    const manualAmount = parseFloat(document.getElementById('bill-amount').value);

    try {
        for (const meal of meals) {
            let amount = manualAmount;

            // Override Amount for Hostel (Per Meal)
            if (userType === 'hostel') {
                if (meal === 'Breakfast') amount = 20;
                else if (meal === 'Lunch') amount = 40;
                else if (meal === 'Dinner') amount = 40;
            }

            // 1. Create Bill in Backend
            const res = await fetch('/api/bill', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_type: userType,
                    student_id: studentId,
                    guest_name: guestName,
                    meal_type: meal,
                    amount: amount,
                    payment_mode: mode,
                    operator_id: currentOperatorId
                })
            });

            const data = await res.json();
            if (data.status !== 'success') {
                alert(`Error creating bill for ${meal}: ${data.message}`);
                continue;
            }

            // 2. Silent Print
            // Construct Payload for Python Service
            const now = new Date();
            const dateStr = `${String(now.getDate()).padStart(2, '0')}/${String(now.getMonth() + 1).padStart(2, '0')}/${String(now.getFullYear()).slice(-2)}`;

            const printPayload = {
                bill_no: data.bill_no,
                date: dateStr,
                operator: currentOperatorName || 'Staff',
                customer: {
                    name: guestName,
                    type: userType,
                    id: studentId
                },
                items: [
                    { name: meal, qty: 1, price: amount }
                ],
                total: amount
            };

            try {
                await fetch('http://localhost:5001/print', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(printPayload)
                });
            } catch (printErr) {
                console.error("Silent Print Failed:", printErr);
                alert("Bill Saved, but Printer Service Unreachable!\nMake sure 'python print_service.py' is running.");
            }
        }

        // Success feedback messages (accumulated above if loop alerts, but here for general success)

        // Clear inputs
        if (userType === 'normal') document.getElementById('bill-guest-name').value = '';
        if (userType === 'staff') document.getElementById('bill-staff-search').value = '';
        if (userType === 'hostel') {
            document.getElementById('bill-student-search').value = '';
            document.getElementById('bill-student-id').value = '';
            // Reset to default breakfast cleanly
            document.querySelectorAll('#opt-meal-type .option-btn').forEach(b => b.classList.remove('active'));
            const defBtn = document.querySelector('#opt-meal-type button[data-value="Breakfast"]');
            if (defBtn) defBtn.classList.add('active');
            document.getElementById('bill-meal-type').value = 'Breakfast';
            recalculateHostelTotal();
        }

        loadLiveStats();
        // Feedback
        const statusDiv = document.createElement('div');
        statusDiv.textContent = "✔ Done";
        statusDiv.style.cssText = "position: fixed; top: 20px; right: 20px; background: #2ecc71; color: white; padding: 15px; border-radius: 5px; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);";
        document.body.appendChild(statusDiv);
        setTimeout(() => statusDiv.remove(), 2000);

    } catch (e) { console.error(e); alert("Network Error during billing"); }
}

async function loadOperatorData() {
    try {
        // Load Students
        const res = await fetch('/api/students');
        const data = await res.json();
        const datalist = document.getElementById('student-list');
        if (datalist) {
            datalist.innerHTML = '';
            data.forEach(s => {
                const opt = document.createElement('option');
                // Improved format: Name (Regd: X) [ID: Y]
                const regdStr = s.regd_no ? `Regd: ${s.regd_no}` : 'No Regd';
                opt.value = `${s.name} (${regdStr}) [ID: ${s.id}]`;
                datalist.appendChild(opt);
            });
        }

        // Load Staff (New)
        const resStaff = await fetch('/api/staff');
        const staffData = await resStaff.json();
        const staffList = document.getElementById('staff-list');
        if (staffList) {
            staffList.innerHTML = '';
            staffData.forEach(s => {
                const opt = document.createElement('option');
                opt.value = `${s.name} (${s.dept || 'Staff'}) [ID: ${s.id}]`;
                staffList.appendChild(opt);
            });
        }
        loadLiveStats();
    } catch (e) { console.error("Load Op Data Error", e); }
}

function handleStudentSearch(e) {
    const val = e.target.value;
    // Match [ID: 123]
    const match = val.match(/\[ID: (\d+)\]/);
    if (match) {
        document.getElementById('bill-student-id').value = match[1];
    } else {
        document.getElementById('bill-student-id').value = '';
    }
}

async function loadLiveStats() {
    try {
        const res = await fetch('/api/reports/meals');
        const stats = await res.json();
        const div = document.getElementById('op-meal-stats');
        if (div) {
            let html = '';
            for (const [meal, count] of Object.entries(stats)) {
                if (meal === 'revenue') continue;
                html += `<div>${meal}: ${count}</div>`;
            }
            if (stats.revenue !== undefined) {
                html += `<div style="margin-top: 10px; border-top: 1px solid #ccc; padding-top: 5px; font-weight: bold;">
                            Total: <span style="color: #2ecc71;">₹${stats.revenue}</span>
                          </div>`;
            }
            div.innerHTML = html || 'No meals served.';
        }
    } catch (e) { console.error("Stats Error", e); }
}

window.selectOption = function (inputId, value, btnElement) {
    // defined global to be accessible from onclick
    document.getElementById(inputId).value = value;

    // Toggle active class on buttons in the same group
    const group = btnElement.parentElement;
    const buttons = group.querySelectorAll('.option-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');
}

window.selectAmount = function (value, btnElement) {
    const input = document.getElementById('bill-amount');

    // Toggle active class
    const group = btnElement.parentElement;
    const buttons = group.querySelectorAll('.option-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');

    if (value === 'other') {
        input.focus();
        // If user types, we keep "Other" selected visually
    } else {
        input.value = value;
    }
}

// --- Operator Logic (Extras) ---
window.showOpSection = function (sectionId) {
    // Hide all first
    document.getElementById('sec-billing').classList.add('hidden-section');
    document.getElementById('sec-billing').classList.remove('active-section');
    document.getElementById('sec-payment').classList.add('hidden-section');
    document.getElementById('sec-payment').classList.remove('active-section');

    // Reset Buttons
    document.getElementById('btn-sec-billing').classList.remove('active');
    document.getElementById('btn-sec-payment').classList.remove('active');

    if (sectionId === 'billing') {
        document.getElementById('sec-billing').classList.remove('hidden-section');
        document.getElementById('sec-billing').classList.add('active-section');
        document.getElementById('btn-sec-billing').classList.add('active');
    } else if (sectionId === 'payment') {
        document.getElementById('sec-payment').classList.remove('hidden-section');
        document.getElementById('sec-payment').classList.add('active-section');
        document.getElementById('btn-sec-payment').classList.add('active');
    }
}

window.initiateOpPayment = function () {
    const val = document.getElementById('pay-student-search').value;
    const match = val.match(/\[ID: (\d+)\]/);

    if (!match) return alert("Please search and select a student first.");

    const id = match[1];
    const nameMatch = val.match(/^(.*?) \(/);
    const name = nameMatch ? nameMatch[1] : "Unknown";

    document.getElementById('op-pay-student-id').value = id;
    document.getElementById('op-pay-student-name').textContent = "Student: " + name;
    document.getElementById('op-pay-amount').value = '';

    document.getElementById('op-pay-modal').classList.remove('hidden');
    document.getElementById('op-pay-amount').focus();
}

window.submitOpPayment = async function () {
    const id = document.getElementById('op-pay-student-id').value;
    const amount = document.getElementById('op-pay-amount').value;
    const mode = document.getElementById('op-pay-mode').value;

    if (!amount || amount <= 0) return alert("Enter valid amount");

    try {
        const res = await fetch('/api/students/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: id,
                amount: amount,
                mode: mode,
                operator_id: sessionStorage.getItem('canteen_op_id')
            })
        });

        const data = await res.json();
        if (data.status === 'success') {
            alert("Payment Successful");
            document.getElementById('op-pay-modal').classList.add('hidden');
            document.getElementById('pay-student-search').value = '';
        } else {
            alert("Error: " + data.error);
        }
    } catch (e) { alert("Network Error: " + e); }
}

// --- Staff Logic ---
window.loadStaff = async function () {
    try {
        const res = await fetch('/api/staff', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-staff-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach(s => {
                const sData = JSON.stringify(s).replace(/"/g, "&quot;");
                const balanceColor = s.balance > 0 ? 'red' : 'green';
                tbody.innerHTML += `
                    <tr>
                        <td>${s.name}</td>
                        <td>${s.dept || '-'}</td>
                        <td>${s.phone || '-'}</td>
                        <td style="color:${balanceColor}; font-weight:bold;">₹${s.balance || 0}</td>
                        <td style="color:${balanceColor}; font-weight:bold;">₹${s.balance || 0}</td>
                        <td>
                            <button onclick="window.viewStaffReport(${s.id})" class="secondary-btn" style="padding: 5px 10px; font-size: 0.8em; margin-right: 5px;">Report</button>
                            <button onclick="window.deleteStaff(${s.id})" class="danger-btn">Delete</button>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Staff Error", e); }
}

window.addStaff = async function () {
    const name = document.getElementById('new-staff-name').value;
    const dept = document.getElementById('new-staff-dept').value;
    const phone = document.getElementById('new-staff-phone').value;

    if (!name) return alert("Staff Name is required");

    try {
        const res = await fetch('/api/staff', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, dept, phone })
        });
        if (res.ok) {
            document.getElementById('new-staff-name').value = '';
            document.getElementById('new-staff-dept').value = '';
            document.getElementById('new-staff-phone').value = '';
            loadStaff();
            alert("Staff Added Successfully");
        } else {
            alert("Error adding staff");
        }
    } catch (e) { alert("Network Error: " + e); }
}

window.deleteStaff = async function (id) {
    if (confirm("Delete this staff member? This will remove their history.")) {
        try {
            const res = await fetch(`/api/staff?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                loadStaff();
            } else {
                alert("Failed to delete staff");
            }
        } catch (e) { alert("Error: " + e); }
    }
}

window.viewStaffReport = async function (id) {
    try {
        const res = await fetch(`/api/reports/staff/${id}`);
        const data = await res.json();

        if (data.error) return alert(data.error);

        const s = data.staff;
        const txs = data.transactions;

        // Populate Meta
        document.getElementById('staff-report-meta').innerHTML = `
            <p><strong>Name:</strong> ${s.name} (${s.dept || 'Staff'})</p>
            <p><strong>Balance (Due):</strong> <span style="color:${s.balance > 0 ? 'red' : 'green'}">₹${s.balance}</span></p>
            <p><strong>Total Food:</strong> ₹${s.total_food} | <strong>Paid:</strong> ₹${s.total_paid}</p>
        `;

        const tbody = document.getElementById('staff-report-list');
        tbody.innerHTML = '';

        if (txs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No transactions found.</td></tr>';
        } else {
            txs.forEach(t => {
                const isPay = t.type === 'Payment';
                tbody.innerHTML += `
                    <tr style="background-color: ${isPay ? '#e8f8f5' : 'inherit'}">
                        <td>${t.date ? t.date.split(' ')[0] : '-'}</td>
                        <td>${t.type}</td>
                        <td style="font-weight:bold; color:${isPay ? 'green' : 'red'}">₹${t.amount}</td>
                        <td>${t.mode || '-'}</td>
                        <td>${t.remarks || '-'}</td>
                    </tr>
                `;
            });
        }

        document.getElementById('staff-report-modal').classList.remove('hidden');

    } catch (e) {
        console.error(e);
        alert("Error loading staff report: " + e);
    }
}

// --- Monthly Report Logic ---
let currentMonthlyData = [];

window.viewMonthlyReport = async function () {
    const month = document.getElementById('report-month').value;
    const year = document.getElementById('report-year').value;
    const start = document.getElementById('report-start-date').value;
    const end = document.getElementById('report-end-date').value;

    let queryParams = '';
    let reportTitle = '';

    if (start && end) {
        if (start > end) return alert("Start Date cannot be after End Date");
        queryParams = `start_date=${start}&end_date=${end}`;
        reportTitle = `Report: ${formatDate(start)} to ${formatDate(end)}`;
    } else {
        if (!year) return alert("Enter Year or Date Range");
        queryParams = `month=${month}&year=${year}`;
        reportTitle = `Monthly Report: ${month}/${year}`;
    }

    try {
        const btn = document.querySelector('button[onclick="viewMonthlyReport()"]');
        if (btn) { btn.textContent = "Loading..."; btn.disabled = true; }

        const res = await fetch(`/api/reports/monthly?${queryParams}`);
        const data = await res.json();

        if (btn) { btn.textContent = "View Report"; btn.disabled = false; }

        if (res.ok) {
            currentMonthlyData = data;
            const tbody = document.getElementById('monthly-report-list');
            if (tbody) {
                tbody.innerHTML = '';

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6">No data found for this period.</td></tr>';
                } else {
                    let totalBill = 0;
                    data.forEach(r => {
                        totalBill += r.total_cost;
                        tbody.innerHTML += `
                            <tr>
                                <td>${r.name}</td>
                                <td>${r.regd_no || '-'}</td>
                                <td>${r.breakfast}</td>
                                <td>${r.lunch}</td>
                                <td>${r.dinner}</td>
                                <td style="font-weight:bold;">₹${r.total_cost}</td>
                            </tr>
                        `;
                    });
                    // Total Row
                    tbody.innerHTML += `
                        <tr style="background-color: #f0f0f0; font-weight: bold;">
                            <td colspan="5" style="text-align: right;">Total For Period:</td>
                            <td>₹${totalBill}</td>
                        </tr>
                    `;
                }
            }

            document.getElementById('monthly-report-title').textContent = reportTitle;
            document.getElementById('monthly-report-modal').classList.remove('hidden');
        } else {
            alert("Error: " + data.error);
        }
    } catch (e) {
        alert("Network Error: " + e);
        const btn = document.querySelector('button[onclick="viewMonthlyReport()"]');
        if (btn) btn.disabled = false;
    }
}

window.exportMonthlyCSV = function () {
    if (!currentMonthlyData || currentMonthlyData.length === 0) return alert("No data to export");

    let csv = "Name,Regd No,Breakfast,Lunch,Dinner,Total Cost\n";
    currentMonthlyData.forEach(r => {
        csv += `"${r.name}","${r.regd_no}",${r.breakfast},${r.lunch},${r.dinner},${r.total_cost}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `monthly_report.csv`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
window.checkAndShowReport = function (inputId) {
    const val = document.getElementById(inputId).value;
    const match = val.match(/\[ID: (\d+)\]/);
    if (match) {
        viewStudentReport(match[1]);
    } else {
        alert("Please select a student/staff first.");
    }
}
